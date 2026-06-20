from groq import AsyncGroq

from backend.config import get_settings
from backend.retrieval.classifier import QueryType
from backend.llm.prompts import build_messages


async def synthesize_answer(
    context: str,
    question: str,
    query_type: QueryType,
) -> tuple[str, int]:
    """Returns (answer_text, total_tokens_used)."""
    settings = get_settings()
    client = AsyncGroq(api_key=settings.groq_api_key)
    messages = build_messages(context, question, query_type)

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.0,
        max_tokens=1500,
    )

    tokens = response.usage.total_tokens if response.usage else 0
    return response.choices[0].message.content, tokens
