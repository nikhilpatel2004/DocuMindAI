"""Per-route implementations for the DocuMind AI API."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from pydantic import BaseModel

from ..core.config import settings
from ..core.exceptions import (
    AuthenticationError, ConflictError, ForbiddenError, NotFoundError,
    PayloadTooLargeError, UnsupportedMediaTypeError, ValidationError,
    ProcessingError, ModelUnavailableError, ModelNotDownloadedError,
)
from ..core.security import (
    create_access_token, get_current_user,
    verify_password, validate_email, validate_password_strength,
)
from ..models.users import create_user, get_user_by_email, get_user_by_id
from ..models.documents import (
    create_document, delete_document, get_document, list_documents,
    update_document_status
)
from ..services.pdf import validate_file, extract_text
from ..services.rag import Chunk, chunk_text, generate_embeddings
from ..services.vector import upsert_chunks, delete_chunks_for_document

router = APIRouter(prefix=settings.api_prefix, tags=["DocuMind AI"])

logger = logging.getLogger(__name__)


class AuthRequest(BaseModel):
    email: str
    password: str
    username: str | None = None

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

UPLOAD_DIR = settings.upload_dir
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _save_upload(upload: UploadFile) -> Path:
    """Save the uploaded file and return the ``Path`` to it."""
    data = upload.file.read()
    storage_name = f"{os.urandom(16).hex()}.pdf"
    path = UPLOAD_DIR / storage_name
    path.write_bytes(data)
    return path


def _extract_and_chunk(
    pdf_path: Path, owner_id: int, document_id: str, chunk_size: int,
    chunk_overlap: int, source_filename: str
) -> tuple[list[Chunk], int]:
    """Extract text from PDF → chunks → generate embeddings → return ``(chunks, page_count)``."""
    full_text, page_count = extract_text(pdf_path)
    if not full_text.strip():
        raise ProcessingError("The PDF contains no extractable text.")
    chunks = chunk_text(full_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    # Annotate each chunk with document/owner/metadata
    for i, chunk in enumerate(chunks):
        chunk.document_id = document_id
        chunk.owner_id = owner_id
        chunk.page_number = (i % page_count) + 1  # simple round-robin
        chunk.chunk_index = i
        chunk.source_filename = source_filename
    # Generate embeddings for the chunks
    chunk_texts = [chunk.text for chunk in chunks]
    try:
        embeddings = generate_embeddings(chunk_texts)
        for i, chunk in enumerate(chunks):
            chunk.embedding = embeddings[i]
    except ImportError as e:
        logger.warning("Sentence Transformers not available: %s", e)
        raise ProcessingError("Embedding generation not available")
    except Exception as e:
        logger.warning("Failed to generate embeddings: %s", e)
        raise ProcessingError("Embedding generation failed")
    return chunks, page_count


def _store_chunks_in_qdrant(chunks: list[Chunk]) -> None:
    """Store chunks in Qdrant vector store."""
    try:
        upsert_chunks(chunks)
        logger.info("Stored %d chunks in Qdrant collection %s", len(chunks), settings.qdrant_collection)
    except ImportError as e:
        logger.warning("Qdrant client not available: %s", e)
        raise ProcessingError("Vector storage not available")
    except Exception as e:
        logger.warning("Failed to store chunks in Qdrant: %s", e)
        raise ProcessingError("Vector storage failed")


# -------------------------------------------------------------------------
# Auth endpoints
# -------------------------------------------------------------------------


@router.post("/auth/register")
async def register(body: AuthRequest):
    """Register a new user account with hashed password and return access token."""
    validate_email(body.email)
    validate_password_strength(body.password)
    user = create_user(body.email, body.password, body.username)
    token = create_access_token(user["id"], user["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
        },
    }


@router.post("/auth/login")
async def login(body: AuthRequest):
    """Authenticate user with email and password, return JWT access token."""
    user = get_user_by_email(body.email)
    if user is None or not verify_password(body.password, user["password"]):
        raise AuthenticationError("Invalid email or password")
    token = create_access_token(user["id"], user["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
        },
    }


@router.get("/auth/me")
async def get_me(current_user_id: int = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    user = get_user_by_id(current_user_id)
    if user is None:
        raise NotFoundError("User not found")
    return {
        "id": user["id"],
        "email": user["email"],
        "username": user["username"],
    }


# -------------------------------------------------------------------------
# Document endpoints
# -------------------------------------------------------------------------


@router.post("/documents")
async def upload_document(
    current_user_id: int = Depends(get_current_user),
    file: UploadFile = File(...),
):
    """Upload a PDF document.

    Only PDF files up to ``MAX_UPLOAD_MB`` (default 20) are accepted.
    The backend validates the file, extracts text, chunks it, generates
    local embeddings, and stores vectors in Qdrant scoped to the user.
    """
    # Validate file type
    # FastAPI gives us the original filename — we must not trust it as a path.
    original_name = file.filename or "unknown"
    if not original_name.lower().endswith(".pdf"):
        raise UnsupportedMediaTypeError("Only PDF files are accepted")

    # Read and save
    try:
        upload_path = _save_upload(file)
    except Exception as exc:  # noqa: broad-except
        raise PayloadTooLargeError(
            f"Could not save uploaded file: {exc}"
        )

    # Validate size and type
    try:
        validate_file(upload_path)
    except ValueError as exc:
        # Clean up the bad file
        try:
            upload_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=str(exc))

    # Generate a server-controlled ID and store metadata
    try:
        doc = create_document(
            owner_id=current_user_id,
            original_name=original_name,
            storage_name=upload_path.name,
        )
    except Exception:
        try:
            upload_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise

    # Process: extract, chunk, embed, store in Qdrant
    try:
        chunks, page_count = _extract_and_chunk(
            pdf_path=upload_path,
            owner_id=current_user_id,
            document_id=doc["id"],
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            source_filename=original_name,
        )
        _store_chunks_in_qdrant(chunks)

        # Mark document as ready
        update_document_status(
            document_id=doc["id"],
            status="ready",
            file_size=upload_path.stat().st_size,
            page_count=page_count,
            chunk_count=len(chunks),
        )
    except ProcessingError as exc:
        # Document stays in 'uploaded' / 'failed' state
        try:
            delete_document(document_id=doc["id"], owner_id=current_user_id)
        except Exception:
            pass
        try:
            upload_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=422, detail=str(exc))
    except ModelNotDownloadedError as exc:
        try:
            delete_document(document_id=doc["id"], owner_id=current_user_id)
        except Exception:
            pass
        try:
            upload_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=503, detail=str(exc))
    except ModelUnavailableError as exc:
        try:
            delete_document(document_id=doc["id"], owner_id=current_user_id)
        except Exception:
            pass
        try:
            upload_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:  # noqa: broad-except
        try:
            delete_document(document_id=doc["id"], owner_id=current_user_id)
        except Exception:
            pass
        try:
            upload_path.unlink(missing_ok=True)
        except Exception:
            pass
        logger.exception("Unexpected error during PDF processing")
        raise HTTPException(status_code=500, detail="Document processing failed")

    return {
        "document_id": doc["id"],
        "original_name": doc["original_name"],
        "status": "ready",
        "page_count": page_count,
        "chunk_count": len(chunks),
    }


@router.get("/documents")
async def list_my_documents(
    current_user_id: int = Depends(get_current_user),
):
    """List the authenticated user's documents."""
    docs = list_documents(current_user_id)
    return {"documents": docs}


@router.get("/documents/{document_id}")
async def get_my_document(
    document_id: str,
    current_user_id: int = Depends(get_current_user),
):
    """Inspect a single document owned by the authenticated user."""
    doc = get_document(document_id, current_user_id)
    return doc


@router.delete("/documents/{document_id}")
async def delete_my_document(
    document_id: str,
    current_user_id: int = Depends(get_current_user),
):
    """Delete a document and all its stored vectors."""
    try:
        deleted = delete_document(document_id, current_user_id)
        # Purge user's vectors for this document from Qdrant
        try:
            delete_chunks_for_document(document_id, current_user_id)
        except Exception as exc:
            logger.warning("Failed to delete Qdrant vectors: %s", exc)
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"detail": "Document deleted", "document_id": document_id}
