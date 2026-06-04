"""CloudWatch metric emission for agent invocations.

All metrics live in the ``AICoE/Agents`` namespace. The client is created lazily
so importing this module never touches AWS; pass an explicit client in tests.
"""

from __future__ import annotations

from typing import Any

from .logging import Outcome
from .models import REGION

NAMESPACE = "AICoE/Agents"

_client: Any = None


def _default_client() -> Any:
    global _client
    if _client is None:
        import boto3  # local import keeps module import AWS-free

        _client = boto3.client("cloudwatch", region_name=REGION)
    return _client


def _dims(d: dict[str, str | None]) -> list[dict[str, str]]:
    return [{"Name": k, "Value": v} for k, v in d.items() if v]


def record_invocation(
    *,
    agent_id: str,
    outcome: Outcome,
    latency_ms: int,
    tokens_in: int,
    tokens_out: int,
    model_id: str,
    cost_usd: float,
    client: Any = None,
) -> None:
    """Emit the standard metric set for one invocation.

    Metrics: AgentInvocations, AgentLatency, AgentTokensIn, AgentTokensOut,
    AgentCostUSD — dimensioned per the observability conventions in task 00.
    """
    cw = client or _default_client()
    data = [
        {
            "MetricName": "AgentInvocations",
            "Value": 1,
            "Unit": "Count",
            "Dimensions": _dims({"agent_id": agent_id, "outcome": outcome}),
        },
        {
            "MetricName": "AgentLatency",
            "Value": latency_ms,
            "Unit": "Milliseconds",
            "Dimensions": _dims({"agent_id": agent_id}),
        },
        {
            "MetricName": "AgentTokensIn",
            "Value": tokens_in,
            "Unit": "Count",
            "Dimensions": _dims({"agent_id": agent_id, "model_id": model_id}),
        },
        {
            "MetricName": "AgentTokensOut",
            "Value": tokens_out,
            "Unit": "Count",
            "Dimensions": _dims({"agent_id": agent_id, "model_id": model_id}),
        },
        {
            "MetricName": "AgentCostUSD",
            "Value": cost_usd,
            "Unit": "None",
            "Dimensions": _dims({"agent_id": agent_id, "model_id": model_id}),
        },
        # --- Low-cardinality roll-ups for alarms (CloudWatch can't alarm on
        # SEARCH expressions, so we publish alarm-friendly single series here). ---
        {
            # Dimensionless total cost — backs the daily cost-warning alarm.
            "MetricName": "InvocationCostUSD",
            "Value": cost_usd,
            "Unit": "None",
            "Dimensions": [],
        },
        {
            # Per-model cost — backs the Opus cost-critical alarm.
            "MetricName": "InvocationCostUSD",
            "Value": cost_usd,
            "Unit": "None",
            "Dimensions": _dims({"model_id": model_id}),
        },
        {
            # Dimensionless invocation + error counts — back the error-rate alarm.
            "MetricName": "Invocations",
            "Value": 1,
            "Unit": "Count",
            "Dimensions": [],
        },
        {
            "MetricName": "InvocationErrors",
            "Value": 0 if outcome == "success" else 1,
            "Unit": "Count",
            "Dimensions": [],
        },
    ]
    cw.put_metric_data(Namespace=NAMESPACE, MetricData=data)
