
import json
import asyncio
from functools import lru_cache


from ollama import AsyncClient
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.schemas.chat import BookingDetails


# -------------------------
# Local Ollama client
# -------------------------

@lru_cache(maxsize=1)
def get_ollama_client() -> AsyncClient:
    return AsyncClient(host=settings.OLLAMA_BASE_URL)


# -------------------------
# Local embedding model
# -------------------------

@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings locally using Sentence Transformers."""
    model = get_embedding_model()

    embeddings = await asyncio.to_thread(
        model.encode,
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return embeddings.tolist()


async def embed_query(text: str) -> list[float]:
    vectors = await embed_texts([text])
    return vectors[0]


# -------------------------
# Query rewriting
# -------------------------

async def rewrite_query(
    question: str,
    history: list[dict[str, str]],
) -> str:
    """Rewrite follow-up questions into standalone retrieval queries."""
    if not history:
        return question

    client = get_ollama_client()

    response = await client.chat(
        model=settings.OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Rewrite the latest user question as a standalone retrieval "
                    "query using the conversation history. Preserve its meaning. "
                    "Return only the rewritten query; do not answer it."
                ),
            },
            *history[-8:],
            {"role": "user", "content": question},
        ],
        options={"temperature": 0},
    )

    return response.message.content or question


# -------------------------
# RAG answer generation
# -------------------------

async def generate_answer(
    question: str,
    history: list[dict[str, str]],
    contexts: list[dict],
) -> str:
    """Generate an answer using retrieved document context and Ollama."""
    client = get_ollama_client()

    context_text = "\n\n".join(
        f"[Source {i + 1}: {item['filename']}]\n{item['text']}"
        for i, item in enumerate(contexts)
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Answer using the supplied document "
                "context when relevant. If the answer is not supported by the "
                "context, say so rather than inventing facts. Use conversation "
                "history to resolve follow-up questions. Do not claim a booking "
                "is confirmed unless the application confirms it.\n\n"
                "DOCUMENT CONTEXT:\n"
                + (context_text or "No relevant documents found.")
            ),
        },
        *history[-12:],
        {"role": "user", "content": question},
    ]

    response = await client.chat(
        model=settings.OLLAMA_MODEL,
        messages=messages,
        options={"temperature": 0.2},
    )

    return response.message.content or ""


# -------------------------
# Interview booking extraction
# -------------------------

async def extract_booking_details(
    conversation: list[dict[str, str]],
) -> BookingDetails | None:
    """Extract complete interview booking details using Ollama."""
    client = get_ollama_client()

    prompt = (
    "Extract interview booking details from the user's message. "
    "Return JSON with exactly these keys: "
    "intent, name, email, date, time, timezone. "
    "intent must be true when the user explicitly requests a booking "
    "and provides all five fields. "
    "Do not invent missing values."
)   

    response = await client.chat(
        model=settings.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            *conversation[-10:],
        ],
        format="json",
        options={"temperature": 0},
    )

    try:
        data = json.loads(response.message.content or "{}")

        if not data.get("intent"):
            return None

        return BookingDetails(
            name=data["name"],
            email=data["email"],
            date=data["date"],
            time=data["time"],
            timezone=data.get("timezone") or "Asia/Kathmandu",
        )

    except (KeyError, ValueError, TypeError):
        return None
