from collections.abc import Sequence

from sentence_transformers import SentenceTransformer


class EmbedService:
    def __init__(self, model_name: str, encoder: object | None = None) -> None:
        self.model_name = model_name
        self._encoder = encoder

    def _get_encoder(self) -> object:
        if self._encoder is None:
            self._encoder = SentenceTransformer(self.model_name)
        return self._encoder

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        encoder = self._get_encoder()
        vectors = encoder.encode(list(texts), normalize_embeddings=True)
        return [[float(value) for value in vector] for vector in vectors]
