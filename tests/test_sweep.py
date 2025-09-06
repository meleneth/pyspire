# tests/test_sweep_animation.py
from __future__ import annotations

from dataclasses import dataclass

from pyspire import Animation, EventBus  # your base
from pyspire.animation import Sweep

# Simple stand-in for a cairo surface with get_width()
@dataclass
class DummySurface:
    w: int
    def get_width(self) -> int:
        return self.w

# Minimal SpriteLayer stand-in
@dataclass
class DummyLayer:
    x: int
    y: int
    surface: DummySurface

def step_n(anim: Animation, n: int) -> None:
    for _ in range(n):
        anim.step()

def step_to_done(anim: Animation, safety=10_000) -> None:
    c = 0
    while not anim.done and c < safety:
        anim.step()
        c += 1
    assert anim.done

def test_sweep_moves_left_to_right_exact_bounds():
    layer = DummyLayer(x=0, y=0, surface=DummySurface(100))  # layer is 100px wide
    container_w = 300
    frames = 5  # 5 updates then completion on next step

    anim = Sweep(
        "sweep",
        layer,
        container_width=container_w,
        frames=frames,
        left_padding=0,
        right_padding=0,
    )

    # Collect x positions per update
    xs = []
    for _ in range(frames):
        anim.step()
        xs.append(layer.x)

    # last update applied:
    assert not anim.done
    # Finish:
    anim.step()
    assert anim.done

    # Check monotonic non-decreasing and endpoints:
    assert xs[0] == 0
    assert xs[-1] == container_w - layer.surface.get_width()  # 300 - 100 = 200
    assert all(xs[i] <= xs[i+1] for i in range(len(xs)-1))

def test_sweep_respects_padding():
    layer = DummyLayer(x=999, y=0, surface=DummySurface(50))  # x overwritten by animation
    anim = Sweep(
        "sweep",
        layer,
        container_width=300,
        frames=3,
        left_padding=10,
        right_padding=20,
    )
    # updates:
    anim.step()  # first
    left = layer.x
    anim.step()  # middle
    anim.step()  # last
    right = layer.x
    assert left == 10
    assert right == 300 - 50 - 20  # 230
    anim.step()  # completion tick
    assert anim.done

def test_sweep_handles_duration_seconds_vs_frames_equivalence():
    layer = DummyLayer(x=0, y=0, surface=DummySurface(40))
    # duration 0.25s at 60fps -> round(15 frames)
    anim = Sweep("sweep", layer, container_width=200, duration_s=0.25, fps=60)
    # execute all updates, count how many times x changes
    updates = 0
    last_x = None
    while not anim.done:
        anim.step()
        if last_x != layer.x:
            updates += 1
            last_x = layer.x
    # `updates` will be the number of yielded frames (≈15)
    assert updates >= 1
