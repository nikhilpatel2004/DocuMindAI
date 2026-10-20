"""Chat / RAG question-answering endpoint.

Answers a user's question over their own uploaded documents:
question → embedding → Qdrant similarity search → KIE LLM generation,
with source citations attached to the response.
"""
from __future__ import annotations

import json
import logging
import re

from fastapi import APIRouter, Depends, Request

from ..core.config import settings
from ..core.exceptions import (
    AppError, ProcessingError, ValidationError,
)
from ..core.security import get_current_user
from ..models.conversations import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    list_messages,
)
from ..models.documents import get_document
from ..services.llm import Citation, generate_answer
from ..services.personality import (
    PersonalityCategory,
    classify_message,
    pick_banter_reply,
    pick_greeting_reply,
    pick_no_document_reply,
    pick_no_evidence_reply,
    pick_no_ready_document_reply,
    pick_serious_reply,
    reset_unrelated_streak,
)
from ..services.rag import generate_embeddings
from ..services.vector import search_chunks

router = APIRouter(prefix=settings.api_prefix, tags=["DocuMind AI"])

logger = logging.getLogger(__name__)


def _persist_turn(
    owner_id: int,
    conversation_id: str | None,
    question: str,
    answer: str,
    sources: list[dict],
) -> str | None:
    """Save the user question and assistant answer to the conversation.

    Returns the conversation id, or ``None`` when persistence fails so the
    answer is still returned to the client.
    """
    try:
        if conversation_id:
            conv_id = conversation_id
        else:
            conversation = create_conversation(owner_id, title=question.strip()[:80])
            conv_id = conversation["id"]
        add_message(conv_id, owner_id, "user", question.strip())
        add_message(conv_id, owner_id, "assistant", answer, sources)
        return conv_id
    except Exception as exc:
        logger.warning("Failed to persist conversation turn: %s", exc)
        return None


_STOPWORDS = {
    "what", "why", "how", "when", "where", "who", "which", "whom", "whose",
    "does", "did", "do", "is", "are", "was", "were", "be", "been", "being",
    "the", "a", "an", "of", "to", "in", "on", "at", "for", "and", "or",
    "but", "about", "tell", "explain", "give", "list", "please", "according",
    "say", "says", "said", "main", "key", "important", "summary", "summarize",
    "overview", "mention", "mentioned", "this", "that", "these", "those",
    "it", "its", "can", "could", "would", "should", "may", "might", "will",
    "document", "documents", "pdf", "page", "pages", "file", "files",
    "content", "kya", "kyun", "kyu", "kaise", "kab", "kahan", "kaun",
    "kitna", "kitne", "hai", "ha", "ho", "ka", "ki", "ke", "me", "mein",
    "se", "ko", "batao", "bata", "karo", "kar", "ek", "aur", "par", "tha",
    "thi", "hoga", "hain",
}

_SUMMARY_RE = re.compile(
    r"(summar|overview|main points?|key points?|"
    r"what .*(document|pdf).*(about|say|cover)|"
    r"what is (this|the) (document|pdf) about|"
    r"explain (this|the) (document|pdf)|"
    r"about this (document|pdf))",
    re.I,
)


def _content_tokens(text: str) -> set[str]:
    """Return meaningful lowercase tokens used for lexical evidence checks."""
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    result: set[str] = set()
    for token in tokens:
        if len(token) < 3 or token in _STOPWORDS:
            continue
        if len(token) > 4 and token.endswith("s"):
            token = token[:-1]
        result.add(token)
    return result


def _has_sufficient_evidence(question: str, results) -> bool:
    """Decide whether retrieved chunks contain usable evidence.

    Uses the calibrated similarity floor plus a lexical-overlap fallback so
    genuinely relevant questions are not rejected solely on a low score.
    """
    if not results:
        return False

    scores = [float(score) for _, score in results if isinstance(score, (int, float))]
    if not scores:
        return False
    best_score = max(scores)
    if best_score < settings.min_similarity:
        return False
    # Strong semantic match: accept without further checks.
    if best_score >= 0.35:
        return True
    # Summary/overview requests are legitimately document-scoped.
    if _SUMMARY_RE.search(question):
        return True

    question_tokens = _content_tokens(question)
    if not question_tokens:
        return False
    context_text = " ".join(getattr(chunk, "text", "") for chunk, _ in results)
    return bool(question_tokens & _content_tokens(context_text))


@router.post("/chat/ask")
async def ask_question(
    request: Request,
    current_user_id: int = Depends(get_current_user),
):
    """Answer a user question using RAG over their uploaded documents."""
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON body: {exc.msg}")

    question: str = body.get("question", "")
    document_ids = body.get("document_ids", None)
    conversation_id = body.get("conversation_id", None)

    if not isinstance(question, str) or not question.strip():
        raise ValidationError("Question is required")
    if conversation_id is not None and not isinstance(conversation_id, str):
        raise ValidationError("conversation_id must be a string")

    # Fail fast if the caller references a conversation they do not own.
    if conversation_id:
        get_conversation(conversation_id, current_user_id)

    user_key = f"user:{current_user_id}"

    # --- Non-factual conversational messages (no retrieval, no LLM) ---
    category = classify_message(question)
    if category in (
        PersonalityCategory.GREETING,
        PersonalityCategory.BANTER,
        PersonalityCategory.SERIOUS,
    ):
        if category is PersonalityCategory.GREETING:
            reply = pick_greeting_reply(user_key)
        elif category is PersonalityCategory.BANTER:
            reply = pick_banter_reply(user_key)
        else:
            reply = pick_serious_reply(user_key)
        return {
            "answer": reply,
            "citations": [],
            "conversation_id": _persist_turn(
                current_user_id, conversation_id, question, reply, []
            ),
            "personality": category.value,
        }

    # --- Document questions require an explicit selection ---
    if document_ids is None or document_ids == []:
        reply = pick_no_document_reply(user_key)
        return {
            "answer": reply,
            "citations": [],
            "conversation_id": _persist_turn(
                current_user_id, conversation_id, question, reply, []
            ),
            "personality": "no_document",
        }
    if not isinstance(document_ids, list):
        raise ValidationError("document_ids must be a list")

    # Resolve selected documents. Ownership violations propagate as 403/404.
    try:
        allowed = []
        for did in document_ids:
            if not isinstance(did, str):
                raise ValidationError("document_ids must contain strings")
            doc = get_document(did, current_user_id)
            if doc.get("status") == "ready":
                allowed.append(did)
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Failed to resolve accessible documents")
        raise ProcessingError("Could not load your documents") from exc

    if not allowed:
        reply = pick_no_ready_document_reply(user_key)
        return {
            "answer": reply,
            "citations": [],
            "conversation_id": _persist_turn(
                current_user_id, conversation_id, question, reply, []
            ),
            "personality": "no_ready_document",
        }

    # --- Retrieve context ---
    try:
        embeddings = generate_embeddings([question])
    except ImportError as e:
        logger.warning("Sentence Transformers not available: %s", e)
        raise ProcessingError("Embedding generation not available")
    except Exception as e:
        logger.warning("Failed to generate query embedding: %s", e)
        raise ProcessingError("Query embedding generation failed")

    if not embeddings:
        raise ProcessingError("Query embedding generation returned no result")
    query_embedding = embeddings[0]

    try:
        results = search_chunks(
            query_embedding=query_embedding,
            owner_id=current_user_id,
            document_ids=allowed,
            limit=settings.top_k,
        )
    except ImportError as e:
        logger.warning("Qdrant client not available: %s", e)
        raise ProcessingError("Vector storage not available")
    except AppError:
        raise
    except Exception as e:
        logger.warning("Failed to search Qdrant: %s", e)
        raise ProcessingError("Vector search failed")

    # --- Evidence gate: no LLM without usable document evidence ---
    if not results or not _has_sufficient_evidence(question, results):
        reply = pick_no_evidence_reply(user_key)
        return {
            "answer": reply,
            "citations": [],
            "conversation_id": _persist_turn(
                current_user_id, conversation_id, question, reply, []
            ),
            "insufficient_context": True,
            "personality": "no_evidence",
        }

    # Build context and citations
    context_parts = []
    citations = []
    for chunk, _score in results:
        context_parts.append(chunk.text)
        citations.append(Citation(
            source_filename=chunk.source_filename,
            page_number=chunk.page_number,
            chunk_id=chunk.chunk_id,
        ))
    context = "\n\n---\n\n".join(context_parts)

    # --- Generate the answer with KIE (context only, no chat history) ---
    try:
        generation_result = generate_answer(
            question=question,
            context=context,
            citations=citations,
            api_key=settings.kie_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    except AppError:
        # ModelUnavailableError / ModelNotDownloadedError / TimeoutError keep
        # their own 503/504 status and message so the client can react.
        raise
    except ImportError as e:
        logger.warning("LLM service not available: %s", e)
        raise ProcessingError("LLM generation not available")
    except Exception as e:
        logger.warning("Failed to generate answer: %s", e)
        raise ProcessingError("Answer generation failed")

    if (
        generation_result.fallback
        or generation_result.insufficient_context
        or not generation_result.answer.strip()
    ):
        reply = pick_no_evidence_reply(user_key)
        return {
            "answer": reply,
            "citations": [],
            "conversation_id": _persist_turn(
                current_user_id, conversation_id, question, reply, []
            ),
            "insufficient_context": True,
            "personality": "no_evidence",
        }

    citations_payload = [
        {
            "source_filename": c.source_filename,
            "page_number": c.page_number,
            "chunk_id": c.chunk_id,
        }
        for c in generation_result.citations
    ]
    reset_unrelated_streak(user_key)
    return {
        "answer": generation_result.answer,
        "citations": citations_payload,
        "conversation_id": _persist_turn(
            current_user_id,
            conversation_id,
            question,
            generation_result.answer,
            citations_payload,
        ),
        "personality": "document",
    }


# -------------------------------------------------------------------------
# Conversation history endpoints
# -------------------------------------------------------------------------


@router.get("/conversations")
def list_my_conversations(current_user_id: int = Depends(get_current_user)):
    """List the current user's conversations, newest first."""
    return {"conversations": list_conversations(current_user_id)}


@router.get("/conversations/{conversation_id}")
def get_my_conversation(
    conversation_id: str,
    current_user_id: int = Depends(get_current_user),
):
    """Return one owned conversation and its messages in order."""
    conversation = get_conversation(conversation_id, current_user_id)
    messages = list_messages(conversation_id, current_user_id)
    for message in messages:
        raw_sources = message.pop("sources_json", None)
        if raw_sources:
            try:
                message["sources"] = json.loads(raw_sources)
            except (TypeError, json.JSONDecodeError):
                message["sources"] = []
        else:
            message["sources"] = []
    return {"conversation": conversation, "messages": messages}


@router.delete("/conversations/{conversation_id}")
def delete_my_conversation(
    conversation_id: str,
    current_user_id: int = Depends(get_current_user),
):
    """Delete an owned conversation and all of its messages."""
    deleted = delete_conversation(conversation_id, current_user_id)
    return {"detail": "Conversation deleted", "conversation_id": deleted["id"]}
