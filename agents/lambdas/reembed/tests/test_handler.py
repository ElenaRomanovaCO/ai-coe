import io
import json

from agents.lambdas.reembed.handler import ReEmbedder, extract_records


class FakeS3:
    def __init__(self, objects):
        self.objects = objects  # {(bucket, key): bytes}

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}


class FakeBedrock:
    def __init__(self):
        self.calls = 0

    def invoke_model(self, modelId, body):
        self.calls += 1
        return {"body": io.BytesIO(json.dumps({"embedding": [0.1] * 1024}).encode())}


class FakeS3Vectors:
    def __init__(self, existing=None):
        self.existing = existing or {}  # key -> metadata
        self.put = []
        self.deleted = []

    def get_vectors(self, vectorBucketName, indexName, keys, returnMetadata):
        vectors = [
            {"key": k, "metadata": self.existing[k]} for k in keys if k in self.existing
        ]
        return {"vectors": vectors}

    def put_vectors(self, vectorBucketName, indexName, vectors):
        self.put.extend(vectors)

    def delete_vectors(self, vectorBucketName, indexName, keys):
        self.deleted.extend(keys)


def _event(detail_type, bucket, key):
    return {
        "detail-type": detail_type,
        "detail": {"bucket": {"name": bucket}, "object": {"key": key}},
    }


def _created(bucket, key):
    return _event("Object Created", bucket, key)


def _deleted(bucket, key):
    return _event("Object Deleted", bucket, key)


def _embedder(s3, bedrock, vectors):
    return ReEmbedder(
        vector_bucket="vb",
        index_name="aicoe-content",
        embed_model="amazon.titan-embed-text-v2:0",
        s3=s3,
        bedrock=bedrock,
        s3vectors=vectors,
    )


def test_extract_eventbridge_created():
    event = {
        "detail-type": "Object Created",
        "detail": {"bucket": {"name": "vault"}, "object": {"key": "vault/a%20b.md"}},
    }
    assert extract_records(event) == [("vault", "vault/a b.md", "created")]


def test_extract_records_removed():
    event = {
        "Records": [
            {
                "eventName": "ObjectRemoved:Delete",
                "s3": {"bucket": {"name": "v"}, "object": {"key": "x.md"}},
            }
        ]
    }
    assert extract_records(event) == [("v", "x.md", "removed")]


def test_skips_non_markdown():
    emb = _embedder(FakeS3({}), FakeBedrock(), FakeS3Vectors())
    assert emb.process_event(_created("v", "notes.txt")) == [
        {"key": "notes.txt", "action": "skipped_non_md"}
    ]


def test_embeds_new_markdown():
    key = "vault/assets/x.md"
    s3 = FakeS3({("v", key): b"# Hello\n\nworld content here\n"})
    bedrock = FakeBedrock()
    vectors = FakeS3Vectors()
    emb = _embedder(s3, bedrock, vectors)
    result = emb.process_event(_created("v", key))
    assert result[0]["action"] == "embedded"
    assert result[0]["chunks"] == len(vectors.put)
    assert bedrock.calls == len(vectors.put)
    # Metadata captures the derived content type and file path.
    assert vectors.put[0]["metadata"]["content_type"] == "assets"
    assert vectors.put[0]["metadata"]["file_path"] == key


def test_unchanged_hash_skips_embedding():
    key = "vault/x.md"
    body = b"# H\n\nsame content\n"
    import hashlib

    digest = hashlib.sha256(body).hexdigest()
    s3 = FakeS3({("v", key): body})
    bedrock = FakeBedrock()
    vectors = FakeS3Vectors(existing={f"{key}#0": {"content_hash": digest}})
    emb = _embedder(s3, bedrock, vectors)
    result = emb.process_event(_created("v", key))
    assert result[0]["action"] == "unchanged"
    assert bedrock.calls == 0
    assert vectors.put == []


def test_removed_deletes_vectors():
    vectors = FakeS3Vectors()
    emb = _embedder(FakeS3({}), FakeBedrock(), vectors)
    result = emb.process_event(_deleted("v", "vault/x.md"))
    assert result[0]["action"] == "deleted"
    assert "vault/x.md#0" in vectors.deleted
