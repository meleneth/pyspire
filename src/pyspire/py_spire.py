from dataclasses import dataclass, field
from collections import defaultdict
from typing import Callable, Dict, List, Any

import cairocffi

from .sprite import Sprite
from .primitives import Size

@dataclass
class PySpire:
    size: Size
    base_filename: str
    sprites: List[Sprite] = field(default_factory=list)
    frame_no: int = 0

    def add_sprite(self, name):
        new_sprite = Sprite(name=name)
        self.sprites.append(new_sprite)
        return new_sprite

    def render_frame(self):
        surface = cairocffi.ImageSurface(cairocffi.FORMAT_ARGB32, self.size.width, self.size.height)
        ctx = cairocffi.Context(surface)
        for sprite in self.sprites:
            sprite.render(ctx)
        surface.write_to_png(self.output_filename())
        self.frame_no = self.frame_no + 1

    def output_filename(self) -> str:
        return f"{self.base_filename}_{self.frame_no:06}.png"
