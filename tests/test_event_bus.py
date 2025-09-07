# test_event_bus.py
import pytest
from typing import List, Tuple, Any
from pyspire import EventBus

class TestEventBus:
    def test_on_and_emit_kwargs_only(self):
        bus = EventBus()
        seen: List[dict] = []

        def handler(**kwargs):
            seen.append(kwargs)

        bus.on("ping", handler)
        bus.emit("ping", a=3, b=4)

        assert seen == [{"a": 3, "b": 4}]

    def test_emit_rejects_positional_args(self):
        bus = EventBus()
        bus.on("oops", lambda **_: None)
        with pytest.raises(TypeError):
            bus.emit("oops", 1, 2, a=3)

    def test_off_via_method_stops_delivery(self):
        bus = EventBus()
        count = {"n": 0}

        def handler():
            count["n"] += 1

        bus.on("evt", handler)
        bus.emit("evt")
        bus.off("evt", handler)
        bus.emit("evt")

        assert count["n"] == 1

    def test_on_returns_off_callable_idempotent(self):
        bus = EventBus()
        calls = {"n": 0}

        def h():
            calls["n"] += 1

        off = bus.on("e", h)
        bus.emit("e")
        off()          # remove
        off()          # second time should be a no-op
        bus.emit("e")  # no delivery

        assert calls["n"] == 1

    def test_once_only_fires_once(self):
        bus = EventBus()
        calls = {"n": 0}

        def h(*, x):
            calls["n"] += x

        off = bus.once("one", h)  # off should be valid but unused here
        bus.emit("one", x=5)
        bus.emit("one", x=5)

        assert calls["n"] == 5
        # off() should be safe even after it already unsubscribed itself
        off()

    def test_multiple_handlers_preserve_order(self):
        bus = EventBus()
        order: List[int] = []

        def h1():
            order.append(1)

        def h2():
            order.append(2)

        def h3():
            order.append(3)

        bus.on("seq", h1)
        bus.on("seq", h2)
        bus.on("seq", h3)

        bus.emit("seq")
        assert order == [1, 2, 3]

    def test_emit_safe_if_handler_removes_self(self):
        bus = EventBus()
        calls: List[str] = []

        def h1():
            calls.append("h1")
            bus.off("boom", h1)  # remove during emit

        def h2():
            calls.append("h2")

        bus.on("boom", h1)
        bus.on("boom", h2)

        # Because emit iterates over a snapshot, both should run this round
        bus.emit("boom")
        assert calls == ["h1", "h2"]

        # h1 was removed; next emit only calls h2
        calls.clear()
        bus.emit("boom")
        assert calls == ["h2"]

    def test_emit_safe_if_handler_adds_new_handler(self):
        bus = EventBus()
        calls: List[str] = []

        def h_add():
            calls.append("add")
            # Adding a new handler during emit should NOT run in the same cycle
            bus.on("grow", lambda: calls.append("late"))

        def h_other():
            calls.append("other")

        bus.on("grow", h_add)
        bus.on("grow", h_other)

        bus.emit("grow")
        # Only the original handlers fire in this cycle
        assert calls == ["add", "other"]

        calls.clear()
        bus.emit("grow")
        # Now the newly-added handler participates
        assert calls == ["add", "other", "late"]

    def test_off_nonexistent_is_noop_and_event_key_cleared(self):
        bus = EventBus()
        # Removing non-existent event/handler should not raise
        bus.off("missing", lambda: None)

        # Add & then remove to clear key
        h = lambda: None
        bus.on("x", h)
        bus.off("x", h)

        # Private internals: verify event key was removed when list became empty
        assert "x" not in bus._subs

    def test_emit_with_no_handlers_is_noop(self):
        bus = EventBus()
        # Should not raise
        bus.emit("nobody")
