from app.services.moderation import validate_content_safety

def test_valid_poll_content():
    is_safe, reason = validate_content_safety("Which Python framework do you prefer?")
    assert is_safe is True
    assert reason is None

def test_short_poll_content():
    is_safe, reason = validate_content_safety("No")
    assert is_safe is False
    assert "too short" in reason

def test_profanity_blocked():
    is_safe, reason = validate_content_safety("Check out this crypto-giveaway now!")
    assert is_safe is False
    assert "prohibited term" in reason
