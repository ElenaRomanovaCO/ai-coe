"""Fakes for the module-agents suite (no AWS)."""

from __future__ import annotations

import io
import json

# Two seed-shaped asset markdown files keyed by S3 key.
ASSET_A = """---
id: reference-arch-clinical-notes-rag
title: Reference Architecture — Clinical Notes RAG
type: reference-architecture
industry: healthcare
ai_stage: 2
tags: ["rag", "healthcare", "clinical-notes"]
contributor: demo
updated_at: "2026-04-29"
---

# Clinical Notes RAG

A reference architecture for retrieval over clinical notes.
"""

ASSET_B = """---
id: solution-pattern-fraud-scoring-agent
title: Solution Pattern — Fraud Scoring Agent
type: solution-pattern
industry: financial-services
ai_stage: 3
tags: ["fraud", "scoring", "agent"]
contributor: demo
updated_at: "2026-05-01"
---

# Fraud Scoring Agent

A pattern for real-time fraud scoring.
"""

ASSET_KEYS = {
    "assets/healthcare/2/reference-arch-clinical-notes-rag.md": ASSET_A,
    "assets/financial-services/3/solution-pattern-fraud-scoring-agent.md": ASSET_B,
}


class FakeS3:
    """In-memory S3 keyed by Key (Bucket ignored — tests use distinct prefixes)."""

    def __init__(self, objects: dict[str, str]):
        self.objects = dict(objects)  # key -> text

    def list_objects_v2(self, Bucket, Prefix="", ContinuationToken=None):
        contents = [{"Key": k} for k in self.objects if k.startswith(Prefix)]
        return {"Contents": contents, "IsTruncated": False}

    def get_object(self, Bucket, Key):
        if Key not in self.objects:
            raise KeyError(Key)
        return {"Body": io.BytesIO(self.objects[Key].encode("utf-8"))}

    def put_object(self, Bucket, Key, Body, **kwargs):
        self.objects[Key] = Body.decode("utf-8") if isinstance(Body, bytes) else Body


class FakeBedrockEmbed:
    def invoke_model(self, **kwargs):
        body = json.dumps({"embedding": [0.1] * 1024}).encode("utf-8")
        return {"body": io.BytesIO(body)}


class FakeS3Vectors:
    def __init__(self, vectors):
        self._vectors = vectors

    def query_vectors(self, **kwargs):
        return {"vectors": self._vectors}


class FakeMetrics:
    """No-op CloudWatch client so run_tool's instrumentation stays offline in tests."""

    def put_metric_data(self, **kwargs):
        pass


def make_agent(*, vectors=None):
    from agents.lambdas.modules.agent_03_asset_library import AssetLibraryAgent

    return AssetLibraryAgent(
        vault_bucket="vault-bucket",
        sessions_bucket="sessions-bucket",
        s3=FakeS3(dict(ASSET_KEYS)),
        bedrock=FakeBedrockEmbed(),
        s3vectors=FakeS3Vectors(vectors or []),
        metrics_client=FakeMetrics(),
    )


def vec(key: str, content_type: str = "assets"):
    return {
        "key": f"{key}#0",
        "metadata": {"file_path": key, "content_type": content_type, "chunk_index": 0},
    }
