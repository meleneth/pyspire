from __future__ import annotations
from math import hypot
from typing import Tuple

Point = Tuple[float, float]
Vec   = Tuple[float, float]

def dot(a: Vec, b: Vec) -> float:
    return a[0]*b[0] + a[1]*b[1]

def normalize(v: Vec) -> Vec:
    x, y = v
    d = hypot(x, y)
    return (1.0, 0.0) if d == 0.0 else (x/d, y/d)

def center_of(sprite) -> Point:
    return (sprite.x + sprite.get_width() * 0.5,
            sprite.y + sprite.get_height() * 0.5)

def half_extent_along(sprite, vhat: Vec) -> float:
    # Axis-aligned rect projected onto vhat
    return abs(vhat[0]) * (sprite.get_width() * 0.5) + \
           abs(vhat[1]) * (sprite.get_height() * 0.5)

def distance_to_touch_along(bumper, target, vhat: Vec) -> float:
    cbx, cby = center_of(bumper)
    ctx, cty = center_of(target)
    sep = dot((ctx - cbx, cty - cby), vhat)
    need = sep - (half_extent_along(bumper, vhat) + half_extent_along(target, vhat))
    return max(0.0, need)
