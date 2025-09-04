from dataclasses import dataclass
from typing import Optional, Any, Dict

class Tickable:
    def tick(self, frame_no: int) -> None: ...
    @property
    def done(self) -> bool: ...

