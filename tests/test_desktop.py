import sys
from types import SimpleNamespace

from image2prompt import desktop


def test_desktop_uses_internal_window_and_closes_server(monkeypatch) -> None:
    events = []

    class ClosingEvent:
        def __iadd__(self, callback):
            events.append(("on_closing", callback))
            return self

    def create_window(*args, **kwargs):
        events.append(("window", args, kwargs))
        return SimpleNamespace(events=SimpleNamespace(closing=ClosingEvent()))

    class App:
        def queue(self, **kwargs):
            events.append(("queue", kwargs))
            return self

        def launch(self, **kwargs):
            events.append(("launch", kwargs))
            return None, "http://127.0.0.1:7860/", None

        def close(self, **kwargs):
            events.append(("close", kwargs))

    monkeypatch.setattr(desktop, "build_app", App)
    monkeypatch.setattr(desktop, "shutdown_runtime", lambda: events.append(("shutdown",)))
    monkeypatch.setitem(
        sys.modules,
        "webview",
        SimpleNamespace(
            create_window=create_window,
            start=lambda: events.append(("start",)),
        ),
    )

    desktop.main()

    launch = next(event for event in events if event[0] == "launch")
    assert launch[1]["inbrowser"] is False
    assert launch[1]["prevent_thread_lock"] is True
    assert [event[0] for event in events[-5:]] == ["window", "on_closing", "start", "shutdown", "close"]
