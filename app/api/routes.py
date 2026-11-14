from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Base, Booking, Document
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.documents import DocumentUploadResponse
from app.services.extraction import extract_text
from app.services.chunking import make_chunks
from app.services.llm import embed_texts, embed_query, generate_answer, extract_booking_details, rewrite_query
from app.services.vector_store import upsert_chunks, search_vectors
from app.services.memory import get_history, save_turn
from app.services.booking import create_booking

router = APIRouter()

@router.post("/documents/upload", response_model=DocumentUploadResponse, tags=["documents"])
async def upload_document(
    file: UploadFile = File(...),
    strategy: str = "recursive",
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    if strategy not in {"recursive", "sentence"}:
        raise HTTPException(status_code=422, detail="strategy must be 'recursive' or 'sentence'.")
    if not file.filename or not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=415, detail="Only .pdf and .txt files are supported.")
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB.")
    await file.seek(0)
    text = await extract_text(file)
    chunks = list(make_chunks(text, strategy, settings.DEFAULT_CHUNK_SIZE, settings.DEFAULT_CHUNK_OVERLAP))
    if not chunks:
        raise HTTPException(status_code=422, detail="Document produced no chunks.")
    doc = Document(filename=file.filename, content_type=file.content_type or "application/octet-stream",
                   chunk_count=len(chunks), chunking_strategy=strategy)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    try:
        vectors = await embed_texts(chunks)
        await upsert_chunks(doc.id, doc.filename, chunks, vectors)
    except Exception as exc:
        await db.rollback()
        import traceback
        traceback.print_exc()

        raise HTTPException(
        status_code=502,
        detail=f"Vector ingestion failed: {str(exc)}"
        ) from exc
    return DocumentUploadResponse(document_id=doc.id, filename=doc.filename,
                                   chunks_created=len(chunks), chunking_strategy=strategy)

@router.get("/documents", tags=["documents"])
async def list_documents(db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return [
        {"id": d.id, "filename": d.filename, "content_type": d.content_type,
         "chunk_count": d.chunk_count, "chunking_strategy": d.chunking_strategy,
         "created_at": d.created_at.isoformat() if d.created_at else None}
        for d in result.scalars().all()
    ]

@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    history = await get_history(request.session_id)
    retrieval_query = await rewrite_query(request.message, history)
    query_vector = await embed_query(retrieval_query)
    contexts = await search_vectors(query_vector, settings.TOP_K)
    answer = await generate_answer(request.message, history, contexts)

    candidate_history = history + [
    {"role": "user", "content": request.message},
    {"role": "assistant", "content": answer},
    ]

    # Extract booking details only from user messages.
    booking_conversation = [
        message
        for message in candidate_history
        if message["role"] == "user"
    ]

    booking_details = await extract_booking_details(booking_conversation)

    
    booking_id = None
    booking_created = False
    if booking_details:
        booking = await create_booking(db, request.session_id, booking_details)
        booking_id = booking.id
        booking_created = True

        answer = (
            f"Your interview booking request has been saved successfully. "
            f"Reference number: {booking.id}. "
            f"Requested date: {booking.booking_date} at "
            f"{booking.booking_time} ({booking.timezone}). "
            "Please note that this is a booking request, not a confirmed appointment."
     )
    await save_turn(request.session_id, history, request.message, answer)
    sources = [
        {"document_id": int(c["document_id"]), "filename": str(c["filename"]), "score": float(c["score"])}
        for c in contexts if c.get("document_id") is not None
    ]
    return ChatResponse(session_id=request.session_id, answer=answer,
                        booking_created=booking_created, booking_id=booking_id, sources=sources)

@router.get("/bookings", tags=["bookings"])
async def list_bookings(db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(Booking).order_by(Booking.created_at.desc()))
    return [
        {"id": b.id, "session_id": b.session_id, "name": b.name, "email": b.email,
         "date": b.booking_date, "time": b.booking_time, "timezone": b.timezone,
         "status": b.status, "created_at": b.created_at.isoformat() if b.created_at else None}
        for b in result.scalars().all()
    ]
