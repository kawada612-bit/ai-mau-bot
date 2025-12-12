import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from src.domain.ai_service import AIBrain
from src.core import config

@pytest.mark.asyncio
async def test_generate_sql_success(mock_env_vars, mock_groq):
    """Test successful SQL generation using Groq"""
    # Setup
    ai_brain = AIBrain()
    
    # Mock Groq response
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="SELECT * FROM schedules"))]
    mock_groq.chat.completions.create.return_value = mock_completion
    
    # Inject mock
    ai_brain.groq_client = mock_groq
    
    # Execute
    schema_info = "Table: schedules..."
    result = await ai_brain.generate_sql("list schedules", schema_info)
    
    # Assert
    assert result == "SELECT * FROM schedules"
    mock_groq.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_generate_sql_fallback(mock_env_vars):
    """Test SQL generation fallback when Groq fails"""
    # Setup
    ai_brain = AIBrain()
    
    # Mock Groq to fail
    ai_brain.groq_client = MagicMock()
    ai_brain.groq_client.chat.completions.create.side_effect = Exception("Groq Error")
    
    # Mock Gemini (Priority Model)
    mock_model = MagicMock()
    mock_response = AsyncMock()
    mock_response.text = "SELECT * FROM schedules WHERE 1=1"
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    
    ai_brain.model_priority = mock_model
    
    # Execute
    result = await ai_brain.generate_sql("list schedules", "schema")
    
    # Assert
    assert result == "SELECT * FROM schedules WHERE 1=1"
    ai_brain.model_priority.generate_content_async.assert_called_once()

@pytest.mark.asyncio
async def test_generate_response_success(mock_env_vars, monkeypatch):
    """Test response generation with Gemini"""
    # Setup
    monkeypatch.setattr(config, "MAU_ENV", "development")
    ai_brain = AIBrain()
    
    mock_model = MagicMock()
    mock_response = AsyncMock()
    mock_response.text = "Hello user!"
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    
    ai_brain.model_priority = mock_model
    
    # Execute
    result = await ai_brain.generate_response("User", "History")
    
    # Assert
    assert "Hello user!" in result
    assert "(Dev Check)" in result
