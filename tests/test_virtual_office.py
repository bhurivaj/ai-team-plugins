"""Tests for the virtual office (pure Python parts, no web framework needed)."""
import json, os, pathlib, sys, tempfile, unittest
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "deploy" / "virtual-office"))
from office import access, catalog, mapdata, world  # noqa: E402

DATA = ROOT / "deploy" / "virtual-office" / "data"
_tmp = []  # keep TemporaryDirectory objects alive until process exit


def write_tmp(obj, name="catalog.json"):
    d = tempfile.TemporaryDirectory()
    _tmp.append(d)
    p = pathlib.Path(d.name) / name
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


def minimal_level(objects=(), areas=(), w=4, h=4, extra_levels=None):
    """A tiny valid data dir (4x4, a spawn at 3,3); `objects`/`areas` are added to it."""
    d = tempfile.TemporaryDirectory()
    _tmp.append(d)
    root = pathlib.Path(d.name)
    (root / "maps").mkdir()
    objs = [{"id": 99, "type": "spawn", "x": 48, "y": 48, "properties": []}]
    for i, o in enumerate(objects):
        objs.append({"id": i + 1, "type": o["type"], "x": o["x"] * 16, "y": o["y"] * 16, "properties": o.get("properties", [])})
    tmap = {"width": w, "height": h, "tilewidth": 16, "tileheight": 16, "layers": [
        {"name": "walls", "type": "tilelayer", "data": [0] * (w * h)},
        {"name": "objects", "type": "objectgroup", "objects": objs},
        {"name": "areas", "type": "objectgroup", "objects": [
            {"name": a, "x": 0, "y": 0, "width": 16, "height": 16} for a in areas]}]}
    (root / "maps" / "m.json").write_text(json.dumps(tmap))
    levels = {"a": {"name": "A", "map": "maps/m.json"}, **(extra_levels or {})}
    (root / "levels.json").write_text(json.dumps({"levels": levels}))
    return root


def reachable(lv, start, extra_blocked=()):
    seen, q = {start}, deque([start])
    while q:
        x, y = q.popleft()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if n not in seen and n not in extra_blocked and not lv.blocked(*n):
                seen.add(n)
                q.append(n)
    return seen


def _walk(w, uid, goal):
    """BFS over Level.blocked to a tile satisfying goal(x, y), then replay through World.move only."""
    p = w.players[uid]
    lv = w.levels[p.level]
    prev, q = {(p.x, p.y): None}, deque([(p.x, p.y)])
    end = None
    while q:
        c = q.popleft()
        if goal(*c):
            end = c
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + dx, c[1] + dy)
            if n not in prev and not lv.blocked(*n):
                prev[n] = c
                q.append(n)
    assert end, "no path"
    steps = []
    while prev[end]:
        steps.append((end[0] - prev[end][0], end[1] - prev[end][1]))
        end = prev[end]
    for dx, dy in reversed(steps):
        if not w.move(uid, dx, dy):
            return False
    return True


def walk_to_lift(w, uid):
    lv = w.levels[w.players[uid].level]
    lifts = [(o, lv.types[o.type]) for o in lv.objects if lv.types[o.type].behaviour == "lift"]
    return _walk(w, uid, lambda x, y: any(o.x - 1 <= x <= o.x + t.w and o.y - 1 <= y <= o.y + t.h for o, t in lifts))


def walk_into_area(w, uid, area):
    """Try to walk into `area`; True only if the player ends up inside it."""
    lv = w.levels[w.players[uid].level]
    _walk(w, uid, lambda x, y: lv.area_at(x, y) == area)
    p = w.players[uid]
    return lv.area_at(p.x, p.y) == area


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

    def test_catalog_rejects_ragged_and_unpainted_pixels(self):
        row, ok = "a" * 16, {"w": 1, "h": 1, "blocks": True, "behaviour": None, "palette": {"a": "#000"}}
        catalog.load(write_tmp({"x": {**ok, "pixels": [row] * 16}}))
        for pixels in ([row] * 15 + ["a" * 15], [row] * 15 + ["a" * 15 + "z"]):
            with self.assertRaises(ValueError):
                catalog.load(write_tmp({"x": {**ok, "pixels": pixels}}))

    def test_level_rejects_other_bad_objects(self):
        cases = {
            "unknown type": [{"type": "ufo", "x": 0, "y": 0}],
            "off the map": [{"type": "desk", "x": 3, "y": 0}],  # desk is 2 wide on a 4 wide map
            "overlap": [{"type": "desk", "x": 0, "y": 0}, {"type": "plant", "x": 1, "y": 0}],
            "lift to nowhere": [{"type": "lift", "x": 0, "y": 0, "properties": [{"name": "to", "value": "a,nope"}]}],
        }
        for label, objs in cases.items():
            with self.subTest(label), self.assertRaises(ValueError):
                mapdata.load_levels(minimal_level(objects=objs), self.types)
        ok = mapdata.load_levels(minimal_level(objects=[{"type": "lift", "x": 0, "y": 0, "properties": [{"name": "to", "value": "a"}]}]), self.types)
        self.assertEqual(ok["a"].spawn, (3, 3))
        d = minimal_level()
        m = json.loads((d / "maps" / "m.json").read_text())
        m["layers"][1]["objects"] = []
        (d / "maps" / "m.json").write_text(json.dumps(m))
        with self.assertRaises(ValueError):
            mapdata.load_levels(d, self.types)

    def test_blocked_and_area_at(self):
        lob = self.levels["lobby"]
        door = next(o for o in lob.objects if o.type == "door")
        self.assertFalse(lob.blocked(door.x, door.y))  # R1: doors do not block
        self.assertTrue(lob.blocked(-1, 0) and lob.blocked(0, 0) and lob.blocked(lob.width, 0))
        console = next(o for o in lob.objects if o.type == "security-console")
        self.assertTrue(lob.blocked(console.x, console.y))
        self.assertEqual(lob.area_at(2, 2), "security")
        self.assertIsNone(lob.area_at(12, 12))

    def test_every_room_and_lift_reachable_from_spawn(self):
        for lid, lv in self.levels.items():
            seen = reachable(lv, lv.spawn)
            for a in lv.areas:
                self.assertTrue(any(lv.area_at(x, y) == a.id for x, y in seen), f"{lid}: {a.id} unreachable")
            for o in lv.objects:
                if o.type == "lift":
                    t = self.types["lift"]
                    ring = {(o.x + dx, o.y + dy) for dx in range(-1, t.w + 1) for dy in range(-1, t.h + 1)}
                    self.assertTrue(ring & seen, f"{lid}: lift unreachable")

    def test_security_only_entered_through_its_door(self):
        lob = self.levels["lobby"]
        inside = lambda s: any(lob.area_at(x, y) == "security" for x, y in s)
        door = next(o for o in lob.objects if o.type == "door")
        self.assertTrue(inside(reachable(lob, lob.spawn)))
        self.assertFalse(inside(reachable(lob, lob.spawn, extra_blocked={(door.x, door.y)})))


class AccessTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = os.path.join(tmp.name, "o.db")
        self.a = access.AccessStore(self.path, admins={"boss"})

    def test_floor_needs_grant_lobby_open_security_admin_only(self):
        self.assertTrue(self.a.can_enter("u1", "lobby"))
        self.assertTrue(self.a.can_enter("u1", None))
        self.assertTrue(self.a.can_enter("u1", "room:meeting"))
        self.assertFalse(self.a.can_enter("u1", "floor:catice"))
        self.assertFalse(self.a.can_enter("u1", "security"))
        self.assertTrue(self.a.can_enter("boss", "security"))
        self.assertTrue(self.a.can_enter("boss", "floor:catice"))
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

    def test_only_floor_areas_can_be_granted_and_refusal_is_audited(self):
        with self.assertRaises(ValueError):
            self.a.set_grant("boss", "u1", "security", True)
        self.assertEqual(self.a.grants(), {})
        self.assertFalse(self.a.audit()[0]["ok"])

    def test_audit_newest_first_with_fields_and_limit(self):
        self.a.set_grant("boss", "u1", "floor:catice", True)
        self.a.set_grant("boss", "u1", "floor:catice", False)
        rows = self.a.audit()
        self.assertEqual([r["allowed"] for r in rows], [False, True])
        self.assertEqual(set(rows[0]), {"ts", "actor", "user", "area", "allowed", "ok"})
        self.assertEqual(rows[0]["user"], "u1")
        self.assertEqual(len(self.a.audit(limit=1)), 1)

    def test_users_remembered_and_renamed(self):
        self.a.remember_user("u1", "Ann")
        self.a.remember_user("u1", "Anna")
        self.assertEqual(self.a.users(), [("u1", "Anna")])

    def test_grants_survive_reopen(self):
        self.a.set_grant("boss", "u2", "floor:classmat", True)
        again = access.AccessStore(self.path, admins={"boss"})
        self.assertEqual(again.grants(), {"u2": {"floor:classmat"}})


class WorldTests(unittest.TestCase):
    def setUp(self):
        self.types = catalog.load(DATA / "catalog.json")
        self.levels = mapdata.load_levels(DATA, self.types)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.acc = access.AccessStore(os.path.join(tmp.name, "o.db"), admins={"boss"})
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
        self.assertFalse(self.w.move("u1", True, 0))
        self.assertFalse(self.w.move("nobody", 1, 0))
        self.assertEqual((p.x, p.y), start)
        # walk to the security door: a non-admin is stopped at it
        self.assertFalse(walk_into_area(self.w, "u1", "security"))

    def test_admin_passes_security_door(self):
        self.w.join("boss", "Boss")
        self.assertTrue(walk_into_area(self.w, "boss", "security"))

    def test_lift_needs_grant_then_eviction_on_revoke(self):
        self.w.join("u1", "U1")
        walk_to_lift(self.w, "u1")
        self.assertFalse(self.w.ride("u1", "floor:catice"))
        self.acc.set_grant("boss", "u1", "floor:catice", True)
        self.assertTrue(self.w.ride("u1", "floor:catice"))
        self.acc.set_grant("boss", "u1", "floor:catice", False)
        self.assertEqual(self.w.enforce(), ["u1"])
        self.assertEqual(self.w.players["u1"].level, "lobby")

    def test_ride_needs_lift_nearby(self):
        self.w.join("boss", "Boss")
        self.assertFalse(self.w.ride("boss", "floor:catice"))

    def test_rejoin_replaces_not_duplicates(self):
        self.w.join("u1", "U1")
        _, replaced = self.w.join("u1", "U1")
        self.assertTrue(replaced)
        self.assertEqual(len(self.w.players_on("lobby")), 1)
        self.w.leave("u1")
        self.assertEqual(self.w.players_on("lobby"), [])


if __name__ == "__main__":
    unittest.main()
