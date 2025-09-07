# event_bus.py
from collections import defaultdict
from typing import Callable, Dict, List, Any, Iterable
import traceback

class EventBus:
    def __init__(self, *, raise_on_error: bool = True, log_errors: bool = True):
        self._subs: Dict[str, List[Callable[..., Any]]] = defaultdict(list)
        self._raise = raise_on_error
        self._log = log_errors

    def on(self, event: str, handler: Callable[..., Any]) -> Callable[[], None]:
        self._subs[event].append(handler)
        def off() -> None:
            lst = self._subs.get(event)
            if not lst: return
            try:
                lst.remove(handler)
            except ValueError:
                pass
            if not lst:
                self._subs.pop(event, None)
        return off

    def once(self, event: str, handler: Callable[..., Any]) -> Callable[[], None]:
        def wrapper(**payload: Any) -> None:
            off()
            handler(**payload)
        off = self.on(event, wrapper)
        return off

    def off(self, event: str, handler: Callable[..., Any]) -> None:
        lst = self._subs.get(event)
        if not lst: return
        try:
            lst.remove(handler)
        except ValueError:
            pass
        if not lst:
            self._subs.pop(event, None)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        # DEBUG: print(f"emit: {self} {event}")
        handlers: Iterable[Callable[..., Any]] = list(self._subs.get(event, ()))

        # Normalize to kwargs only.
        if args:
            if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
                kwargs = dict(args[0])  # support emit(event, payload_dict)
            else:
                # mixed/positional calling is disallowed to keep things sane
                msg = f"EventBus.emit('{event}') does not support positional args (got {args})"
                if self._log: print("[EventBus ERROR]", msg)
                if self._raise: raise TypeError(msg)
                return

        errors: List[str] = []
        for h in handlers:
            h(**kwargs)

        if errors and self._raise:
            raise RuntimeError(f"{len(errors)} error(s) during emit('{event}')\n" + "\n---\n".join(errors))
