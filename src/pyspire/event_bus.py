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


    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        handlers = list(self._subs.get(event, ()))

        # If caller passed positional args, respect them verbatim.
        if args:
            for h in handlers:
                h(*args, **kwargs)
            return

        # Otherwise, try common styles in order: (payload_dict) -> (**kwargs) -> ()
        payload = dict(kwargs)
        for h in handlers:
            try:
                h(payload)       # handler expects one positional dict
                continue
            except TypeError:
                pass
            try:
                h(**payload)     # handler expects kwargs
                continue
            except TypeError:
                pass
            h()                  # handler takes no args

