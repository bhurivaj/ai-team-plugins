"""Server-authoritative world: who stands where, and what they may do."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Player:
    id: str
    name: str
    level: str
    x: int
    y: int


class World:
    def __init__(self, levels, access):
        self.levels = levels
        self.access = access
        self.players: dict[str, Player] = {}

    def _to_lobby(self, p):
        p.level = "lobby"
        p.x, p.y = self.levels["lobby"].spawn

    def join(self, user_id, name):
        replaced = user_id in self.players
        p = self.players[user_id] = Player(user_id, name, "lobby", 0, 0)
        self._to_lobby(p)
        return p, replaced

    def leave(self, user_id):
        self.players.pop(user_id, None)

    def _may_stand(self, user_id, lv, x, y):
        ok = self.access.can_enter
        if not (ok(user_id, lv.id) and ok(user_id, lv.area_at(x, y))):
            return False
        for o in lv.objects:  # a door's own tile needs its area, even where the area map is silent
            if o.x == x and o.y == y and lv.types[o.type].behaviour == "door" and not ok(user_id, o.props.get("area")):
                return False
        return True

    def move(self, user_id, dx, dy):
        p = self.players.get(user_id)
        if p is None or type(dx) is not int or type(dy) is not int or abs(dx) + abs(dy) != 1:
            return False
        lv = self.levels[p.level]
        x, y = p.x + dx, p.y + dy
        if lv.blocked(x, y) or not self._may_stand(user_id, lv, x, y):
            return False
        p.x, p.y = x, y
        return True

    def near(self, user_id, behaviour):
        """The object with this behaviour the player touches (its footprint plus one tile), else None."""
        p = self.players.get(user_id)
        if p is None:
            return None
        lv = self.levels[p.level]
        for o in lv.objects:
            t = lv.types[o.type]
            if t.behaviour == behaviour and o.x - 1 <= p.x <= o.x + t.w and o.y - 1 <= p.y <= o.y + t.h:
                return o
        return None

    def _arrival(self, user_id, level_id):
        """A free tile next to the target level's lift, so a ride lands at the lift; the spawn if none."""
        lv = self.levels[level_id]
        for o in lv.objects:
            t = lv.types[o.type]
            if t.behaviour != "lift":
                continue
            ring = ([(x, o.y + t.h) for x in range(o.x, o.x + t.w)] + [(o.x - 1, y) for y in range(o.y, o.y + t.h)]
                    + [(o.x + t.w, y) for y in range(o.y, o.y + t.h)] + [(x, o.y - 1) for x in range(o.x, o.x + t.w)])
            for x, y in ring:
                if not lv.blocked(x, y) and self._may_stand(user_id, lv, x, y):
                    return x, y
        return lv.spawn

    def ride(self, user_id, to_level):
        lift = self.near(user_id, "lift")
        if (lift is None or to_level not in self.levels or not self.access.can_enter(user_id, to_level)
                or to_level not in str(lift.props.get("to", "")).split(",")):
            return False
        p = self.players[user_id]
        p.level = to_level
        p.x, p.y = self._arrival(user_id, to_level)
        return True

    def enforce(self):
        out = []
        for p in self.players.values():
            if not self._may_stand(p.id, self.levels[p.level], p.x, p.y):
                self._to_lobby(p)
                out.append(p.id)
        return out

    def players_on(self, level_id):
        return [{"id": p.id, "name": p.name, "x": p.x, "y": p.y} for p in self.players.values() if p.level == level_id]
