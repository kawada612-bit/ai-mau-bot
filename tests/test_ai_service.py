import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from src.domain.ai_service import AIBrain
from src.core import config


class MockResponse:
    """Helper class to mock Gemini responses"""
    def __init__(self, text: str):
        self.text = text


# ==============================================================================
# AIBrain Initialization Tests
# ==============================================================================

def test_ai_brain_init_with_key(mock_env_vars):
    """Test AIBrain initializes correctly with API key"""
    with patch('google.generativeai.configure') as mock_configure:
        with patch('google.generativeai.GenerativeModel') as mock_model:
            ai_brain = AIBrain()
            mock_configure.assert_called_once_with(api_key="fake_gemini_key")


def test_ai_brain_init_without_key(monkeypatch):
    """Test AIBrain handles missing API key gracefully"""
    monkeypatch.setattr(config, "GEMINI_API_KEY", None)
    
    ai_brain = AIBrain()
    
    assert ai_brain.model_priority is None
    assert ai_brain.model_lite is None
    assert ai_brain.model_backup_1 is None


# ==============================================================================
# generate_sql Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_generate_sql_success(mock_env_vars):
    """Test successful SQL generation using Priority Model"""
    ai_brain = AIBrain()
    
    # Mock Priority Model
    mock_model = MagicMock()
    mock_response = MockResponse("SELECT * FROM schedules WHERE datetime(start_at) > datetime('2026-01-14T10:00:00')")
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    ai_brain.model_priority = mock_model
    
    # Execute
    schema_info = "Table: schedules (id, title, start_at, place, price_details)"
    result = await ai_brain.generate_sql("今後のライブを教えて", schema_info)
    
    # Assert
    assert "SELECT" in result
    assert "schedules" in result
    mock_model.generate_content_async.assert_called_once()


@pytest.mark.asyncio
async def test_generate_sql_fallback_to_lite(mock_env_vars):
    """Test SQL generation falls back to Lite model when Priority fails"""
    ai_brain = AIBrain()
    
    # Mock Priority Model to fail
    mock_priority = MagicMock()
    mock_priority.generate_content_async = AsyncMock(side_effect=Exception("429 Quota Exceeded"))
    ai_brain.model_priority = mock_priority
    
    # Mock Lite Model to succeed
    mock_lite = MagicMock()
    mock_response = MockResponse("SELECT * FROM schedules LIMIT 10")
    mock_lite.generate_content_async = AsyncMock(return_value=mock_response)
    ai_brain.model_lite = mock_lite
    
    # Execute
    result = await ai_brain.generate_sql("list schedules", "schema")
    
    # Assert
    assert result == "SELECT * FROM schedules LIMIT 10"
    mock_lite.generate_content_async.assert_called_once()


@pytest.mark.asyncio
async def test_generate_sql_all_models_fail(mock_env_vars):
    """Test SQL generation returns fallback when all models fail"""
    ai_brain = AIBrain()
    
    # Mock both models to fail
    mock_priority = MagicMock()
    mock_priority.generate_content_async = AsyncMock(side_effect=Exception("Priority Error"))
    ai_brain.model_priority = mock_priority
    
    mock_lite = MagicMock()
    mock_lite.generate_content_async = AsyncMock(side_effect=Exception("Lite Error"))
    ai_brain.model_lite = mock_lite
    
    # Execute
    result = await ai_brain.generate_sql("test", "schema")
    
    # Assert - should return safe fallback
    assert result == "SELECT * FROM schedules LIMIT 0;"


@pytest.mark.asyncio
async def test_generate_sql_no_model(monkeypatch):
    """Test SQL generation without configured models"""
    monkeypatch.setattr(config, "GEMINI_API_KEY", None)
    ai_brain = AIBrain()
    
    result = await ai_brain.generate_sql("test", "schema")
    
    assert result == "SELECT * FROM schedules LIMIT 0;"


# ==============================================================================
# generate_response Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_generate_response_success(mock_env_vars, monkeypatch):
    """Test response generation with Priority Model"""
    monkeypatch.setattr(config, "MAU_ENV", "development")
    ai_brain = AIBrain()
    
    mock_model = MagicMock()
    mock_response = MockResponse("今度のライブ楽しみにしててね！✨\n===SUGGESTIONS===\n元気だよ！\nちょっと疲れてる\nまうちゃんは？")
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    ai_brain.model_priority = mock_model
    
    # Execute - Use message that doesn't trigger reflex (no keywords, long enough)
    response_text, mode, suggestions = await ai_brain.generate_response("テストユーザー", "テストユーザー: 今度のライブの情報を教えてください")
    
    # Assert
    assert "ライブ" in response_text
    assert "(Dev Check)" in response_text
    assert mode == "GENIUS"
    assert len(suggestions) == 3
    assert "元気だよ！" in suggestions


@pytest.mark.asyncio
async def test_generate_response_fallback_to_lite(mock_env_vars, monkeypatch):
    """Test response falls back to Lite model when Priority fails"""
    monkeypatch.setattr(config, "MAU_ENV", "production")
    ai_brain = AIBrain()
    
    # Priority fails
    mock_priority = MagicMock()
    mock_priority.generate_content_async = AsyncMock(side_effect=Exception("Quota Error"))
    ai_brain.model_priority = mock_priority
    
    # Lite succeeds
    mock_lite = MagicMock()
    mock_response = MockResponse("こんにちは！✨")
    mock_lite.generate_content_async = AsyncMock(return_value=mock_response)
    ai_brain.model_lite = mock_lite
    
    # Execute
    response_text, mode, suggestions = await ai_brain.generate_response("User", "User: hi")
    
    # Assert
    assert "こんにちは" in response_text
    assert "(※Liteモード🔋)" in response_text
    assert mode == "MAIN"


@pytest.mark.asyncio
async def test_generate_response_fallback_to_gemma(mock_env_vars, monkeypatch):
    """Test response falls back to Gemma 3 when Priority and Lite fail"""
    monkeypatch.setattr(config, "MAU_ENV", "production")
    ai_brain = AIBrain()
    
    # Priority fails
    mock_priority = MagicMock()
    mock_priority.generate_content_async = AsyncMock(side_effect=Exception("Error 1"))
    ai_brain.model_priority = mock_priority
    
    # Lite fails
    mock_lite = MagicMock()
    mock_lite.generate_content_async = AsyncMock(side_effect=Exception("Error 2"))
    ai_brain.model_lite = mock_lite
    
    # Gemma succeeds
    mock_gemma = MagicMock()
    mock_response = MockResponse("ありがとう！")
    mock_gemma.generate_content_async = AsyncMock(return_value=mock_response)
    ai_brain.model_backup_1 = mock_gemma
    
    # Execute
    response_text, mode, suggestions = await ai_brain.generate_response("User", "User: thanks")
    
    # Assert
    assert "ありがとう" in response_text
    assert "(※ポンコツモード🤪)" in response_text
    assert mode == "PONKOTSU"


@pytest.mark.asyncio
async def test_generate_response_all_models_fail(mock_env_vars, monkeypatch):
    """Test error message when all models fail"""
    monkeypatch.setattr(config, "MAU_ENV", "production")
    ai_brain = AIBrain()
    
    # All models fail
    for model_name in ['model_priority', 'model_lite', 'model_backup_1']:
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(side_effect=Exception("Fatal Error"))
        setattr(ai_brain, model_name, mock_model)
    
    # Execute
    response_text, mode, suggestions = await ai_brain.generate_response("User", "User: hello")
    
    # Assert - should return friendly error
    assert "パンク" in response_text or "ごめんね" in response_text


# ==============================================================================
# Reflex Layer Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_reflex_response_ohayo(mock_env_vars):
    """Test reflex response for 'おはよう'"""
    ai_brain = AIBrain()
    
    # Execute with short greeting
    response_text, mode, suggestions = await ai_brain.generate_response("User", "User: おはよう")
    
    # Assert
    assert mode == "REFLEX"
    assert "(⚡0.01s)" in response_text
    assert any(word in response_text for word in ["おはよー", "おはよ"])


@pytest.mark.asyncio
async def test_reflex_response_oyasumi(mock_env_vars):
    """Test reflex response for 'おやすみ'"""
    ai_brain = AIBrain()
    
    response_text, mode, suggestions = await ai_brain.generate_response("User", "User: おやすみ")
    
    assert mode == "REFLEX"
    assert "おやすみ" in response_text


@pytest.mark.asyncio
async def test_reflex_response_suki(mock_env_vars):
    """Test reflex response for '好き'"""
    ai_brain = AIBrain()
    
    response_text, mode, suggestions = await ai_brain.generate_response("User", "User: 好き")
    
    assert mode == "REFLEX"
    # Reflex can return various responses for "好き" keyword
    assert "(⚡0.01s)" in response_text


@pytest.mark.asyncio
async def test_reflex_not_triggered_for_long_message(mock_env_vars):
    """Test reflex is NOT triggered for long messages containing keywords"""
    ai_brain = AIBrain()
    
    # Mock Priority Model
    mock_model = MagicMock()
    mock_response = MockResponse("AIからの応答です")
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    ai_brain.model_priority = mock_model
    
    # Long message containing "おはよう"
    response_text, mode, suggestions = await ai_brain.generate_response(
        "User", 
        "User: おはようございます。今日のライブ情報を教えてください。"
    )
    
    # Assert - should NOT be reflex because message is too long
    assert mode != "REFLEX"


# ==============================================================================
# Suggestions Parsing Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_suggestions_parsing(mock_env_vars):
    """Test that suggestions are correctly parsed from response"""
    ai_brain = AIBrain()
    
    mock_model = MagicMock()
    mock_response = MockResponse("""今週のスケジュールを確認するね！✨

===SUGGESTIONS===
今日の予定は？
ライブ情報教えて
疲れた〜
余分な4つ目""")
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    ai_brain.model_priority = mock_model
    
    # Use a long message that won't trigger reflex
    response_text, mode, suggestions = await ai_brain.generate_response("User", "User: 今週のスケジュールを確認したいのですが")
    
    # Assert - suggestions should be parsed and limited to 3
    assert "===SUGGESTIONS===" not in response_text
    assert len(suggestions) == 3
    assert "今日の予定は？" in suggestions
    assert "ライブ情報教えて" in suggestions
    assert "疲れた〜" in suggestions


# ==============================================================================
# Language / Timezone Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_global_user_english_prompt(mock_env_vars):
    """Test that global users get English prompt instructions"""
    ai_brain = AIBrain()
    
    mock_model = MagicMock()
    mock_response = MockResponse("Hello! How are you?")
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    ai_brain.model_priority = mock_model
    
    # Execute with non-Japan timezone
    response_text, mode, suggestions = await ai_brain.generate_response(
        "User", 
        "User: Hello!",
        timezone="America/New_York"
    )
    
    # Assert model was called
    mock_model.generate_content_async.assert_called_once()
    
    # Check the prompt contains English instructions
    call_args = mock_model.generate_content_async.call_args
    prompt = call_args[0][0]
    assert "ENGLISH" in prompt or "English" in prompt


@pytest.mark.asyncio
async def test_japan_user_japanese_prompt(mock_env_vars):
    """Test that Japan users get Japanese prompt instructions"""
    ai_brain = AIBrain()
    
    mock_model = MagicMock()
    mock_response = MockResponse("スケジュール確認するね！")
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    ai_brain.model_priority = mock_model
    
    # Execute with Japan timezone - Use long message to avoid reflex
    response_text, mode, suggestions = await ai_brain.generate_response(
        "User", 
        "User: 今週の予定を確認したいのですが",
        timezone="Asia/Tokyo"
    )
    
    # Check the prompt contains Japanese instructions
    call_args = mock_model.generate_content_async.call_args
    prompt = call_args[0][0]
    assert "Japan" in prompt or "Japanese" in prompt


# ==============================================================================
# Live API Smoke Tests (全モデル疎通確認)
# Run with: pytest tests/test_ai_service.py -m live -v
# ==============================================================================

@pytest.mark.live
@pytest.mark.asyncio
async def test_live_gemini_3_flash():
    """Live API test for Gemini 3 Flash Preview (Latest Model)"""
    import google.generativeai as genai
    from src.core import config
    
    if not config.GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not set")
    
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name='gemini-3-flash-preview')
    
    response = await model.generate_content_async("Say 'OK' if you can hear me.")
    
    assert response.text is not None
    assert len(response.text) > 0
    print(f"✅ Gemini 3 Flash Preview: {response.text[:50]}...")


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_gemini_2_5_flash():
    """Live API test for Gemini 2.5 Flash (High Performance)"""
    import google.generativeai as genai
    from src.core import config
    
    if not config.GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not set")
    
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name='gemini-2.5-flash')
    
    response = await model.generate_content_async("Say 'OK' if you can hear me.")
    
    assert response.text is not None
    assert len(response.text) > 0
    print(f"✅ Gemini 2.5 Flash: {response.text[:50]}...")


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_gemini_2_5_lite():
    """Live API test for Gemini 2.5 Flash-Lite (Free Tier)"""
    import google.generativeai as genai
    from src.core import config
    
    if not config.GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not set")
    
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name='gemini-2.5-flash-lite')
    
    response = await model.generate_content_async("Say 'OK' if you can hear me.")
    
    assert response.text is not None
    assert len(response.text) > 0
    print(f"✅ Gemini 2.5 Flash-Lite: {response.text[:50]}...")


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_gemini_2_0_flash_exp():
    """Live API test for Gemini 2.0 Flash Exp (Search Support)"""
    import google.generativeai as genai
    from src.core import config
    
    if not config.GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not set")
    
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name='gemini-2.0-flash-exp')
    
    response = await model.generate_content_async("Say 'OK' if you can hear me.")
    
    assert response.text is not None
    assert len(response.text) > 0
    print(f"✅ Gemini 2.0 Flash Exp: {response.text[:50]}...")


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_gemma_3():
    """Live API test for Gemma 3 27B (Backup Model)"""
    import google.generativeai as genai
    from src.core import config
    
    if not config.GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not set")
    
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name='gemma-3-27b-it')
    
    response = await model.generate_content_async("Say 'OK' if you can hear me.")
    
    assert response.text is not None
    assert len(response.text) > 0
    print(f"✅ Gemma 3 27B: {response.text[:50]}...")

