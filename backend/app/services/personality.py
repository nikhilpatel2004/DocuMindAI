"""Hinglish personality layer for DocuMind AI.

Deterministic, non-factual conversational replies (greetings, banter,
refusals) live here so they never consume an LLM request. Factual answers
still come exclusively from the RAG pipeline in ``app.api.chat``.
"""
from __future__ import annotations

import random
import re
import threading
from enum import Enum


class PersonalityCategory(str, Enum):
    GREETING = "greeting"
    BANTER = "banter"
    SERIOUS = "serious"
    DOCUMENT = "document"


GREETING_REPLIES = [
    "Arey bhai! 😎 Kya scene hai? PDF khol aur sawaal pooch!",
    "Oye, welcome back! 😂 Aaj kis document ki pol kholni hai?",
    "Hello ji! 📄 Document ready hai toh shuru karein?",
    "Namaste! 🙏 Aaj kya jaanna hai? PDF ready rakho.",
    "Hey hey! 😄 Main ready hoon — document select karo aur sawaal daalo.",
    "Arre welcome! 😎 Chalo, document ke andar ki duniya explore karte hain.",
]

BANTER_REPLIES = [
    "Software wala thoda pagal hoon bhai 🤖😂",
    "Bhai, PDF toh de de pehle, phir knowledge ka test le lena! 😎",
    "Achha ji 😂 ab ek document-related sawaal bhi pooch do!",
    "Main useless hoon? 😭 Theek hai, ek PDF do — phir dekhte hain kaun useless hai! 😏",
    "Arre, gaali nahi, sawaal do! 😄 Document kya kehta hai, wahi bataunga.",
    "Chal chal, drama kam kar 😂 Document kholo, main kaam dikhata hoon!",
]

SERIOUS_REPLIES = [
    "Main yahan documented sawaalon mein madad ke liye hoon. Agar koi document-related sawaal ho toh batao.",
    "Let's keep it respectful. Main aapke PDFs ke basis par answer dene ke liye ready hoon.",
    "Main is baat ko seriously le raha hoon. Document-related sawaal poocho, main wahi jawab dunga.",
]

# Escalating refusal tiers for repeated unrelated questions.
NO_EVIDENCE_TIERS = [
    [
        "Bhai 😂 main PDF ka detective hoon, Google ka replacement nahi! Document mein ye nahi mila.",
        "Oye genius 😏 iska answer teri selected PDF mein nahi hai. Document se related kuch pooch!",
        "Bhai, hawa mein answer bana doon kya? 😂 PDF mein evidence nahi mila.",
        "Ye sawaal document ke syllabus se bahar hai bhai! 📄😎",
        "Arre yaar 😂 apni PDF mein iska clue nahi mila. Agla sawaal daal!",
    ],
    [
        "Oye detective 😂 thoda PDF ke andar bhi khoj le!",
        "Bhai, ye answer document mein nahi hai — main sirf evidence pe chalta hoon 😄",
        "Dekh bhai, PDF mein iska zikr nahi hai. Kuch aur pooch! 📄",
        "Hmm, ye clue selected document mein nahi mila. Ek aur try kar 😎",
    ],
    [
        "Bhai, bina evidence ke answer banana mana hai 🤖 Agla document-related sawaal pooch!",
        "Ab toh PDF se hi poochna padega! 😅 Iska jawab document mein nahi hai.",
        "Detective mode on hai, lekin evidence zero! 🔍📄 Document se related kuch pooch.",
        "Main guess nahi karunga bhai 😌 Document mein iska answer nahi hai. Kuch aur poocho.",
    ],
]

NO_DOCUMENT_REPLIES = [
    "Pehle koi PDF select karo bhai! 📄 Tab tak main sirf hawa mein nahi bolunga 😄",
    "Document select kiye bina main kya answer doon? 😅 Left side se ek PDF choose karo!",
    "Bhai, pehle PDF toh do! 📄 Selected document ke andar se hi jawab milega.",
    "Arre, document select karo pehle! 📄 Phir main full detective mode mein aaunga 😎",
]

NO_READY_DOCUMENT_REPLIES = [
    "Selected document abhi ready nahi hai. 📄 Thoda wait karo ya doosra PDF choose karo.",
    "Bhai, ye document abhi process ho raha hai. Ready hone ke baad poocho! ⏳",
    "Document ka processing complete hone do, phir sawaal daalna 😄",
]

# Words that can appear in a short, greeting-only message. A message is a
# greeting only when *every* word is in this set, so "Hello, what does the
# policy say?" is correctly treated as a document question.
_GREETING_WORDS = {
    "hi", "hii", "hiii", "hello", "helo", "hey", "heyy", "yo", "namaste",
    "namaskar", "good", "morning", "afternoon", "evening", "night", "gm",
    "gn", "bhai", "bro", "dude", "ji", "yaar", "dost", "oye", "arey", "arre",
    "sir", "madam", "kya", "haal", "hal", "hai", "ho", "kaise", "kaisi",
    "scene", "sup", "wassup", "whats", "up", "sab", "badhiya", "theek",
    "tum", "aap", "ka", "ki", "chal", "raha", "rahi", "hoon", "hu",
    "welcome", "back", "again", "there",
}

_BANTER_RE = re.compile(
    r"\b(pagal|paagal|useless|faltu|bakwas|bakwaas|bewakoof|bewaqoof|nalayak|"
    r"stupid|idiot|dumb|shut up|chup|nikal|kuch nahi (jaanta|jaanti|jaante|know)|"
    r"tujhe kuch nahi aata|tumse na ho payega)\b",
    re.I,
)

_SERIOUS_RE = re.compile(
    r"\b(kill|murder|hurt|harm|threaten|threat|abuse|hate you|"
    r"i will (hurt|kill)|tujhe (maar|mar) dunga)\b",
    re.I,
)

_DOCUMENT_HINT_RE = re.compile(
    r"\b(pdf|document|documents|file|files|page|pages|policy|report|contract|"
    r"resume|invoice|notes|section|chapter|paragraph|upload|uploaded|selected)\b",
    re.I,
)

MAX_RECENT = 3


class _RecentResponseStore:
    """In-memory, thread-safe recent-template history per user and category."""

    def __init__(self) -> None:
        self._recent: dict[str, list[str]] = {}
        self._streak: dict[str, int] = {}
        self._lock = threading.Lock()

    def choose(self, bucket: str, templates: list[str]) -> str:
        with self._lock:
            recent = self._recent.setdefault(bucket, [])
            available = [t for t in templates if t not in recent]
            if not available:
                recent.clear()
                available = list(templates)
            choice = random.choice(available)
            recent.append(choice)
            del recent[:-MAX_RECENT]
            return choice

    def bump_unrelated(self, user_key: str) -> int:
        with self._lock:
            value = min(3, self._streak.get(user_key, 0) + 1)
            self._streak[user_key] = value
            return value

    def reset_unrelated(self, user_key: str) -> None:
        with self._lock:
            self._streak.pop(user_key, None)


_store = _RecentResponseStore()


def classify_message(text: str) -> PersonalityCategory:
    """Classify a chat message as greeting, banter, serious, or document."""
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    if not normalized:
        return PersonalityCategory.DOCUMENT

    if _SERIOUS_RE.search(normalized):
        return PersonalityCategory.SERIOUS

    lowered = normalized.lower().replace("'", "").replace("’", "")
    words = re.findall(r"[a-z0-9]+", lowered)

    if words and len(words) <= 10 and all(w in _GREETING_WORDS for w in words):
        return PersonalityCategory.GREETING

    if (
        _BANTER_RE.search(normalized)
        and len(words) <= 12
        and not _DOCUMENT_HINT_RE.search(normalized)
    ):
        if len(words) > 20 or normalized.count("!") >= 3:
            return PersonalityCategory.SERIOUS
        return PersonalityCategory.BANTER

    return PersonalityCategory.DOCUMENT


def pick_greeting_reply(user_key: str) -> str:
    return _store.choose(f"{user_key}:greeting", GREETING_REPLIES)


def pick_banter_reply(user_key: str) -> str:
    return _store.choose(f"{user_key}:banter", BANTER_REPLIES)


def pick_serious_reply(user_key: str) -> str:
    return _store.choose(f"{user_key}:serious", SERIOUS_REPLIES)


def pick_no_document_reply(user_key: str) -> str:
    return _store.choose(f"{user_key}:no_document", NO_DOCUMENT_REPLIES)


def pick_no_ready_document_reply(user_key: str) -> str:
    return _store.choose(f"{user_key}:no_ready", NO_READY_DOCUMENT_REPLIES)


def pick_no_evidence_reply(user_key: str) -> str:
    """Return an escalating refusal; also advances the unrelated streak."""
    streak = _store.bump_unrelated(user_key)
    tier = min(streak, 3) - 1
    return _store.choose(
        f"{user_key}:no_evidence:{tier}", NO_EVIDENCE_TIERS[tier]
    )


def reset_unrelated_streak(user_key: str) -> None:
    """Reset escalation after a successful, document-grounded answer."""
    _store.reset_unrelated(user_key)
