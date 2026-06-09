"""Agents stack: AGENT-01 (Chat orchestrator) as a streaming Lambda.

Per ``vault/decisions/poc-runtime.md`` the POC orchestrator runs as a container
Lambda fronted by the Lambda Web Adapter, exposed through a Function URL with
``InvokeMode=RESPONSE_STREAM`` and IAM auth — ~$0 when idle, streaming when used.
The Next.js SSR role invokes the Function URL with SigV4; there is no ALB and no
separate proxy Lambda.

The function keeps the name ``aicoe-fargate-orchestrator-endpoint-lambda`` (wired
into the SSR role and web/lib/aws.ts by the foundation) even though it is now a
Lambda rather than a Fargate endpoint. The Fargate variant lives in
``agents_fargate.py`` as a documented, un-deployed scale-up path.
"""

from __future__ import annotations

from pathlib import Path

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from constructs import Construct

from . import config
from .iam import MODULE_AGENTS_FN, ORCHESTRATOR_ENDPOINT_FN, WORKERS_FN

# infra/stacks/agents.py -> repo root (build context for the Docker images).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOCKERFILE = "agents/orchestrator/Dockerfile"
_MODULES_DOCKERFILE = "agents/lambdas/modules/Dockerfile"
_WORKERS_DOCKERFILE = "agents/lambdas/workers/Dockerfile"


class AgentsStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vault_bucket: s3.IBucket,
        sessions_bucket: s3.IBucket,
        orchestrator_role: iam.IRole,
        module_agents_role: iam.IRole,
        workers_role: iam.IRole,
        guardrail: bedrock.CfnGuardrail,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        log_group = logs.LogGroup(
            self,
            "OrchestratorLogGroup",
            log_group_name=f"/aws/lambda/{ORCHESTRATOR_ENDPOINT_FN}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.function = lambda_.DockerImageFunction(
            self,
            "OrchestratorFunction",
            function_name=ORCHESTRATOR_ENDPOINT_FN,
            code=lambda_.DockerImageCode.from_image_asset(
                directory=str(_REPO_ROOT),
                file=_DOCKERFILE,
                # x86_64 (not ARM64): the image builds natively on the Windows dev
                # host; ARM64 would need slow/flaky QEMU emulation. The Lambda cost
                # edge of ARM is negligible at POC scale. The Dockerfile is
                # arch-agnostic (python:3.12-slim + LWA are multi-arch).
                platform=ecr_assets.Platform.LINUX_AMD64,
            ),
            architecture=lambda_.Architecture.X86_64,
            role=orchestrator_role,
            memory_size=1024,
            # First-token p95 < 3s, but allow a long ceiling for multi-tool turns
            # and streamed completions (well under the Function URL 15-min cap).
            timeout=Duration.minutes(5),
            environment={
                "VAULT_BUCKET": vault_bucket.bucket_name,
                "SESSIONS_BUCKET": sessions_bucket.bucket_name,
                "VECTOR_BUCKET": config.VECTOR_BUCKET_NAME,
                "VECTOR_INDEX": config.VECTOR_INDEX_NAME,
                "GUARDRAIL_ID": guardrail.attr_guardrail_id,
                "MODULE_AGENTS_FN": MODULE_AGENTS_FN,
                # AWS_LWA_INVOKE_MODE is baked into the image (the AWS_* prefix is
                # reserved for Lambda env vars), so it is not set here.
            },
            log_group=log_group,
        )

        # Streaming Function URL with IAM auth. RESPONSE_STREAM is what makes the
        # Lambda Web Adapter stream SSE through to the caller. The SSR role and this
        # function are in the same account, so the identity-based
        # lambda:InvokeFunctionUrl grant on the SSR role (IAM stack) is sufficient
        # to authorize invocation — no resource-based policy is required.
        self.function_url = self.function.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.AWS_IAM,
            invoke_mode=lambda_.InvokeMode.RESPONSE_STREAM,
        )

        self.function_url_value = self.function_url.url
        CfnOutput(self, "OrchestratorFunctionUrl", value=self.function_url.url)
        CfnOutput(self, "OrchestratorFunctionName", value=self.function.function_name)

        # --- Module agents Lambda (AGENT-03+, static dispatch router) ---------
        # One Lambda hosts all Layer 2 module agents (AD-01). The orchestrator's
        # invoke_module sends {agent_id, args}; router.py dispatches. Non-streaming,
        # so a plain handler image (no Lambda Web Adapter). Direct lambda:Invoke
        # both from the orchestrator and from the web's read-only server actions.
        module_log_group = logs.LogGroup(
            self,
            "ModuleAgentsLogGroup",
            log_group_name=f"/aws/lambda/{MODULE_AGENTS_FN}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.module_agents_function = lambda_.DockerImageFunction(
            self,
            "ModuleAgentsFunction",
            function_name=MODULE_AGENTS_FN,
            code=lambda_.DockerImageCode.from_image_asset(
                directory=str(_REPO_ROOT),
                file=_MODULES_DOCKERFILE,
                platform=ecr_assets.Platform.LINUX_AMD64,  # matches orchestrator (x86_64)
            ),
            architecture=lambda_.Architecture.X86_64,
            role=module_agents_role,
            memory_size=512,
            timeout=Duration.minutes(2),
            environment={
                "VAULT_BUCKET": vault_bucket.bucket_name,
                "SESSIONS_BUCKET": sessions_bucket.bucket_name,
                "VECTOR_BUCKET": config.VECTOR_BUCKET_NAME,
                "VECTOR_INDEX": config.VECTOR_INDEX_NAME,
            },
            log_group=module_log_group,
        )
        CfnOutput(self, "ModuleAgentsFunctionName", value=self.module_agents_function.function_name)

        # --- Workers Lambda (WORKER-01/02/03+, Layer 3) -----------------------
        # Module agents invoke this via lambda:Invoke {worker_id, args}. Same
        # container/handler pattern as the module-agents Lambda.
        workers_log_group = logs.LogGroup(
            self,
            "WorkersLogGroup",
            log_group_name=f"/aws/lambda/{WORKERS_FN}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.workers_function = lambda_.DockerImageFunction(
            self,
            "WorkersFunction",
            function_name=WORKERS_FN,
            code=lambda_.DockerImageCode.from_image_asset(
                directory=str(_REPO_ROOT),
                file=_WORKERS_DOCKERFILE,
                platform=ecr_assets.Platform.LINUX_AMD64,
            ),
            architecture=lambda_.Architecture.X86_64,
            role=workers_role,
            memory_size=512,
            timeout=Duration.minutes(2),
            environment={
                "VAULT_BUCKET": vault_bucket.bucket_name,
                "VECTOR_BUCKET": config.VECTOR_BUCKET_NAME,
                "VECTOR_INDEX": config.VECTOR_INDEX_NAME,
            },
            log_group=workers_log_group,
        )
        CfnOutput(self, "WorkersFunctionName", value=self.workers_function.function_name)
