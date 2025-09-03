from dataclasses import dataclass
from collections import defaultdict
from typing import Callable, Dict, List, Any

class EventBus:
    def __init__(self) -> None:

        self._subs: Dict[str, List[Callable[..., Any]]] = defaultdict(list)

    # Vue-style: bus.on('event', handler)
    def on(self, event: str, handler: Callable[..., Any]) -> Callable[[], None]:
        self._subs[event].append(handler)
        def off() -> None:
            lst = self._subs.get(event)
            if not lst:
                return
            try:
                lst.remove(handler)
            except ValueError:
                pass
            if not lst:
                self._subs.pop(event, None)
        return off

    # Vue-style: bus.once('event', handler)

    def once(self, event: str, handler: Callable[..., Any]) -> Callable[[], None]:
        def wrapper(*args: Any, **kwargs: Any) -> None:
            off()
            handler(*args, **kwargs)
        off = self.on(event, wrapper)
        return off

    # Vue-style: bus.off('event', handler)
    def off(self, event: str, handler: Callable[..., Any]) -> None:
        lst = self._subs.get(event)
        if not lst:
            return
        try:
            lst.remove(handler)
        except ValueError:
            pass
        if not lst:
            self._subs.pop(event, None)

    # Vue-style: bus.emit('event', payload)
    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        # copy to avoid issues if handlers add/remove during emit

        for h in list(self._subs.get(event, ())):
            h(*args, **kwargs)

