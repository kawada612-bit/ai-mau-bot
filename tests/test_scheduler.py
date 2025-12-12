import pytest
import json
from unittest.mock import MagicMock
from src.workers import scheduler

def test_extract_details_with_groq_success(mock_env_vars, mock_groq):
    """Test AI extraction of event details"""
    # Setup
    scheduler.groq_client = mock_groq
    
    # Mock Groq response
    extracted_data = {
        "start_at": "2025-12-25T18:00:00+09:00",
        "end_at": None,
        "place": "Tokyo Dome",
        "ticket_url": "https://ticket.com",
        "price": "10000yen",
        "bonus": "Free Drink"
    }
    
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=json.dumps(extracted_data)))
    ]
    mock_groq.chat.completions.create.return_value = mock_completion
    
    # Execute
    result = scheduler.extract_details_with_groq("Live Title", "2025-12-25", "Some note")
    
    # Assert
    assert result["place"] == "Tokyo Dome"
    assert result["bonus"] == "Free Drink"
    assert result["price"] == "10000yen"

def test_extract_details_with_groq_no_client(mock_env_vars):
    """Test extraction returns empty if Groq client is None"""
    scheduler.groq_client = None
    result = scheduler.extract_details_with_groq("Title", "Date", "Note")
    assert result == {}

def test_extract_details_with_groq_exception(mock_env_vars, mock_groq):
    """Test handling of exceptions from Groq"""
    scheduler.groq_client = mock_groq
    mock_groq.chat.completions.create.side_effect = Exception("API Error")
    
    result = scheduler.extract_details_with_groq("Title", "Date", "Note")
    assert result == {}
