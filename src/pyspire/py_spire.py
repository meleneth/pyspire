from dataclasses import dataclass, field
from collections import defaultdict
from typing import Callable, Dict, List, Any

import cairocffi

from .sprite import Sprite
from .primitives import Size
from .event_bus import EventBus
from .tickable import Tickable

@dataclass
class PySpire:
    size: Size
    base_filename: str
    sprites: List[Sprite] = field(default_factory=list)
    frame_no: int = 0
    bus: EventBus = field(default_factory=EventBus)
    animations: List[Tickable] = field(default_factory=list)
    done: bool = False

    def add_sprite(self, name):
        new_sprite = Sprite(name=name)
        self.sprites.append(new_sprite)
        return new_sprite

    def add_animation(self, a: Tickable) -> None:
        self.animations.append(a)

    def render_frame(self):
        for anim in list(self.animations):  # copy so we can remove safely
            anim.tick(self.frame_no)
            if anim.done:
                self.animations.remove(anim)
                self.bus.emit("animation.done", animation=anim)

        surface = cairocffi.ImageSurface(cairocffi.FORMAT_ARGB32, self.size.width, self.size.height)
        ctx = cairocffi.Context(surface)
        for sprite in self.sprites:
            sprite.render(ctx)
        surface.write_to_png(self.output_filename())
        self.frame_no = self.frame_no + 1

    def render_until_done(self):
        while not self.done:
              self.render_frame()

    def output_filename(self) -> str:
        return f"{self.base_filename}_{self.frame_no:06}.png"
