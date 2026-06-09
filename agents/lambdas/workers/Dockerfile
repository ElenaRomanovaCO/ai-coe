# Workers Lambda image (WORKER-01/02/03+). Non-streaming handler image, same shape
# as the module-agents image. Build context is the REPO ROOT:
#   docker build -f agents/lambdas/workers/Dockerfile .
#
# syntax=docker/dockerfile:1
FROM public.ecr.aws/lambda/python:3.12

COPY pyproject.toml README.md ${LAMBDA_TASK_ROOT}/
COPY agents ${LAMBDA_TASK_ROOT}/agents
RUN pip install --no-cache-dir "${LAMBDA_TASK_ROOT}[modules]"

CMD ["agents.lambdas.workers.router.handler"]
