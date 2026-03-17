from collections.abc import Sequence

import httpx


class LLMService:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def build_prompt(self, question: str, chunks: Sequence[dict]) -> str:
        context_blocks = []
        for chunk in chunks:
            context_blocks.append(
                f"[Page {chunk['page_number']}, Chunk {chunk['chunk_index']}]\n{chunk['text']}"
            )

        context = "\n\n".join(context_blocks)
        return (
            "You are answering questions about an uploaded PDF.\n"
            "Use only the provided context. If the answer is not in the context, say you do not have enough context.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer concisely and stay grounded in the context."
        )

    def answer_question(self, question: str, chunks: Sequence[dict]) -> dict:
        prompt = self.build_prompt(question, chunks)
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "answer": payload.get("response", "").strip(),
            "model": self.model,
            "prompt_context_count": len(chunks),
        }
