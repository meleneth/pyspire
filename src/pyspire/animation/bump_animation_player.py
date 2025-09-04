from dataclasses import dataclass
from typing import Optional, Any, Dict

from .bump import BumpAnimation
from pyspire import Tickable

@dataclass
class BumpAnimationPlayer(Tickable):
    bump: BumpAnimation
    _it: Optional[Any] = None
    _done: bool = False

    def _ensure_started(self) -> None:
        if self._it is None:
            # Use the existing generator; we will mutate bumper.x/y per step.
            self._it = self.bump.frames()

    def tick(self, frame_no: int) -> None:
        if self._done:
            return
        self._ensure_started()
        try:
            step: Dict[str, Any] = next(self._it)  # advance exactly one frame
            self.bump.bumper.x = step["x"]
            self.bump.bumper.y = step["y"]
            # (optional) if you ever emit per-frame events, you can read step["event"]
        except StopIteration:
            # Generator completed; BumpAnimation already published "bump_completed" if bus set
            self._done = True

    @property
    def done(self) -> bool:
        return self._done
