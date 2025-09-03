# pyspire/sprite.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Protocol

from pyspire import Vec2, Size, Rect, lerp

class HasSize(Protocol):
    def get_width(self) -> int: ...
    def get_height(self) -> int: ...

@dataclass(slots=True)
class Sprite:
    # Back-compat with existing tests:
    x: int = 0
    y: int = 0
    name: str = ""                             # defaulted so tests don't need to pass it
    layers: List[HasSize] = field(default_factory=list)

    # --- computed dimension methods (what the tests call) ---
    def get_width(self) -> int:
        return max((layer.get_width() for layer in self.layers), default=0)

    def get_height(self) -> int:
        return max((layer.get_height() for layer in self.layers), default=0)

    # --- affordances: position/size/bounds using Vec2/Size/Rect ---
    @property
    def position(self) -> Vec2:
        return Vec2(float(self.x), float(self.y))

    @position.setter
    def position(self, p: Vec2) -> None:
        self.x = int(p.x)
        self.y = int(p.y)

    @property
    def size(self) -> Size:
        return Size(float(self.get_width()), float(self.get_height()))

    @property
    def bounds(self) -> Rect:
        return Rect(self.position, self.size)

    # --- helpers that play nicely with animation/math ---
    def move_by(self, delta: Vec2) -> None:
        self.position = self.position + delta

    def align_in(self, container: Rect, anchor: str = "center", offset: Vec2 = Vec2(0, 0)) -> None:
        self.position = container.align(self.size, anchor=anchor, offset=offset)

    def tween_to(self, target: Vec2, t: float) -> None:
        self.position = lerp(self.position, target, t)
