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

        # --- Orchestrator Lambda (POC runtime, AGENT-01) ------------------
        # Same permission set as the Fargate role, but with a lambda trust policy.
        # Per vault/decisions/poc-runtime.md the orchestrator runs as a streaming
        # Lambda (Function URL + Lambda Web Adapter) for ~$0 idle; the Fargate role
        # above stays for the documented scale-up path. Search-only on S3 Vectors
        # (no PutVectors — that's the ReEmbed Lambda's job).
        self.orchestrator_lambda_role = iam.Role(
            self,
            "OrchestratorLambdaRole",
            role_name="aicoe-orchestrator-lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        self.orchestrator_lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"], resources=[fn_arn(MODULE_AGENTS_FN)]
            )
        )
        self.orchestrator_lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:ApplyGuardrail",
                ],
                resources=chat_model_arns + ["*"],  # ApplyGuardrail is on a guardrail ARN
            )
        )
        self.orchestrator_lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject"], resources=[vault_objs, sessions_objs]
            )
        )
        # ListBucket on the buckets themselves so a GetObject for a not-yet-created
        # session key returns 404 NoSuchKey (handled as an empty session) rather than
        # 403 AccessDenied (which crashes the load).
        self.orchestrator_lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket"],
                resources=[vault_bucket.bucket_arn, sessions_bucket.bucket_arn],
            )
        )
        self.orchestrator_lambda_role.add_to_policy(
            iam.PolicyStatement(
                # QueryVectors does the similarity search; GetVectors fetches the
                # matched chunks' content/metadata for citations.
                actions=["s3vectors:QueryVectors", "s3vectors:GetVectors"],
                resources=[vector_index],
            )
        )
        self.orchestrator_lambda_role.add_to_policy(cw_put_metrics)
        self.orchestrator_lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[log_group_arn(ORCHESTRATOR_ENDPOINT_FN)],
            )
        )

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
        # Chat models + Titan: AGENT-03's search embeds the query with Titan, so
        # InvokeModel must cover the embedding model, not just the chat tiers
        # (the orchestrator role hit this same gap live).
        self.module_agents_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"], resources=chat_model_arns + titan_arns
            )
        )
        self.module_agents_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject"], resources=[vault_objs, sessions_objs]
            )
        )
        # ListBucket so a GetObject for a not-yet-created key (e.g. a user profile
        # sidecar) returns 404 NoSuchKey rather than 403 AccessDenied — the
        # orchestrator role hit exactly this.
        self.module_agents_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket"],
                resources=[vault_bucket.bucket_arn, sessions_bucket.bucket_arn],
            )
        )
        self.module_agents_role.add_to_policy(
            iam.PolicyStatement(
                # QueryVectors searches; GetVectors fetches matched chunk content for
                # citations; PutVectors stays for any write-capable future module.
                actions=["s3vectors:QueryVectors", "s3vectors:GetVectors", "s3vectors:PutVectors"],
                resources=[vector_index],
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
        # ListBucket on the vault so WORKER-03 can enumerate assets (and any worker
        # GetObject on a missing key returns 404, not 403).
        self.workers_role.add_to_policy(
            iam.PolicyStatement(actions=["s3:ListBucket"], resources=[vault_bucket.bucket_arn])
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

        # --- Amplify SSR compute role -------------------------------------
        # Attached to the Next.js SSR Lambda(s) Amplify Hosting (Gen 2) creates.
        # The compute service assumes this role at runtime, so server actions can
        # call AWS directly with no static keys and no AssumeRole step.
        self.amplify_ssr_role = iam.Role(
            self,
            "AmplifySsrRole",
            role_name="aicoe-amplify-ssr-role",
            assumed_by=iam.ServicePrincipal("amplify.amazonaws.com"),
        )
        # Frontend may only invoke the orchestrator's Function URL — no S3, no
        # Bedrock, no S3 Vectors. The orchestrator streams via a Function URL
        # (InvokeMode=RESPONSE_STREAM, IAM auth), so the action is
        # lambda:InvokeFunctionUrl, constrained to IAM-authed URLs. The function's
        # matching resource-based permission is added in the agents stack.
        self.amplify_ssr_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunctionUrl"],
                resources=[fn_arn(ORCHESTRATOR_ENDPOINT_FN)],
                conditions={"StringEquals": {"lambda:FunctionUrlAuthType": "AWS_IAM"}},
            )
        )
        # Read-only module flows (e.g. Asset Library browse/detail, save/rate/flag)
        # invoke the module-agents Lambda directly — no orchestrator in the loop.
        # Buffered lambda:Invoke (not the streaming Function URL), so the web still
        # never touches S3/Bedrock directly.
        self.amplify_ssr_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[fn_arn(MODULE_AGENTS_FN)],
            )
        )
        # Amplify manages the SSR compute log groups under /aws/amplify/.
        self.amplify_ssr_role.add_to_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[
                    f"arn:aws:logs:{config.REGION}:{account}:log-group:/aws/amplify/*"
                ],
            )
        )
