import pytest
import os
import sys
from unittest.mock import MagicMock

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core import config

@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake_gemini_key")
    monkeypatch.setattr(config, "GROQ_API_KEY", "fake_groq_key")
    monkeypatch.setattr(config, "SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setattr(config, "SUPABASE_KEY", "fake_supabase_key")
    monkeypatch.setattr(config, "MAU_ENV", "test")

@pytest.fixture
def mock_supabase():
    mock_client = MagicMock()
    return mock_client

@pytest.fixture
def mock_groq():
    mock_client = MagicMock()
    return mock_client

@pytest.fixture
def mock_gemini_model():
    mock_model = MagicMock()
    return mock_model
