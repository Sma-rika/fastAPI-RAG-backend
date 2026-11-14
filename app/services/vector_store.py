from typing import Any
from uuid import uuid5, NAMESPACE_URL
from qdrant_client.http import models
from app.core.config import settings
from app.core.dependencies import get_qdrant_client

async def ensure_collection() -> None:
    client = get_qdrant_client()
    collections = await client.get_collections()
    names = {item.name for item in collections.collections}
    if settings.QDRANT_COLLECTION not in names:
        await client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=models.VectorParams(size=settings.EMBEDDING_DIMENSION, distance=models.Distance.COSINE),
        )

async def upsert_chunks(document_id: int, filename: str, chunks: list[str], vectors: list[list[float]]) -> None:
    await ensure_collection()
    client = get_qdrant_client()
    points = [
        models.PointStruct(
            id=str(uuid5(NAMESPACE_URL, f"document:{document_id}:chunk:{index}")),
            vector=vector,
            payload={"document_id": document_id, "filename": filename, "chunk_index": index, "text": chunk},
        )
        for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
    ]
    await client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)

async def search_vectors(vector: list[float], limit: int) -> list[dict[str, Any]]:
    await ensure_collection()
    result = await get_qdrant_client().query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=vector,
        limit=limit,
        with_payload=True,
    )
    return [
        {"text": point.payload.get("text", ""), "document_id": point.payload.get("document_id"),
         "filename": point.payload.get("filename"), "score": point.score}
        for point in result.points
    ]
