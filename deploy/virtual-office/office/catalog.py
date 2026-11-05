"""Object catalog: every fitting is defined once here and placed by map data."""
from __future__ import annotations
import json
import re
from dataclasses import dataclass

BEHAVIOURS = frozenset({"door", "flap-gate", "lift", "desk", "bookshelf", "filing-cabinet",
                        "board", "screen", "meeting-table", "security-console", "sign"})
TILE = 16
_COLOUR = re.compile(r"^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")


@dataclass(frozen=True)
class ObjectType:
    id: str
    w: int
    h: int
    blocks: bool
    behaviour: str | None
    pixels: list[str]  # h*16 rows of w*16 chars; "." is transparent, others key into palette
    palette: dict[str, str]


def _build(tid, d) -> ObjectType:
    try:
        t = ObjectType(tid, int(d["w"]), int(d["h"]), bool(d["blocks"]), d.get("behaviour"),
                       list(d["pixels"]), dict(d["palette"]))
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"catalog type {tid!r}: bad definition ({e!r})")
    if t.behaviour is not None and t.behaviour not in BEHAVIOURS:
        raise ValueError(f"catalog type {tid!r}: unknown behaviour {t.behaviour!r}")
    if t.w < 1 or t.h < 1:
        raise ValueError(f"catalog type {tid!r}: bad size")
    for k, v in t.palette.items():
        if len(k) != 1 or k == "." or not isinstance(v, str) or not _COLOUR.match(v):
            raise ValueError(f"catalog type {tid!r}: bad palette entry {k!r}")
    if len(t.pixels) != t.h * TILE:
        raise ValueError(f"catalog type {tid!r}: expected {t.h * TILE} pixel rows")
    for row in t.pixels:
        if len(row) != t.w * TILE:
            raise ValueError(f"catalog type {tid!r}: ragged pixel row")
        for ch in row:
            if ch != "." and ch not in t.palette:
                raise ValueError(f"catalog type {tid!r}: colour {ch!r} not in palette")
    return t


def load(path) -> dict[str, ObjectType]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {tid: _build(tid, d) for tid, d in raw.items()}
