from app.core.rate_limit import hash_ip, check_ip_rate_limit
from app.core.config import settings

def test_ip_hashing():
    hash1 = hash_ip("192.168.1.100")
    hash2 = hash_ip("192.168.1.100")
    hash3 = hash_ip("192.168.1.101")
    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64  # SHA-256 length

def test_rate_limiting():
    test_ip = "10.0.0.99"
    # Consume within limit
    for _ in range(settings.VOTE_RATE_LIMIT_PER_MINUTE):
        assert check_ip_rate_limit(test_ip) is True

    # Exceed limit
    assert check_ip_rate_limit(test_ip) is False
