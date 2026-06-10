"""Shared names and ARN helpers used across stacks.

S3 Vectors has no stable CDK/CloudFormation support yet, so the vector bucket and
index are created out-of-band by ``infra/scripts/create_vector_index.py``. The
names here are the contract: IAM policies, the ReEmbed Lambda env, and that script
all reference the same constants.
"""

from __future__ import annotations

REGION = "us-east-1"

# S3 Vectors (created by scripts/create_vector_index.py).
VECTOR_BUCKET_NAME = "aicoe-content-vectors"
VECTOR_INDEX_NAME = "aicoe-content"
EMBED_DIMENSIONS = 1024

# Bedrock model IDs (confirmed via list-foundation-models, us-east-1).
SONNET_4_6 = "anthropic.claude-sonnet-4-6"
HAIKU_4_5 = "anthropic.claude-haiku-4-5-20251001-v1:0"
OPUS_4_7 = "anthropic.claude-opus-4-7"
TITAN_EMBED_V2 = "amazon.titan-embed-text-v2:0"

CHAT_MODEL_IDS = [SONNET_4_6, HAIKU_4_5, OPUS_4_7]


def foundation_model_arn(model_id: str) -> str:
    # Account-less, and region-wildcarded: a `us.` cross-region inference profile
    # routes Converse to any of us-east-1 / us-east-2 / us-west-2, and InvokeModel is
    # authorized against the foundation-model resource in whichever region it lands.
    # Pinning us-east-1 here caused AccessDenied when the profile routed to us-east-2.
    return f"arn:aws:bedrock:*::foundation-model/{model_id}"


def inference_profile_arn(account: str, model_id: str) -> str:
    # The inference profile itself is regional to the caller (us-east-1).
    return f"arn:aws:bedrock:{REGION}:{account}:inference-profile/us.{model_id}"


def invoke_model_resource_arns(account: str, model_ids: list[str]) -> list[str]:
    """Both the foundation-model and regional inference-profile ARNs for invocation."""
    arns: list[str] = []
    for mid in model_ids:
        arns.append(foundation_model_arn(mid))
        if mid.startswith("anthropic."):
            arns.append(inference_profile_arn(account, mid))
    return arns


def vector_index_arn(account: str) -> str:
    return (
        f"arn:aws:s3vectors:{REGION}:{account}:bucket/"
        f"{VECTOR_BUCKET_NAME}/index/{VECTOR_INDEX_NAME}"
    )


def vector_bucket_arn(account: str) -> str:
    return f"arn:aws:s3vectors:{REGION}:{account}:bucket/{VECTOR_BUCKET_NAME}"
