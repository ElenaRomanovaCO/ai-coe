"""Observability stack: SNS topic + the three foundational CloudWatch alarms.

Alarms target the low-cardinality roll-up metrics emitted by ``agents/lib/metrics.py``
(InvocationCostUSD, Invocations, InvocationErrors) — CloudWatch cannot alarm on
SEARCH expressions, so per-invocation high-cardinality series are not used here.
Per-service log groups are created alongside each Lambda, not in this stack.
"""

from __future__ import annotations

from aws_cdk import Duration, Stack
from aws_cdk import aws_cloudwatch as cw
from aws_cdk import aws_cloudwatch_actions as cw_actions
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subs
from constructs import Construct

from . import config

NAMESPACE = "AICoE/Agents"


class ObservabilityStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        alarm_email: str | None = None,
        opus_cap_usd: float = 5.0,
        daily_cost_warning_usd: float = 5.0,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        topic = sns.Topic(self, "AlarmsTopic", topic_name="aicoe-alarms")
        if alarm_email:
            topic.add_subscription(subs.EmailSubscription(alarm_email))
        action = cw_actions.SnsAction(topic)

        def metric(name: str, dimensions: dict | None = None, stat: str = "Sum") -> cw.Metric:
            return cw.Metric(
                namespace=NAMESPACE,
                metric_name=name,
                dimensions_map=dimensions or {},
                statistic=stat,
                period=Duration.days(1),
            )

        # 1. Daily total cost > $5
        daily_cost = cw.Alarm(
            self,
            "DailyCostWarning",
            alarm_name="aicoe-daily-cost-warning",
            metric=metric("InvocationCostUSD"),
            threshold=daily_cost_warning_usd,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
            alarm_description="Daily total agent cost exceeded the warning threshold.",
        )
        daily_cost.add_alarm_action(action)

        # 2. Daily Opus cost > cap
        opus_cost = cw.Alarm(
            self,
            "OpusCostCritical",
            alarm_name="aicoe-opus-cost-critical",
            metric=metric("InvocationCostUSD", {"model_id": config.OPUS_4_7}),
            threshold=opus_cap_usd,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
            alarm_description="Daily Opus spend exceeded the configured cap.",
        )
        opus_cost.add_alarm_action(action)

        # 3. 1-hour error rate > 5%
        invocations = cw.Metric(
            namespace=NAMESPACE,
            metric_name="Invocations",
            statistic="Sum",
            period=Duration.hours(1),
        )
        errors = cw.Metric(
            namespace=NAMESPACE,
            metric_name="InvocationErrors",
            statistic="Sum",
            period=Duration.hours(1),
        )
        error_rate = cw.MathExpression(
            expression="100 * errors / FILL(invocations, 1)",
            using_metrics={"errors": errors, "invocations": invocations},
            label="ErrorRatePct",
            period=Duration.hours(1),
        )
        error_alarm = cw.Alarm(
            self,
            "ErrorRateWarning",
            alarm_name="aicoe-error-rate-warning",
            metric=error_rate,
            threshold=5,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
            alarm_description="More than 5% of invocations failed in the last hour.",
        )
        error_alarm.add_alarm_action(action)

        self.topic = topic
