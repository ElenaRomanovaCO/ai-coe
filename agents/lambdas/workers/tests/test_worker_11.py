from agents.lambdas.workers.worker_11_commentary_writer import CommentaryWriterWorker

from .conftest import FakeMetrics

BODY = """# New mid-tier model improves grounded summarization

A new mid-tier model release reports stronger faithfulness on long documents.

## What this means

For cited-summarization workloads, re-run your eval set before swapping. Radar: trial.
"""

ITEM = {
    "frontmatter": {"id": "feed-x", "title": "New mid-tier model", "category": "model-release"},
    "body": BODY,
}


class FakeBedrockClient:
    def __init__(self, text="For healthcare teams at stage 2, this matters because..."):
        self.text = text
        self.calls = 0
        self.last_system = None
        self.last_messages = None

    def converse(self, **kwargs):
        self.calls += 1
        self.last_system = kwargs.get("system")
        self.last_messages = kwargs.get("messages")
        return {"output": {"message": {"content": [{"text": self.text}]}}, "usage": {}}


def _worker(bedrock):
    return CommentaryWriterWorker(bedrock_client=bedrock, metrics_client=FakeMetrics())


def test_uses_llm_commentary_when_available():
    fake = FakeBedrockClient()
    out = _worker(fake).handle(
        {"item": ITEM, "user_profile": {"industries": ["healthcare"], "ai_stage": 2}}
    )
    assert out["status"] == "ok"
    assert out["commentary"] == fake.text
    assert out["tailored"] is True
    assert out["industry"] == "healthcare"
    assert fake.calls == 1


def test_profile_is_woven_into_the_prompt():
    fake = FakeBedrockClient()
    _worker(fake).handle(
        {
            "item": ITEM,
            "user_profile": {"industries": ["financial-services"], "ai_stage": 3,
                             "tech_focus": ["evals"]},
        }
    )
    user_text = fake.last_messages[0]["content"][0]["text"]
    assert "financial services" in user_text  # de-hyphenated for prose
    assert "stage 3" in user_text
    assert "evals" in user_text
    # The item body is the grounding source.
    assert "grounded summarization" in user_text


def test_falls_back_to_means_section_when_llm_errors():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("bedrock down")

    out = _worker(Boom()).handle(
        {"item": ITEM, "user_profile": {"industries": ["healthcare"], "ai_stage": 2}}
    )
    assert out["status"] == "ok"
    assert out["tailored"] is False
    # Pulls the item's own "What this means" section into the deterministic note.
    assert "re-run your eval set" in out["commentary"]
    assert "healthcare" in out["commentary"]


def test_fallback_uses_lede_when_no_means_section():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("down")

    body = "# Title\n\nThis is the opening paragraph with the gist.\n"
    out = _worker(Boom()).handle(
        {"item": {"frontmatter": {"title": "T"}, "body": body}, "user_profile": {}}
    )
    assert out["status"] == "ok"
    assert "opening paragraph" in out["commentary"]
