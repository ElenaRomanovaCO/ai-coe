"""Hot-reload for the config cache (FR-005 / AD-03).

Two strategies, one cache:

  - :func:`refresh_if_stale` — a per-invocation check. This is the strategy used
    on Lambda, where the execution environment is *frozen* between invocations so
    a background thread can't be relied on to tick. Each request reloads the
    config only if it's older than ``max_age`` (default 60s).
  - :func:`start_refresh_loop` — a daemon thread that ticks every ``interval``
    seconds. Used for always-on hosts (local dev, future Fargate) where a thread
    runs continuously.

Both call :meth:`ConfigCache.refresh`, which is best-effort: a bad edit or
transient error leaves the last good value in place.
"""

from __future__ import annotations

import json
import sys
import threading
from datetime import UTC, datetime

from .cache import ConfigCache

DEFAULT_INTERVAL_SECONDS = 60


def _log(status: dict[str, str]) -> None:
    ts = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    print(
        json.dumps({"ts": ts, "event": "config_refresh", **status}, separators=(",", ":")),
        file=sys.stdout,
        flush=True,
    )


def refresh_if_stale(cache: ConfigCache, *, max_age: float = DEFAULT_INTERVAL_SECONDS) -> bool:
    """Reload config if it's older than ``max_age``. Returns True if it refreshed.

    Cheap to call on every request: when the config is fresh it only compares two
    timestamps. This is the Lambda hot-reload path (the daemon can't tick while
    the environment is frozen between invocations).
    """
    if not cache.is_stale(max_age):
        return False
    _log(cache.refresh())
    return True


def start_refresh_loop(
    cache: ConfigCache,
    *,
    interval: float = DEFAULT_INTERVAL_SECONDS,
    stop: threading.Event | None = None,
) -> threading.Thread:
    """Start the refresh loop in a daemon thread and return it.

    Pass a :class:`threading.Event` as ``stop`` to make the loop exit promptly
    (it waits on the event, so shutdown doesn't block for a full interval).
    """
    stop_event = stop or threading.Event()

    def _run() -> None:
        while not stop_event.is_set():
            if stop_event.wait(interval):
                break
            _log(cache.refresh())

    thread = threading.Thread(target=_run, name="config-refresh", daemon=True)
    thread.start()
    return thread
