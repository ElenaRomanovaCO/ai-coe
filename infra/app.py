#!/usr/bin/env python3
"""CDK app entry. One stack per concern (storage, IAM, guardrails, events,
observability). Account comes from the environment (CDK_DEFAULT_ACCOUNT); region
is pinned to us-east-1.
"""

from __future__ import annotations

import os

import aws_cdk as cdk

from stacks.agents import AgentsStack
from stacks.config import REGION
from stacks.events import EventsStack
from stacks.frontend import FrontendStack
from stacks.guardrails import GuardrailsStack
from stacks.iam import IamStack
from stacks.observability import ObservabilityStack
from stacks.storage import StorageStack

app = cdk.App()
env = cdk.Environment(account=os.environ.get("CDK_DEFAULT_ACCOUNT"), region=REGION)

storage = StorageStack(app, "AiCoE-Storage", env=env)

iam_stack = IamStack(
    app,
    "AiCoE-Iam",
    vault_bucket=storage.vault_bucket,
    sessions_bucket=storage.sessions_bucket,
    env=env,
)

guardrails = GuardrailsStack(app, "AiCoE-Guardrails", env=env)

EventsStack(
    app,
    "AiCoE-Events",
    vault_bucket=storage.vault_bucket,
    reembed_role=iam_stack.reembed_role,
    env=env,
)

ObservabilityStack(
    app,
    "AiCoE-Observability",
    alarm_email=app.node.try_get_context("alarm_email"),
    env=env,
)

# AGENT-01 orchestrator (streaming Lambda + Function URL). See agents_fargate.py
# for the documented, un-deployed Fargate scale-up path.
agents = AgentsStack(
    app,
    "AiCoE-Agents",
    vault_bucket=storage.vault_bucket,
    sessions_bucket=storage.sessions_bucket,
    orchestrator_role=iam_stack.orchestrator_lambda_role,
    module_agents_role=iam_stack.module_agents_role,
    workers_role=iam_stack.workers_role,
    guardrail=guardrails.guardrail,
    env=env,
)

FrontendStack(
    app,
    "AiCoE-Frontend",
    ssr_role=iam_stack.amplify_ssr_role,
    orchestrator_url=agents.function_url_value,
    env=env,
)

app.synth()
