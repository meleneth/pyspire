from __future__ import annotations

from typing import Any, Callable, Optional, Dict, Iterator
from ..animation_base import Animation

def _linear(t: float) -> float:
    return t

class Sweep(Animation):
    """
    Move a SpriteLayer horizontally within a container (e.g., a background)
    from left to right.

    Args:
      name: event name base
      target: SpriteLayer to move (must have `.x` and a way to get intrinsic width)
      container_width: width (px) of the background/container
      duration_s: seconds to complete (optional iff `frames` provided)
      frames: exact number of frames (optional; overrides duration_s)
      left_padding: starting left inset in pixels (default 0)
      right_padding: ending right inset in pixels (default 0)
      easing: easing fn t∈[0..1] -> [0..1] (default linear)

    Behavior:
      - Y is untouched; we only yield {"x": ...}
      - Completion is discovered on the *next* tick after the last update
        (per your chosen base-class contract).
    """
    def __init__(
        self,
        target: Any,
        *,
        container_width: int,
        duration_s: Optional[float] = None,
        frames: Optional[int] = None,
        left_padding: int = 0,
        right_padding: int = 0,
        easing: Callable[[float], float] = _linear,
        fps: int = 60
    ) -> None:
        super().__init__("sweep", target, fps=fps)
        if frames is None and duration_s is None:
            raise ValueError("Provide either frames or duration_s for Sweep.")
        self._frames: int = int(frames if frames is not None else max(1, round(duration_s * fps)))
        self._container_width = int(container_width)
        self._left_pad = int(left_padding)
        self._right_pad = int(right_padding)
        self._ease = easing

    # optional hint; if you later adopt total_frames() in the base, this will align
    def total_frames(self) -> Optional[int]:
        return self._frames

    # --- internals ---------------------------------------------------------

    def _layer_width(self) -> int:
        """Best-effort to get the intrinsic width of the target layer."""
        t = self.target
        # Common patterns:
        # - cairo surface: t.surface.get_width()
        # - explicit attr: t.width
        # - method: t.get_intrinsic_width()
        if hasattr(t, "surface") and hasattr(t.surface, "get_width"):
            return int(t.surface.get_width())
        if hasattr(t, "width"):
            return int(getattr(t, "width"))
        if hasattr(t, "get_intrinsic_width"):
            return int(t.get_intrinsic_width())
        # Fallback: if target has get_width() that returns x + width (your earlier draft),
        # try to derive intrinsic by subtracting current x.
        if hasattr(t, "get_width"):
            gw = int(t.get_width())
            x = int(getattr(t, "x", 0))
            return max(0, gw - x)
        raise AttributeError("Sweep target must expose a width (surface.get_width, .width, or get_intrinsic_width).")

    def _updates(self) -> Iterator[Dict[str, int]]:
        layer_w = self._layer_width()
        start_x = self._left_pad
        end_x = max(self._left_pad, self._container_width - layer_w - self._right_pad)

        # avoid division by zero in t (single-frame path places at end)
        n = self._frames
        if n <= 1:
            yield {"x": end_x}
            return

        for i in range(n):
            t = i / (n - 1)          # 0.0 .. 1.0 inclusive
            u = self._ease(t)        # eased parameter
            x = round(start_x + (end_x - start_x) * u)
            yield {"x": x}
