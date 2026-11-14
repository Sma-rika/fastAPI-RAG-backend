# FastAPI Conversational RAG Backend

A modular backend with document ingestion, custom retrieval-augmented generation, Redis chat history, and LLM-assisted interview booking.

## Stack
- FastAPI + Pydantic v2
- Qdrant vector database
- PostgreSQL + SQLAlchemy 2.0 (async)
- Redis chat history
- OpenAI chat and embedding APIs
- PyMuPDF for PDF extraction

## Run locally

Requirements: Python 3.12+, Docker, and an OpenAI API key.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add OPENAI_API_KEY to .env
docker compose up -d
python -m app.db_init
uvicorn app.main:app --reload
```

OpenAPI docs: http://localhost:8000/docs

## Endpoints

### 1. Ingest a document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload?strategy=recursive" \\
  -F "file=@./sample.pdf"
```

Choose `strategy=recursive` or `strategy=sentence`.

### 2. Chat

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \\
  -H "Content-Type: application/json" \\
  -d '{"session_id":"candidate-001","message":"Summarize the uploaded document."}'
```

Use the same `session_id` across requests to continue a conversation. Redis stores the last 20 messages with a configurable TTL.

### 3. List documents and bookings

```bash
curl http://localhost:8000/api/v1/documents
curl http://localhost:8000/api/v1/bookings
```

## Booking flow

The chat service asks the LLM to extract a booking only when the conversation expresses explicit booking intent and includes name, email, date, time, and timezone. Pydantic validates the extracted fields before PostgreSQL persistence. The API saves a **booking request**, not a confirmed calendar event. Add availability checks and a confirmation workflow before treating it as a confirmed appointment.

## RAG flow (custom; no RetrievalQAChain)

1. Rewrite the latest question into a standalone retrieval query using recent conversation history.
2. Embed the rewritten query.
3. Search Qdrant for the top-k nearest chunks.
4. Build a prompt from retrieved context and Redis conversation history.
5. Call the chat completion API.
6. Persist the new user/assistant messages in Redis.

## Production hardening checklist

- Add Alembic migrations instead of `create_all`.
- Add authentication, authorization, rate limiting, and per-user session ownership.
- Add upload MIME/signature validation, malware scanning, and stricter file limits.
- Add OCR for scanned PDFs.
- Add document deletion and Qdrant point cleanup.
- Use background jobs for large ingestion jobs and idempotency keys for retries.
- Add retries/timeouts, structured logging, tracing, and metrics.
- Query rewriting uses recent Redis history to resolve ambiguous follow-up questions before vector retrieval.
- Add booking deduplication, timezone-aware date validation, calendar availability, and explicit user confirmation.
- Add tests for chunking, extraction, vector persistence, RAG, and booking extraction.
- Restrict `/bookings` behind admin authentication; it is intentionally a simple demonstration endpoint here.

## Important implementation notes

- Qdrant point IDs use deterministic document/chunk identifiers. For production, use UUIDs or integer point IDs and store the mapping.
- The ingestion route stores SQL metadata first and rolls it back if vector ingestion fails. For robust distributed consistency, use an ingestion-status field and retryable outbox/background worker.
- The sentence chunker preserves sentence boundaries where possible; exceptionally long sentences are split.
- Scanned PDFs need OCR; text extraction alone cannot read image-only pages.
