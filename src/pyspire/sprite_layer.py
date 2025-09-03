import os
from dataclasses import dataclass
import cairocffi as cairo

from collections import defaultdict
from typing import Callable, Dict, List, Any

@dataclass
class SpriteLayer:
    x: int
    y: int
    surface: cairo.ImageSurface

    def get_height(self):
        return self.y + self.surface.get_height()

    def get_width(self):
        return self.x + self.surface.get_width()
