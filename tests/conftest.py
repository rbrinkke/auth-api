"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import fixtures
from tests.fixtures.database import *
