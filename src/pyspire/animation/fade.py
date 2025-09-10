from __future__ import annotations

from typing import Any, Callable, Optional, Dict, Iterator
from ..animation_base import Animation

def _linear(t: float) -> float:
    return t

def _clamp01(x: float) -> float:
    if x != x:  # NaN guard
        return 1.0
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else float(x))

class Fade(Animation):
    """
    Animate target.opacity from start -> end.

    Args:
      target: Any object with a float `.opacity` attribute in [0..1]
      duration_s: seconds to complete (optional iff `frames` provided)
      frames: exact number of frames (optional; overrides duration_s)
      start: starting opacity (default 0.0 if target has no opacity yet)
      end: ending opacity (default 1.0)
      easing: easing fn t∈[0..1] -> [0..1] (default linear)
      fps: frames per second (default 60)

    Behavior:
      - Yields {"opacity": value} each tick.
      - If `frames <= 1`, we snap directly to `end`.
      - Opacity values are clamped to [0..1].
    """
    def __init__(
        self,
        target: Any,
        *,
        duration_s: Optional[float] = None,
        frames: Optional[int] = None,
        start: Optional[float] = None,
        end: float = 1.0,
        easing: Callable[[float], float] = _linear,
        fps: int = 60,
    ) -> None:
        super().__init__("fade", target, fps=fps)
        if frames is None and duration_s is None:
            raise ValueError("Provide either frames or duration_s for Fade.")
        self._frames: int = int(frames if frames is not None else max(1, round(duration_s * fps)))
        # If start not provided, try current target.opacity, else default to 0.0
        cur = getattr(target, "opacity", 0.0)
        self._start: float = _clamp01(cur if start is None else start)
        self._end: float = _clamp01(end)
        self._ease = easing

    # optional hint for your base if it uses it
    def total_frames(self) -> Optional[int]:
        return self._frames

    # --- internals ---------------------------------------------------------

    def _updates(self) -> Iterator[Dict[str, float]]:
        n = self._frames
        s = self._start
        e = self._end

        if n <= 1:
            yield {"opacity": e}
            return

        for i in range(n):
            t = i / (n - 1)      # 0.0 .. 1.0 inclusive
            u = self._ease(t)    # eased progress
            v = s + (e - s) * u
            # light snapping to reduce float fuzz at the ends
            if v < 1e-6: v = 0.0
            elif 1.0 - v < 1e-6: v = 1.0
            yield {"opacity": _clamp01(v)}
