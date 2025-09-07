from __future__ import annotations

from math import ceil
from typing import Any, Dict, Generator, Optional, Tuple

from ..animation_base import Animation
from .ease import ease_out_cubic, ease_in_cubic
from .geom import Point, Vec, normalize, center_of, distance_to_touch_along


class Bump(Animation):
    """
    Bump animation built on Animation base.

    name: fixed to "bump" so lifecycle events match previous usage:
      - bump_start, bump_paused, bump_resume, bump_completed
    Custom events:
      - bump_contact (fires at the moment of impact)
    """

    def __init__(
        self,
        subject: Any,                     # object whose x/y will be updated
        against: Any,                     # object we move toward then away from
        *,
        fps: int = 60,
        forward_time_s: float = 0.10,     # time to reach contact
        hold_time_s: float = 0.04,        # time to stay at contact
        return_time_s: float = 0.12,      # time to return to start
        ease_forward = ease_out_cubic,
        ease_return  = ease_in_cubic,
        epsilon: float = 0.0,             # shorten travel distance by this much
    ) -> None:
        super().__init__(name="bump", target=subject, fps=fps)
        self.against = against

        self.forward_time_s = float(forward_time_s)
        self.hold_time_s    = float(hold_time_s)
        self.return_time_s  = float(return_time_s)

        self.ease_forward = ease_forward
        self.ease_return  = ease_return
        self.epsilon = float(epsilon)

        # planned values (filled lazily)
        self._planned: bool = False
        self._start: Point = (0.0, 0.0)
        self._delta: Vec   = (0.0, 0.0)
        self._nf = 0  # forward frames
        self._nh = 0  # hold frames
        self._nr = 0  # return frames

    # ---- public helpers (useful in tests) ---------------------------------

    def plan_summary(self) -> Dict[str, Any]:
        """Expose the computed plan for tests/introspection."""
        self._ensure_plan()
        return {
            "start": self._start,
            "delta": self._delta,
            "frames": {
                "forward": self._nf,
                "hold": self._nh,
                "return": self._nr,
                "total": self._nf + self._nh + self._nr,
            },
        }

    # ---- Animation subclass contract --------------------------------------

    def _updates(self) -> Generator[Dict[str, Any], None, None]:
        """
        Yields dicts like {"x": ..., "y": ...} once per frame.
        Base class will apply these to self.target and handle pause/resume.
        """
        self._ensure_plan()
        sx, sy = self._start
        dx, dy = self._delta
        nf, nh, nr = self._nf, self._nh, self._nr

        # forward phase (1..nf) – ease to contact
        for i in range(1, nf + 1):
            t = i / nf
            a = self.ease_forward(t)
            yield {"x": sx + dx * a, "y": sy + dy * a}

        # contact (emit right at impact; keep position stable this frame)
        cx, cy = sx + dx, sy + dy
        self.bus.emit("bump_contact", {
            "source": self.target,
            "target": self.against,
            "at": {"x": cx, "y": cy},
        })
        yield {"x": cx, "y": cy}

        # hold phase (nh frames) – stay at contact
        for _ in range(nh):
            yield {"x": cx, "y": cy}

        # return phase (1..nr) – ease back to start
        for i in range(1, nr + 1):
            t = i / nr
            a = self.ease_return(t)
            rx = cx + (sx - cx) * a
            ry = cy + (sy - cy) * a
            yield {"x": rx, "y": ry}

        # ensure exact start at the very end (guards against easing rounding)
        yield {"x": sx, "y": sy}

        # StopIteration here; base will emit "bump_completed"

    # ---- internals ---------------------------------------------------------

    def _ensure_plan(self) -> None:
        if self._planned:
            return

        # record starting position from the subject (the animation target)
        sx, sy = float(getattr(self.target, "x")), float(getattr(self.target, "y"))
        self._start = (sx, sy)

        # unit direction from subject center toward against center
        scx, scy = center_of(self.target)
        tcx, tcy = center_of(self.against)
        vhat = normalize((tcx - scx, tcy - scy))

        # distance along vhat until subject touches against; back off epsilon
        dist = max(0.0, distance_to_touch_along(self.target, self.against, vhat) - self.epsilon)
        self._delta = (vhat[0] * dist, vhat[1] * dist)

        # frame counts
        self._nf = max(1, ceil(self.fps * self.forward_time_s))
        self._nh = max(0, ceil(self.fps * self.hold_time_s))
        self._nr = max(1, ceil(self.fps * self.return_time_s))

        self._planned = True
