from __future__ import annotations
from dataclasses import dataclass, field
from math import ceil
from typing import Callable, Dict, Generator, Optional, Any, Iterator, Tuple

from pyspire import Tickable
from .ease import ease_out_cubic, ease_in_cubic
from .geom import Point, Vec, normalize, center_of, distance_to_touch_along

class EventBusProtocol:
    def emit(self, event: str, payload: Dict[str, Any]) -> None: ...

@dataclass
class Bump(Tickable):
    subject: Any
    target: Any
    bus: Optional[EventBusProtocol] = None

    fps: int = 60
    forward_time_s: float = 0.10
    hold_time_s: float    = 0.04
    return_time_s: float  = 0.12

    ease_forward: Callable[[float], float] = ease_out_cubic
    ease_return:  Callable[[float], float] = ease_in_cubic
    epsilon: float = 0.0

    # internal state
    _planned: bool = field(default=False, init=False)
    _start: Point = field(default=(0.0, 0.0), init=False)
    _delta: Vec   = field(default=(0.0, 0.0), init=False)
    _nf: int = field(default=0, init=False)
    _nh: int = field(default=0, init=False)
    _nr: int = field(default=0, init=False)
    _iter: Optional[Iterator[Dict[str, Any]]] = field(default=None, init=False)
    _done: bool = field(default=False, init=False)

    # ---------- Tickable ----------
    def tick(self, frame_no: int) -> None:
        if self._done:
            return
        if self._iter is None:
            # single source of truth: math + bus emitting live inside frames()
            self._iter = self.frames()
        try:
            step = next(self._iter)             # advance exactly one frame
            self.subject.x = step["x"]          # mutate based on yielded coords
            self.subject.y = step["y"]
            # step["event"] is informational; frames() already emitted on the bus
        except StopIteration:
            self._done = True

    @property
    def done(self) -> bool:
        return self._done

    # ---------- test/introspection helpers ----------
    def plan(self) -> Dict[str, Any]:
        self._ensure_plan()
        return {
            "start": self._start,
            "delta": self._delta,
            "frames": {
                "forward": self._nf, "hold": self._nh, "return": self._nr,
                "total": self._nf + self._nh + self._nr,
            },
        }

    # ---------- single source of math + events ----------
    def frames(self) -> Generator[Dict[str, Any], None, None]:
        """
        Yields per-frame dicts and emits bus events at exact moments.
        Does NOT mutate subject; the caller chooses to apply x/y.
        """
        self._ensure_plan()
        sx, sy = self._start
        dx, dy = self._delta
        nf, nh, nr = self._nf, self._nh, self._nr

        frame = 0

        # forward
        for i in range(1, nf + 1):
            t = i / nf
            a = self.ease_forward(t)
            yield {"frame": frame, "x": sx + dx * a, "y": sy + dy * a, "event": None}
            frame += 1

        # contact
        contact = {"x": sx + dx, "y": sy + dy}
        if self.bus is not None:
            self.bus.emit("bump", {"source": self.subject, "target": self.target,
                                   "at": contact, "frame": frame - 1})
        yield {"frame": frame - 1, "x": contact["x"], "y": contact["y"], "event": "bump"}

        # hold
        for _ in range(nh):
            yield {"frame": frame, "x": contact["x"], "y": contact["y"], "event": None}
            frame += 1

        # return
        for i in range(1, nr + 1):
            t = i / nr
            a = self.ease_return(t)
            rx = contact["x"] + (sx - contact["x"]) * a
            ry = contact["y"] + (sy - contact["y"]) * a
            yield {"frame": frame, "x": rx, "y": ry, "event": None}
            frame += 1

        if self.bus is not None:
            self.bus.emit("bump_completed", {
                "source": self.subject, "target": self.target,
                "at": {"x": sx, "y": sy}, "frame": frame - 1
            })
        yield {"frame": frame - 1, "x": sx, "y": sy, "event": "bump_completed"}

    # ---------- internals ----------
    def _ensure_plan(self) -> None:
        if self._planned:
            return
        self._start = (float(self.subject.x), float(self.subject.y))
        vhat = normalize((
            center_of(self.target)[0] - center_of(self.subject)[0],
            center_of(self.target)[1] - center_of(self.subject)[1],
        ))
        dist = max(0.0, distance_to_touch_along(self.subject, self.target, vhat) - self.epsilon)
        self._delta = (vhat[0] * dist, vhat[1] * dist)
        self._nf = max(1, ceil(self.fps * self.forward_time_s))
        self._nh = max(0, ceil(self.fps * self.hold_time_s))
        self._nr = max(1, ceil(self.fps * self.return_time_s))
        self._planned = True
