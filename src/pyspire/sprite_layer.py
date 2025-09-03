# pyspire/sprite_layer.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Union

import cairocffi

from .primitives import Vec2, Size, Rect

class SurfaceLike(Protocol):
    def get_width(self) -> int: ...
    def get_height(self) -> int: ...


@dataclass(slots=True)
class SpriteLayer:
    """
    A single layer within a Sprite.

    - `offset` is the top-left position in sprite-local coordinates.
    - `size` comes from the underlying surface (optionally scaled).
    - `get_width()` / `get_height()` return **extents** (offset + size), matching
      your earlier usage where sprite size = max over layer extents.
    """
    surface: SurfaceLike
    name: str = ""
    offset: Vec2 = Vec2(0, 0)
    scale: float = 1.0  # uniform scale; extend to Vec2 if you want non-uniform

    # --- Back-compat sugar for code that still uses .x / .y ---
    @property
    def x(self) -> float: return self.offset.x
    @x.setter
    def x(self, v: float) -> None: self.offset = self.offset.with_x(v)

    @property
    def y(self) -> float: return self.offset.y
    @y.setter
    def y(self, v: float) -> None: self.offset = self.offset.with_y(v)

    # --- Size & rect (no offset baked into size) ---
    @property
    def width(self) -> float:
        return float(self.surface.get_width()) * self.scale

    @property
    def height(self) -> float:
        return float(self.surface.get_height()) * self.scale

    @property
    def size(self) -> Size:
        return Size(self.width, self.height)

    @property
    def rect_local(self) -> Rect:
        """This layer's rectangle in sprite-local coordinates."""
        return Rect(self.offset, self.size)

    # --- Extents API (offset + size), preserving your earlier semantics ---
    def get_width(self) -> int:
        """Rightmost extent in local space (offset.x + width)."""
        return int(self.offset.x + self.width)

    def get_height(self) -> int:
        """Bottom extent in local space (offset.y + height)."""
        return int(self.offset.y + self.height)

    # --- Centering / aligning helpers ---
    def align(self, target: Union["SpriteLayer", Rect], *, anchor: str = "center", offset: Vec2 = Vec2(0, 0)) -> None:
        """
        Place this layer within `target` (another layer's rect or a Rect),
        using Rect.align anchors: 'topleft','top','topright','left','center',
        'right','bottomleft','bottom','bottomright'.
        """
        target_rect = target.rect_local if isinstance(target, SpriteLayer) else target
        self.offset = target_rect.align(self.size, anchor=anchor, offset=offset)

    def center(self, target: Union["SpriteLayer", Rect]) -> None:
        """Convenience: center within the target."""
        self.align(target, anchor="center")

    # Aliases for your WIP API
    def center_on(self, target: Union["SpriteLayer", Rect]) -> None:
        self.center(target)

    # Legacy helpers you referenced
    def get_image_center_x(self) -> float:
        return self.offset.x + self.width / 2.0

    def get_image_center_y(self) -> float:
        return self.offset.y + self.height / 2.0
