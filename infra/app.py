#!/usr/bin/env python3
"""CDK app entry. One stack per concern (storage, IAM, guardrails, events,
observability). Account comes from the environment (CDK_DEFAULT_ACCOUNT); region
is pinned to us-east-1.
"""

from __future__ import annotations

import os

import aws_cdk as cdk

from stacks.config import REGION
from stacks.events import EventsStack
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

GuardrailsStack(app, "AiCoE-Guardrails", env=env)

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

app.synth()
