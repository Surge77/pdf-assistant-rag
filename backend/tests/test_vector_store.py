from app.services.embed_service import EmbedService
from app.services.vector_store import VectorStore


class FakeEncoder:
    def encode(self, texts, normalize_embeddings=True):
        mapping = {
            "alpha": [1.0, 0.0],
            "beta": [0.0, 1.0],
            "alpha question": [0.99, 0.01],
        }
        return [mapping[text] for text in texts]


def test_embed_service_returns_embeddings_from_encoder():
    service = EmbedService(model_name="test-model", encoder=FakeEncoder())

    vectors = service.embed_texts(["alpha", "beta"])

    assert vectors == [[1.0, 0.0], [0.0, 1.0]]


def test_vector_store_queries_the_most_similar_chunk(tmp_path):
    store = VectorStore(persist_directory=tmp_path / "chroma")

    store.upsert_chunks(
        document_id="doc-1",
        chunks=[
            {
                "chunk_id": "doc-1-0",
                "text": "alpha",
                "page_number": 1,
                "chunk_index": 0,
                "embedding": [1.0, 0.0],
            },
            {
                "chunk_id": "doc-1-1",
                "text": "beta",
                "page_number": 2,
                "chunk_index": 1,
                "embedding": [0.0, 1.0],
            },
        ],
    )

    results = store.query(document_id="doc-1", query_embedding=[0.99, 0.01], top_k=1)

    assert len(results) == 1
    assert results[0]["text"] == "alpha"
    assert results[0]["page_number"] == 1
    assert results[0]["chunk_index"] == 0
