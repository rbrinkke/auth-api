"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import fixtures based on test type
# Unit tests use mocks from unit/conftest.py
# Integration tests use real DB/Redis from integration/conftest.py
# E2E tests use HTTP client from e2e/conftest.py

# Import shared fixtures from database module
from tests.fixtures.database import *
