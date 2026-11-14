import re
from collections.abc import Sequence

def recursive_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Character-window chunker with overlap and paragraph/sentence boundary preference."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = max(text.rfind(". ", start, end), text.rfind(" ", start, end))
            if boundary > start + int(chunk_size * 0.65):
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks

def sentence_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Pack complete sentences into chunks; long sentences are split by character windows."""
    sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text).strip())
    chunks: list[str] = []
    current = ""
    for sentence in filter(None, sentences):
        if len(sentence) > chunk_size:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(recursive_chunks(sentence, chunk_size, overlap))
        elif not current or len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current} {sentence}".strip()
        else:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            current = f"{tail} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks

def make_chunks(text: str, strategy: str, chunk_size: int, overlap: int) -> Sequence[str]:
    if strategy == "recursive":
        return recursive_chunks(text, chunk_size, overlap)
    if strategy == "sentence":
        return sentence_chunks(text, chunk_size, overlap)
    raise ValueError(f"Unsupported chunking strategy: {strategy}")
