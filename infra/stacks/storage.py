"""Storage stack: vault bucket + sessions bucket.

S3 Vectors index ``aicoe-content`` is created separately (see config.py) — it has
no CloudFormation support yet. Both buckets are versioned with a 90-day
non-current-version expiry, and the vault bucket emits events to EventBridge so
the ReEmbed Lambda can react to content changes.
"""

from __future__ import annotations

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_s3 as s3
from constructs import Construct


class StorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lifecycle = [
            s3.LifecycleRule(
                noncurrent_version_expiration=Duration.days(90),
                abort_incomplete_multipart_upload_after=Duration.days(7),
            )
        ]
        common = dict(
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            lifecycle_rules=lifecycle,
            # Demo: retain data on stack delete is unnecessary; destroy + autodelete.
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.vault_bucket = s3.Bucket(
            self,
            "VaultBucket",
            event_bridge_enabled=True,  # drives the ReEmbed pipeline
            **common,
        )
        self.sessions_bucket = s3.Bucket(self, "SessionsBucket", **common)
