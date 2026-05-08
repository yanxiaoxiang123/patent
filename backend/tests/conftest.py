"""Pytest configuration for backend tests"""
import os
import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# Set up test DATABASE_URL before any imports
os.environ["DATABASE_URL"] = "mysql+aiomysql://root:Root%402026%21@localhost:3306/iprs"

# Load dotenv
from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

import pytest

@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy"""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
