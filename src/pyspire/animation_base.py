from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .event_bus import EventBus

class Animation:
    """
    Base class for PySpire animations.

    Contract:
      - default fps = 60
      - ticks advance by WHOLE FRAMES
      - pausing keeps re-applying the LAST UPDATE without advancing
      - each animation has its own EventBus
      - events: <name>_start, <name>_paused, <name>_resume, <name>_completed
      - queue_event_in(seconds, event, **data) schedules per-frame emission
      - subclass must implement `_updates()` generator yielding dicts of updates
      - `apply_update` applies arbitrary key/value pairs to target
    """
    def __init__(self, name: str, target: Any, fps: int = 60) -> None:
        self.name = name
        self.target = target
        self.fps = int(fps)
        self.bus = EventBus()

        self._started = False
        self._paused = False
        self._done = False

        self._frame: int = 0
        self._last_update: Dict[str, Any] = {}
        self._gen = None

        self._scheduled: Dict[int, List[Dict[str, Any]]] = {}

    # ---- lifecycle

    def start(self) -> None:
        if self._started:
            return
        self._gen = self._updates()
        self._started = True
        self.bus.emit(f"{self.name}_start")

    def pause(self) -> None:
        if not self._paused and not self._done:
            self._paused = True
            self.bus.emit(f"{self.name}_paused")

    def resume(self) -> None:
        if self._paused and not self._done:
            self._paused = False
            self.bus.emit(f"{self.name}_resume")

    def toggle_paused(self) -> None:
        if self._paused:
            self.resume()
        else:
            self.pause()

    @property
    def done(self) -> bool:
        return self._done

    # ---- core ticking
#    def tick(self, frame_no) -> None:
#        """Legacy alias for step()."""
#        self.step()

    def step(self) -> None:
        """
        Advance by exactly one frame. Emits scheduled events for this frame,
        then applies one update (or re-applies last when paused).
        """
        if self._done:
            return
        if self._paused:
            return
        if not self._started:
            self.start()

        # 1) scheduled events for this frame
        for payload in self._scheduled.pop(self._frame, []):
            self.bus.emit(payload["event"], **payload["data"])

        # 2) update application
        if self._paused:
            if self._last_update:
                self.apply_update(self._last_update)
            return

        try:
            update = next(self._gen)
            if not isinstance(update, dict):
                raise TypeError("Animation._updates must yield dict updates")
            self.apply_update(update)
            self._last_update = update
            self._frame += 1
        except StopIteration:
            self._done = True
            self.bus.emit(f"{self.name}_completed")

    # ---- scheduling

    def queue_event_in(self, seconds: float, event: str, **data: Any) -> None:
        frames_from_now = self.seconds_to_frames(seconds)
        self.queue_event_at_frame(self._frame + frames_from_now, event, **data)

    def queue_event_at_frame(self, frame_index: int, event: str, **data: Any) -> None:
        self._scheduled.setdefault(int(frame_index), []).append({"event": event, "data": dict(data)})

    # ---- helpers

    def seconds_to_frames(self, seconds: float) -> int:
        return int(round(seconds * self.fps))

    def frames_to_seconds(self, frames: int) -> float:
        return frames / float(self.fps)

    def apply_update(self, update: Dict[str, Any]) -> None:
        for k, v in update.items():
            try:
                setattr(self.target, k, v)
            except Exception:
                if hasattr(self.target, "__setitem__"):
                    self.target[k] = v
                else:
                    object.__setattr__(self.target, k, v)

    def __repr__(self) -> str:
        state = (
            "done" if self._done
            else "paused" if self._paused
            else "idle" if not self._started
            else "running"
        )
        queued = sum(len(v) for v in self._scheduled.values())
        last_keys = ",".join(sorted(self._last_update.keys())) if self._last_update else "-"
        tgt = f"{type(self.target).__name__}@{hex(id(self.target))}"
        return (
            f"Animation(name='{self.name}', state='{state}', fps={self.fps}, "
            f"frame={self._frame}, queued={queued}, last=[{last_keys}], target={tgt})"
        )

    def __str__(self) -> str:
        return self.__repr__()


    # ---- subclass API

    def _updates(self):
        raise NotImplementedError

