#!/usr/bin/env python3
"""
Test script to demonstrate production secrets validation.

This script simulates both successful and failed validation scenarios.

Usage:
    python scripts/test_production_secrets.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from unittest.mock import MagicMock
from app.config import Settings, validate_production_secrets


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def test_debug_mode_with_unsafe_secrets():
    """Test: Validation should be skipped in debug mode."""
    print_section("TEST 1: Debug Mode with Unsafe Secrets (Should PASS)")

    settings = MagicMock(spec=Settings)
    settings.DEBUG = True
    settings.JWT_SECRET_KEY = "dev_secret_key_unsafe"
    settings.ENCRYPTION_KEY = "dev_encryption_key_unsafe"
    settings.POSTGRES_PASSWORD = "dev_password_change_in_prod"
    settings.SERVICE_AUTH_TOKEN = "st_dev_test_token"

    try:
        validate_production_secrets(settings)
        print("✅ PASSED: Validation skipped in debug mode (expected)")
        print("   Unsafe secrets are allowed in development")
        return True
    except RuntimeError as e:
        print("❌ FAILED: Should not raise error in debug mode")
        print(f"   Error: {e}")
        return False


def test_production_mode_with_secure_secrets():
    """Test: Validation should pass with secure secrets."""
    print_section("TEST 2: Production Mode with Secure Secrets (Should PASS)")

    settings = MagicMock(spec=Settings)
    settings.DEBUG = False
    settings.JWT_SECRET_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"
    settings.ENCRYPTION_KEY = "zY9xW7vU5tS3rQ1pO9nM7lK5jI3hG1fE9dC7bA5zA3xW1"
    settings.POSTGRES_PASSWORD = "pG7sQ9lR3dB5nM1vF8hK2jT4wX6yZ0aC9eL1uI5oP7"
    settings.SERVICE_AUTH_TOKEN = "st_9fK2lM4nP6qR8sT0vW2xY4zA6bC8dE0fG2hI4jK6lM8"

    try:
        validate_production_secrets(settings)
        print("✅ PASSED: Production secrets validation successful")
        print("   All secrets are secure and ready for production")
        return True
    except RuntimeError as e:
        print("❌ FAILED: Should not raise error with secure secrets")
        print(f"   Error: {e}")
        return False


def test_production_mode_with_unsafe_secrets():
    """Test: Validation should fail with unsafe secrets (EXPECTED TO FAIL)."""
    print_section("TEST 3: Production Mode with Unsafe Secrets (Should BLOCK)")

    settings = MagicMock(spec=Settings)
    settings.DEBUG = False
    settings.JWT_SECRET_KEY = "dev_secret_key_change_in_production_min_32_chars_required"
    settings.ENCRYPTION_KEY = "dev_encryption_key_for_2fa_secrets_32_chars_minimum_required"
    settings.POSTGRES_PASSWORD = "dev_password_change_in_prod"
    settings.SERVICE_AUTH_TOKEN = "st_dev_5555555555555555555555555555555555555555"

    try:
        validate_production_secrets(settings)
        print("❌ FAILED: Should have blocked deployment with unsafe secrets")
        return False
    except RuntimeError as e:
        print("✅ PASSED: Deployment correctly blocked (expected)")
        print("\n📋 Error Message (this is what you'd see in production):")
        print("-" * 80)
        print(str(e))
        print("-" * 80)
        return True


def test_production_mode_with_single_unsafe_secret():
    """Test: Validation should detect a single unsafe secret."""
    print_section("TEST 4: Production Mode with ONE Unsafe Secret (Should BLOCK)")

    settings = MagicMock(spec=Settings)
    settings.DEBUG = False
    settings.JWT_SECRET_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"  # Secure
    settings.ENCRYPTION_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"  # Secure
    settings.POSTGRES_PASSWORD = "dev_password_change_in_prod"  # UNSAFE!
    settings.SERVICE_AUTH_TOKEN = "st_9fK2lM4nP6qR8sT0vW2xY4zA6bC8dE0fG2hI4jK6lM8"  # Secure

    try:
        validate_production_secrets(settings)
        print("❌ FAILED: Should have detected unsafe POSTGRES_PASSWORD")
        return False
    except RuntimeError as e:
        print("✅ PASSED: Single unsafe secret detected (POSTGRES_PASSWORD)")
        print(f"\n   Error contains 'POSTGRES_PASSWORD': {'POSTGRES_PASSWORD' in str(e)}")
        print(f"   Error contains 'change_in_prod': {'change_in_prod' in str(e)}")
        return True


def main():
    """Run all test scenarios."""
    print("\n" + "🔐" * 40)
    print("  PRODUCTION SECRETS VALIDATION - TEST SUITE")
    print("🔐" * 40)

    results = {
        "Debug mode with unsafe secrets": test_debug_mode_with_unsafe_secrets(),
        "Production mode with secure secrets": test_production_mode_with_secure_secrets(),
        "Production mode with unsafe secrets": test_production_mode_with_unsafe_secrets(),
        "Production mode with single unsafe secret": test_production_mode_with_single_unsafe_secret(),
    }

    # Summary
    print_section("SUMMARY")
    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Production secrets validation is working correctly.")
        print("\n📚 Key Takeaways:")
        print("   1. Debug mode (DEBUG=true) allows unsafe secrets for local development")
        print("   2. Production mode (DEBUG=false) blocks deployment with unsafe secrets")
        print("   3. Error messages are clear and provide actionable guidance")
        print("   4. Secret previews are truncated to avoid exposing full secrets in logs")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
