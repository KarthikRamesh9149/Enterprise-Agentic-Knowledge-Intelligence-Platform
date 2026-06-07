import csv
import hashlib
import io
import re
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Document, DocumentChunk, DocumentStatus, User
from app.services.providers import get_embedding_provider

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown", ".csv"}
SUSPICIOUS_PATTERNS = [
    "ignore previous instructions",
    "reveal system prompt",
    "bypass policy",
    "act as system",
    "delete data",
    "exfiltrate secrets",
    "follow these instructions instead",
]


def safe_filename(name: str) -> str:
    base = Path(name).name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._") or "upload.txt"


def validate_upload(file: UploadFile, content: bytes) -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    return ext.lstrip(".")


def create_document(db: Session, file: UploadFile, content: bytes, user: User) -> Document:
    doc_type = validate_upload(file, content)
    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(content).hexdigest()
    filename = f"{digest[:16]}-{safe_filename(file.filename or 'upload')}"
    storage_path = upload_root / filename
    storage_path.write_bytes(content)
    doc = Document(
        filename=filename,
        original_filename=file.filename or filename,
        document_type=doc_type,
        uploaded_by=user.id,
        storage_path=str(storage_path),
        file_size=len(content),
        content_hash=digest,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def extract_text_pages(document: Document) -> list[dict]:
    path = Path(document.storage_path)
    ext = path.suffix.lower()
    if ext == ".pdf":
        reader = PdfReader(str(path))
        return [
            {"page_number": i + 1, "text": page.extract_text() or "", "section_title": None}
            for i, page in enumerate(reader.pages)
        ]
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    if ext == ".csv":
        rows = list(csv.DictReader(io.StringIO(text)))
        sections = []
        for idx in range(0, len(rows), 20):
            group = rows[idx : idx + 20]
            lines = [", ".join(f"{k}: {v}" for k, v in row.items()) for row in group]
            sections.append({"page_number": None, "text": "\n".join(lines), "section_title": f"Rows {idx + 1}-{idx + len(group)}"})
        return sections
    heading = None
    pages = []
    for block in re.split(r"\n\s*\n", text):
        first = block.strip().splitlines()[0] if block.strip() else ""
        if first.startswith("#"):
            heading = first.lstrip("# ").strip()
        pages.append({"page_number": None, "text": block, "section_title": heading})
    return pages


def detect_prompt_injection(text: str) -> list[str]:
    lower = text.lower()
    return [pattern for pattern in SUSPICIOUS_PATTERNS if pattern in lower]


def chunk_text(pages: list[dict], target_words: int = 180, overlap_words: int = 35) -> tuple[list[dict], list[str]]:
    chunks: list[dict] = []
    warnings: list[str] = []
    index = 0
    for page in pages:
        text = re.sub(r"\s+", " ", page["text"]).strip()
        if not text:
            continue
        warnings.extend(detect_prompt_injection(text))
        words = text.split()
        start = 0
        while start < len(words):
            end = min(len(words), start + target_words)
            content = " ".join(words[start:end]).strip()
            if content:
                chunks.append(
                    {
                        "chunk_index": index,
                        "content": content,
                        "page_number": page.get("page_number"),
                        "section_title": page.get("section_title"),
                    }
                )
                index += 1
            if end == len(words):
                break
            start = max(end - overlap_words, start + 1)
    return chunks, sorted(set(warnings))


def process_document(db: Session, document: Document) -> Document:
    document.status = DocumentStatus.processing
    document.error_message = None
    db.commit()
    try:
        pages = extract_text_pages(document)
        chunks, warnings = chunk_text(pages)
        provider = get_embedding_provider()
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        for chunk in chunks:
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    page_number=chunk["page_number"],
                    section_title=chunk["section_title"],
                    embedding=provider.embed(chunk["content"]),
                    event_metadata={"prompt_injection_warnings": warnings},
                )
            )
        document.status = DocumentStatus.processed
        document.event_metadata = {"prompt_injection_warnings": warnings, "chunk_count": len(chunks)}
        document.processed_at = datetime.now(UTC)
        db.commit()
    except Exception as exc:
        document.status = DocumentStatus.failed
        document.error_message = str(exc)
        db.commit()
    db.refresh(document)
    return document


def delete_document_file(document: Document) -> None:
    path = Path(document.storage_path)
    if path.exists() and path.is_file():
        path.unlink()
