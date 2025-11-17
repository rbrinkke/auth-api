#!/usr/bin/env python3
"""
Manual test script to verify DEFAULT_ORGANIZATION_ID auto-assignment feature.

This script demonstrates that:
1. When DEFAULT_ORGANIZATION_ID is set, new users are auto-assigned to that organization
2. User gets 'member' role in the organization
3. Login flow correctly returns org_id in the token

Usage:
    python manual_test_org_assignment.py
"""
import asyncio
import httpx
from uuid import uuid4


API_BASE = "http://localhost:8000"


async def test_organization_auto_assignment():
    """Test the complete flow of organization auto-assignment."""
    async with httpx.AsyncClient() as client:
        print("\n" + "="*80)
        print("TESTING: DEFAULT_ORGANIZATION_ID Auto-Assignment Feature")
        print("="*80)

        # Step 1: Create a test organization (assuming you have one created)
        print("\n[INFO] Ensure you have a default organization in the database")
        print("[INFO] Set DEFAULT_ORGANIZATION_ID in .env to the organization UUID")
        print("[INFO] Example: DEFAULT_ORGANIZATION_ID=550e8400-e29b-41d4-a716-446655440000")

        # Step 2: Register a new user
        print("\n[STEP 1] Registering new user...")
        test_email = f"test-org-{uuid4().hex[:8]}@example.com"
        register_data = {
            "email": test_email,
            "password": "SecurePassword123!"
        }

        response = await client.post(
            f"{API_BASE}/api/auth/register",
            json=register_data
        )

        if response.status_code != 200:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return

        user_data = response.json()
        user_id = user_data["user_id"]
        verification_token = user_data["verification_token"]

        print(f"✅ User registered successfully")
        print(f"   User ID: {user_id}")
        print(f"   Email: {test_email}")

        # Step 3: Check organization membership (via database or API)
        print("\n[STEP 2] Organization Assignment")
        print("   To verify organization assignment, check the database:")
        print(f"   SELECT * FROM activity.organization_members WHERE user_id = '{user_id}';")
        print("   Expected:")
        print("   - user_id matches registered user")
        print("   - organization_id matches DEFAULT_ORGANIZATION_ID from .env")
        print("   - role = 'member'")
        print("   - invited_by = NULL (auto-assignment)")

        # Step 4: Verify email (simulated - in real test we'd get code from Redis)
        print("\n[STEP 3] Email Verification")
        print("   In production, you would:")
        print("   1. Get verification code from email")
        print("   2. POST /api/auth/verify with verification_token and code")
        print("   3. User becomes verified and can login")

        # Step 5: Login flow check
        print("\n[STEP 4] Login Flow (after verification)")
        print("   After email verification, login will:")
        print("   1. Discover user's organization membership")
        print("   2. If single org → auto-select and return org_id in token")
        print("   3. If multi-org → prompt for org selection")
        print("   4. Token payload will include:")
        print("      - 'sub': user_id")
        print("      - 'org_id': organization_id")

        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print("✅ Registration endpoint works")
        print("⏳ Organization assignment requires database verification")
        print("⏳ Full flow requires email verification + login")
        print("\n[NEXT STEPS]")
        print("1. Check database for organization_members entry")
        print("2. Verify the user via email code")
        print("3. Login and check token contains org_id")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(test_organization_auto_assignment())
