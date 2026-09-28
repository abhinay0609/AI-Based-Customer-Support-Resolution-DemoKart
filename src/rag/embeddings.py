import hashlib
import math

from src.config.settings import GOOGLE_API_KEY


class LocalEmbeddings:
    """Deterministic offline embeddings used only when Gemini is unavailable."""

    def _embed(self, text: str) -> list[float]:
        values = [0.0] * 64
        for token in text.lower().split():
            index = int(hashlib.sha256(token.encode()).hexdigest(), 16) % len(values)
            values[index] += 1.0
        magnitude = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / magnitude for value in values]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def get_embeddings():
    if GOOGLE_API_KEY:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=GOOGLE_API_KEY)
    return LocalEmbeddings()