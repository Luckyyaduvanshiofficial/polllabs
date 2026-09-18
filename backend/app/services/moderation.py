"""Content moderation for poll titles, descriptions and options (PRD §4.6).

The previous pattern matched topic words ("hate", "abuse", "spam") and so
rejected ordinary questions like "Do you hate JavaScript?" while passing actual
slurs. This version separates the two concerns it was conflating:

  * profanity — matched on whole words, so "assess" and "Scunthorpe" pass;
  * spam/scam solicitation — matched on phrases, which is where the real
    false-positive risk lives.

A word list is a floor, not a ceiling: it cannot catch obfuscation or slurs it
does not enumerate. For production-grade coverage, put a managed moderation
service in front of this and keep this as the cheap local check.
"""

import re

# Common profanity, matched as whole words. Deliberately short: this is a
# tripwire for casual abuse, not a comprehensive list.
_PROFANITY_WORDS = (
    "fuck",
    "shit",
    "bitch",
    "cunt",
    "asshole",
    "bastard",
    "dickhead",
    "motherfucker",
    "whore",
    "slut",
    "retard",
    "faggot",
    "nigger",
)

# Solicitation and scam phrases. Multi-word by design so that legitimate polls
# about crypto, giveaways or pharmacology are not caught.
_SPAM_PHRASES = (
    r"crypto[\s\-]?giveaway",
    r"free\s+(?:bitcoin|btc|eth|crypto|money|cash|gift\s?cards?)",
    r"click\s+(?:here|this\s+link)\s+to\s+(?:win|claim|earn)",
    r"double\s+your\s+(?:money|crypto|investment)",
    r"work\s+from\s+home\s+and\s+earn",
    r"buy\s+(?:viagra|cialis)",
    r"(?:verify|confirm)\s+your\s+(?:wallet|seed\s?phrase|password)",
    r"send\s+(?:your\s+)?(?:seed\s?phrase|private\s+key)",
)

PROFANITY_PATTERN = re.compile(
    r"\b(?:" + "|".join(_PROFANITY_WORDS) + r")(?:s|es|ing|ed)?\b",
    re.IGNORECASE,
)
SPAM_PATTERN = re.compile("|".join(_SPAM_PHRASES), re.IGNORECASE)

MIN_CONTENT_LENGTH = 3


def validate_content_safety(text: str) -> tuple[bool, str | None]:
    """
    Checks text against the profanity and solicitation filters.
    Returns (is_safe, error_reason).
    """
    if not text or not text.strip():
        return False, "Content cannot be empty"

    stripped = text.strip()
    if len(stripped) < MIN_CONTENT_LENGTH:
        return False, f"Content is too short (min {MIN_CONTENT_LENGTH} characters)"

    if PROFANITY_PATTERN.search(stripped):
        return False, "Content contains profanity. Please rephrase."

    if SPAM_PATTERN.search(stripped):
        return False, "Content looks like spam or a scam solicitation."

    return True, None
