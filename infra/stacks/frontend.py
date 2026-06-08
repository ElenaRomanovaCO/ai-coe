"""Frontend stack: AWS Amplify Hosting (Gen 2) app + branch for the Next.js web app.

Amplify auto-deploys the Next.js App Router app (SSR + Server Actions) on push to
``main`` via its native GitHub integration — there is no GitHub Actions job for the
frontend. The SSR compute role (defined in the IAM stack) is attached here so server
actions can invoke the orchestrator Lambda with no static AWS keys.

The repository connection needs a GitHub token. To keep secrets out of code, it is
read at deploy time from Secrets Manager via a CloudFormation dynamic reference; the
secret name is overridable via the ``github_token_secret`` context key.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_amplify as amplify
from aws_cdk import aws_iam as iam
from constructs import Construct

# Amplify auto-detects the repo-root amplify.yml (monorepo build spec with appRoot
# web), so the build spec is not duplicated inline here.


class FrontendStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        ssr_role: iam.IRole,
        orchestrator_url: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Repo URL and the Secrets Manager secret holding the GitHub PAT are
        # supplied via context so no token is committed.
        repository = (
            self.node.try_get_context("github_repository")
            or "https://github.com/your-org/ai-coe"
        )
        token_secret = self.node.try_get_context("github_token_secret") or "aicoe/github-token"
        access_token = f"{{{{resolve:secretsmanager:{token_secret}:SecretString:token}}}}"

        env_vars = [
            # NB: Amplify forbids env vars with the reserved "AWS" prefix; the
            # SSR runtime injects AWS_REGION automatically, and lib/aws.ts
            # defaults to us-east-1, so it is not set here.
            amplify.CfnApp.EnvironmentVariableProperty(
                name="AICOE_ORCHESTRATOR_FN",
                value="aicoe-fargate-orchestrator-endpoint-lambda",
            ),
            # Monorepo: the Next.js app lives in web/. Amplify's framework
            # detection needs this even though amplify.yml sets appRoot.
            amplify.CfnApp.EnvironmentVariableProperty(
                name="AMPLIFY_MONOREPO_APP_ROOT", value="web"
            ),
            # APP_PASSWORD (FR-001) is set out-of-band as a branch env var in
            # the Amplify console, never in code.
        ]
        if orchestrator_url is not None:
            # The streaming orchestrator's Function URL (SigV4 streaming fetch in
            # web/lib/aws.ts). Supplied by the agents stack.
            env_vars.append(
                amplify.CfnApp.EnvironmentVariableProperty(
                    name="AICOE_ORCHESTRATOR_URL", value=orchestrator_url
                )
            )

        app = amplify.CfnApp(
            self,
            "WebApp",
            name="aicoe-web",
            repository=repository,
            access_token=access_token,
            # WEB_COMPUTE = SSR (App Router + Server Actions) on Amplify Hosting.
            platform="WEB_COMPUTE",
            compute_role_arn=ssr_role.role_arn,
            environment_variables=env_vars,
        )

        amplify.CfnBranch(
            self,
            "MainBranch",
            app_id=app.attr_app_id,
            branch_name="main",
            stage="PRODUCTION",
            enable_auto_build=True,
            framework="Next.js - SSR",
            compute_role_arn=ssr_role.role_arn,
        )

        self.amplify_app = app
