"""Virtual office server: Entra login, WebSocket game channel, static files. Glue only."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

from aiohttp import WSMsgType, web

from office import catalog, mapdata, session
from office.access import AccessStore
from office.world import World

HERE = Path(__file__).resolve().parent
COOKIE, FLOW_COOKIE = "office_session", "office_flow"
SESSION_TTL_S, FLOW_TTL_S = 12 * 3600, 600
REQUIRED = ["ENTRA_CLIENT_ID", "ENTRA_CLIENT_SECRET", "ENTRA_TENANT_ID", "OFFICE_GROUP_ID",
            "ADMIN_USERS", "SESSION_SECRET", "PUBLIC_URL"]


def load_env() -> dict:
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    if missing:
        sys.exit("missing required env vars: " + ", ".join(missing))
    try:
        secret = bytes.fromhex(os.environ["SESSION_SECRET"])
    except ValueError:
        sys.exit("SESSION_SECRET must be hex")
    if len(secret) < 32:
        sys.exit("SESSION_SECRET must decode to at least 32 bytes (64 hex chars)")
    env = {k: os.environ[k] for k in REQUIRED}
    env.update(secret=secret, public_url=os.environ["PUBLIC_URL"].rstrip("/"),
               data_dir=os.environ.get("DATA_DIR", "/data"), port=int(os.environ.get("PORT", "8080")))
    return env


def make_app(env: dict) -> web.Application:
    secret = env["secret"]
    types = catalog.load(HERE / "data" / "catalog.json")
    levels = mapdata.load_levels(HERE / "data", types)
    access = AccessStore(os.path.join(env["data_dir"], "office.db"), {u.strip() for u in env["ADMIN_USERS"].split(",") if u.strip()})
    world = World(levels, access)
    socks: dict = {}   # user_id -> WebSocketResponse
    auth_time: dict = {}  # user_id -> auth_time of the live session
    msal_app = []

    def msal_client():  # lazy: building it fetches tenant metadata over the network
        if not msal_app:
            import msal
            msal_app.append(msal.ConfidentialClientApplication(
                env["ENTRA_CLIENT_ID"], client_credential=env["ENTRA_CLIENT_SECRET"],
                authority="https://login.microsoftonline.com/" + env["ENTRA_TENANT_ID"]))
        return msal_app[0]

    def who(request):
        tok = request.cookies.get(COOKIE)
        s = session.verify(tok, secret, time.time()) if tok else None
        return s if s and {"oid", "name", "auth_time"} <= s.keys() else None

    def set_cookie(resp, name, payload, ttl):
        resp.set_cookie(name, session.sign(payload, secret, ttl, time.time()), max_age=ttl,
                        httponly=True, secure=True, samesite="Lax", path="/")

    async def send(user_id, msg):
        ws = socks.get(user_id)
        if ws is not None and not ws.closed:
            try:
                await ws.send_json(msg)
            except Exception:
                pass  # a dying socket is cleaned up by its own handler

    async def broadcast(level_ids):
        for lid in set(level_ids):
            msg = {"t": "players", "level": lid, "players": world.players_on(lid)}
            for p in list(world.players.values()):
                if p.level == lid:
                    await send(p.id, msg)

    async def index(request):
        if not who(request):
            raise web.HTTPFound("/login")
        return web.FileResponse(HERE / "static" / "index.html")

    async def login(request):
        flow = msal_client().initiate_auth_code_flow(
            ["User.Read"], redirect_uri=env["public_url"] + "/auth/callback",
            prompt="login" if "fresh" in request.query else None)
        resp = web.HTTPFound(flow["auth_uri"])
        set_cookie(resp, FLOW_COOKIE, {"flow": flow}, FLOW_TTL_S)
        return resp

    async def callback(request):
        tok = request.cookies.get(FLOW_COOKIE)
        data = session.verify(tok, secret, time.time()) if tok else None
        if not data:
            raise web.HTTPFound("/login")
        try:
            result = await asyncio.get_running_loop().run_in_executor(
                None, lambda: msal_client().acquire_token_by_auth_code_flow(data["flow"], dict(request.query)))
        except ValueError:  # state mismatch
            raise web.HTTPFound("/login")
        claims = result.get("id_token_claims")
        if "error" in result or not claims:
            return web.Response(status=400, text="sign-in failed")
        if env["OFFICE_GROUP_ID"] not in claims.get("groups", []):
            return web.Response(status=403, text="ยังไม่ได้รับสิทธิ์เข้าออฟฟิศ")
        resp = web.HTTPFound("/")
        # auth_time is an optional Entra claim; 0 when absent means grants always ask for re-auth
        set_cookie(resp, COOKIE, {"oid": claims["oid"], "name": claims.get("name", ""),
                                  "auth_time": claims.get("auth_time", 0)}, SESSION_TTL_S)
        resp.del_cookie(FLOW_COOKIE, path="/")
        return resp

    async def logout(request):
        resp = web.HTTPFound("/")
        resp.del_cookie(COOKIE, path="/")
        return resp

    async def admin_state(user_id):
        await send(user_id, {"t": "admin_state", "users": access.users(),
                             "grants": {u: sorted(a) for u, a in access.grants().items()},
                             "audit": access.audit()})

    async def handle_message(user_id, raw):
        p = world.players.get(user_id)
        try:
            m = json.loads(raw)
            t = m["t"]
            if p is None:
                return
            before = p.level
            if t == "move":
                if world.move(user_id, m.get("dx"), m.get("dy")):
                    await broadcast([p.level])
            elif t == "ride":
                if world.ride(user_id, m.get("to")):
                    await send(user_id, {"t": "moved", "level": p.level})
                    await broadcast([before, p.level])
                else:
                    await send(user_id, {"t": "refused", "msg": "ไม่มีสิทธิ์เข้าชั้นนี้"})
            elif t in ("admin_state", "grant"):
                in_sec = access.is_admin(user_id) and levels[p.level].area_at(p.x, p.y) == "security"
                if t == "admin_state":
                    if in_sec:
                        await admin_state(user_id)
                    else:
                        await send(user_id, {"t": "error", "msg": "not allowed"})
                    return
                target, area, allowed = m.get("user"), m.get("area"), m.get("allowed")
                valid = (isinstance(target, str) and isinstance(area, str) and area in levels
                         and area.startswith("floor:") and isinstance(allowed, bool))
                if not valid or not in_sec:
                    access.refuse(user_id, target, area, allowed)  # every attempt is audited
                    await send(user_id, {"t": "error", "msg": "not allowed" if valid else "invalid grant"})
                elif time.time() - auth_time.get(user_id, 0) > session.FRESH_AUTH_S:
                    access.refuse(user_id, target, area, allowed)
                    await send(user_id, {"t": "reauth"})
                else:
                    access.set_grant(user_id, target, area, allowed)
                    moved = world.enforce()
                    for uid in moved:
                        await send(uid, {"t": "evicted", "reason": "ไม่มีสิทธิ์เข้าชั้นนี้แล้ว"})
                    await broadcast(list(levels))  # every level: an evicted user may have left meanwhile
                    await admin_state(user_id)
            else:
                await send(user_id, {"t": "error", "msg": "unknown message"})
        except Exception as e:  # bad JSON, bad fields, db down: refuse, keep the socket
            await send(user_id, {"t": "error", "msg": "refused: " + type(e).__name__})

    async def ws_handler(request):
        s = who(request)
        if not s:
            raise web.HTTPUnauthorized()
        if request.headers.get("Origin") != env["public_url"]:  # blocks cross-site WS hijacking
            raise web.HTTPForbidden()
        uid = s["oid"]
        ws = web.WebSocketResponse(heartbeat=30)
        await ws.prepare(request)
        try:
            access.remember_user(uid, s["name"])
            old = world.players.get(uid)
            old_level = old.level if old else None
            me, _ = world.join(uid, s["name"])
        except Exception:
            await ws.send_json({"t": "error", "msg": "unavailable"})
            await ws.close()
            return ws
        old_ws, socks[uid], auth_time[uid] = socks.get(uid), ws, s["auth_time"]  # swap before any await
        if old_ws is not None:
            try:
                await old_ws.send_json({"t": "replaced"})
                await old_ws.close()
            except Exception:
                pass
        await send(uid, {"t": "hello", "you": uid, "level": "lobby", "levels": {k: v.name for k, v in levels.items()}})
        await broadcast(["lobby"] + ([old_level] if old_level else []))
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await handle_message(uid, msg.data)
        finally:
            if socks.get(uid) is ws and world.players.get(uid) is me:  # a replaced socket must not evict its successor
                del socks[uid]
                world.leave(uid)
                await broadcast([me.level])
        return ws

    async def healthz(_request):
        return web.json_response({"status": "ok"})

    app = web.Application()
    app.add_routes([web.get("/healthz", healthz), web.get("/", index), web.get("/login", login), web.get("/auth/callback", callback),
                    web.get("/logout", logout), web.get("/ws", ws_handler)])
    if (HERE / "static").is_dir():
        app.router.add_static("/static", HERE / "static")
    app.router.add_static("/mapdata", HERE / "data")
    return app


if __name__ == "__main__":
    env = load_env()
    web.run_app(make_app(env), host="0.0.0.0", port=env["port"])
