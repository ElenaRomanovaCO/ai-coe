import json

from agents.orchestrator.models import ModuleDescription, ModuleSummary
from agents.orchestrator.tools import describe_module, list_modules, read_agents_md
from agents.orchestrator.tools.invoke_module import ModuleInvoker
from agents.orchestrator.tools.search_knowledge_base import (
    KnowledgeBaseSearcher,
    asset_library_url,
)

from .conftest import SAMPLE_MODULES, make_cache


# --- describe_module -------------------------------------------------------
def test_describe_module_found():
    cache = make_cache()
    result = describe_module("module-4", registry=cache.registry)
    assert isinstance(result, ModuleDescription)
    assert result.name == "Kit Builder"
    assert result.example_queries


def test_describe_module_not_found():
    cache = make_cache()
    result = describe_module("module-999", registry=cache.registry)
    assert result["status"] == "not_found"


# --- list_modules ----------------------------------------------------------
def test_list_modules_by_wave():
    cache = make_cache()
    rows = list_modules(wave=3, registry=cache.registry)
    assert [r.id for r in rows] == ["module-4"]
    assert all(isinstance(r, ModuleSummary) for r in rows)


def test_list_modules_by_keyword_matches_when_to_use():
    cache = make_cache()
    rows = list_modules(keyword="readiness", registry=cache.registry)
    assert [r.id for r in rows] == ["module-1"]


def test_list_modules_no_filter_returns_all():
    cache = make_cache()
    rows = list_modules(registry=cache.registry)
    assert len(rows) == len(SAMPLE_MODULES["modules"])


# --- read_agents_md --------------------------------------------------------
def test_read_agents_md_returns_cached():
    cache = make_cache(agents_md="be terse")
    assert read_agents_md(cache=cache) == "be terse"


# --- asset_library_url -----------------------------------------------------
def test_asset_library_url_none_when_module_disabled():
    cache = make_cache()
    assert asset_library_url("asset", "assets/x.md", cache.registry) is None


def test_asset_library_url_present_when_enabled():
    modules = json.loads(json.dumps(SAMPLE_MODULES))
    for m in modules["modules"]:
        if m["id"] == "module-2":
            m["enabled"] = True
    cache = make_cache(modules=modules)
    url = asset_library_url("asset", "assets/healthcare/2/clinical-notes-rag.md", cache.registry)
    assert url == "/modules/asset-library/clinical-notes-rag"


def test_asset_library_url_none_for_non_asset():
    cache = make_cache()
    assert asset_library_url("tool", "tools/x.md", cache.registry) is None


# --- search_knowledge_base -------------------------------------------------
class FakeBedrockEmbed:
    def invoke_model(self, **kwargs):
        body = json.dumps({"embedding": [0.1] * 1024}).encode("utf-8")

        class _B:
            def read(self_inner):
                return body

        return {"body": _B()}


class FakeS3Vectors:
    def __init__(self, vectors):
        self._vectors = vectors
        self.last_query = None

    def query_vectors(self, **kwargs):
        self.last_query = kwargs
        return {"vectors": self._vectors}


def _vec(file_path, ctype_dir, idx=0, distance=0.2):
    return {
        "key": f"{file_path}#{idx}",
        "distance": distance,
        "metadata": {"file_path": file_path, "content_type": ctype_dir, "chunk_index": idx},
    }


def test_search_maps_dir_to_singular_and_scores():
    cache = make_cache()
    s3v = FakeS3Vectors([_vec("assets/a.md", "assets"), _vec("tools/b.md", "tools")])
    searcher = KnowledgeBaseSearcher(
        registry_provider=cache, bedrock=FakeBedrockEmbed(), s3vectors=s3v
    )
    cites = searcher.search("anything", top_k=5)
    assert [c.content_type for c in cites] == ["asset", "tool"]
    assert cites[0].score == 0.8  # 1 - distance
    assert cites[0].file_path == "assets/a.md"


def test_search_content_type_filter():
    cache = make_cache()
    s3v = FakeS3Vectors([_vec("assets/a.md", "assets"), _vec("tools/b.md", "tools")])
    searcher = KnowledgeBaseSearcher(
        registry_provider=cache, bedrock=FakeBedrockEmbed(), s3vectors=s3v
    )
    cites = searcher.search("anything", top_k=5, content_types=["tool"])
    assert [c.content_type for c in cites] == ["tool"]


def test_search_respects_top_k():
    cache = make_cache()
    s3v = FakeS3Vectors([_vec(f"assets/{i}.md", "assets", idx=i) for i in range(10)])
    searcher = KnowledgeBaseSearcher(
        registry_provider=cache, bedrock=FakeBedrockEmbed(), s3vectors=s3v
    )
    assert len(searcher.search("q", top_k=3)) == 3


# --- invoke_module ---------------------------------------------------------
class FakeLambda:
    def __init__(self, payload=None, function_error=None):
        self._payload = payload or {}
        self._function_error = function_error
        self.last_invoke = None

    def invoke(self, **kwargs):
        self.last_invoke = kwargs

        class _P:
            def __init__(self_inner, data):
                self_inner._data = data

            def read(self_inner):
                return json.dumps(self_inner._data).encode("utf-8")

        out = {"Payload": _P(self._payload)}
        if self._function_error:
            out["FunctionError"] = self._function_error
        return out


def test_invoke_module_not_enabled_returns_stub_without_lambda():
    cache = make_cache()
    fake = FakeLambda(payload={"should": "not be called"})
    invoker = ModuleInvoker(registry_provider=cache, lambda_client=fake)
    result = invoker.invoke("module-1", {"q": "x"})
    assert result["status"] == "not_implemented"
    assert result["agent_id"] == "AGENT-02"
    assert fake.last_invoke is None  # never reached Lambda


def test_invoke_module_unknown_id():
    cache = make_cache()
    invoker = ModuleInvoker(registry_provider=cache, lambda_client=FakeLambda())
    result = invoker.invoke("module-999", {})
    assert result["status"] == "not_implemented"


def test_invoke_module_enabled_calls_lambda():
    import copy

    modules = copy.deepcopy(SAMPLE_MODULES)
    for m in modules["modules"]:
        if m["id"] == "module-4":
            m["enabled"] = True
    cache = make_cache(modules=modules)
    fake = FakeLambda(payload={"status": "ok", "answer": 42})
    invoker = ModuleInvoker(registry_provider=cache, lambda_client=fake)
    result = invoker.invoke("module-4", {"q": "build"})
    assert result == {"status": "ok", "answer": 42}
    sent = json.loads(fake.last_invoke["Payload"].decode("utf-8"))
    assert sent == {"agent_id": "AGENT-05", "args": {"q": "build"}}


def test_invoke_module_function_error_degrades():
    import copy

    modules = copy.deepcopy(SAMPLE_MODULES)
    for m in modules["modules"]:
        if m["id"] == "module-4":
            m["enabled"] = True
    cache = make_cache(modules=modules)
    fake = FakeLambda(payload={"errorMessage": "boom"}, function_error="Unhandled")
    invoker = ModuleInvoker(registry_provider=cache, lambda_client=fake)
    result = invoker.invoke("module-4", {})
    assert result["status"] == "error"
