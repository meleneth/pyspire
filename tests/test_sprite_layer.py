# tests/test_sprite_layer.py
import pytest

# Adjust this import to your project layout:
# from pyspire.sprite_layer import SpriteLayer
from pyspire.sprite_layer import SpriteLayer  # <-- change if needed


class FakeSurface:
    """Minimal stand-in for cairo.ImageSurface with the same API used by SpriteLayer."""
    def __init__(self, w: int, h: int) -> None:
        self._w = w
        self._h = h

    def get_width(self) -> int:
        return self._w

    def get_height(self) -> int:
        return self._h


def test_sprite_layer_width_is_x_plus_surface_width():
    layer = SpriteLayer(x=10, y=20, surface=FakeSurface(64, 32))
    assert layer.get_width() == 10 + 64


def test_sprite_layer_height_is_y_plus_surface_height():
    layer = SpriteLayer(x=10, y=20, surface=FakeSurface(64, 32))
    assert layer.get_height() == 20 + 32


def test_zero_offsets_just_return_surface_dims():
    layer = SpriteLayer(x=0, y=0, surface=FakeSurface(100, 50))
    assert layer.get_width() == 100
    assert layer.get_height() == 50


def test_negative_offsets_are_reflected_in_totals():
    layer = SpriteLayer(x=-5, y=-7, surface=FakeSurface(10, 20))
    assert layer.get_width() == 5     # -5 + 10
    assert layer.get_height() == 13   # -7 + 20


@pytest.mark.parametrize(
    "x,y,w,h,expected_w,expected_h",
    [
        (1, 1, 1, 1, 2, 2),
        (5, 0, 0, 9, 5, 9),
        (0, 5, 9, 0, 9, 5),
        (123, 456, 321, 654, 444, 1110),
    ],
)
def test_parametrized_dimensions(x, y, w, h, expected_w, expected_h):
    layer = SpriteLayer(x=x, y=y, surface=FakeSurface(w, h))
    assert layer.get_width() == expected_w
    assert layer.get_height() == expected_h
