#!/usr/bin/env python3
import sqlite3
import json
import sys
from datetime import datetime, timedelta

def create_enhanced_test_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cursorDiskKV (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Create test data
    base_time = datetime.now().timestamp()
    test_data = []
    
    # Regular conversation format
    for i in range(10):
        # User message
        test_data.append((
            f'prompt_{i}',
            json.dumps({
                'prompt': f'Test user message {i} with some special chars: $&*()!',
                'timestamp': base_time + i * 60
            })
        ))
        
        # Assistant response
        test_data.append((
            f'response_{i}',
            json.dumps({
                'response': f'Test assistant response {i} with code:\n```python\ndef test():\n    return "hello"\n```',
                'model': f'test-model-{i % 3}',
                'timestamp': base_time + i * 60 + 30
            })
        ))
    
    # Chat format (newer format)
    for i in range(5):
        chat_data = {
            "messages": [
                {
                    "role": "user", 
                    "content": f"Question {i}: How do I implement a binary search tree in Python?"
                },
                {
                    "role": "assistant", 
                    "content": f"Answer {i}: Here's a basic implementation of a binary search tree in Python:\n\n```python\nclass Node:\n    def __init__(self, value):\n        self.value = value\n        self.left = None\n        self.right = None\n\nclass BinarySearchTree:\n    def __init__(self):\n        self.root = None\n```"
                }
            ],
            "timestamp": base_time + (i + 10) * 60
        }
        test_data.append((f'chat:{i}', json.dumps(chat_data)))
    
    # Edge cases
    test_data.extend([
        # Empty content
        ('chat:empty', json.dumps({"messages": [{"role": "user", "content": ""}, {"role": "assistant", "content": ""}]})),
        
        # Very long content
        ('chat:long', json.dumps({"messages": [{"role": "user", "content": "A" * 1000}, {"role": "assistant", "content": "B" * 1000}]})),
        
        # Special characters
        ('chat:special', json.dumps({"messages": [{"role": "user", "content": "Special chars: !@#$%^&*()_+{}:\"|<>?"}, {"role": "assistant", "content": "More special chars: ¡™£¢∞§¶•ªº–≠œ∑´®†¥¨ˆøπ"}]})),
        
        # Markdown formatting
        ('chat:markdown', json.dumps({"messages": [{"role": "user", "content": "# Heading\n## Subheading\n- List item 1\n- List item 2"}, {"role": "assistant", "content": "**Bold** and *italic* with `code` and [link](https://example.com)"}]})),
        
        # Invalid JSON (should be ignored by extractor)
        ('invalid_json', 'This is not valid JSON')
    ])
    
    # Insert test data
    cursor.executemany('INSERT OR REPLACE INTO cursorDiskKV VALUES (?, ?)', test_data)
    conn.commit()
    conn.close()
    
    print(f"Created enhanced test database with {len(test_data)} entries at {db_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: enhanced_test_db.py <db_path>")
        sys.exit(1)
    create_enhanced_test_db(sys.argv[1]) 