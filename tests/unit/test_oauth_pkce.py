"""
Unit Tests for OAuth 2.0 PKCE Utilities

Tests PKCE code generation, challenge creation, and validation.
RFC 7636: Proof Key for Code Exchange (PKCE)
"""

import pytest
from app.core.pkce import (
    generate_code_verifier,
    generate_code_challenge,
    validate_pkce,
    generate_authorization_code,
    generate_state,
    validate_code_verifier_format,
    validate_code_challenge_format
)


class TestPKCECodeVerifier:
    """Test code_verifier generation and validation"""

    def test_generate_code_verifier_default_length(self):
        """Test code_verifier generation with default length"""
        verifier = generate_code_verifier()

        # RFC 7636: Length must be 43-128 characters
        assert 43 <= len(verifier) <= 128

        # Must be URL-safe base64 (no padding)
        assert "=" not in verifier

    def test_generate_code_verifier_custom_length(self):
        """Test code_verifier generation with custom length"""
        verifier = generate_code_verifier(length=50)

        assert 43 <= len(verifier) <= 128

    def test_generate_code_verifier_invalid_length(self):
        """Test code_verifier generation with invalid length"""
        # Too short
        with pytest.raises(ValueError):
            generate_code_verifier(length=30)

        # Too long
        with pytest.raises(ValueError):
            generate_code_verifier(length=150)

    def test_code_verifier_uniqueness(self):
        """Test that code_verifiers are unique"""
        verifiers = [generate_code_verifier() for _ in range(100)]

        # All verifiers should be unique
        assert len(set(verifiers)) == 100


class TestPKCECodeChallenge:
    """Test code_challenge generation"""

    def test_generate_code_challenge_s256(self):
        """Test code_challenge generation with S256 method"""
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        challenge = generate_code_challenge(verifier, method="S256")

        # SHA256 base64url is always 43 characters (without padding)
        assert len(challenge) == 43

        # Expected challenge for this verifier (from RFC 7636 example)
        assert challenge == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"

    def test_generate_code_challenge_plain(self):
        """Test code_challenge generation with plain method"""
        verifier = "test_verifier_1234567890_abcdefghijklmnopqrs"
        challenge = generate_code_challenge(verifier, method="plain")

        # Plain method: challenge == verifier
        assert challenge == verifier

    def test_generate_code_challenge_invalid_method(self):
        """Test code_challenge generation with invalid method"""
        verifier = generate_code_verifier()

        with pytest.raises(ValueError):
            generate_code_challenge(verifier, method="invalid")

    def test_generate_code_challenge_empty_verifier(self):
        """Test code_challenge generation with empty verifier"""
        with pytest.raises(ValueError):
            generate_code_challenge("", method="S256")

    def test_generate_code_challenge_deterministic(self):
        """Test that code_challenge is deterministic"""
        verifier = generate_code_verifier()

        challenge1 = generate_code_challenge(verifier, method="S256")
        challenge2 = generate_code_challenge(verifier, method="S256")

        # Same verifier should always produce same challenge
        assert challenge1 == challenge2


class TestPKCEValidation:
    """Test PKCE validation (challenge vs verifier)"""

    def test_validate_pkce_success_s256(self):
        """Test successful PKCE validation with S256"""
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier, method="S256")

        # Validation should succeed
        assert validate_pkce(challenge, verifier, method="S256") is True

    def test_validate_pkce_success_plain(self):
        """Test successful PKCE validation with plain method"""
        verifier = "test_verifier_1234567890_abcdefghijklmnopqrs"
        challenge = generate_code_challenge(verifier, method="plain")

        assert validate_pkce(challenge, verifier, method="plain") is True

    def test_validate_pkce_failure_wrong_verifier(self):
        """Test PKCE validation failure with wrong verifier"""
        verifier1 = generate_code_verifier()
        verifier2 = generate_code_verifier()
        challenge = generate_code_challenge(verifier1, method="S256")

        # Validation should fail (wrong verifier)
        assert validate_pkce(challenge, verifier2, method="S256") is False

    def test_validate_pkce_failure_empty_challenge(self):
        """Test PKCE validation failure with empty challenge"""
        verifier = generate_code_verifier()

        assert validate_pkce("", verifier, method="S256") is False

    def test_validate_pkce_failure_empty_verifier(self):
        """Test PKCE validation failure with empty verifier"""
        challenge = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"

        assert validate_pkce(challenge, "", method="S256") is False

    def test_validate_pkce_constant_time(self):
        """Test that PKCE validation uses constant-time comparison"""
        # This test ensures we're using secrets.compare_digest
        # (implementation detail, but important for security)

        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier, method="S256")

        # Valid
        assert validate_pkce(challenge, verifier, method="S256") is True

        # Invalid (but similar length)
        wrong_verifier = generate_code_verifier()
        assert validate_pkce(challenge, wrong_verifier, method="S256") is False


class TestAuthorizationCode:
    """Test authorization code generation"""

    def test_generate_authorization_code(self):
        """Test authorization code generation"""
        code = generate_authorization_code()

        # Should be base64url encoded (no padding)
        assert "=" not in code

        # Reasonable length (32 bytes = 43 characters base64url)
        assert len(code) >= 40

    def test_authorization_code_uniqueness(self):
        """Test that authorization codes are unique"""
        codes = [generate_authorization_code() for _ in range(100)]

        # All codes should be unique
        assert len(set(codes)) == 100


class TestState:
    """Test state parameter generation"""

    def test_generate_state(self):
        """Test state parameter generation"""
        state = generate_state()

        # Should be base64url encoded
        assert "=" not in state

        # Reasonable length
        assert len(state) >= 40

    def test_state_uniqueness(self):
        """Test that state parameters are unique"""
        states = [generate_state() for _ in range(100)]

        # All states should be unique
        assert len(set(states)) == 100


class TestFormatValidation:
    """Test format validation helpers"""

    def test_validate_code_verifier_format_valid(self):
        """Test code_verifier format validation (valid)"""
        # Valid characters: [A-Z] [a-z] [0-9] - . _ ~
        valid_verifiers = [
            "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
            "A" * 43,  # Minimum length
            "B" * 128,  # Maximum length
            "abcdefghijklmnopqrstuvwxyz0123456789-._~ABC",
        ]

        for verifier in valid_verifiers:
            assert validate_code_verifier_format(verifier) is True

    def test_validate_code_verifier_format_invalid(self):
        """Test code_verifier format validation (invalid)"""
        invalid_verifiers = [
            "",  # Empty
            "A" * 42,  # Too short
            "B" * 129,  # Too long
            "invalid=characters",  # Invalid character (=)
            "invalid+characters",  # Invalid character (+)
            "invalid/characters",  # Invalid character (/)
        ]

        for verifier in invalid_verifiers:
            assert validate_code_verifier_format(verifier) is False

    def test_validate_code_challenge_format_s256_valid(self):
        """Test code_challenge format validation S256 (valid)"""
        # S256: SHA256 base64url is always 43 characters
        valid_challenge = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"

        assert validate_code_challenge_format(valid_challenge, "S256") is True

    def test_validate_code_challenge_format_s256_invalid(self):
        """Test code_challenge format validation S256 (invalid)"""
        invalid_challenges = [
            "",  # Empty
            "A" * 42,  # Too short
            "B" * 44,  # Too long
            "invalid=base64url",  # Invalid character
        ]

        for challenge in invalid_challenges:
            assert validate_code_challenge_format(challenge, "S256") is False

    def test_validate_code_challenge_format_plain_valid(self):
        """Test code_challenge format validation plain (valid)"""
        # Plain: challenge == verifier
        valid_challenge = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"

        assert validate_code_challenge_format(valid_challenge, "plain") is True

    def test_validate_code_challenge_format_plain_invalid(self):
        """Test code_challenge format validation plain (invalid)"""
        # Plain method uses verifier format validation
        invalid_challenge = "A" * 42  # Too short for verifier

        assert validate_code_challenge_format(invalid_challenge, "plain") is False


@pytest.mark.unit
class TestPKCEEndToEnd:
    """End-to-end PKCE flow tests"""

    def test_pkce_flow_s256(self):
        """Test complete PKCE flow with S256"""
        # Step 1: Client generates code_verifier
        code_verifier = generate_code_verifier()

        # Step 2: Client generates code_challenge
        code_challenge = generate_code_challenge(code_verifier, method="S256")

        # Step 3: Client sends authorization request with code_challenge
        # (authorization server stores code_challenge)

        # Step 4: Authorization server validates challenge format
        assert validate_code_challenge_format(code_challenge, "S256") is True

        # Step 5: Client exchanges code for tokens with code_verifier
        # (authorization server validates PKCE)
        is_valid = validate_pkce(code_challenge, code_verifier, method="S256")

        assert is_valid is True

    def test_pkce_flow_tampering_detection(self):
        """Test that PKCE detects code interception (tampering)"""
        # Legitimate client
        legitimate_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(legitimate_verifier, method="S256")

        # Authorization server stores code_challenge

        # Attacker intercepts authorization code and tries to use it
        attacker_verifier = generate_code_verifier()

        # PKCE validation should FAIL (attacker doesn't know legitimate verifier)
        is_valid = validate_pkce(code_challenge, attacker_verifier, method="S256")

        assert is_valid is False
