# FastAPI RAG Backend

A modular backend with document ingestion, custom retrieval-augmented generation, Redis chat history, and LLM-assisted interview booking.

## Stack
- FastAPI + Pydantic v2
- Qdrant vector database
- PostgreSQL + SQLAlchemy 2.0 (async)
- Redis chat history
- PyMuPDF for PDF extraction
- Ollama 3.2

## Create a virtual environment
'''python -m venv .venv'''


## Activate it on windows
'''.venv\Scripts\activate '''

## Install dependencies
'''pip install -r requirements.txt'''

## Configire environment variables
## Start the supporting services
'''docker compose up -d'''

## Initialize database
'''python -m app.db_init'''

## Start the server
'''uvicorn app.main:app --reload'''

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



### 3. List documents and bookings

```bash
curl http://localhost:8000/api/v1/documents
curl http://localhost:8000/api/v1/bookings
```

