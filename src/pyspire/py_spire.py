from dataclasses import dataclass, field

from collections import defaultdict
from typing import Callable, Dict, List, Any

from .sprite import Sprite
from .primitives import Size

@dataclass
class PySpire:
    size: Size
    base_filename: str
    sprites: List[Sprite] = field(default_factory=list)

    def add_sprite(self, name):
        new_sprite = Sprite(name=name)
        self.sprites.append(new_sprite)
        return new_sprite

