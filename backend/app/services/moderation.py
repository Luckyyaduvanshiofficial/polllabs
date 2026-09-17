import re

# Standard profanity & abuse pattern filter (PRD §4.6)
PROFANITY_PATTERN = re.compile(
    r"\b(abuse|slur|hate|spam|scam|viagra|crypto-giveaway|phishing)\b",
    re.IGNORECASE,
)

def validate_content_safety(text: str) -> tuple[bool, str | None]:
    """
    Checks if text violates basic content moderation guidelines.
    Returns (is_safe, error_reason).
    """
    if not text or not text.strip():
        return False, "Content cannot be empty"

    if len(text.strip()) < 3:
        return False, "Content is too short (min 3 characters)"

    match = PROFANITY_PATTERN.search(text)
    if match:
        return False, f"Content contains prohibited term: '{match.group(0)}'"

    return True, None
