# tests/test_sprite_dimensions.py
import pytest
from dataclasses import dataclass

# Adjust this import to match your package layout:
# from yourpkg.sprite import Sprite
# For example, if Sprite lives in pyspire/sprite.py, use:
# from pyspire.sprite import Sprite
from pyspire.sprite import Sprite  # <-- change if needed


@dataclass
class DummyLayer:
    w: int
    h: int

    def get_width(self) -> int:
        return self.w

    def get_height(self) -> int:
        return self.h


def test_empty_sprite_dimensions_are_zero():
    s = Sprite(x=0, y=0, layers=[])
    assert s.get_width() == 0
    assert s.get_height() == 0


def test_width_is_max_of_layer_widths():
    layers = [DummyLayer(10, 5), DummyLayer(64, 32), DummyLayer(48, 90)]
    s = Sprite(x=0, y=0, layers=layers)
    assert s.get_width() == 64  # max of (10, 64, 48)


def test_height_is_max_of_layer_heights():
    layers = [DummyLayer(10, 5), DummyLayer(64, 32), DummyLayer(48, 90)]
    s = Sprite(x=0, y=0, layers=layers)
    assert s.get_height() == 90  # max of (5, 32, 90)


def test_dimensions_update_when_layers_change():
    s = Sprite(x=0, y=0, layers=[DummyLayer(10, 5)])
    assert s.get_width() == 10
    assert s.get_height() == 5

    # mutate layers
    s.layers.append(DummyLayer(128, 20))
    assert s.get_width() == 128
    assert s.get_height() == 20

    # add a taller layer
    s.layers.append(DummyLayer(50, 200))
    assert s.get_width() == 128
    assert s.get_height() == 200


def test_handles_single_layer():
    s = Sprite(x=5, y=7, layers=[DummyLayer(42, 24)])
    assert s.get_width() == 42
    assert s.get_height() == 24
