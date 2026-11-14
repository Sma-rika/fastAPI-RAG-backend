from typing import Literal
from pydantic import BaseModel, ConfigDict

ChunkingStrategy = Literal["recursive", "sentence"]

class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    chunks_created: int
    chunking_strategy: ChunkingStrategy

class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    content_type: str
    chunk_count: int
    chunking_strategy: str
    created_at: str | None = None
