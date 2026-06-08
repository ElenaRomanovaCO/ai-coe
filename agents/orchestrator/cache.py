"""In-memory cache of the two live config files: ``agents.md`` and ``modules.json``.

Both live in the vault bucket (AD-03). The orchestrator reads them on every turn
from this cache rather than from S3, and a background loop (see ``refresh.py``)
calls :meth:`ConfigCache.refresh` every 60s so edits land within one turn without
a redeploy. Loaders are injectable so the cache is unit-testable without AWS.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agents.lib.registry import ModuleRegistry, load_registry

# Keys within the vault bucket (content mirrors the local ``vault/`` at the root).
AGENTS_MD_KEY = "agents.md"
MODULES_JSON_KEY = "modules.json"

AgentsMdLoader = Callable[[], str]
ModulesLoader = Callable[[], str | bytes | dict]


def s3_text_loader(
    bucket: str, key: str, *, s3: Any = None, region: str = "us-east-1"
) -> AgentsMdLoader:
    """Build a loader that reads ``key`` from ``bucket`` as UTF-8 text on each call."""

    def _load() -> str:
        client = s3
        if client is None:
            import boto3

            client = boto3.client("s3", region_name=region)
        return client.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")

    return _load


def local_text_loader(path: str | Path) -> AgentsMdLoader:
    """Build a loader that reads a local file (dev/test fallback)."""
    p = Path(path)

    def _load() -> str:
        return p.read_text(encoding="utf-8")

    return _load


class ConfigCache:
    """Thread-safe cache of agents.md text and the parsed module registry.

    On :meth:`refresh`, each source is reloaded independently: a failure to load
    one (e.g. transient S3 error, or a bad edit to modules.json) leaves the last
    good value in place rather than blanking the cache. The first successful load
    of each is required at construction-time via :meth:`load_or_raise`.
    """

    def __init__(self, *, agents_md_loader: AgentsMdLoader, modules_loader: ModulesLoader) -> None:
        self._agents_md_loader = agents_md_loader
        self._modules_loader = modules_loader
        self._lock = threading.RLock()
        self._agents_md: str = ""
        self._registry: ModuleRegistry = ModuleRegistry()
        # Wall-clock (time.time) of the last refresh attempt. Wall-clock, not
        # monotonic: on Lambda the process is frozen between invocations, and we
        # want staleness measured against real elapsed time across freezes.
        self._last_refresh: float = 0.0

    @property
    def agents_md(self) -> str:
        with self._lock:
            return self._agents_md

    @property
    def registry(self) -> ModuleRegistry:
        with self._lock:
            return self._registry

    def seconds_since_refresh(self, *, now: float | None = None) -> float:
        return (now if now is not None else time.time()) - self._last_refresh

    def is_stale(self, max_age_seconds: float, *, now: float | None = None) -> bool:
        return self.seconds_since_refresh(now=now) >= max_age_seconds

    def load_or_raise(self) -> None:
        """Initial load. Unlike :meth:`refresh`, propagates errors so a misconfigured
        orchestrator fails fast at startup instead of serving an empty cache."""
        agents_md = self._agents_md_loader()
        registry = load_registry(self._modules_loader())
        with self._lock:
            self._agents_md = agents_md
            self._registry = registry
            self._last_refresh = time.time()

    def refresh(self) -> dict[str, str]:
        """Reload both sources best-effort. Returns a per-source status map."""
        status: dict[str, str] = {}
        self._last_refresh = time.time()
        try:
            agents_md = self._agents_md_loader()
            with self._lock:
                self._agents_md = agents_md
            status["agents_md"] = "ok"
        except Exception as exc:  # noqa: BLE001 — keep last good value
            status["agents_md"] = f"error: {type(exc).__name__}"
        try:
            registry = load_registry(self._modules_loader())
            with self._lock:
                self._registry = registry
            status["modules_json"] = "ok"
        except Exception as exc:  # noqa: BLE001 — keep last good value
            status["modules_json"] = f"error: {type(exc).__name__}"
        return status


def build_default_cache(
    *,
    vault_bucket: str,
    s3: Any = None,
    region: str = "us-east-1",
) -> ConfigCache:
    """Construct the production cache wired to the vault bucket over S3."""
    return ConfigCache(
        agents_md_loader=s3_text_loader(vault_bucket, AGENTS_MD_KEY, s3=s3, region=region),
        modules_loader=s3_text_loader(vault_bucket, MODULES_JSON_KEY, s3=s3, region=region),
    )
