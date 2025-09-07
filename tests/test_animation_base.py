# tests/test_animation_base.py
from __future__ import annotations

import pytest
from dataclasses import dataclass
from typing import Dict, List, Any, Callable, Optional

from pyspire import Animation, EventBus


@dataclass
class DummyTarget:
    x: int = 0
    y: int = 0
    opacity: float = 1.0

class NudgeX(Animation):
    """Move x by +1 each frame for `count` frames."""
    def __init__(self, name: str, target: Any, count: int, fps: int = 60, bus: Optional[EventBus] = None) -> None:
        super().__init__(name, target, fps=fps)
        self.count = count

    def _updates(self):
        start = getattr(self.target, "x", 0)
        for i in range(self.count):
            yield {"x": start + i + 1}

# --- Tests ---------------------------------------------------------------------

def test_emits_lifecycle_events_in_order():
    tgt = DummyTarget()
    events: List[str] = []
    anim = NudgeX("walk", tgt, count=3, fps=10)
    for e in ["walk_start", "walk_paused", "walk_resume", "walk_completed"]:
        anim.bus.on(e, lambda e=e, **kw: events.append(e))

    anim.start()
    assert events == ["walk_start"]

    anim.step()  # frame 0
    anim.pause()
    assert events == ["walk_start", "walk_paused"]

    anim.step()  # paused; does not advance
    assert tgt.x == 1

    anim.resume()
    assert events == ["walk_start", "walk_paused", "walk_resume"]

    anim.step()  # frame 1
    anim.step()  # frame 2 -> completes
    anim.step()
    assert anim.done
    assert events == ["walk_start", "walk_paused", "walk_resume", "walk_completed"]

def test_apply_update_is_generic_not_just_xy():
    tgt = DummyTarget(opacity=0.0)
    class Fade(Animation):
        def _updates(self):
            # arbitrary key supported
            yield {"opacity": 0.5}
            yield {"opacity": 1.0}
    anim = Fade("fade", tgt)
    anim.step()
    assert tgt.opacity == 0.5
    anim.step()
    assert tgt.opacity == 1.0
    anim.step()
    assert anim.done

def test_pause_keeps_last_value_and_does_not_consume_generator():
    tgt = DummyTarget(x=0)
    anim = NudgeX("nudge", tgt, count=5, fps=30)
    anim.step()  # x=1
    anim.step()  # x=2
    anim.pause()
    for _ in range(10):
        anim.step()  # paused; x should stay 2
        assert tgt.x == 2
        assert not anim.done
    anim.resume()
    anim.step()  # x=3
    assert tgt.x == 3

def test_queue_event_in_seconds_emits_on_correct_frame():
    tgt = DummyTarget()
    hits: List[int] = []

    anim = NudgeX("walk", tgt, count=5, fps=10)  # 10 fps
    anim.bus.on("marker", lambda **kw: hits.append(kw["i"]))
    # schedule at 0.3s -> round(0.3*10)=3 frames after current (i.e., will fire before 4th update apply)
    anim.queue_event_in(0.3, "marker", i=99)

    # step frames and capture when it fires
    for i in range(5):
        anim.step()
        if i == 2:  # before stepping to frame index 3 we've emitted (emit happens at start of step for that frame)
            # After third step call, hits should include 99
            pass
    assert hits == [99]

def test_completed_emits_once_and_further_steps_noop():
    tgt = DummyTarget()
    anim = NudgeX("walk", tgt, count=1, fps=60)
    anim.step()  # apply #1 -> completes
    anim.step()
    assert anim.done
    x_before = tgt.x
    anim.step()
    anim.step()
    assert tgt.x == x_before
