"""``search_knowledge_base`` — RAG over S3 Vectors (FR-003).

Embeds the query with Titan Embed v2, runs an S3 Vectors similarity search over
the ``aicoe-content`` index, and returns :class:`Citation` rows. The vector index
records the vault's plural directory prefix as ``content_type`` (assets/, tools/,
...); we map that to the singular Citation content type the UI expects.
"""

from __future__ import annotations

import json
from typing import Any

from agents.lib import models as lib_models
from agents.lib.registry import ModuleRegistry

from ..models import CONTENT_TYPE_FROM_DIR, DIR_FROM_CONTENT_TYPE, Citation, ContentType

# Asset Library is module-2; its browse UI only exists once that module is enabled.
ASSET_LIBRARY_MODULE_ID = "module-2"


def asset_library_url(
    content_type: ContentType, file_path: str, registry: ModuleRegistry
) -> str | None:
    """Deep-link into the Asset Library browse view, or None if not browseable yet.

    Only ``asset`` content has an Asset Library view, and only once module-2 is
    enabled in the registry. Until then the UI links to ``file_path`` directly.
    """
    if content_type != "asset":
        return None
    module = registry.by_id(ASSET_LIBRARY_MODULE_ID)
    if module is None or not module.enabled:
        return None
    # The Asset Library detail route is /modules/asset-library/{id}; for assets the
    # frontmatter id equals the file slug (basename without .md).
    asset_id = file_path.rsplit("/", 1)[-1].removesuffix(".md")
    return f"/modules/asset-library/{asset_id}"


class KnowledgeBaseSearcher:
    """Holds the vector-store coordinates and (lazily-created) AWS clients."""

    def __init__(
        self,
        *,
        registry_provider: Any,
        vector_bucket: str = "aicoe-content-vectors",
        index_name: str = "aicoe-content",
        embed_model: str = lib_models.TITAN_EMBED_V2,
        region: str = lib_models.REGION,
        bedrock: Any = None,
        s3vectors: Any = None,
    ) -> None:
        # ``registry_provider`` is any object exposing a ``registry`` property
        # (the ConfigCache), so asset_library_url reflects live module state.
        self._registry_provider = registry_provider
        self.vector_bucket = vector_bucket
        self.index_name = index_name
        self.embed_model = embed_model
        self.region = region
        self._bedrock = bedrock
        self._s3vectors = s3vectors

    @property
    def bedrock(self) -> Any:
        if self._bedrock is None:
            import boto3

            self._bedrock = boto3.client("bedrock-runtime", region_name=self.region)
        return self._bedrock

    @property
    def s3vectors(self) -> Any:
        if self._s3vectors is None:
            import boto3

            self._s3vectors = boto3.client("s3vectors", region_name=self.region)
        return self._s3vectors

    def _embed(self, text: str) -> list[float]:
        resp = self.bedrock.invoke_model(
            modelId=self.embed_model,
            body=json.dumps(
                {
                    "inputText": text,
                    "dimensions": lib_models.EMBED_DIMENSIONS,
                    "normalize": True,
                }
            ),
        )
        return json.loads(resp["body"].read())["embedding"]

    def search(
        self,
        query: str,
        top_k: int = 5,
        content_types: list[str] | None = None,
    ) -> list[Citation]:
        """Return up to ``top_k`` citations, optionally filtered to content types.

        ``content_types`` uses the singular Citation forms (e.g. ["asset"]). When
        a filter is given we over-fetch and filter client-side so the filter never
        starves the result set, which keeps us independent of S3 Vectors filter
        syntax quirks.
        """
        wanted: set[str] | None = None
        fetch_k = top_k
        if content_types:
            wanted = {c for c in content_types if c in DIR_FROM_CONTENT_TYPE}
            fetch_k = max(top_k * 4, top_k)

        resp = self.s3vectors.query_vectors(
            vectorBucketName=self.vector_bucket,
            indexName=self.index_name,
            queryVector={"float32": self._embed(query)},
            topK=fetch_k,
            returnMetadata=True,
            returnDistance=True,
        )

        registry = self._registry_provider.registry
        citations: list[Citation] = []
        for v in resp.get("vectors", []):
            meta = v.get("metadata", {}) or {}
            dir_prefix = meta.get("content_type", "")
            content_type = CONTENT_TYPE_FROM_DIR.get(dir_prefix)
            if content_type is None:
                continue
            if wanted is not None and content_type not in wanted:
                continue
            file_path = meta.get("file_path") or v.get("key", "").split("#", 1)[0]
            distance = v.get("distance")
            citations.append(
                Citation(
                    file_path=file_path,
                    chunk_index=int(meta.get("chunk_index", 0)),
                    content_type=content_type,
                    asset_library_url=asset_library_url(content_type, file_path, registry),
                    score=(round(1.0 - distance, 4) if isinstance(distance, int | float) else None),
                )
            )
            if len(citations) >= top_k:
                break
        return citations
