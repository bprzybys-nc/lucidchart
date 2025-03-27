#!/usr/bin/env python3
"""Tests for the extract_responses module."""

import os
import sqlite3
import tempfile
from pathlib import Path
import pytest
from scripts.extract_responses import (
    extract_responses,
    format_responses,
    save_responses,
    process_conversation
)

@pytest.fixture
def temp_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
        
    # Create test database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create test table
    c.execute('''CREATE TABLE cursorDiskKV
                 (key TEXT PRIMARY KEY, value TEXT)''')
    
    # Insert test data
    test_data = {
        'chat:1': '{"messages":[{"role":"user","content":"Test message 1"},{"role":"assistant","content":"Test response 1"}]}',
        'chat:2': '{"messages":[{"role":"user","content":"Test message 2"},{"role":"assistant","content":"Test response 2"}]}'
    }
    
    for key, value in test_data.items():
        c.execute("INSERT INTO cursorDiskKV VALUES (?, ?)", (key, value))
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)

def test_extract_responses(temp_db):
    """Test basic response extraction."""
    responses = extract_responses(temp_db)
    assert len(responses) == 2
    assert all(isinstance(r, dict) for r in responses)
    assert all('messages' in r for r in responses)

def test_format_responses():
    """Test response formatting."""
    test_responses = [
        {
            'messages': [
                {'role': 'user', 'content': 'Test message'},
                {'role': 'assistant', 'content': 'Test response'}
            ]
        }
    ]
    
    formatted = format_responses(test_responses)
    assert isinstance(formatted, str)
    assert 'Test message' in formatted
    assert 'Test response' in formatted

def test_save_responses(tmp_path):
    """Test saving responses to file."""
    output_file = tmp_path / "test_output.md"
    test_content = "Test content"
    
    save_responses(test_content, str(output_file))
    assert output_file.exists()
    assert output_file.read_text() == test_content

def test_process_conversation():
    """Test conversation processing."""
    test_conversation = {
        'messages': [
            {'role': 'user', 'content': 'Test message'},
            {'role': 'assistant', 'content': 'Test response'}
        ]
    }
    
    result = process_conversation(test_conversation)
    assert isinstance(result, str)
    assert 'Test message' in result
    assert 'Test response' in result

def test_extract_responses_with_limit(temp_db):
    """Test extracting responses with a sample limit."""
    responses = extract_responses(temp_db, sample_limit=1)
    assert len(responses) == 1

def test_extract_responses_empty_db():
    """Test extraction from empty database."""
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        conn = sqlite3.connect(f.name)
        c = conn.cursor()
        c.execute('''CREATE TABLE cursorDiskKV
                     (key TEXT PRIMARY KEY, value TEXT)''')
        conn.commit()
        conn.close()
        
        responses = extract_responses(f.name)
        assert len(responses) == 0

def test_extract_responses_invalid_json():
    """Test handling of invalid JSON in database."""
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        conn = sqlite3.connect(f.name)
        c = conn.cursor()
        c.execute('''CREATE TABLE cursorDiskKV
                     (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute("INSERT INTO cursorDiskKV VALUES (?, ?)",
                 ('chat:1', 'invalid json'))
        conn.commit()
        conn.close()
        
        responses = extract_responses(f.name)
        assert len(responses) == 0

def test_extract_responses_no_table():
    """Test handling of missing table."""
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        conn = sqlite3.connect(f.name)
        conn.commit()
        conn.close()
        
        try:
            extract_responses(f.name)
            pytest.fail("Expected sqlite3.OperationalError to be raised")
        except sqlite3.OperationalError:
            # This is the expected behavior
            pass

if __name__ == '__main__':
    pytest.main([__file__]) 