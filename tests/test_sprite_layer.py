# tests/test_sprite_layer.py
from __future__ import annotations
from pyspire import Vec2, Size, Rect, SpriteLayer

class FakeSurface:
    def __init__(self, w: int, h: int) -> None:
        self._w, self._h = w, h
    def get_width(self) -> int: return self._w
    def get_height(self) -> int: return self._h


def test_size_and_extents_include_offset():
    layer = SpriteLayer(surface=FakeSurface(100, 50))
    assert layer.width == 100
    assert layer.height == 50
    assert layer.get_width() == 100     # offset (0) + width
    assert layer.get_height() == 50

    layer.offset = Vec2(10, 20)
    assert layer.get_width() == 110     # 10 + 100
    assert layer.get_height() == 70     # 20 + 50


def test_back_compat_x_y_properties():
    layer = SpriteLayer(surface=FakeSurface(10, 10))
    layer.x = 7
    layer.y = 9
    assert layer.offset == Vec2(7, 9)
    assert (layer.x, layer.y) == (7, 9)


def test_center_over_another_layer():
    bg = SpriteLayer(surface=FakeSurface(200, 120))          # offset (0,0)
    txt = SpriteLayer(surface=FakeSurface(140, 40))
    txt.center(bg)
    # Centered at ((200-140)/2, (120-40)/2)
    assert (txt.offset.x, txt.offset.y) == (30, 40)


def test_align_to_rect_with_anchor_and_offset():
    target_rect = Rect.from_xywh(10, 20, 200, 100)
    badge = SpriteLayer(surface=FakeSurface(20, 10))

    badge.align(target_rect, anchor="bottomright", offset=Vec2(-4, -6))
    # bottom-right is (10+200-20, 20+100-10) = (190, 110); apply offset (-4,-6)
    assert (badge.offset.x, badge.offset.y) == (186, 104)


def test_scale_affects_size_and_extents():
    layer = SpriteLayer(surface=FakeSurface(100, 50), offset=Vec2(5, 5), scale=1.5)
    # width/height scaled; extents include offset
    assert layer.width == 150
    assert layer.height == 75
    assert layer.get_width() == 155
    assert layer.get_height() == 80


def test_rect_local_matches_offset_and_size():
    layer = SpriteLayer(surface=FakeSurface(64, 32), offset=Vec2(8, 12))
    r = layer.rect_local
    assert (r.x, r.y, r.w, r.h) == (8, 12, 64, 32)
