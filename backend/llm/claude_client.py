import httpx

from backend.retrieval.classifier import QueryType
from backend.llm.prompts import build_messages

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2"


async def synthesize_answer(
    context: str,
    question: str,
    query_type: QueryType,
) -> tuple[str, int]:
    """Returns (answer_text, total_tokens_used)."""
    messages = build_messages(context, question, query_type)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
        })
        response.raise_for_status()
        data = response.json()

    answer = data["message"]["content"]
    tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
    return answer, tokens
