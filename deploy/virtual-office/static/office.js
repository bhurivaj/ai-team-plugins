"use strict";
// Browser client: draws what the server says, sends intents. Never moves the local player itself.
const T = 16;
const $ = (id) => document.getElementById(id);
const cv = $("game"), ctx = cv.getContext("2d");
let catalog, levelsSpec, maps = {}, levelNames = {};
let me = null, level = null, players = [], retry = 2000, stopped = false, ws = null;
let secArea = false, rideTimer = null, toastTimer = null;
const sprites = {}, chars = {};

function sprite(name) { // catalog pixels -> cached canvas; "." or unknown palette char is transparent
  if (sprites[name]) return sprites[name];
  const t = catalog[name], c = document.createElement("canvas");
  c.width = t.w * T; c.height = t.h * T;
  const g = c.getContext("2d");
  t.pixels.forEach((row, y) => [...row].forEach((ch, x) => {
    if (t.palette[ch]) { g.fillStyle = t.palette[ch]; g.fillRect(x, y, 1, 1); }
  }));
  return (sprites[name] = c);
}

const TEMPLATE = [ // original 16x16 person: h hair, s skin, b shirt, l legs
  "................", "................", "......hhhh......", ".....hhhhhh.....", ".....hssssh.....", ".....ssssss.....",
  ".....ssssss.....", "......ssss......", "....bbbbbbbb....", "...bbbbbbbbbb...", "...sbbbbbbbbs...", "...sbbbbbbbbs...",
  "....bbbbbbbb....", ".....llllll.....", ".....ll..ll.....", ".....ll..ll.....",
];
function character(id, seated) { // colour derived from the id; seated shows head and shoulders only
  const key = id + (seated ? "#" : "");
  if (chars[key]) return chars[key];
  let h = 0;
  for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  const col = { h: "#3b2a20", s: "#e8b88a", b: `hsl(${h % 360} 60% 50%)`, l: "#2d3142" };
  const c = document.createElement("canvas"); c.width = c.height = T;
  const g = c.getContext("2d");
  TEMPLATE.slice(0, seated ? 13 : 16).forEach((row, y) => [...row].forEach((ch, x) => {
    if (col[ch]) { g.fillStyle = col[ch]; g.fillRect(x, y, 1, 1); }
  }));
  return (chars[key] = c);
}

function toast(msg) {
  const el = $("toast"); el.textContent = msg; el.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => (el.hidden = true), 4000);
}

// Map reading mirrors office/mapdata.py: objects x/y are pixel top-left; areas in pixels.
function layer(m, name) { return m.layers.find((l) => l.name === name); }
function objs(m) {
  return layer(m, "objects").objects.map((o) => {
    const props = {};
    (o.properties || []).forEach((p) => (props[p.name] = p.value));
    return { type: o.type || o.class, x: Math.floor(o.x / T), y: Math.floor(o.y / T), props };
  });
}
function areaAt(m, x, y) {
  const a = layer(m, "areas").objects.find((a) => a.x / T <= x && x < (a.x + a.width) / T && a.y / T <= y && y < (a.y + a.height) / T);
  return a ? a.name : null;
}

function scaleFor(m) {
  const s = Math.max(1, Math.floor(Math.min(innerWidth / (m.width * T), innerHeight / (m.height * T))));
  cv.width = m.width * T * s; cv.height = m.height * T * s; cv.style.width = cv.width + "px";
  return s;
}

function label(text, cx, y, s) {
  ctx.font = `${Math.max(10, 5 * s)}px system-ui, sans-serif`; ctx.textAlign = "center"; ctx.textBaseline = "top";
  ctx.lineWidth = 3; ctx.strokeStyle = "#000"; ctx.strokeText(text, cx, y);
  ctx.fillStyle = "#fff"; ctx.fillText(text, cx, y);
}

function draw() {
  const m = maps[level];
  if (!m) return;
  const s = scaleFor(m);
  ctx.imageSmoothingEnabled = false;
  const walls = layer(m, "walls").data;
  for (let y = 0; y < m.height; y++) for (let x = 0; x < m.width; x++) {
    ctx.fillStyle = walls[y * m.width + x] ? "#4a4e69" : (x + y) % 2 ? "#c9c5b8" : "#d2cec1";
    ctx.fillRect(x * T * s, y * T * s, T * s, T * s);
  }
  const list = objs(m);
  list.forEach((o) => ctx.drawImage(sprite(o.type), o.x * T * s, o.y * T * s, catalog[o.type].w * T * s, catalog[o.type].h * T * s));
  list.forEach((o) => {
    const t = catalog[o.type], cx = (o.x + t.w / 2) * T * s;
    if (o.props.agent) { // seated and still: the idle state
      ctx.drawImage(character(o.props.agent, true), (o.x + t.w / 2 - 0.5) * T * s, (o.y - 0.5) * T * s, T * s, T * s);
      label("agent: " + o.props.agent, cx, (o.y + t.h) * T * s, s);
    }
    if (o.type === "sign" && o.props.text) label(o.props.text, cx, (o.y + 1) * T * s, s);
  });
  players.forEach((p) => {
    ctx.drawImage(character(p.id, false), p.x * T * s, p.y * T * s, T * s, T * s);
    label(p.name, (p.x + 0.5) * T * s, (p.y + 1) * T * s, s);
  });
}

function nearLift() { // same reach as World.ride: footprint plus one tile
  const m = maps[level], p = players.find((q) => q.id === me);
  if (!m || !p) return null;
  return objs(m).find((o) => o.type === "lift" && o.x - 1 <= p.x && p.x <= o.x + catalog.lift.w && o.y - 1 <= p.y && p.y <= o.y + catalog.lift.h) || null;
}

function refresh() { // lift buttons and security overlay follow where I stand
  const lift = nearLift(), box = $("lift");
  box.replaceChildren();
  box.hidden = !lift;
  if (lift) {
    const lbl = document.createElement("span"); lbl.textContent = "ไปชั้น:"; box.append(lbl);
    String(lift.props.to).split(",").forEach((to) => {
      const b = document.createElement("button");
      b.textContent = levelNames[to] || to;
      b.onclick = () => ride(to);
      box.append(b);
    });
  }
  const p = players.find((q) => q.id === me), inSec = !!p && areaAt(maps[level], p.x, p.y) === "security";
  if (inSec && !secArea) send({ t: "admin_state" }); // non-admins get a silent "not allowed"
  if (!inSec) $("security").hidden = true;
  secArea = inSec;
}

function ride(to) {
  send({ t: "ride", to });
  clearTimeout(rideTimer); // the server answers a refused ride with silence; success sends "moved"
  rideTimer = setTimeout(() => toast("ไม่มีสิทธิ์เข้าชั้นนี้"), 1500);
}

function name(id, users) { const u = users.find((x) => x[0] === id); return u ? u[1] : id; }

function showAdmin(m) {
  const box = $("security"), floors = Object.keys(levelNames).filter((k) => k.startsWith("floor:"));
  box.replaceChildren();
  const h = document.createElement("h2"); h.textContent = "ห้องความปลอดภัย"; box.append(h);
  const tb = document.createElement("table"), head = tb.createTHead().insertRow();
  head.insertCell().textContent = "ผู้ใช้";
  floors.forEach((f) => { const c = document.createElement("th"); c.className = "c"; c.textContent = levelNames[f]; head.append(c); });
  m.users.forEach(([id, uname]) => {
    const r = tb.insertRow(); r.insertCell().textContent = uname;
    floors.forEach((f) => {
      const cb = document.createElement("input"); cb.type = "checkbox";
      cb.checked = (m.grants[id] || []).includes(f);
      cb.setAttribute("aria-label", `${uname} ${levelNames[f]}`);
      cb.onchange = () => send({ t: "grant", user: id, area: f, allowed: cb.checked });
      const c = r.insertCell(); c.className = "c"; c.append(cb);
    });
  });
  box.append(tb);
  const h3 = document.createElement("h2"); h3.textContent = "บันทึกการเปลี่ยนแปลงล่าสุด"; box.append(h3);
  const ul = document.createElement("ul");
  m.audit.slice(0, 20).forEach((a) => {
    const li = document.createElement("li");
    li.textContent = `${new Date(a.ts * 1000).toLocaleString("th-TH")} ${name(a.actor, m.users)} ${a.allowed ? "อนุญาต" : "ยกเลิก"} ${name(a.user, m.users)} ${levelNames[a.area] || a.area}${a.ok ? "" : " (ไม่สำเร็จ)"}`;
    ul.append(li);
  });
  box.append(ul);
  box.hidden = false;
}

function showReauth() {
  const box = $("security");
  box.replaceChildren();
  const a = document.createElement("a"); a.href = "/login?fresh=1"; a.textContent = "ยืนยันตัวตนอีกครั้งเพื่อแก้ไขสิทธิ์";
  box.append(a); box.hidden = false;
}

function onMessage(m) {
  if (m.t === "hello") { me = m.you; level = m.level; levelNames = m.levels; players = []; retry = 2000; }
  else if (m.t === "moved") { level = m.level; clearTimeout(rideTimer); players = []; secArea = false; }
  else if (m.t === "players") { if (m.level !== level) return; players = m.players; }
  else if (m.t === "evicted") toast(m.reason);
  else if (m.t === "replaced") { stopped = true; toast("เปิดออฟฟิศในแท็บอื่นแล้ว"); }
  else if (m.t === "admin_state") showAdmin(m);
  else if (m.t === "reauth") showReauth();
  draw(); refresh();
}

function send(m) { if (ws && ws.readyState === 1) ws.send(JSON.stringify(m)); }

function connect() {
  ws = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws");
  ws.onmessage = (e) => { try { onMessage(JSON.parse(e.data)); } catch (err) { console.error(err); } };
  ws.onclose = () => {
    if (stopped) return;
    toast("ขาดการเชื่อมต่อ กำลังเชื่อมต่อใหม่");
    setTimeout(connect, retry);
    retry = Math.min(retry * 2, 30000);
  };
}

const KEYS = { ArrowUp: [0, -1], w: [0, -1], ArrowDown: [0, 1], s: [0, 1], ArrowLeft: [-1, 0], a: [-1, 0], ArrowRight: [1, 0], d: [1, 0] };
addEventListener("keydown", (e) => {
  const d = KEYS[e.key.length === 1 ? e.key.toLowerCase() : e.key];
  if (!d || e.ctrlKey || e.metaKey || e.altKey || /^INPUT$/.test(e.target.tagName)) return;
  e.preventDefault();
  send({ t: "move", dx: d[0], dy: d[1] });
});
addEventListener("resize", draw);

(async () => {
  const get = (u) => fetch("/mapdata/" + u).then((r) => r.json());
  catalog = await get("catalog.json");
  levelsSpec = (await get("levels.json")).levels;
  for (const f of new Set(Object.values(levelsSpec).map((l) => l.map))) maps[f] = await get(f);
  maps = Object.fromEntries(Object.entries(levelsSpec).map(([id, l]) => [id, maps[l.map]]));
  connect();
})();
