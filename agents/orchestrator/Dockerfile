# AGENT-01 orchestrator image. ONE image, two runtimes:
#   - POC: AWS Lambda via the Lambda Web Adapter (Function URL, RESPONSE_STREAM).
#   - Scale-up: AWS Fargate (the adapter is a Lambda extension, inert on ECS).
# See vault/decisions/poc-runtime.md. Build context is the REPO ROOT so the
# agents/ package and pyproject are available:
#   docker build -f agents/orchestrator/Dockerfile .
#
# syntax=docker/dockerfile:1
FROM public.ecr.aws/docker/library/python:3.12-slim

# Lambda Web Adapter: bridges the Lambda runtime API to a normal web server and
# enables HTTP response streaming. On Fargate this extension is never loaded, so
# the same image serves both targets.
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter

ENV PORT=8080 \
    AWS_LWA_INVOKE_MODE=response_stream \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# uv for installs (matches the repo's toolchain), bootstrapped via pip so we don't
# depend on an external image tag.
RUN pip install --no-cache-dir uv

# Install runtime deps (fastapi, uvicorn, pydantic, boto3) + the agents package.
COPY pyproject.toml README.md ./
COPY agents ./agents
RUN uv pip install --system --no-cache ".[runtime]"

# Single worker; response streaming must not be buffered by a worker pool.
CMD ["uvicorn", "agents.orchestrator.server:app", "--host", "0.0.0.0", "--port", "8080"]
