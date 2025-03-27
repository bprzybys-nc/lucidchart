#!/usr/bin/env python3
import sqlite3
import json
import sys
from datetime import datetime, timedelta

def create_test_db(db_path):
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
    
    for i in range(10):
        # User message
        test_data.append((
            f'prompt_{i}',
            json.dumps({
                'prompt': f'Test user message {i}',
                'timestamp': base_time + i * 60
            })
        ))
        
        # Assistant response
        test_data.append((
            f'response_{i}',
            json.dumps({
                'response': f'Test assistant response {i}',
                'model': 'test-model',
                'timestamp': base_time + i * 60 + 30
            })
        ))
    
    # Insert test data
    cursor.executemany('INSERT OR REPLACE INTO cursorDiskKV VALUES (?, ?)', test_data)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: create_test_db.py <db_path>")
        sys.exit(1)
    create_test_db(sys.argv[1])
