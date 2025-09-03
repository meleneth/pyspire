from dataclasses import dataclass, field

from collections import defaultdict
from typing import Callable, Dict, List, Any

from .sprite_layer import SpriteLayer

@dataclass
class Sprite:
    x: int
    y: int
    layers: List[SpriteLayer] = field(default_factory=list)

    def get_height(self):
        if not self.layers:
            return 0
        return max(layer.get_height() for layer in self.layers)

    def get_width(self):
        if not self.layers:
            return 0
        return max(layer.get_width() for layer in self.layers)
