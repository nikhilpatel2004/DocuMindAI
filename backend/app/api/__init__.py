"""FastAPI routes for DocuMind AI.

Endpoints follow the ``/api/v1`` prefix documented in the PRD.
All routes enforce authentication and ownership checks.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from ..core.config import settings
from ..core.exceptions import (
    AuthenticationError, ConflictError, NotFoundError,
    ProcessingError, InsufficientContextError, ModelUnavailableError,
    PayloadTooLargeError, UnsupportedMediaTypeError
)
from ..core.security import get_current_user_id, hash_password, verify_password, create_access_token
from ..models.users import create_user, get_user_by_email, get_user_by_id
from ..models.documents import (
    create_document, list_documents, get_document,
    update_document_status, delete_document
)
from ..models.conversations import (
    create_conversation, list_conversations, get_conversation,
    list_messages, add_message, touch_conversation
)
from ..services.pdf import validate_file, extract_text
from ..services.vector import QDRANT_PAYLOAD_LIMIT_KEYS
from ..services.llm import Citation, GenerationResult, SYSTEM_PROMPT

api_router = APIRouter(prefix=settings.api_prefix, tags=["DocuMind AI"])
