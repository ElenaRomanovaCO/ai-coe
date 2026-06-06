#!/usr/bin/env python3
"""Verify the vault is retrievable: one representative S3 Vectors query per content type.

Embeds a query with Titan Embed v2 and runs an S3 Vectors similarity search, checking
that at least one hit's key falls under the expected content-type prefix. Polls for a
while because the ReEmbed Lambda indexes asynchronously after an S3 sync.

    uv run python scripts/verify_retrieval.py
"""

from __future__ import annotations

import json
import sys
import time

import boto3

REGION = "us-east-1"
VECTOR_BUCKET = "aicoe-content-vectors"
VECTOR_INDEX = "aicoe-content"
EMBED_MODEL = "amazon.titan-embed-text-v2:0"

# (content-type prefix, representative query)
CHECKS = [
    ("assets/", "healthcare RAG reference architecture for clinical notes"),
    ("tools/", "managed vector database on AWS for retrieval"),
    ("vendors/", "compare Claude GPT and Gemini for document analysis"),
    ("regs/", "EU AI Act high-risk obligations and risk tiers"),
    ("feed/", "new model release improves grounded summarization"),
    ("prompts/", "facilitate a client kickoff discovery workshop"),
    ("assessments/", "regional bank AI maturity assessment stage 2"),
    ("kits/", "fintech fraud scoring engagement kit"),
    ("decisions/", "decision on default vector store"),
]

_bedrock = boto3.client("bedrock-runtime", region_name=REGION)
_s3v = boto3.client("s3vectors", region_name=REGION)


def embed(text: str) -> list[float]:
    resp = _bedrock.invoke_model(
        modelId=EMBED_MODEL,
        body=json.dumps({"inputText": text, "dimensions": 1024, "normalize": True}),
    )
    return json.loads(resp["body"].read())["embedding"]


def top_hits(query: str, k: int = 5) -> list[str]:
    resp = _s3v.query_vectors(
        vectorBucketName=VECTOR_BUCKET,
        indexName=VECTOR_INDEX,
        queryVector={"float32": embed(query)},
        topK=k,
        returnMetadata=True,
    )
    return [v["key"] for v in resp.get("vectors", [])]


def main() -> int:
    deadline = time.monotonic() + 120
    pending = dict(CHECKS)
    passed: dict[str, str] = {}

    while pending and time.monotonic() < deadline:
        for prefix, query in list(pending.items()):
            keys = top_hits(query)
            hit = next((kk for kk in keys if kk.startswith(prefix)), None)
            if hit:
                passed[prefix] = hit
                del pending[prefix]
        if pending:
            time.sleep(8)

    for prefix, _ in CHECKS:
        if prefix in passed:
            print(f"OK   {prefix:<14} -> {passed[prefix]}")
        else:
            print(f"MISS {prefix:<14} -> no hit under prefix", file=sys.stderr)

    return 0 if not pending else 1


if __name__ == "__main__":
    sys.exit(main())
