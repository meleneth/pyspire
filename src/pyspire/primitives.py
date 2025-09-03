from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, runtime_checkable, Tuple, Union

# --- tuple-friendly aliases
XY = Tuple[float, float]
WH = Tuple[float, float]

# --- generic interpolation contract (lets your animator stay generic)
@runtime_checkable
class Interpolatable(Protocol):
    def __add__(self, other: object) -> object: ...
    def __sub__(self, other: object) -> object: ...
    def __mul__(self, scalar: float) -> object: ...

def lerp(a: Interpolatable, b: Interpolatable, t: float) -> Interpolatable:
    return a + (b - a) * t

# --- core value types

@dataclass(frozen=True, slots=True)
class Vec2:
    x: float
    y: float

    # tuple ergonomics
    def __iter__(self):  # allows: x, y = vec
        yield self.x; yield self.y
    def __len__(self): return 2
    def __getitem__(self, i: int) -> float:
        if i == 0: return self.x
        if i == 1: return self.y
        raise IndexError

    # math (supports Interpolatable)
    def __add__(self, other: Union["Vec2", XY]) -> "Vec2":
        ox, oy = (other if isinstance(other, tuple) else (other.x, other.y))
        return Vec2(self.x + ox, self.y + oy)

    def __sub__(self, other: Union["Vec2", XY]) -> "Vec2":
        ox, oy = (other if isinstance(other, tuple) else (other.x, other.y))
        return Vec2(self.x - ox, self.y - oy)

    def __mul__(self, s: float) -> "Vec2":
        return Vec2(self.x * s, self.y * s)
    __rmul__ = __mul__

    def map(self, f) -> "Vec2":  # convenience
        return Vec2(f(self.x), f(self.y))

    def with_x(self, x: float) -> "Vec2": return Vec2(x, self.y)
    def with_y(self, y: float) -> "Vec2": return Vec2(self.x, y)

@dataclass(frozen=True, slots=True)
class Size:
    w: float
    h: float

    # synonyms for ergonomics
    @property
    def width(self) -> float: return self.w
    @property
    def height(self) -> float: return self.h

    def __iter__(self):
        yield self.w; yield self.h
    def __len__(self): return 2
    def __getitem__(self, i: int) -> float:
        if i == 0: return self.w
        if i == 1: return self.h
        raise IndexError

    def __add__(self, other: Union["Size", WH]) -> "Size":
        ow, oh = (other if isinstance(other, tuple) else (other.w, other.h))
        return Size(self.w + ow, self.h + oh)

    def __sub__(self, other: Union["Size", WH]) -> "Size":
        ow, oh = (other if isinstance(other, tuple) else (other.w, other.h))
        return Size(self.w - ow, self.h - oh)

    def __mul__(self, s: float) -> "Size":
        return Size(self.w * s, self.h * s)
    __rmul__ = __mul__

@dataclass(frozen=True, slots=True)
class Rect:
    origin: Vec2  # top-left (x,y)
    size: Size    # (w,h)

    # handy props
    @property
    def x(self) -> float: return self.origin.x
    @property
    def y(self) -> float: return self.origin.y
    @property
    def w(self) -> float: return self.size.w
    @property
    def h(self) -> float: return self.size.h
    @property
    def max_x(self) -> float: return self.x + self.w
    @property
    def max_y(self) -> float: return self.y + self.h
    @property
    def center(self) -> Vec2: return Vec2(self.x + self.w/2, self.y + self.h/2)

    @staticmethod
    def from_xywh(x: float, y: float, w: float, h: float) -> "Rect":
        return Rect(Vec2(x, y), Size(w, h))

    def inset(self, dx: float, dy: float) -> "Rect":
        return Rect(Vec2(self.x + dx, self.y + dy), Size(self.w - 2*dx, self.h - 2*dy))

    def contains(self, p: Union[Vec2, XY]) -> bool:
        px, py = (p if isinstance(p, tuple) else (p.x, p.y))
        return self.x <= px < self.max_x and self.y <= py < self.max_y

    def align(self, child: Size, anchor: str = "center", offset: Vec2 = Vec2(0, 0)) -> Vec2:
        ax, ay = {
            "topleft":   (self.x, self.y),
            "top":       (self.x + (self.w - child.w)/2, self.y),
            "topright":  (self.max_x - child.w, self.y),
            "left":      (self.x, self.y + (self.h - child.h)/2),
            "center":    (self.x + (self.w - child.w)/2, self.y + (self.h - child.h)/2),
            "right":     (self.max_x - child.w, self.y + (self.h - child.h)/2),
            "bottomleft":(self.x, self.max_y - child.h),
            "bottom":    (self.x + (self.w - child.w)/2, self.max_y - child.h),
            "bottomright":(self.max_x - child.w, self.max_y - child.h),
        }[anchor]
        return Vec2(ax, ay) + offset
