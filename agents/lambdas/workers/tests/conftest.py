"""Fakes + asset fixtures for the workers suite (no AWS)."""

from __future__ import annotations

import io


def _asset(id_, title, type_, industry, stage, tags):
    tag_list = ", ".join(f'"{t}"' for t in tags)
    return (
        f"---\nid: {id_}\ntitle: {title}\ntype: {type_}\nindustry: {industry}\n"
        f"ai_stage: {stage}\ntags: [{tag_list}]\n"
        f'contributor: demo\nupdated_at: "2026-05-01"\n---\n\n# {title}\n\nBody.\n'
    )


ASSET_KEYS = {
    "assets/healthcare/2/ref-arch-clinical.md": _asset(
        "ref-arch-clinical", "Clinical Notes RAG", "reference-architecture", "healthcare", 2,
        ["rag", "governance", "clinical"],
    ),
    "assets/healthcare/3/pattern-triage.md": _asset(
        "pattern-triage", "Triage ML Pattern", "solution-pattern", "healthcare", 3,
        ["ml", "triage"],
    ),
    "assets/financial-services/2/risk-checklist.md": _asset(
        "risk-checklist", "Model Risk Checklist", "checklist", "financial-services", 2,
        ["governance", "risk"],
    ),
    "assets/cross-industry/1/kickoff.md": _asset(
        "kickoff-template", "Kickoff Template", "kickoff-template", "cross-industry", 1,
        ["workshop"],
    ),
}


class FakeS3:
    def __init__(self, objects: dict[str, str]):
        self.objects = dict(objects)

    def list_objects_v2(self, Bucket, Prefix="", ContinuationToken=None):
        return {
            "Contents": [{"Key": k} for k in self.objects if k.startswith(Prefix)],
            "IsTruncated": False,
        }

    def get_object(self, Bucket, Key):
        if Key not in self.objects:
            raise KeyError(Key)
        return {"Body": io.BytesIO(self.objects[Key].encode("utf-8"))}

    def put_object(self, Bucket, Key, Body, **kwargs):
        self.objects[Key] = Body.decode("utf-8") if isinstance(Body, bytes) else Body


class FakeMetrics:
    def put_metric_data(self, **kwargs):
        pass


def qa(dimension: str, answer: str, question: str = "q"):
    return {"question": question, "dimension": dimension, "answer": answer}
