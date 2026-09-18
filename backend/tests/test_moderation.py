from app.services.moderation import validate_content_safety

def test_valid_poll_content():
    is_safe, reason = validate_content_safety("Which Python framework do you prefer?")
    assert is_safe is True
    assert reason is None

def test_short_poll_content():
    is_safe, reason = validate_content_safety("No")
    assert is_safe is False
    assert "too short" in reason

def test_spam_solicitation_blocked():
    is_safe, reason = validate_content_safety("Check out this crypto-giveaway now!")
    assert is_safe is False
    assert "spam" in reason.lower()


def test_profanity_blocked():
    is_safe, reason = validate_content_safety("Which fucking framework wins?")
    assert is_safe is False
    assert "profanity" in reason.lower()


def test_topic_words_are_not_profanity():
    """Regression: topical words must not be treated as abuse (PRD §4.6)."""
    for text in (
        "Do you hate JavaScript?",
        "Is crypto a good investment?",
        "How do we assess spam filters?",
    ):
        is_safe, reason = validate_content_safety(text)
        assert is_safe is True, f"{text!r} was wrongly blocked: {reason}"
