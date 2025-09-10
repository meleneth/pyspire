# sprite.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

import cairocffi  # pycairo / cairocffi (whichever you’re using)

from .primitives import Vec2, Size, Rect, lerp
from .sprite_layer import SpriteLayer
from .event_bus import EventBus

@dataclass(slots=True)
class Sprite:
    name: str
    position: Vec2 = Vec2(0, 0)                    # replaces x,y
    layers: List[SpriteLayer] = field(default_factory=list)
    opacity: float = 1.0

    # --- ergonomic compat so existing code can still use .x / .y ---
    @property
    def x(self) -> float: return self.position.x
    @x.setter
    def x(self, v: float) -> None: self.position = self.position.with_x(v)

    @property
    def y(self) -> float: return self.position.y
    @y.setter
    def y(self, v: float) -> None: self.position = self.position.with_y(v)

    # --- size & bounds computed from layers ---
    @property
    def size(self) -> Size:
        if not self.layers:
            return Size(0, 0)
        w = max(layer.get_width() for layer in self.layers)
        h = max(layer.get_height() for layer in self.layers)
        return Size(w, h)

    def get_width(self) -> float:
        return self.size.width

    def get_height(self) -> float:
        return self.size.height

    @property
    def bounds(self) -> Rect:
        """World-space rect of the sprite."""
        return Rect(self.position, self.size)

    # --- movement/placement helpers (Vec2/Rect make these trivial) ---
    def move_by(self, delta: Vec2) -> None:
        self.position = self.position + delta

    def center_in(self, container: Rect) -> None:
        """Place sprite centered within container."""
        self.position = container.align(self.size, anchor="center")

    def align_in(self, container: Rect, anchor: str, offset: Vec2 = Vec2(0, 0)) -> None:
        """General placement within container via Rect.align anchors."""
        self.position = container.align(self.size, anchor=anchor, offset=offset)

    def tween_to(self, target: Vec2, t: float) -> None:
        """Simple in-place position interpolation (useful for animations)."""
        self.position = lerp(self.position, target, t)

    # --- layer management ---
    def add_image(self, filename: str, anchor: str = "topleft", offset: Vec2 = Vec2(0, 0)) -> SpriteLayer:
        """
        Load an image as a new layer and position it in sprite-local space using an anchor.
        Sprite-local = (0,0) at sprite's top-left; final draw uses sprite.position + layer.offset.
        """
        surface = cairocffi.ImageSurface.create_from_png(filename)
        layer = SpriteLayer(surface=surface)

        # Local rect for the sprite (origin at 0,0 in local space)
        local_sprite_rect = Rect.from_xywh(0, 0, max(self.size.w, layer.get_width()), max(self.size.h, layer.get_height()))
        layer_size = Size(layer.get_width(), layer.get_height())

        # Where should this layer's top-left be placed within the sprite?
        layer.offset = local_sprite_rect.align(layer_size, anchor=anchor, offset=offset)  # requires SpriteLayer.offset: Vec2
        self.layers.append(layer)
        return layer

    def replace_layer_image(self, layer_no: int, filename: str):
        surface = cairocffi.ImageSurface.create_from_png(filename)
        self.layers[layer_no].surface = surface

    # --- rendering example (using the affordances for clean math) ---
    def render(self, ctx: cairo.Context) -> None:
        for layer in self.layers:
            # final position = sprite.position (world) + layer.offset (sprite-local)
            px, py = tuple(self.position + layer.offset)
            ctx.save()
            ctx.set_source_surface(layer.surface, px, py)
            ctx.paint_with_alpha(self.opacity * layer.opacity)
            ctx.restore()
