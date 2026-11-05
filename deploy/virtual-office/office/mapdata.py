"""Levels from Tiled-compatible JSON maps."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass

from .catalog import TILE, ObjectType


@dataclass
class Obj:
    id: int
    type: str
    x: int
    y: int
    props: dict


@dataclass
class Area:
    id: str
    x: int
    y: int
    w: int
    h: int


@dataclass
class Level:
    id: str
    name: str
    width: int
    height: int
    walls: list[list[bool]]
    objects: list[Obj]
    areas: list[Area]
    spawn: tuple[int, int]
    types: dict[str, ObjectType] | None = None

    def area_at(self, x, y):
        for a in self.areas:
            if a.x <= x < a.x + a.w and a.y <= y < a.y + a.h:
                return a.id
        return None

    def blocked(self, x, y) -> bool:
        if not (0 <= x < self.width and 0 <= y < self.height) or self.walls[y][x]:
            return True
        for o in self.objects:
            t = self.types[o.type]
            if t.blocks and o.x <= x < o.x + t.w and o.y <= y < o.y + t.h:
                return True
        return False


def _layer(tmap, name, kind):
    for ly in tmap.get("layers", []):
        if ly.get("name") == name and ly.get("type") == kind:
            return ly
    raise ValueError(f"map has no {kind} layer {name!r}")


def _read(lid, name, tmap, types) -> Level:
    if tmap.get("tilewidth") != TILE or tmap.get("tileheight") != TILE:
        raise ValueError(f"level {lid}: tiles must be {TILE}px")
    w, h = tmap["width"], tmap["height"]
    data = _layer(tmap, "walls", "tilelayer")["data"]
    if len(data) != w * h:
        raise ValueError(f"level {lid}: walls layer size mismatch")
    walls = [[bool(data[y * w + x]) for x in range(w)] for y in range(h)]
    areas = [Area(a["name"], int(a["x"]) // TILE, int(a["y"]) // TILE, int(a["width"]) // TILE, int(a["height"]) // TILE)
             for a in _layer(tmap, "areas", "objectgroup")["objects"]]
    objs = []
    for o in _layer(tmap, "objects", "objectgroup")["objects"]:
        typ = o.get("type") or o.get("class")
        if typ not in types:
            raise ValueError(f"level {lid}: unknown object type {typ!r}")
        props = {p["name"]: p["value"] for p in o.get("properties", [])}
        objs.append(Obj(o.get("id", len(objs) + 1), typ, int(o["x"]) // TILE, int(o["y"]) // TILE, props))
    spawns = [o for o in objs if o.type == "spawn"]
    if not spawns:
        raise ValueError(f"level {lid}: no spawn object")
    return Level(lid, name, w, h, walls, objs, areas, (spawns[0].x, spawns[0].y), types)


def _check(lv: Level, level_ids):
    taken = {}
    area_ids = {a.id for a in lv.areas}
    for o in lv.objects:
        t = lv.types[o.type]
        if o.x < 0 or o.y < 0 or o.x + t.w > lv.width or o.y + t.h > lv.height:
            raise ValueError(f"level {lv.id}: {o.type} at ({o.x},{o.y}) is off the map")
        if t.blocks:
            for dx in range(t.w):
                for dy in range(t.h):
                    cell = (o.x + dx, o.y + dy)
                    if cell in taken:
                        raise ValueError(f"level {lv.id}: {o.type} overlaps {taken[cell]} at {cell}")
                    taken[cell] = o.type
        if t.behaviour == "door" and o.props.get("area") not in area_ids:
            raise ValueError(f"level {lv.id}: door area {o.props.get('area')!r} is not an area here")
        if t.behaviour == "lift":
            for dest in str(o.props.get("to", "")).split(","):
                if dest not in level_ids:
                    raise ValueError(f"level {lv.id}: lift goes to unknown level {dest!r}")


def load_levels(data_dir, types) -> dict[str, Level]:
    with open(os.path.join(data_dir, "levels.json"), encoding="utf-8") as f:
        spec = json.load(f)["levels"]
    levels = {}
    for lid, d in spec.items():
        with open(os.path.join(data_dir, d["map"]), encoding="utf-8") as f:
            levels[lid] = _read(lid, d["name"], json.load(f), types)
    for lv in levels.values():
        _check(lv, set(levels))
    return levels
