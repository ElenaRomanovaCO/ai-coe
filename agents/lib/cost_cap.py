"""Daily Opus cost cap, backed by S3 with optimistic locking.

State lives at ``s3://{vault_bucket}/usage/{yyyy-mm-dd}/opus.json``. Reads use
the object ETag; writes are conditional (``If-Match`` on update, ``If-None-Match: *``
on create) so concurrent invocations can't silently clobber each other's counters.

Usage::

    cap = OpusCostCap(vault_bucket)
    cap.pre_check(estimated_cost_usd)   # raises OpusCapExceeded if it would bust
    ...                                 # make the Opus call
    cap.add_usage(tokens, actual_cost_usd)
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import ClientError

from .models import REGION

DEFAULT_CAP_USD = float(os.getenv("AICOE_OPUS_DAILY_CAP_USD", "5.00"))
_MAX_RETRIES = 5
_NOT_FOUND = {"NoSuchKey", "404", "NoSuchBucket"}
_PRECONDITION = {"PreconditionFailed", "412"}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class OpusCapExceeded(Exception):
    """Raised when an Opus call would push daily spend past the cap."""

    def __init__(self, spent_usd: float, estimate_usd: float, cap_usd: float) -> None:
        self.spent_usd = spent_usd
        self.estimate_usd = estimate_usd
        self.cap_usd = cap_usd
        super().__init__(
            f"Opus daily cap exceeded: spent ${spent_usd:.4f} + estimate "
            f"${estimate_usd:.4f} > cap ${cap_usd:.2f}"
        )


@dataclass
class OpusUsage:
    date: str
    tokens_consumed: int = 0
    cost_usd: float = 0.0
    cap_usd: float = DEFAULT_CAP_USD
    cap_hit_at: str | None = None


class OpusCostCap:
    def __init__(
        self,
        bucket: str,
        *,
        cap_usd: float | None = None,
        s3: Any = None,
        today: str | None = None,
    ) -> None:
        self.bucket = bucket
        self.cap_usd = DEFAULT_CAP_USD if cap_usd is None else cap_usd
        self._s3 = s3
        self._today = today

    @property
    def s3(self) -> Any:
        if self._s3 is None:
            import boto3  # lazy: importing this module stays AWS-free

            self._s3 = boto3.client("s3", region_name=REGION)
        return self._s3

    def _date(self) -> str:
        return self._today or datetime.now(UTC).date().isoformat()

    def _key(self) -> str:
        return f"usage/{self._date()}/opus.json"

    def _read(self) -> tuple[OpusUsage, str | None]:
        try:
            resp = self.s3.get_object(Bucket=self.bucket, Key=self._key())
        except ClientError as exc:
            if exc.response["Error"]["Code"] in _NOT_FOUND:
                return OpusUsage(date=self._date(), cap_usd=self.cap_usd), None
            raise
        data = json.loads(resp["Body"].read())
        usage = OpusUsage(
            date=data.get("date", self._date()),
            tokens_consumed=int(data.get("tokens_consumed", 0)),
            cost_usd=float(data.get("cost_usd", 0.0)),
            cap_usd=float(data.get("cap_usd", self.cap_usd)),
            cap_hit_at=data.get("cap_hit_at"),
        )
        return usage, resp.get("ETag")

    def _write(self, usage: OpusUsage, etag: str | None) -> None:
        kwargs: dict[str, Any] = {
            "Bucket": self.bucket,
            "Key": self._key(),
            "Body": json.dumps(asdict(usage), separators=(",", ":")).encode("utf-8"),
            "ContentType": "application/json",
        }
        if etag is None:
            kwargs["IfNoneMatch"] = "*"
        else:
            kwargs["IfMatch"] = etag
        self.s3.put_object(**kwargs)

    def remaining_usd(self) -> float:
        usage, _ = self._read()
        return max(0.0, usage.cap_usd - usage.cost_usd)

    def pre_check(self, estimated_cost_usd: float) -> OpusUsage:
        """Raise OpusCapExceeded if this call would bust the cap; else return usage."""
        usage, etag = self._read()
        if usage.cost_usd + estimated_cost_usd > usage.cap_usd:
            if usage.cap_hit_at is None:
                usage.cap_hit_at = _now_iso()
                try:
                    self._write(usage, etag)
                except ClientError:
                    pass  # marker is best-effort; the raise below is what matters
            raise OpusCapExceeded(usage.cost_usd, estimated_cost_usd, usage.cap_usd)
        return usage

    def add_usage(self, tokens: int, cost_usd: float) -> OpusUsage:
        """Atomically add consumed tokens/cost, retrying on write contention."""
        for _ in range(_MAX_RETRIES):
            usage, etag = self._read()
            usage.tokens_consumed += tokens
            usage.cost_usd = round(usage.cost_usd + cost_usd, 6)
            usage.cap_usd = self.cap_usd
            if usage.cost_usd >= usage.cap_usd and usage.cap_hit_at is None:
                usage.cap_hit_at = _now_iso()
            try:
                self._write(usage, etag)
                return usage
            except ClientError as exc:
                if exc.response["Error"]["Code"] in _PRECONDITION:
                    continue
                raise
        raise RuntimeError("Opus cap write contention: exceeded retries")
