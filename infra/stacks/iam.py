"""IAM stack: the 5 least-privilege roles every later task builds on.

Roles are created with explicit inline policies (no managed policies) per the
conventions in task 00. Later module tasks attach *incremental* permissions to
these same roles — they must not create new roles.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct

from . import config

# Conventional function names later tasks will use when creating these Lambdas.
MODULE_AGENTS_FN = "aicoe-module-agents-lambda"
WORKERS_FN = "aicoe-workers-lambda"
ORCHESTRATOR_ENDPOINT_FN = "aicoe-fargate-orchestrator-endpoint-lambda"
REEMBED_FN = "aicoe-reembed-lambda"


class IamStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vault_bucket: s3.IBucket,
        sessions_bucket: s3.IBucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        account = self.account
        vault_objs = vault_bucket.arn_for_objects("*")
        sessions_objs = sessions_bucket.arn_for_objects("*")
        chat_model_arns = config.invoke_model_resource_arns(account, config.CHAT_MODEL_IDS)
        titan_arns = config.invoke_model_resource_arns(account, [config.TITAN_EMBED_V2])
        vector_index = config.vector_index_arn(account)

        def fn_arn(name: str) -> str:
            return f"arn:aws:lambda:{config.REGION}:{account}:function:{name}"

        def log_group_arn(name: str) -> str:
            return f"arn:aws:logs:{config.REGION}:{account}:log-group:/aws/lambda/{name}:*"

        cw_put_metrics = iam.PolicyStatement(
            actions=["cloudwatch:PutMetricData"],
            resources=["*"],  # PutMetricData does not support resource-level scoping
        )

        # --- Fargate orchestrator -----------------------------------------
        self.fargate_role = iam.Role(
            self,
            "FargateOrchestratorRole",
            role_name="aicoe-fargate-orchestrator-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        self.fargate_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"], resources=[fn_arn(MODULE_AGENTS_FN)]
            )
        )
        self.fargate_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:ApplyGuardrail",
                ],
                resources=chat_model_arns + ["*"],  # ApplyGuardrail is on a guardrail ARN
            )
        )
        self.fargate_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject"], resources=[vault_objs, sessions_objs]
            )
        )
        self.fargate_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3vectors:QueryVectors", "s3vectors:PutVectors"], resources=[vector_index]
            )
        )
        self.fargate_role.add_to_policy(cw_put_metrics)

        # --- Module agents Lambda -----------------------------------------
        self.module_agents_role = iam.Role(
            self,
            "ModuleAgentsLambdaRole",
            role_name="aicoe-module-agents-lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        self.module_agents_role.add_to_policy(
            iam.PolicyStatement(actions=["lambda:InvokeFunction"], resources=[fn_arn(WORKERS_FN)])
        )
        self.module_agents_role.add_to_policy(
            iam.PolicyStatement(actions=["bedrock:InvokeModel"], resources=chat_model_arns)
        )
        self.module_agents_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject"], resources=[vault_objs, sessions_objs]
            )
        )
        self.module_agents_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3vectors:QueryVectors", "s3vectors:PutVectors"], resources=[vector_index]
            )
        )
        self.module_agents_role.add_to_policy(cw_put_metrics)
        self.module_agents_role.add_to_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[log_group_arn(MODULE_AGENTS_FN)],
            )
        )

        # --- Workers Lambda (no sessions bucket, no lambda:Invoke) ---------
        self.workers_role = iam.Role(
            self,
            "WorkersLambdaRole",
            role_name="aicoe-workers-lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        self.workers_role.add_to_policy(
            iam.PolicyStatement(actions=["bedrock:InvokeModel"], resources=chat_model_arns)
        )
        self.workers_role.add_to_policy(
            iam.PolicyStatement(actions=["s3:GetObject", "s3:PutObject"], resources=[vault_objs])
        )
        self.workers_role.add_to_policy(cw_put_metrics)
        self.workers_role.add_to_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[log_group_arn(WORKERS_FN)],
            )
        )

        # --- ReEmbed Lambda ------------------------------------------------
        self.reembed_role = iam.Role(
            self,
            "ReEmbedLambdaRole",
            role_name="aicoe-reembed-lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        self.reembed_role.add_to_policy(
            iam.PolicyStatement(actions=["s3:GetObject"], resources=[vault_objs])
        )
        self.reembed_role.add_to_policy(
            iam.PolicyStatement(actions=["bedrock:InvokeModel"], resources=titan_arns)
        )
        self.reembed_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3vectors:PutVectors", "s3vectors:DeleteVectors", "s3vectors:GetVectors"],
                resources=[vector_index],
            )
        )
        self.reembed_role.add_to_policy(cw_put_metrics)
        self.reembed_role.add_to_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[log_group_arn(REEMBED_FN)],
            )
        )

        # --- Vercel OIDC ---------------------------------------------------
        issuer = self.node.try_get_context("vercel_oidc_issuer") or "oidc.vercel.com"
        audience = self.node.try_get_context("vercel_oidc_audience") or "https://vercel.com"
        sub = (
            self.node.try_get_context("vercel_oidc_sub")
            or "owner:ACME:project:aicoe:environment:preview"
        )
        provider_arn = f"arn:aws:iam::{account}:oidc-provider/{issuer}"
        self.vercel_role = iam.Role(
            self,
            "VercelOidcRole",
            role_name="aicoe-vercel-oidc-role",
            assumed_by=iam.FederatedPrincipal(
                provider_arn,
                conditions={
                    "StringEquals": {f"{issuer}:aud": audience, f"{issuer}:sub": sub},
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
        )
        # Frontend may only invoke the orchestrator endpoint Lambda — no S3, no Bedrock.
        self.vercel_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"], resources=[fn_arn(ORCHESTRATOR_ENDPOINT_FN)]
            )
        )
