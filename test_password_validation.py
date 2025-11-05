#!/usr/bin/env python3
"""
Test script for professional password validation.
Tests zxcvbn strength scoring and pwnedpasswords breach checking.
"""

import asyncio
import sys
import httpx

API_URL = "http://localhost:8000"

async def test_weak_password():
    """Test that weak passwords are rejected."""
    print("=" * 60)
    print("TEST 1: Weak Password (should be REJECTED)")
    print("=" * 60)

    weak_passwords = [
        ("password", "Very common password"),
        ("123456", "Numeric sequence"),
        ("abc123", "Simple alphanumeric"),
        ("qwerty", "Keyboard pattern"),
    ]

    for password, description in weak_passwords:
        print(f"\nTesting: {description} - '{password}'")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_URL}/auth/register",
                    json={
                        "email": f"test_{password.replace(' ', '_')}@example.com",
                        "password": password
                    }
                )

                if response.status_code == 422:
                    # Validation error is expected
                    error_detail = response.json().get("detail", [{}])[0].get("msg", "")
                    print(f"  ✅ REJECTED (as expected)")
                    print(f"  📝 Error: {error_detail[:100]}...")
                else:
                    print(f"  ❌ ACCEPTED (unexpected!)")
                    print(f"  Status: {response.status_code}")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")


async def test_strong_password():
    """Test that strong passwords are accepted."""
    print("\n" + "=" * 60)
    print("TEST 2: Strong Password (should be ACCEPTED)")
    print("=" * 60)

    strong_passwords = [
        ("CorrectHorseBatteryStaple!42", "Long passphrase with symbols"),
        ("My$D3centP@ssw0rd2024!", "Complex password with year"),
        ("Tr0ub4dor&3", "zxcvbn example password"),
        ("P@ssw0rd!Mn2QjZ8kL9", "Random complex password"),
    ]

    for password, description in strong_passwords:
        print(f"\nTesting: {description}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_URL}/auth/register",
                    json={
                        "email": f"strong_{password[:8].replace('$', 's').replace('@', 'a')}@example.com",
                        "password": password
                    }
                )

                if response.status_code == 201:
                    print(f"  ✅ ACCEPTED (as expected)")
                    # Extract user ID for cleanup
                    user_email = response.json().get("email", "")
                    print(f"  📧 User: {user_email}")
                elif response.status_code == 422:
                    print(f"  ⚠️  REJECTED (validation error)")
                    error_detail = response.json().get("detail", [{}])[0].get("msg", "")
                    print(f"  📝 Error: {error_detail[:100]}...")
                else:
                    print(f"  ❓ Status: {response.status_code}")
                    print(f"  📝 Response: {response.text[:200]}")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")


async def test_breached_password():
    """Test that passwords known to be breached are rejected."""
    print("\n" + "=" * 60)
    print("TEST 3: Breached Password (should be REJECTED)")
    print("=" * 60)

    # These are passwords known to be in data breaches
    breached_passwords = [
        "password123",
        "123456789",
        "password1",
        "qwerty123",
    ]

    for password in breached_passwords:
        print(f"\nTesting breached password: '{password}'")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_URL}/auth/register",
                    json={
                        "email": f"breached_{password[:5]}@example.com",
                        "password": password
                    }
                )

                if response.status_code == 422:
                    error_detail = response.json().get("detail", [{}])[0].get("msg", "")
                    if "data breaches" in error_detail.lower():
                        print(f"  ✅ REJECTED for breach (as expected)")
                        print(f"  📝 Error: {error_detail[:100]}...")
                    else:
                        print(f"  ⚠️  REJECTED (zxcvbn validation)")
                        print(f"  📝 Error: {error_detail[:100]}...")
                elif response.status_code == 201:
                    print(f"  ⚠️  ACCEPTED (may not be in HIBP or check failed)")
                else:
                    print(f"  ❓ Status: {response.status_code}")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")


async def main():
    """Run all password validation tests."""
    print("\n" + "=" * 60)
    print("PROFESSIONAL PASSWORD VALIDATION TEST SUITE")
    print("Using zxcvbn + pwnedpasswords")
    print("=" * 60)

    # Check if API is healthy
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/health")
            if response.status_code == 200:
                print("\n✅ API is healthy and ready for testing\n")
            else:
                print("\n❌ API is not responding correctly\n")
                return
    except Exception as e:
        print(f"\n❌ Cannot connect to API: {e}\n")
        return

    # Run tests
    await test_weak_password()
    await test_strong_password()
    await test_breached_password()

    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
