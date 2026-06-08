"""Agents (Fargate) stack — DOCUMENTED SCALE-UP PATH, NOT DEPLOYED.

This is the warm, always-on variant of AGENT-01 for when real traffic makes the
streaming-Lambda cold starts (see ``agents.py``) unacceptable. It is intentionally
**not** wired into ``app.py``, so ``cdk synth``/``deploy`` never touch it. Promote
it by adding it to ``app.py`` (and removing or scaling down the Lambda) when warm
latency matters.

Why keep it: the POC decision (``vault/decisions/poc-runtime.md``) was to defer
Fargate-warm until there's real traffic, but the orchestrator container image is
identical (the Lambda Web Adapter is inert on ECS), so the move is config-only.

Topology: internal ALB (HTTP :80, health check ``/healthz``) -> Fargate Spot
service (1 task, ARM64) running the same uvicorn image. The Next.js side would
then call the ALB through a thin proxy/VPC link instead of the Function URL.
"""

from __future__ import annotations

from pathlib import Path

from aws_cdk import Duration, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from constructs import Construct

from . import config

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOCKERFILE = "agents/orchestrator/Dockerfile"


class AgentsFargateStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vault_bucket: s3.IBucket,
        sessions_bucket: s3.IBucket,
        task_role: iam.IRole,
        guardrail_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "OrchestratorVpc", max_azs=2, nat_gateways=1)

        cluster = ecs.Cluster(
            self,
            "OrchestratorCluster",
            vpc=vpc,
            enable_fargate_capacity_providers=True,
        )

        image = ecs.ContainerImage.from_asset(
            directory=str(_REPO_ROOT),
            file=_DOCKERFILE,
            platform=ecr_assets.Platform.LINUX_ARM64,
        )

        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "OrchestratorService",
            cluster=cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            public_load_balancer=False,  # internal ALB
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.ARM64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(capacity_provider="FARGATE_SPOT", weight=1)
            ],
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=image,
                container_port=8080,
                task_role=task_role,
                environment={
                    "VAULT_BUCKET": vault_bucket.bucket_name,
                    "SESSIONS_BUCKET": sessions_bucket.bucket_name,
                    "VECTOR_BUCKET": config.VECTOR_BUCKET_NAME,
                    "VECTOR_INDEX": config.VECTOR_INDEX_NAME,
                    "GUARDRAIL_ID": guardrail_id,
                },
                log_driver=ecs.LogDrivers.aws_logs(
                    stream_prefix="aicoe-orchestrator",
                    log_retention=logs.RetentionDays.ONE_MONTH,
                ),
            ),
        )

        # On Fargate the background refresh daemon ticks, so /healthz is a plain
        # liveness probe.
        service.target_group.configure_health_check(
            path="/healthz",
            healthy_http_codes="200",
            interval=Duration.seconds(30),
        )

        self.service = service
