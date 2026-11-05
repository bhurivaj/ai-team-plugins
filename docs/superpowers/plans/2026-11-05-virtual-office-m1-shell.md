# Virtual Office — Milestone 1 (Office Shell) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A walkable pixel office: Entra login, a lobby and two company floors drawn from catalog objects and map data, live presence of the people, idle agents at their desks, and a security room whose grants open and shut floor doors, enforced by the server. No Claude yet.

**Architecture:**
- Pure-Python logic modules, stdlib only so CI can unit-test them:
  - catalog and map loading
  - access store
  - world, movement and doors
  - signed sessions
- They sit under a thin aiohttp server that does the Entra OIDC login (msal) and one WebSocket per browser. The server is authoritative: clients send intents and the server validates and broadcasts.
- The browser is plain HTML and canvas with no build step. It draws sprites from pixel grids stored in the catalog.

**Tech Stack:**
- Python 3.12
- aiohttp (WebSocket + static files)
- msal (OIDC auth-code flow)
- sqlite3 (stdlib)
- vanilla JS + canvas
- Docker Compose behind nginx + Cloudflare

**Spec:** `docs/superpowers/specs/2026-11-05-virtual-office-design.md`. Milestones 2–6 get their own plans after this one ships.

## Global Constraints

- **Hosting:** the company Ubuntu server, Docker Compose, behind the existing nginx and Cloudflare proxied DNS. Not Azure. Ports bind to `127.0.0.1` only.
- **Entra login, rights in the office:**
  - Login is Entra ID (OIDC), single tenant, with no local passwords.
  - Anyone in the Entra group `AI-Office-Users` can log in and lands in the lobby. Which floors they may enter is set in the security room, not in Entra.
- **Doors are enforced by the server, not drawn.** A browser that draws its own way through a door still gets refused.
- **Removing access takes effect at once:** the person is moved to the lobby. **Granting access takes effect at once:** no re-login.
- **Security room:**
  - Admins only, and in Phase 1 that is the owner.
  - Every change is logged: who changed what, and when.
  - A fresh Entra sign-in (MFA) is required before a change is accepted.
- **Objects:** every fitting is defined once in a catalog and placed by map data.
  - Behaviours are a fixed list in code.
  - Map and catalog changes are versioned in git and load without a rebuild.
  - Maps are Tiled-compatible JSON.
- Both company floors share one floor template. The art and layout must be original.
- Secrets never go in git or the image. `.env` is `chmod 600`. `tests/secret_scan.sh` must stay green.
- Tests use stdlib `unittest` in `tests/`, and CI runs `python -m unittest discover -s tests -v` without installing dependencies. **Test-covered modules must not import aiohttp or msal.**

## Review Focus

1. A revoked user reconnects or reloads: they must never respawn inside a forbidden floor. Every join spawns in the lobby. → Task 3 `test_join_always_spawns_in_lobby`.
2. A client sends a multi-tile jump, a diagonal move, a move into a wall, or malformed JSON: the server refuses it and keeps the connection, and the world is unchanged. → Task 3 `test_move_rejects_jumps_walls_and_doors`, Task 5 `handle_message` ignores bad messages.
3. The same person opens two tabs: they keep one character, and the newest connection wins while the older one gets `{"t":"replaced"}`. → Task 3 `test_rejoin_replaces_not_duplicates`.
4. A tampered, expired or wrong-secret session cookie: no WebSocket, and a redirect to login. → Task 4 `test_verify_rejects_tamper_expiry_and_wrong_secret`.
5. A non-admin sends a `grant` message by hand, or an admin's sign-in is older than 10 minutes: refused, no change, nothing logged as granted. The non-admin case is logged with `allowed` unchanged. → Task 2 `test_non_admin_cannot_grant`, Task 5 fresh-auth check.

---

## File Structure

```text
deploy/virtual-office/
  office/__init__.py
  office/catalog.py       # object types + fixed behaviour list
  office/mapdata.py       # Tiled-compatible level loading + validation
  office/access.py        # grants, admins, audit log (sqlite)
  office/world.py         # players, movement, doors, lift, eviction
  office/session.py       # HMAC-signed session tokens
  server.py               # aiohttp: login, callback, ws, static (not unit-tested)
  data/catalog.json
  data/levels.json        # level id -> map file, display names
  data/maps/lobby.json
  data/maps/floor.json    # shared by floor:catice and floor:classmat
  static/index.html
  static/office.js
  Dockerfile  compose.yaml  nginx.conf.example  .env.example  README.md  requirements.txt
tests/test_virtual_office.py
```

Tests import with `sys.path.insert(0, <repo>/deploy/virtual-office)` and then `from office import catalog, mapdata, access, world, session`, following the pattern of `tests/test_teams_bot.py`.

---

### Task 1: Catalog and maps

**Files:**
- Create: `deploy/virtual-office/office/__init__.py` (empty), `office/catalog.py`, `office/mapdata.py`, `data/catalog.json`, `data/levels.json`, `data/maps/lobby.json`, `data/maps/floor.json`
- Test: `tests/test_virtual_office.py`

**Interfaces:**
- Produces:
  - `catalog.BEHAVIOURS: frozenset[str]`, exactly `{"door","flap-gate","lift","desk","bookshelf","filing-cabinet","board","screen","meeting-table","security-console","sign"}`
  - `@dataclass(frozen=True) ObjectType(id: str, w: int, h: int, blocks: bool, behaviour: str | None, pixels: list[str], palette: dict[str, str])`
  - `catalog.load(path) -> dict[str, ObjectType]`, which raises `ValueError` on an unknown behaviour, or on pixel rows that are ragged or use a colour missing from the palette
  - `@dataclass Obj(id: int, type: str, x: int, y: int, props: dict)`, positions in tiles
  - `@dataclass Area(id: str, x: int, y: int, w: int, h: int)`
  - `@dataclass Level(id: str, name: str, width: int, height: int, walls: list[list[bool]], objects: list[Obj], areas: list[Area], spawn: tuple[int, int])`
  - `mapdata.load_levels(data_dir, types) -> dict[str, Level]`, which reads `levels.json` and raises `ValueError` on:
    - an object of unknown type
    - an object off the map
    - two blocking objects overlapping
    - a `door` whose `area` property names no area on that level
    - a `lift` whose `to` names an unknown level
    - a missing `spawn` object
  - `Level.area_at(x, y) -> str | None`
  - `Level.blocked(x, y) -> bool`: a wall, outside the map, or a blocking object

Map format (Tiled JSON):
- `tilewidth`/`tileheight` = 16.
- Layer `walls`: a tilelayer, `data` is non-zero for a wall.
- Layer `objects`: an objectgroup. Each object has `type` or `class`, `x`/`y` in pixels, and `properties: [{name, value}]`.
- Layer `areas`: an objectgroup of rectangles. `name` is the area id; pixels ÷ 16 give tiles.
- The spawn is an object of type `spawn`, defined in the catalog with `behaviour: null` and `blocks: false`.

`levels.json` content:

```json
{"levels": {
  "lobby": {"name": "ล็อบบี้", "map": "maps/lobby.json"},
  "floor:catice": {"name": "ชั้น Catice", "map": "maps/floor.json"},
  "floor:classmat": {"name": "ชั้น Classmat", "map": "maps/floor.json"}}}
```

Rooms to author, following the spec's "Building map" and the mockup `.superpowers/brainstorm/*/content/building-map.html`:
- **Lobby:**
  - area `security` with a `door` (`area: security`) and a `security-console`
  - `flap-gate` ×3 at the entrance
  - a `lift` with `to: "floor:catice,floor:classmat"`
  - `spawn` just inside the gates
- **Floor:**
  - areas `director`, `meeting`, `library`, `documents`, `marketing`, `hr`, `common`
  - `desk` objects with an `agent` property:
    - `marketing-manager`, `research-analyst`, `content-strategist`, `content-writer`, `designer`, `seo-specialist`, `publisher` in `marketing`
    - `hr-manager`, `hr-assistant` in `hr`
    - `director` in `director`
  - one each of `meeting-table`, `bookshelf`, `filing-cabinet`, `board` and `screen`
  - a `sign` (`text: "เร็วๆ นี้"`) in each room that does nothing yet: meeting, library, documents
  - a `lift` with `to: "lobby"`
  - a `spawn` by the lift

Pixel art: a 16×16 grid per tile of the object's footprint, drawn originally. Also add catalog entries `chair`, `plant` and `sofa` (`behaviour: null`).

- [ ] **Step 1: Write failing tests**

```python
class CatalogMapTests(unittest.TestCase):
    def setUp(self):
        self.types = catalog.load(DATA / "catalog.json")
        self.levels = mapdata.load_levels(DATA, self.types)

    def test_levels_and_template_shared(self):
        self.assertEqual(set(self.levels), {"lobby", "floor:catice", "floor:classmat"})
        a, b = self.levels["floor:catice"], self.levels["floor:classmat"]
        self.assertEqual([(o.type, o.x, o.y) for o in a.objects], [(o.type, o.x, o.y) for o in b.objects])

    def test_floor_has_every_room_and_agent(self):
        f = self.levels["floor:catice"]
        self.assertTrue({"director", "meeting", "library", "documents", "marketing", "hr", "common"} <= {a.id for a in f.areas})
        agents = {o.props.get("agent") for o in f.objects if o.type == "desk"}
        self.assertEqual(agents, {"marketing-manager", "research-analyst", "content-strategist", "content-writer",
                                  "designer", "seo-specialist", "publisher", "hr-manager", "hr-assistant", "director"})

    def test_lobby_has_gate_security_and_lift(self):
        lob = self.levels["lobby"]
        kinds = {o.type for o in lob.objects}
        self.assertTrue({"flap-gate", "door", "security-console", "lift", "spawn"} <= kinds)
        self.assertIn("security", {a.id for a in lob.areas})

    def test_validation_rejects_bad_data(self):
        with self.assertRaises(ValueError):
            catalog.load(write_tmp({"x": {"w": 1, "h": 1, "blocks": True, "behaviour": "teleport", "pixels": ["a"], "palette": {"a": "#000"}}}))
        # door pointing at a missing area
        bad = minimal_level(objects=[{"type": "door", "x": 0, "y": 0, "properties": [{"name": "area", "value": "nope"}]}])
        with self.assertRaises(ValueError):
            mapdata.load_levels(bad, self.types)
```

`write_tmp` and `minimal_level` are small helpers in the test file. They write JSON into a `tempfile.TemporaryDirectory` and return the path.

- [ ] **Step 2:** Run `python3 -m unittest tests.test_virtual_office -v`. Expected: FAIL with `ModuleNotFoundError: office`.
- [ ] **Step 3:** Implement `catalog.py` and `mapdata.py`, and author the four data files.
- [ ] **Step 4:** Run the same command. Expected: `CatalogMapTests` all PASS.
- [ ] **Step 5:** Commit: `git add deploy/virtual-office/office deploy/virtual-office/data tests/test_virtual_office.py && git commit -m "virtual office: object catalog and Tiled-compatible levels"`

---

### Task 2: Access store and audit log

**Files:**
- Create: `deploy/virtual-office/office/access.py`
- Test: `tests/test_virtual_office.py`

**Interfaces:**
- Produces: `AccessStore(db_path: str, admins: set[str])` with:
  - `is_admin(user_id) -> bool`
  - `can_enter(user_id, area_id: str | None) -> bool`. The rules:
    - `None` or `"lobby"` → True
    - `"security"` → admin only
    - `"floor:<company>"` → admin, or a stored grant
    - any other area id → True (rooms inside a floor have no doors in Phase 1)
  - `remember_user(user_id, name) -> None`
  - `users() -> list[tuple[str, str]]`
  - `set_grant(actor_id, user_id, area_id, allowed: bool) -> None`. Raises `PermissionError` unless the actor is an admin, and raises `ValueError` unless `area_id` starts with `"floor:"`. Every call, refused or not, appends an audit row.
  - `grants() -> dict[str, set[str]]`, mapping user to areas
  - `audit(limit=100) -> list[dict]`, newest first, with keys `ts, actor, user, area, allowed, ok`
- Tables are `users(id PK, name)`, `grants(user, area, PK(user, area))` and `audit(ts, actor, user, area, allowed, ok)`. Admins come from env only and cannot be revoked from the UI.

- [ ] **Step 1: Write failing tests**

```python
class AccessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.a = access.AccessStore(os.path.join(self.tmp.name, "o.db"), admins={"boss"})

    def test_floor_needs_grant_lobby_open_security_admin_only(self):
        self.assertTrue(self.a.can_enter("u1", "lobby"))
        self.assertFalse(self.a.can_enter("u1", "floor:catice"))
        self.assertFalse(self.a.can_enter("u1", "security"))
        self.assertTrue(self.a.can_enter("boss", "security"))
        self.a.set_grant("boss", "u1", "floor:catice", True)
        self.assertTrue(self.a.can_enter("u1", "floor:catice"))
        self.assertFalse(self.a.can_enter("u1", "floor:classmat"))
        self.a.set_grant("boss", "u1", "floor:catice", False)
        self.assertFalse(self.a.can_enter("u1", "floor:catice"))

    def test_non_admin_cannot_grant(self):
        with self.assertRaises(PermissionError):
            self.a.set_grant("u1", "u1", "floor:catice", True)
        self.assertFalse(self.a.can_enter("u1", "floor:catice"))
        row = self.a.audit()[0]
        self.assertEqual((row["actor"], row["ok"]), ("u1", False))

    def test_grants_survive_reopen(self):
        self.a.set_grant("boss", "u2", "floor:classmat", True)
        again = access.AccessStore(os.path.join(self.tmp.name, "o.db"), admins={"boss"})
        self.assertEqual(again.grants(), {"u2": {"floor:classmat"}})
```

- [ ] **Step 2:** Run the tests. Expected: FAIL (`access` missing).
- [ ] **Step 3:** Implement `access.py` with `sqlite3`. Open a connection per call with `check_same_thread=False`; there is no pooling.
- [ ] **Step 4:** Run the tests. Expected: PASS.
- [ ] **Step 5:** Commit: `git commit -m "virtual office: access grants and audit log"` (after adding the files)

---

### Task 3: World: movement, doors, lift, eviction

**Files:**
- Create: `deploy/virtual-office/office/world.py`
- Test: `tests/test_virtual_office.py`

**Interfaces:**
- Consumes:
  - `Level.blocked`, `Level.area_at`, `Level.spawn` and `Level.objects` (Task 1)
  - `AccessStore.can_enter` (Task 2), through any object that has that method
- Produces:
  - `@dataclass Player(id: str, name: str, level: str, x: int, y: int)`
  - `World(levels: dict[str, Level], access)` with these methods:
    - `join(user_id, name) -> tuple[Player, bool]`. Always spawns at `levels["lobby"].spawn`. The bool is `True` when it replaced an existing player.
    - `leave(user_id) -> None`
    - `move(user_id, dx, dy) -> bool`. Accepts only `abs(dx)+abs(dy) == 1` with `dx`, `dy` as ints. The target must not be blocked, and both `can_enter(user, level.id)` and `can_enter(user, level.area_at(target))` must pass. A `door` tile is passable only when `can_enter` passes for its `area` property.
    - `ride(user_id, to_level) -> bool`. The player must stand on, or next to, a `lift` whose `to` list (comma-separated) contains `to_level`, and `can_enter(user, to_level)` must pass. The player is placed at the target level's spawn.
    - `enforce() -> list[str]`. Every player whose current level or area fails `can_enter` goes to the lobby spawn. Returns their ids.
    - `players_on(level_id) -> list[dict]`, giving `{"id","name","x","y"}` per player
  - Attribute `players: dict[str, Player]`, keyed by user id

- [ ] **Step 1: Write failing tests**

```python
class WorldTests(unittest.TestCase):
    def setUp(self):
        self.types = catalog.load(DATA / "catalog.json")
        self.levels = mapdata.load_levels(DATA, self.types)
        self.tmp = tempfile.TemporaryDirectory()
        self.acc = access.AccessStore(os.path.join(self.tmp.name, "o.db"), admins={"boss"})
        self.w = world.World(self.levels, self.acc)

    def test_join_always_spawns_in_lobby(self):
        p, _ = self.w.join("u1", "U1")
        self.assertEqual((p.level, (p.x, p.y)), ("lobby", self.levels["lobby"].spawn))

    def test_move_rejects_jumps_walls_and_doors(self):
        p, _ = self.w.join("u1", "U1")
        start = (p.x, p.y)
        self.assertFalse(self.w.move("u1", 2, 0))
        self.assertFalse(self.w.move("u1", 1, 1))
        self.assertFalse(self.w.move("u1", "1", 0))
        self.assertEqual((p.x, p.y), start)
        # walk to the security door: a non-admin is stopped at it
        self.assertFalse(walk_into_area(self.w, "u1", "security"))

    def test_lift_needs_grant_then_eviction_on_revoke(self):
        self.w.join("u1", "U1")
        walk_to_lift(self.w, "u1")
        self.assertFalse(self.w.ride("u1", "floor:catice"))
        self.acc.set_grant("boss", "u1", "floor:catice", True)
        self.assertTrue(self.w.ride("u1", "floor:catice"))
        self.acc.set_grant("boss", "u1", "floor:catice", False)
        self.assertEqual(self.w.enforce(), ["u1"])
        self.assertEqual(self.w.players["u1"].level, "lobby")

    def test_rejoin_replaces_not_duplicates(self):
        self.w.join("u1", "U1")
        _, replaced = self.w.join("u1", "U1")
        self.assertTrue(replaced)
        self.assertEqual(len(self.w.players_on("lobby")), 1)
```

`walk_to_lift` and `walk_into_area` are test helpers that run a BFS over `Level.blocked` and call `move` one step at a time. `walk_into_area` returns whether the player ended inside the area.

- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement `world.py`. The `players` dict is keyed by user id.
- [ ] **Step 4:** Run the tests. Expected: PASS.
- [ ] **Step 5:** Commit: `git commit -m "virtual office: server-authoritative movement, doors, lift, eviction"`

---

### Task 4: Signed session tokens

**Files:**
- Create: `deploy/virtual-office/office/session.py`
- Test: `tests/test_virtual_office.py`

**Interfaces:**
- Produces:
  - `sign(payload: dict, secret: bytes, ttl_s: int, now: float) -> str`. The token is `base64url(json) + "." + base64url(hmac_sha256)`, and the payload gets an `exp` field.
  - `verify(token: str, secret: bytes, now: float) -> dict | None`. Compares with `hmac.compare_digest`. Returns `None` on any malformed input; it never raises.
- The session payload is `{"oid", "name", "auth_time"}`. `auth_time` is the Entra `auth_time` claim, used for the fresh-sign-in rule. `FRESH_AUTH_S = 600` is defined here.

- [ ] **Step 1: Write failing test**

```python
class SessionTests(unittest.TestCase):
    def test_verify_rejects_tamper_expiry_and_wrong_secret(self):
        t = session.sign({"oid": "u1"}, b"k", ttl_s=60, now=1000)
        self.assertEqual(session.verify(t, b"k", now=1010)["oid"], "u1")
        self.assertIsNone(session.verify(t, b"k", now=1061))
        self.assertIsNone(session.verify(t, b"other", now=1010))
        body, mac = t.split(".")
        self.assertIsNone(session.verify(body[:-2] + "xx." + mac, b"k", now=1010))
        for junk in ["", "a", "a.b.c", "....", None]:
            self.assertIsNone(session.verify(junk, b"k", now=1010))
```

- [ ] **Step 2:** Run the test. Expected: FAIL.
- [ ] **Step 3:** Implement `session.py`.
- [ ] **Step 4:** Run the test. Expected: PASS.
- [ ] **Step 5:** Commit: `git commit -m "virtual office: HMAC session tokens"`

---

### Task 5: Server: Entra login, WebSocket, static

**Files:**
- Create: `deploy/virtual-office/server.py`, `requirements.txt` (`aiohttp`, `msal`)
- Test: a manual smoke test in Task 7. This file is glue only.

**Interfaces:**
- Consumes: Tasks 1–4.
- Env:
  - `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`, `ENTRA_TENANT_ID`
  - `OFFICE_GROUP_ID`: the object id of `AI-Office-Users`
  - `ADMIN_USERS`: comma-separated Entra object ids
  - `SESSION_SECRET`: at least 32 random bytes, hex
  - `PUBLIC_URL`, for example `https://office.example.com`
  - `DATA_DIR`, default `/data`
  - `PORT`, default `8080`
- Routes:
  - `GET /`: serves `static/index.html` if the session is valid, otherwise 302 to `/login`.
  - `GET /login`: `msal.ConfidentialClientApplication.initiate_auth_code_flow(["User.Read"], redirect_uri=PUBLIC_URL+"/auth/callback", prompt="login" if "fresh" in query else None)`. The flow is stored in a short-lived signed cookie made with `session.sign`.
  - `GET /auth/callback`: `acquire_token_by_auth_code_flow`. Requires `OFFICE_GROUP_ID in id_token_claims.get("groups", [])`, otherwise 403 with "ยังไม่ได้รับสิทธิ์เข้าออฟฟิศ". On success, sets the cookie `office_session` (HttpOnly, Secure, SameSite=Lax, 12 h) and redirects to `/`.
  - `GET /logout`: clears the cookie.
  - `GET /ws`: requires the session. It calls `remember_user`, then `world.join`; any older socket for the same user receives `{"t":"replaced"}` and is closed.
  - Static files: `/static/*` from `static/`, and `/mapdata/*` from `data/`, so map and catalog changes load with no rebuild.
- WebSocket protocol:
  - client → server: `{"t":"move","dx","dy"}`, `{"t":"ride","to"}`, `{"t":"admin_state"}`, `{"t":"grant","user","area","allowed"}`
  - server → client: `{"t":"hello","you","level","levels":{id:name}}`, `{"t":"players","level","players"}`, `{"t":"moved","level"}`, `{"t":"evicted","reason":"ไม่มีสิทธิ์เข้าชั้นนี้แล้ว"}`, `{"t":"admin_state","users","grants","audit"}`, `{"t":"reauth"}`, `{"t":"error","msg"}`
- `handle_message(user_id, raw: str)`:
  - It parses JSON in a `try` block, and a bad message gets `error` while the socket stays open.
  - After every change it broadcasts `players` for each affected level.
  - `grant` requires `is_admin`, that the player stands in the `security` area, and `now - auth_time <= FRESH_AUTH_S`. Otherwise it sends `reauth`.
  - After `set_grant` it runs `world.enforce()`, sends `evicted` to each id returned, and rebroadcasts.

- [ ] **Step 1:** Implement `server.py` as described. Bind to `0.0.0.0:$PORT` inside the container; compose publishes only `127.0.0.1`.
- [ ] **Step 2:** Run `python3 -m unittest discover -s tests -v` to confirm the server import didn't break CI. Expected: all PASS, and `server.py` is not imported by the tests.
- [ ] **Step 3:** Commit: `git commit -m "virtual office: Entra login and WebSocket server"`

---

### Task 6: Browser client

**Files:**
- Create: `deploy/virtual-office/static/index.html`, `static/office.js`
- Test: a manual check in Task 7.

**Interfaces:**
- Consumes: the protocol in Task 5, plus `/mapdata/catalog.json`, `/mapdata/levels.json` and `/mapdata/maps/*.json`.
- Behaviour:
  - **Canvas:** 16 px tiles at an integer scale that fits the window, with `imageSmoothingEnabled = false`. Sprites are drawn from the catalog `pixels`/`palette` and cached per type.
  - **Movement:** the arrow keys and WASD send one `move` per keypress or repeat. The client never moves the local player itself; it draws only the server's `players` messages.
  - **Characters:**
    - People get a generated character with their name shown under it.
    - Agents are drawn sitting at their `desk` with the `agent` label, still, with no animation. That is the idle state from the spec.
  - **Lift:** standing next to a `lift` shows the floor buttons from `to`, labelled with the names from `hello.levels`. A refused ride shows "ไม่มีสิทธิ์เข้าชั้นนี้".
  - **Closed rooms:** a `sign` object shows its `text`.
  - **Security room:** for an admin standing in the `security` area, the client sends `admin_state` and shows an HTML overlay.
    - A table with one row per user and one column per floor, where checkboxes send `grant`.
    - Under the table, the newest 20 audit rows.
    - On `reauth`, a link to `/login?fresh=1`.
  - **Messages:**
    - `evicted` shows a toast with the reason.
    - `replaced` shows "เปิดออฟฟิศในแท็บอื่นแล้ว" and stops reconnecting.
  - **Reconnect:** a lost socket reconnects after 2 s, 4 s, 8 s, up to a maximum of 30 s.
  - **Copy:** all on-screen text is in Thai.

- [ ] **Step 1:** Implement both files.
- [ ] **Step 2:** Commit: `git commit -m "virtual office: canvas client"`

---

### Task 7: Packaging, deploy docs and smoke test

**Files:**
- Create: `deploy/virtual-office/Dockerfile`, `compose.yaml`, `nginx.conf.example`, `.env.example`, `README.md`
- Modify: `docs/team-deployment.md`, to say the Teams bot is replaced and to point at the spec

**Details:**
- **Dockerfile:** `python:3.12-slim`, user `office` uid 10001, `RUN mkdir /data && chown office:office /data` (the fix carried over from the Teams bot), `CMD ["python","server.py"]`.
- **compose.yaml:**
  - Service `office`, `env_file: .env`, port `127.0.0.1:8080:8080`.
  - Volume `office-data:/data`.
  - A read-only bind of `./data:/app/data:ro`, so map edits load without a rebuild. The server validates maps at startup, so a map edit takes effect after `docker compose restart office`, and a broken map fails fast with the `ValueError` message in the logs.
  - A healthcheck on `/healthz`; add that route to `server.py` in this task, returning `{"status":"ok"}`.
- **nginx.conf.example:**
  - `location /` proxies to `127.0.0.1:8080` with `proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 1h;`
  - Header: Cloudflare SSL Full (strict).
  - A note that Cloudflare Access fronts the hostname.
- **README admin steps:**
  1. An Entra app (web redirect `PUBLIC_URL/auth/callback`) with `groupMembershipClaims: SecurityGroup` and the group `AI-Office-Users`.
  2. A Conditional Access policy requiring MFA for this app. The app enforces sign-in freshness; MFA itself comes from Entra.
  3. A Cloudflare DNS record and Access application.
  4. On the server: `cp .env.example .env && chmod 600 .env`, then `docker compose up -d --build`.

- [ ] **Step 1:** Write the files.
- [ ] **Step 2:** Run `docker compose -f deploy/virtual-office/compose.yaml build`, then `curl -s 127.0.0.1:8080/healthz` after `up -d` with a dummy `.env`. Expected: `{"status": "ok"}`.
- [ ] **Step 3:** Run `bash tests/secret_scan.sh && python3 -m unittest discover -s tests -v`. Expected: exit 0, all PASS.
- [ ] **Step 4:** Commit: `git commit -m "virtual office: Docker, nginx and deploy docs"`
- [ ] **Step 5 (needs the owner's Entra app, so not automatable):** Two browsers as two users.
  - Expected:
    - Both see each other move.
    - A non-granted user is stopped at the lift.
    - The owner grants access in the security room and the other user can ride at once.
    - The owner revokes access, and the other user is back in the lobby with the toast.
    - The audit list shows both changes.
  - Record the result in `deploy/virtual-office/README.md` under "Milestone 1 proven".
