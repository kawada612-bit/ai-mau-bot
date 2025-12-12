import pytest
import sqlite3
import pandas as pd
from unittest.mock import MagicMock
from src.domain.analytics_service import AnalyticsService

def test_get_schema_info(mock_env_vars):
    """Test schema info retrieval"""
    service = AnalyticsService()
    schema = service.get_schema_info()
    assert "Table: schedules" in schema
    assert "bonus (text)" in schema

def test_execute_query_with_mock_data(mock_env_vars, mock_supabase):
    """Test SQL execution with mock Supabase data"""
    # Setup
    service = AnalyticsService()
    service.supabase = mock_supabase
    
    # Mock data from Supabase
    mock_data = [
        {"title": "Live A", "start_at": "2025-10-10T19:00:00", "description": "Desc A", "place": "Venue A"},
        {"title": "Live B", "start_at": "2025-10-11T19:00:00", "description": "Desc B", "place": "Venue B"}
    ]
    mock_response = MagicMock()
    mock_response.data = mock_data
    mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response

    # Execute
    query = "SELECT title, place FROM schedules"
    result_md = service.execute_query(query)

    # Assert
    assert "Live A" in result_md
    assert "Venue B" in result_md
    # Check if header columns exist (format varies by tabulate version/style)
    assert "title" in result_md
    assert "place" in result_md

def test_execute_query_security(mock_env_vars):
    """Test SQL security (block non-SELECT)"""
    service = AnalyticsService()
    # Mock empty db
    service._get_fresh_connection = MagicMock(return_value=sqlite3.connect(':memory:'))
    
    result = service.execute_query("DELETE FROM schedules")
    assert "エラー: 安全のため、SELECTクエリ以外は実行できません。" in result
