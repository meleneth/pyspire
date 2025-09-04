from __future__ import annotations

from dataclasses import dataclass
from math import hypot, copysign, ceil
from typing import Callable, Generator, Iterable, Optional, Tuple, Dict, Any

from pyspire import Sprite

def _ease_out_cubic(t: float) -> float:
    # fast start, slow finish (forward)
    u = 1.0 - t
    return 1.0 - u * u * u

def _ease_in_cubic(t: float) -> float:
    # slow start, fast finish (return)
    return t * t * t

def _normalize(v: Vec) -> Vec:
    vx, vy = v
    d = hypot(vx, vy)
    if d == 0.0:
        return (1.0, 0.0)
    return (vx / d, vy / d)

def _dot(a: Vec, b: Vec) -> float:
    return a[0]*b[0] + a[1]*b[1]

def _center_of(sprite: Sprite) -> Point:
    return (sprite.x + sprite.get_width() * 0.5,
            sprite.y + sprite.get_height() * 0.5)

def _half_extent_along(sprite: Sprite, vhat: Vec) -> float:
    """Projection of an axis-aligned rectangle's half-extents onto direction vhat."""
    wx = abs(vhat[0]) * (sprite.get_width()  * 0.5)
    hy = abs(vhat[1]) * (sprite.get_height() * 0.5)
    return wx + hy

def _distance_to_touch_along(bumper: Sprite, target: Sprite, vhat: Vec) -> float:
    """How far to translate bumper along vhat so rectangles just touch."""
    cbx, cby = _center_of(bumper)
    ctx, cty = _center_of(target)
    cvec = (ctx - cbx, cty - cby)
    # signed separation along vhat

    sep = _dot(cvec, vhat)
    need = sep - (_half_extent_along(bumper, vhat) + _half_extent_along(target, vhat))
    # If already intersecting/overlapping along vhat, we consider distance 0
    return max(0.0, need)

@dataclass
class BumpAnimation:
    bumper: Sprite
    target: Sprite
    bus: Optional[EventBus] = None

    # Timing knobs
    fps: int = 60                      # YouTube-friendly default
    forward_time_s: float = 0.10       # time to move into contact
    hold_time_s: float = 0.04          # optional “at contact” pause
    return_time_s: float = 0.12        # time to return to start

    # Easing (override if you want)
    ease_forward: Callable[[float], float] = _ease_out_cubic
    ease_return:  Callable[[float], float] = _ease_in_cubic

    # How close is “touching” (in pixels)
    epsilon: float = 0.0

    def plan(self) -> Dict[str, Any]:
        """Compute a deterministic plan you can snapshot in tests."""
        start_pos: Point = (self.bumper.x, self.bumper.y)

        # Direction: from bumper center to target center
        cbx, cby = _center_of(self.bumper)
        ctx, cty = _center_of(self.target)
        vhat = _normalize((ctx - cbx, cty - cby))

        # Distance along vhat to bring perimeters into contact
        dist = max(0.0, _distance_to_touch_along(self.bumper, self.target, vhat) - self.epsilon)
        delta: Vec = (vhat[0] * dist, vhat[1] * dist)

        fwd_frames  = max(1, ceil(self.fps * self.forward_time_s))
        hold_frames = max(0, ceil(self.fps * self.hold_time_s))
        ret_frames  = max(1, ceil(self.fps * self.return_time_s))

        sep = _dot((ctx - cbx, cty - cby), vhat)
        hb = _half_extent_along(self.bumper, vhat)
        ht = _half_extent_along(self.target, vhat)
        need = sep - (hb + ht)

        return {
            "start": start_pos,
            "direction": vhat,
            "distance": dist,
            "delta": delta,
            "frames": {
                "forward": fwd_frames,
                "hold": hold_frames,
                "return": ret_frames,
                "total": fwd_frames + hold_frames + ret_frames,
            },
        }

    def frames(self) -> Generator[Dict[str, Any], None, None]:
        """
        Yields per-frame instructions:
          { "frame": n, "x": float, "y": float, "event": Optional[str] }
        Does not mutate the sprite; your renderer can consume this and set positions.
        """
        plan = self.plan()
        sx, sy = plan["start"]
        dx, dy = plan["delta"]
        nf = plan["frames"]["forward"]
        nh = plan["frames"]["hold"]
        nr = plan["frames"]["return"]

        frame_no = 0

        # Forward (ease toward contact)
        for i in range(1, nf + 1):
            t = i / nf
            a = self.ease_forward(t)
            yield {"frame": frame_no, "x": sx + dx * a, "y": sy + dy * a, "event": None}
            frame_no += 1

        # Emit event exactly at contact (once)
        bump_event_payload = {
            "source": self.bumper,
            "target": self.target,
            "at": {"x": sx + dx, "y": sy + dy},
            "frame": frame_no - 1,
        }
        if self.bus is not None:
            self.bus.publish("bump", bump_event_payload)

        # Optional hold at contact (useful for readability / emphasis)
        for _ in range(nh):
            yield {"frame": frame_no, "x": sx + dx, "y": sy + dy, "event": None}
            frame_no += 1

        # Return (ease back to start)
        for i in range(1, nr + 1):
            t = i / nr
            a = self.ease_return(t)
            # Interpolate from contact back to start
            rx = (sx + dx) + (sx - (sx + dx)) * a
            ry = (sy + dy) + (sy - (sy + dy)) * a
            yield {"frame": frame_no, "x": rx, "y": ry, "event": None}
            frame_no += 1

    def apply_in_place(self) -> None:
        """
        Mutates bumper.x/y over time. Call this during your render loop
        if you prefer side-effects instead of consuming `frames()`.
        """
        for step in self.frames():
            self.bumper.x = step["x"]
            self.bumper.y = step["y"]
            # your render/save logic happens externally per frame
