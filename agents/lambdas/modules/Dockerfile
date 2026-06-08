# Module-agents Lambda image (AGENT-03+). Non-streaming, so a standard Lambda
# Python base image with the static-dispatch router as the handler — no Lambda
# Web Adapter (that's only for the streaming orchestrator). Build context is the
# REPO ROOT (for the agents/ package + pyproject):
#   docker build -f agents/lambdas/modules/Dockerfile .
#
# syntax=docker/dockerfile:1
FROM public.ecr.aws/lambda/python:3.12

# Install the agents package + its module-runtime deps (pydantic, boto3, pyyaml)
# into the task root. boto3 is already in the base image; pip is a no-op for it.
COPY pyproject.toml README.md ${LAMBDA_TASK_ROOT}/
COPY agents ${LAMBDA_TASK_ROOT}/agents
RUN pip install --no-cache-dir "${LAMBDA_TASK_ROOT}[modules]"

# Static-dispatch router: {agent_id, args} -> agent.handle(args).
CMD ["agents.lambdas.modules.router.handler"]
