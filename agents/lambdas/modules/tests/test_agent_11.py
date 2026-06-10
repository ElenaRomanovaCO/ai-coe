"""AGENT-11 prompt studio: list/get/save(version,fork)/run/suggest/version_history.

Uses a bucket-aware fake S3 (the agent reads vault `prompts/` + sessions `prompts/`
under the same prefix, so the bucket must be distinguished).
"""

import io

from agents.lambdas.modules.agent_11_prompts import PromptStudioAgent

from .conftest import FakeMetrics

VAULT = "vault-bucket"
SESSIONS = "sessions-bucket"


def _seed(id_, title, use_case, targets, variables, prompt_text, version=1, parent=None):
    mt = ", ".join(f'"{m}"' for m in targets)
    vs = ", ".join(f'"{v}"' for v in variables)
    pid = f"parent_id: {parent}" if parent else "parent_id: null"
    return (
        f"---\nid: {id_}\ntitle: {title}\nuse_case: \"{use_case}\"\n"
        f"model_targets: [{mt}]\nvariables: [{vs}]\nversion: {version}\n{pid}\n---\n\n"
        f"# {title}\n\n## Prompt\n\n{prompt_text}\n\n## Guidance\n\nUse well.\n"
    )


SEED_KEYS = {
    (VAULT, "prompts/ai-risk-assessment.md"): _seed(
        "prompt-ai-risk-assessment", "AI Risk Assessment Scaffolding",
        "Produce a first-pass risk assessment", ["sonnet-4-6"],
        ["use_case_description", "industry"],
        "You are a risk reviewer. Assess {{use_case_description}} in {{industry}} as a "
        "markdown table with one row per risk dimension.",
    ),
    (VAULT, "prompts/client-kickoff.md"): _seed(
        "prompt-client-kickoff", "Client Kickoff Facilitation",
        "Facilitate an AI discovery workshop", ["sonnet-4-6", "haiku-4-5"],
        ["client_industry", "session_goal"],
        "You are a workshop facilitator for {{client_industry}}. Goal: {{session_goal}}. "
        "Produce a numbered agenda.",
    ),
}


class BucketFakeS3:
    """In-memory S3 keyed by (Bucket, Key) so vault and sessions stay distinct."""

    def __init__(self, objects):
        self.objects = dict(objects)

    def list_objects_v2(self, Bucket, Prefix="", ContinuationToken=None):
        contents = [
            {"Key": k} for (b, k) in self.objects if b == Bucket and k.startswith(Prefix)
        ]
        return {"Contents": contents, "IsTruncated": False}

    def get_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            raise KeyError(Key)
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)].encode("utf-8"))}

    def put_object(self, Bucket, Key, Body, **kwargs):
        self.objects[(Bucket, Key)] = Body.decode("utf-8") if isinstance(Body, bytes) else Body


class FakeBedrockClient:
    def __init__(self, text="MODEL OUTPUT", bullets="- Tighten the role.\n- Add an example."):
        self.text = text
        self.bullets = bullets
        self.calls = 0
        self.last_messages = None

    def converse(self, **kwargs):
        self.calls += 1
        self.last_messages = kwargs.get("messages")
        u = kwargs.get("usage")
        if u is not None:
            u.tokens_in, u.tokens_out, u.cost_usd = 12, 34, 0.00042
        # suggest_improvements passes a system prompt; run_prompt does not.
        text = self.bullets if kwargs.get("system") else self.text
        return {"output": {"message": {"content": [{"text": text}]}}, "usage": {}}


def _agent(bedrock=None, objects=None):
    return PromptStudioAgent(
        vault_bucket=VAULT,
        sessions_bucket=SESSIONS,
        s3=BucketFakeS3(dict(SEED_KEYS) if objects is None else objects),
        bedrock_client=bedrock or FakeBedrockClient(),
        metrics_client=FakeMetrics(),
    )


# --- list / get ------------------------------------------------------------
def test_list_merges_seed_prompts():
    out = _agent().handle({"op": "list_prompts"})
    assert out["status"] == "ok"
    ids = {p["id"] for p in out["prompts"]}
    assert ids == {"prompt-ai-risk-assessment", "prompt-client-kickoff"}
    assert all(p["source"] == "seed" for p in out["prompts"])


def test_list_filters_by_model_target():
    out = _agent().handle({"op": "list_prompts", "model_target": "haiku-4-5"})
    assert {p["id"] for p in out["prompts"]} == {"prompt-client-kickoff"}


def test_get_extracts_prompt_text():
    out = _agent().handle({"op": "get_prompt", "prompt_id": "prompt-ai-risk-assessment"})
    assert out["status"] == "ok"
    assert out["prompt"]["prompt_text"].startswith("You are a risk reviewer.")
    assert "## Guidance" not in out["prompt"]["prompt_text"]
    assert out["prompt"]["variables"] == ["use_case_description", "industry"]


def test_get_unknown_not_found():
    assert _agent().handle({"op": "get_prompt", "prompt_id": "nope"})["status"] == "not_found"


# --- save (version / fork) -------------------------------------------------
def test_save_version_increments_and_writes_to_sessions():
    agent = _agent()
    out = agent.handle({
        "op": "save_prompt", "mode": "version", "source_id": "prompt-ai-risk-assessment",
        "title": "AI Risk v2", "prompt_text": "You are a reviewer. {{industry}}",
        "variables": ["industry"], "display_name": "Dana",
    })
    assert out["status"] == "ok"
    p = out["prompt"]
    assert p["version"] == 2 and p["parent_id"] == "prompt-ai-risk-assessment"
    assert p["source"] == "user" and p["created_by"] == "Dana"
    # Written to the SESSIONS bucket, not the vault.
    key = (SESSIONS, f"prompts/{p['id']}.md")
    assert key in agent.s3.objects
    assert not any(b == VAULT and p["id"] in k for (b, k) in agent.s3.objects)


def test_save_fork_resets_version():
    out = _agent().handle({
        "op": "save_prompt", "mode": "fork", "source_id": "prompt-client-kickoff",
        "title": "Forked kickoff", "prompt_text": "You are a facilitator. {{x}}",
    })
    assert out["prompt"]["version"] == 1
    assert out["prompt"]["parent_id"] == "prompt-client-kickoff"


def test_save_version_requires_source():
    out = _agent().handle({"op": "save_prompt", "mode": "version", "prompt_text": "hi"})
    assert out["status"] == "error"


def test_saved_prompt_then_listed_as_user_source():
    agent = _agent()
    saved = agent.handle({
        "op": "save_prompt", "mode": "fork", "source_id": "prompt-client-kickoff",
        "title": "Forked", "prompt_text": "You are a facilitator. {{x}}",
    })["prompt"]
    listed = agent.handle({"op": "list_prompts"})["prompts"]
    user = next(p for p in listed if p["id"] == saved["id"])
    assert user["source"] == "user"


# --- run -------------------------------------------------------------------
def test_run_substitutes_variables_and_returns_metrics():
    fake = FakeBedrockClient(text="RISK TABLE")
    out = _agent(bedrock=fake).handle({
        "op": "run_prompt",
        "prompt_text": "Assess {{use_case}} for {{industry}}.",
        "variables": {"use_case": "triage bot", "industry": "healthcare"},
        "model_id": "haiku-4-5",
    })
    assert out["status"] == "ok"
    assert out["output"] == "RISK TABLE"
    assert out["tokens_in"] == 12 and out["tokens_out"] == 34
    assert out["cost_usd"] == 0.00042
    assert out["latency_ms"] >= 0
    assert out["model_id"].endswith("claude-haiku-4-5-20251001-v1:0")
    # The {{vars}} were substituted before the model saw the prompt.
    sent = fake.last_messages[0]["content"][0]["text"]
    assert "triage bot" in sent and "healthcare" in sent and "{{" not in sent


def test_run_rejects_unknown_model():
    out = _agent().handle({"op": "run_prompt", "prompt_text": "hi", "model_id": "gpt-9"})
    assert out["status"] == "error"


# --- suggest ---------------------------------------------------------------
def test_suggest_flags_anti_patterns_and_returns_suggestions():
    out = _agent().handle({
        "op": "suggest_improvements",
        "prompt_text": "Summarize {{doc}}. Make it good.",
        "variables": ["doc", "tone"],
    })
    assert out["status"] == "ok"
    flags = {a["flag"] for a in out["anti_patterns"]}
    assert "unused-variables" in flags  # 'tone' declared, never used
    assert "no-output-format" in flags
    assert "vague-language" in flags  # 'good'
    assert "no-role" in flags
    assert len(out["suggestions"]) >= 1


def test_suggest_falls_back_when_llm_errors():
    class Boom:
        def converse(self, **kwargs):
            raise RuntimeError("bedrock down")

    out = _agent(bedrock=Boom()).handle({
        "op": "suggest_improvements",
        "prompt_text": "Do the thing. Make it nice.",
        "variables": [],
    })
    assert out["status"] == "ok"
    assert out["suggestions"]  # deterministic fallback


# --- version history -------------------------------------------------------
def test_version_history_walks_lineage():
    agent = _agent()
    v2 = agent.handle({
        "op": "save_prompt", "mode": "version", "source_id": "prompt-ai-risk-assessment",
        "title": "AI Risk v2", "prompt_text": "You are a reviewer producing a table. {{industry}}",
        "variables": ["industry"],
    })["prompt"]
    hist = agent.handle({"op": "version_history", "prompt_id": v2["id"]})
    assert hist["status"] == "ok"
    assert hist["root_id"] == "prompt-ai-risk-assessment"
    ids = [v["id"] for v in hist["versions"]]
    assert ids == ["prompt-ai-risk-assessment", v2["id"]]  # sorted by version
