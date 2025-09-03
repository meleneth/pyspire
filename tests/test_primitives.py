# tests/test_geometry.py
import math
import pytest
from dataclasses import FrozenInstanceError

# Change this import to wherever you defined these
# from your_module import Vec2, Size, Rect, lerp
from pyspire import Vec2, Size, Rect, lerp  # <- adjust as needed


# ---------- Vec2 ----------
def test_vec2_equality_and_immutability():
    a = Vec2(1.0, 2.0)
    b = Vec2(1.0, 2.0)
    c = Vec2(1.0, 3.0)
    assert a == b
    assert a != c

    with pytest.raises(FrozenInstanceError):
        a.x = 10  # type: ignore[attr-defined]


def test_vec2_iteration_len_getitem_unpack():
    v = Vec2(3.5, -1.25)
    assert len(v) == 2
    assert list(v) == [3.5, -1.25]
    assert v[0] == 3.5
    assert v[1] == -1.25
    with pytest.raises(IndexError):
        _ = v[2]
    x, y = v
    assert (x, y) == (3.5, -1.25)


def test_vec2_math_add_sub_mul_rmul_and_map_do_not_mutate():
    v = Vec2(2, 5)
    w = Vec2(-1, 3)

    assert v + w == Vec2(1, 8)
    assert v - w == Vec2(3, 2)
    assert v * 2 == Vec2(4, 10)
    assert 2 * v == Vec2(4, 10)

    # tuple interoperability
    assert v + (1, 1) == Vec2(3, 6)
    assert v - (1, 2) == Vec2(1, 3)

    # map convenience
    assert v.map(lambda z: z * 10) == Vec2(20, 50)

    # original unchanged
    assert v == Vec2(2, 5)


def test_vec2_with_x_with_y():
    v = Vec2(7, 9)
    assert v.with_x(100) == Vec2(100, 9)
    assert v.with_y(200) == Vec2(7, 200)
    # and original unchanged
    assert v == Vec2(7, 9)


# ---------- Size ----------
def test_size_equality_iteration_props_and_math():
    s = Size(100, 50)
    t = Size(25, 10)
    assert s.width == 100
    assert s.height == 50
    assert len(s) == 2
    assert list(s) == [100, 50]
    assert s[0] == 100
    assert s[1] == 50
    with pytest.raises(IndexError):
        _ = s[2]

    assert s + t == Size(125, 60)
    assert s - t == Size(75, 40)
    assert s * 0.5 == Size(50, 25)
    assert 2 * t == Size(50, 20)

    # tuple interoperability
    assert s + (1, 2) == Size(101, 52)
    assert s - (1, 2) == Size(99, 48)


# ---------- Rect ----------
def test_rect_construction_and_basic_props():
    r = Rect.from_xywh(10, 20, 200, 100)
    assert r.x == 10
    assert r.y == 20
    assert r.w == 200
    assert r.h == 100
    assert r.max_x == 210
    assert r.max_y == 120
    assert r.center == Vec2(110, 70)


def test_rect_inset_and_contains_half_open_edges():
    r = Rect.from_xywh(0, 0, 100, 50)
    r2 = r.inset(10, 5)
    assert (r2.x, r2.y, r2.w, r2.h) == (10, 5, 80, 40)

    # contains uses [x, max_x) and [y, max_y)
    assert r.contains(Vec2(0, 0)) is True
    assert r.contains(Vec2(99.9999, 49.9999)) is True
    assert r.contains(Vec2(100, 25)) is False  # right edge excluded
    assert r.contains(Vec2(50, 50)) is False   # bottom edge excluded
    assert r.contains(Vec2(-0.0001, 10)) is False
    assert r.contains(Vec2(10, -0.0001)) is False


@pytest.mark.parametrize(
    "anchor, expected",
    [
        ("topleft",      (10, 20)),
        ("top",          (10 + (200 - 80) / 2, 20)),
        ("topright",     (10 + 200 - 80, 20)),
        ("left",         (10, 20 + (100 - 40) / 2)),
        ("center",       (10 + (200 - 80) / 2, 20 + (100 - 40) / 2)),
        ("right",        (10 + 200 - 80, 20 + (100 - 40) / 2)),
        ("bottomleft",   (10, 20 + 100 - 40)),
        ("bottom",       (10 + (200 - 80) / 2, 20 + 100 - 40)),
        ("bottomright",  (10 + 200 - 80, 20 + 100 - 40)),
    ],
)
def test_rect_align_all_anchors(anchor, expected):
    outer = Rect.from_xywh(10, 20, 200, 100)
    child = Size(80, 40)
    pos = outer.align(child, anchor=anchor)
    assert pos == Vec2(*expected)


def test_rect_align_with_offset_and_invalid_anchor_raises():
    outer = Rect.from_xywh(0, 0, 100, 100)
    child = Size(10, 10)
    pos = outer.align(child, anchor="center", offset=Vec2(5, -3))
    assert pos == Vec2(45, 45) + Vec2(5, -3)

    with pytest.raises(KeyError):
        _ = outer.align(child, anchor="nope")


# ---------- lerp ----------
def test_lerp_vec2_and_size_types_and_values():
    a = Vec2(10, 10)
    b = Vec2(110, 50)
    mid = lerp(a, b, 0.5)
    assert isinstance(mid, Vec2)
    assert mid == Vec2(60, 30)

    s0 = Size(100, 50)
    s1 = Size(200, 150)
    q = lerp(s0, s1, 0.25)
    assert isinstance(q, Size)
    # use approx for floats in case of FP changes
    assert q.w == pytest.approx(125)
    assert q.h == pytest.approx(75)


def test_lerp_endpoints_and_out_of_range_t_extrapolates():
    a = Vec2(0, 0)
    b = Vec2(10, 20)
    assert lerp(a, b, 0.0) == a
    assert lerp(a, b, 1.0) == b
    # extrapolation is allowed by the ops
    assert lerp(a, b, 1.5) == Vec2(15, 30)
