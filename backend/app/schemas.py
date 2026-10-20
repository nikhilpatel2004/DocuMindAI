"""Pydantic models for request and response schemas."""
from __future__ import annotations

from pydantic import BaseModel
from typing import List, Optional


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    id: int
    email: str


class Document(BaseModel):
    id: str
    original_name: str
    status: str
    page_number: Optional[int]
    chunk_count: Optional[int]


class DocumentUploadResponse(BaseModel):
    document_id: str
    original_name: str
    status: str
    page_number: Optional[int]
    chunk_count: Optional[int]


class ChatRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None


class CitationResponse(BaseModel):
    source_filename: str
    page_number: Optional[int]
    chunk_id: str


class ChatResponse(BaseModel):
    answer: str
    citations: List[CitationResponse]
    conversation_id: Optional[str] = None
    fallback: bool = False
    insufficient_context: bool = False
