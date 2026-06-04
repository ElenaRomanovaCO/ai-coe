"""Events stack: ReEmbed Lambda + EventBridge wiring.

The vault bucket emits S3 events to EventBridge (see storage.py). This rule
forwards Object Created/Deleted events for the vault bucket to the ReEmbed
Lambda, which re-embeds changed markdown into S3 Vectors.
"""

from __future__ import annotations

from pathlib import Path

from aws_cdk import Duration, Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3
from constructs import Construct

from . import config
from .iam import REEMBED_FN

# infra/stacks/events.py -> repo root -> agents/lambdas/reembed
_REEMBED_CODE = Path(__file__).resolve().parents[2] / "agents" / "lambdas" / "reembed"


class EventsStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vault_bucket: s3.IBucket,
        reembed_role: iam.IRole,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.reembed_fn = lambda_.Function(
            self,
            "ReEmbedFunction",
            function_name=REEMBED_FN,
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.handler",
            code=lambda_.Code.from_asset(str(_REEMBED_CODE)),
            role=reembed_role,
            timeout=Duration.minutes(2),
            memory_size=512,
            environment={
                "VECTOR_BUCKET": config.VECTOR_BUCKET_NAME,
                "VECTOR_INDEX": config.VECTOR_INDEX_NAME,
                "EMBED_MODEL": config.TITAN_EMBED_V2,
            },
        )

        events.Rule(
            self,
            "VaultObjectChangeRule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created", "Object Deleted"],
                detail={"bucket": {"name": [vault_bucket.bucket_name]}},
            ),
            targets=[targets.LambdaFunction(self.reembed_fn)],
        )
