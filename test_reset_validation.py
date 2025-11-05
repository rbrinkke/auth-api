#!/usr/bin/env python3
"""
Test script to verify password reset enforces professional validation.
"""

import asyncio
import sys
import httpx

API_URL = "http://localhost:8000"

async def test_reset_with_weak_password():
    """Test that password reset also rejects weak passwords."""
    print("=" * 60)
    print("TEST: Password Reset Validation")
    print("=" * 60)

    # Test 1: Weak password (should be REJECTED by zxcvbn)
    print("\n1. Testing weak password 'password123' (should be REJECTED):")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/auth/reset-password",
                json={
                    "token": "fake_token_for_validation_test",
                    "new_password": "password123"
                }
            )

            if response.status_code == 422:
                # Validation error is expected
                error_detail = response.json().get("detail", [{}])[0].get("msg", "")
                print(f"  ✅ REJECTED (as expected)")
                print(f"  📝 Error: {error_detail[:100]}...")
                return True
            else:
                print(f"  ❌ ACCEPTED (unexpected!)")
                print(f"  Status: {response.status_code}")
                return False
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return False


async def test_reset_with_strong_password():
    """Test that password reset accepts strong passwords."""
    print("\n2. Testing strong password 'MyD3centP@ssw0rd2024' (should be ACCEPTED by validation):")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/auth/reset-password",
                json={
                    "token": "fake_token_for_validation_test",
                    "new_password": "MyD3centP@ssw0rd2024"
                }
            )

            # Will fail at token validation (expected), but password validation passed
            if response.status_code == 422:
                error_detail = response.json().get("detail", [{}])[0].get("msg", "")
                if "weak password" in error_detail.lower() or "data breaches" in error_detail.lower():
                    print(f"  ❌ REJECTED (validation failed)")
                    print(f"  📝 Error: {error_detail[:100]}...")
                    return False
                else:
                    print(f"  ✅ ACCEPTED by validation (failed at token validation as expected)")
                    print(f"  📝 Token error: {error_detail[:100]}...")
                    return True
            else:
                print(f"  ✅ ACCEPTED by validation")
                return True
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return False


async def main():
    """Run all password reset validation tests."""
    print("\n" + "=" * 60)
    print("PASSWORD RESET VALIDATION TEST")
    print("=" * 60)

    # Check if API is healthy
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/health")
            if response.status_code == 200:
                print("✅ API is healthy and ready for testing\n")
            else:
                print("❌ API is not responding correctly\n")
                return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}\n")
        return

    # Run tests
    result1 = await test_reset_with_weak_password()
    result2 = await test_reset_with_strong_password()

    print("\n" + "=" * 60)
    if result1 and result2:
        print("✅ ALL TESTS PASSED - Password reset enforces professional validation")
    else:
        print("❌ TESTS FAILED - Password reset validation needs fixing")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
