#!/usr/bin/env python3
"""
Extract LLM responses from Cursor logs and combine with user prompts.

This script attempts to extract both user messages and LLM responses from
Cursor logs, combining them into a comprehensive chat history markdown file.
"""

import json
import os
import sqlite3
import re
import argparse
import glob
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import sys
import colorama

# Initialize colorama for cross-platform colored output
colorama.init()

# Configure progress bar for better visibility in all terminals
tqdm.monitor_interval = 0

# Define colors for console output
GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW
RED = colorama.Fore.RED
BLUE = colorama.Fore.CYAN
RESET = colorama.Fore.RESET

def find_cursor_logs(user_specified_path=None):
    """Find Cursor log locations based on operating system."""
    if user_specified_path:
        return Path(user_specified_path)
    
    # Default paths based on OS
    home = Path.home()
    
    # macOS
    if os.name == 'posix' and os.uname().sysname == 'Darwin':
        return home / "Library" / "Application Support" / "Cursor" / "User" / "databases"
    
    # Windows
    elif os.name == 'nt':
        return home / "AppData" / "Roaming" / "Cursor" / "User" / "databases"
    
    # Linux
    elif os.name == 'posix':
        return home / ".config" / "Cursor" / "User" / "databases"
    
    raise NotImplementedError(f"Unsupported operating system: {os.name}")

def extract_prompts(db_path, sample_limit=0):
    """
    Extract user prompts from the database
    Returns a list of dictionaries with prompt information
    """
    prompts = []
    
    if not os.path.exists(db_path):
        print(f"{YELLOW}Database file not found: {db_path}{RESET}")
        return prompts
    
    try:
        print(f"{BLUE}Connecting to database: {db_path}{RESET}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"{BLUE}Found {len(tables)} tables in the database{RESET}")
        
        # Check for ItemTable which might contain prompts
        if ('ItemTable',) in tables:
            print(f"{GREEN}Found ItemTable - extracting prompts...{RESET}")
            
            try:
                # Get column names
                cursor.execute("PRAGMA table_info(ItemTable)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Construct query based on available columns
                query = "SELECT * FROM ItemTable"
                cursor.execute(query)
                rows = cursor.fetchall()
                
                print(f"{GREEN}Found {len(rows)} rows in ItemTable{RESET}")
                
                # Process rows with progress bar
                for row in tqdm(rows, desc="Processing prompts from ItemTable", unit="row"):
                    row_dict = dict(zip(columns, row))
                    
                    # Extract the value field which may contain JSON
                    if 'value' in row_dict and row_dict['value']:
                        try:
                            value_data = json.loads(row_dict['value'])
                            
                            # Look for prompt-like content
                            if isinstance(value_data, dict):
                                for key in ['prompt', 'input', 'message', 'question', 'userMessage']:
                                    if key in value_data and isinstance(value_data[key], str) and len(value_data[key]) > 10:
                                        prompt_text = value_data[key]
                                        
                                        # Extract timestamp if available
                                        timestamp = None
                                        if 'timestamp' in value_data:
                                            timestamp = value_data['timestamp']
                                        elif 'createdAt' in value_data:
                                            timestamp = value_data['createdAt']
                                        
                                        prompts.append({
                                            'prompt': prompt_text,
                                            'timestamp': timestamp,
                                            'source': 'ItemTable'
                                        })
                        except:
                            # Not valid JSON or other error
                            pass
            except Exception as e:
                print(f"{RED}Error extracting from ItemTable: {e}{RESET}")
        
        # Check for key-value store that might contain prompts
        if ('cursorDiskKV',) in tables:
            print(f"{GREEN}Found cursorDiskKV - extracting prompts...{RESET}")
            
            try:
                # Get column names
                cursor.execute("PRAGMA table_info(cursorDiskKV)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Construct query based on available columns
                query = "SELECT * FROM cursorDiskKV"
                cursor.execute(query)
                rows = cursor.fetchall()
                
                print(f"{GREEN}Found {len(rows)} rows in cursorDiskKV{RESET}")
                
                # Process rows with progress bar
                for row in tqdm(rows, desc="Processing prompts from cursorDiskKV", unit="row"):
                    row_dict = dict(zip(columns, row))
                    
                    # Look for keys that might contain prompts
                    key = row_dict.get('key', '')
                    if isinstance(key, str) and any(term in key.lower() for term in ['prompt', 'chat', 'message', 'question']):
                        if 'value' in row_dict and row_dict['value']:
                            try:
                                # Try parsing as JSON
                                value_data = json.loads(row_dict['value'])
                                
                                # Look for prompt-like content
                                if isinstance(value_data, dict):
                                    for key in ['prompt', 'input', 'message', 'question', 'userMessage']:
                                        if key in value_data and isinstance(value_data[key], str) and len(value_data[key]) > 10:
                                            prompt_text = value_data[key]
                                            
                                            # Extract timestamp if available
                                            timestamp = None
                                            if 'timestamp' in value_data:
                                                timestamp = value_data['timestamp']
                                            elif 'createdAt' in value_data:
                                                timestamp = value_data['createdAt']
                                            
                                            prompts.append({
                                                'prompt': prompt_text,
                                                'timestamp': timestamp,
                                                'source': 'cursorDiskKV'
                                            })
                            except:
                                # Not valid JSON, check if the value itself might be a prompt
                                value = row_dict['value']
                                if isinstance(value, str) and len(value) > 20 and not value.startswith('{') and not value.startswith('['):
                                    prompts.append({
                                        'prompt': value,
                                        'timestamp': None,
                                        'source': 'cursorDiskKV_raw'
                                    })
            except Exception as e:
                print(f"{RED}Error extracting from cursorDiskKV: {e}{RESET}")
    
    except Exception as e:
        print(f"{RED}Error connecting to database: {e}{RESET}")
    finally:
        if 'conn' in locals():
            conn.close()
    
    # Remove duplicates and apply sample limit
    unique_prompts = []
    seen_prompts = set()
    
    # Process prompts with progress bar for deduplication
    for prompt in tqdm(prompts, desc="Deduplicating prompts", unit="prompt"):
        if prompt['prompt'] not in seen_prompts:
            seen_prompts.add(prompt['prompt'])
            unique_prompts.append(prompt)
    
    prompts = unique_prompts
    
    if sample_limit > 0 and len(prompts) > sample_limit:
        print(f"{YELLOW}Limiting to {sample_limit} prompts for testing{RESET}")
        prompts = prompts[:sample_limit]
    
    print(f"{GREEN}Extracted {len(prompts)} unique prompts{RESET}")
    return prompts

def extract_responses(db_path, sample_limit=0):
    """
    Extract AI responses from the database
    Returns a list of dictionaries with response information
    """
    responses = []
    
    if not os.path.exists(db_path):
        print(f"{YELLOW}Database file not found: {db_path}{RESET}")
        return responses
    
    try:
        print(f"{BLUE}Connecting to database for responses: {db_path}{RESET}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # Check for tables that might contain responses
        for table_tuple in tables:
            table = table_tuple[0]
            
            # Skip tables unlikely to contain responses
            if table.startswith('sqlite_') or table in ['SQLITE_SEQUENCE']:
                continue
                
            try:
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Skip if no value column
                if 'value' not in columns:
                    continue
                
                print(f"{BLUE}Checking {table} for responses...{RESET}")
                
                # Construct query based on available columns
                query = f"SELECT * FROM {table}"
                cursor.execute(query)
                rows = cursor.fetchall()
                
                # Process rows with progress bar
                for row in tqdm(rows, desc=f"Processing responses from {table}", unit="row", leave=False):
                    row_dict = dict(zip(columns, row))
                    
                    # Extract the value field which may contain JSON
                    if 'value' in row_dict and row_dict['value']:
                        try:
                            # Try parsing as JSON
                            value_data = json.loads(row_dict['value'])
                            
                            # Look for response-like content in JSON
                            if isinstance(value_data, dict):
                                for key in ['response', 'answer', 'result', 'aiMessage', 'content', 'assistantMessage']:
                                    if key in value_data and isinstance(value_data[key], str) and len(value_data[key]) > 20:
                                        response_text = value_data[key]
                                        
                                        # Extract timestamp if available
                                        timestamp = None
                                        if 'timestamp' in value_data:
                                            timestamp = value_data['timestamp']
                                        elif 'createdAt' in value_data:
                                            timestamp = value_data['createdAt']
                                        
                                        responses.append({
                                            'response': response_text,
                                            'timestamp': timestamp,
                                            'source': table
                                        })
                        except:
                            # Not valid JSON, check if the value itself might be a response
                            value = row_dict['value']
                            if isinstance(value, str) and len(value) > 50 and not value.startswith('{') and not value.startswith('['):
                                # Heuristic: responses tend to be longer and more structured
                                if '\n' in value and (value.startswith("I") or value.startswith("The") or value.startswith("Here")):
                                    responses.append({
                                        'response': value,
                                        'timestamp': None,
                                        'source': f"{table}_raw"
                                    })
            except Exception as e:
                print(f"{YELLOW}Error processing table {table}: {e}{RESET}")
                continue
    
    except Exception as e:
        print(f"{RED}Error connecting to database: {e}{RESET}")
    finally:
        if 'conn' in locals():
            conn.close()
    
    # Remove duplicates and apply sample limit
    unique_responses = []
    seen_responses = set()
    
    # Process responses with progress bar for deduplication
    for response in tqdm(responses, desc="Deduplicating responses", unit="response"):
        content = response['response']
        # Use first 100 chars as a fingerprint for deduplication
        fingerprint = content[:min(100, len(content))]
        if fingerprint not in seen_responses:
            seen_responses.add(fingerprint)
            unique_responses.append(response)
    
    responses = unique_responses
    
    if sample_limit > 0 and len(responses) > sample_limit:
        print(f"{YELLOW}Limiting to {sample_limit} responses for testing{RESET}")
        responses = responses[:sample_limit]
    
    print(f"{GREEN}Extracted {len(responses)} unique responses{RESET}")
    return responses

def search_log_files(logs_dir, sample_limit=0, max_files=0):
    """
    Search log files for potential prompts and responses
    Returns a list of dictionaries with extracted information
    """
    results = []
    
    if not os.path.isdir(logs_dir):
        print(f"{YELLOW}Logs directory not found: {logs_dir}{RESET}")
        return results
    
    print(f"{BLUE}Searching log files in: {logs_dir}{RESET}")
    
    # Get all log files recursively
    log_files = []
    for root, dirs, files in os.walk(logs_dir):
        for file in files:
            if file.endswith('.log'):
                log_files.append(os.path.join(root, file))
    
    print(f"{BLUE}Found {len(log_files)} log files{RESET}")
    
    # Limit files for testing if needed
    if max_files > 0 and len(log_files) > max_files:
        print(f"{YELLOW}Limiting to {max_files} log files for testing{RESET}")
        log_files = log_files[:max_files]
    
    # Patterns to search for
    prompt_patterns = [
        r'"prompt"\s*:\s*"(.+?[^\\])"',
        r'"message"\s*:\s*"(.+?[^\\])"',
        r'"userMessage"\s*:\s*"(.+?[^\\])"',
        r'"query"\s*:\s*"(.+?[^\\])"',
        r'"user"\s*:\s*"(.+?[^\\])"',
        r'"question"\s*:\s*"(.+?[^\\])"',
        r'"human"\s*:\s*"(.+?[^\\])"',
        r'"input"\s*:\s*"(.+?[^\\])"',
        r'"content"\s*:\s*"(.+?[^\\])"',
        r'human:\s*(.+?)(?=\n\n|$)',
        r'user:\s*(.+?)(?=\n\n|$)',
        r'USER:\s*(.+?)(?=\n\n|$)'
    ]
    
    response_patterns = [
        r'"response"\s*:\s*"(.+?[^\\])"',
        r'"aiMessage"\s*:\s*"(.+?[^\\])"',
        r'"assistantMessage"\s*:\s*"(.+?[^\\])"',
        r'"answer"\s*:\s*"(.+?[^\\])"',
        r'"content"\s*:\s*"(.+?[^\\])"',
        r'"result"\s*:\s*"(.+?[^\\])"',
        r'"assistant"\s*:\s*"(.+?[^\\])"',
        r'"ai"\s*:\s*"(.+?[^\\])"',
        r'"llm"\s*:\s*"(.+?[^\\])"',
        r'"output"\s*:\s*"(.+?[^\\])"',
        r'assistant:\s*(.+?)(?=\n\n|$)',
        r'ASSISTANT:\s*(.+?)(?=\n\n|$)',
        r'llm:\s*(.+?)(?=\n\n|$)',
        r'LLM:\s*(.+?)(?=\n\n|$)'
    ]
    
    # Process each log file
    for log_file in tqdm(log_files, desc="Scanning log files", unit="file"):
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                try:
                    content = f.read()
                    
                    # Search for prompts
                    for pattern in prompt_patterns:
                        try:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                if len(match) > 20:  # Minimum length filter
                                    results.append({
                                        'type': 'prompt',
                                        'content': match,
                                        'source': os.path.basename(log_file)
                                    })
                        except re.error:
                            continue
                    
                    # Search for responses
                    for pattern in response_patterns:
                        try:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                if len(match) > 50:  # Responses tend to be longer
                                    results.append({
                                        'type': 'response',
                                        'content': match,
                                        'source': os.path.basename(log_file)
                                    })
                        except re.error:
                            continue
                    
                    # Look for conversation chunks (html or json-like)
                    try:
                        if "<div" in content and "</div>" in content:
                            chat_divs = re.findall(r'<div[^>]*chat[^>]*>(.*?)</div>', content, re.DOTALL)
                            for div in chat_divs:
                                try:
                                    # Extract human/user content
                                    user_matches = re.findall(r'<div[^>]*user[^>]*>(.*?)</div>', div, re.DOTALL)
                                    for match in user_matches:
                                        # Clean HTML tags
                                        clean_text = re.sub(r'<[^>]*>', '', match)
                                        if len(clean_text) > 20:
                                            results.append({
                                                'type': 'prompt',
                                                'content': clean_text,
                                                'source': f"html_{os.path.basename(log_file)}"
                                            })
                                    
                                    # Extract AI/assistant content
                                    ai_matches = re.findall(r'<div[^>]*assistant[^>]*>(.*?)</div>', div, re.DOTALL)
                                    for match in ai_matches:
                                        # Clean HTML tags
                                        clean_text = re.sub(r'<[^>]*>', '', match)
                                        if len(clean_text) > 50:
                                            results.append({
                                                'type': 'response',
                                                'content': clean_text,
                                                'source': f"html_{os.path.basename(log_file)}"
                                            })
                                except re.error:
                                    continue
                    except re.error:
                        pass
                except Exception as e:
                    print(f"{YELLOW}Error processing content in file {log_file}: {e}{RESET}")
        except Exception as e:
            print(f"{YELLOW}Error processing log file {log_file}: {e}{RESET}")
            continue
    
    # Remove duplicates and apply sample limit
    unique_results = []
    seen_content = set()
    
    # Process results with progress bar for deduplication
    for result in tqdm(results, desc="Deduplicating log results", unit="result"):
        content = result['content']
        # Use first 100 chars as a fingerprint for deduplication
        fingerprint = content[:min(100, len(content))]
        if fingerprint not in seen_content:
            seen_content.add(fingerprint)
            unique_results.append(result)
    
    results = unique_results
    
    if sample_limit > 0 and len(results) > sample_limit:
        print(f"{YELLOW}Limiting to {sample_limit} log results for testing{RESET}")
        results = results[:sample_limit]
    
    print(f"{GREEN}Extracted {len(results)} unique items from log files{RESET}")
    return results

def extract_conversation_set(db_path, sample_limit=0):
    """
    Extract complete conversation sets (request-response pairs) from the database.
    A conversation set is considered complete if it has both a user message and an LLM response.
    """
    conversation_sets = []
    
    if not os.path.exists(db_path):
        print(f"{YELLOW}Database file not found: {db_path}{RESET}")
        return conversation_sets
    
    try:
        print(f"{BLUE}Connecting to database: {db_path}{RESET}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"{BLUE}Found {len(tables)} tables in the database{RESET}")
        
        # First pass: Extract all potential messages with timestamps
        messages = []
        
        for table_tuple in tables:
            table = table_tuple[0]
            
            # Skip system tables
            if table.startswith('sqlite_'):
                continue
            
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Need at least a value column
                if 'value' not in columns:
                    continue
                
                print(f"{GREEN}Checking {table} for conversation data...{RESET}")
                
                # Get all rows with progress bar
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                
                for row in tqdm(rows, desc=f"Processing {table}", unit="row"):
                    row_dict = dict(zip(columns, row))
                    
                    if 'value' in row_dict and row_dict['value']:
                        try:
                            value_data = json.loads(row_dict['value'])
                            
                            if isinstance(value_data, dict):
                                # Look for message content and role
                                content = None
                                role = None
                                timestamp = None
                                
                                # Check common message patterns
                                for content_key in ['content', 'message', 'prompt', 'response', 'text', 'value']:
                                    if content_key in value_data:
                                        content = value_data[content_key]
                                        break
                                
                                # Determine role
                                if any(key in str(value_data).lower() for key in ['user', 'human', 'prompt']):
                                    role = 'user'
                                elif any(key in str(value_data).lower() for key in ['assistant', 'ai', 'llm', 'response']):
                                    role = 'assistant'
                                
                                # Get timestamp
                                for time_key in ['timestamp', 'createdAt', 'created_at', 'time']:
                                    if time_key in value_data:
                                        timestamp = value_data[time_key]
                                        break
                                
                                if content and role:
                                    messages.append({
                                        'content': content,
                                        'role': role,
                                        'timestamp': timestamp,
                                        'source': table
                                    })
                        except:
                            pass
            except Exception as e:
                print(f"{YELLOW}Error processing table {table}: {e}{RESET}")
                continue
        
        print(f"{GREEN}Found {len(messages)} potential messages{RESET}")
        
        # Sort messages by timestamp if available
        messages_with_time = [m for m in messages if m['timestamp']]
        messages_without_time = [m for m in messages if not m['timestamp']]
        
        if messages_with_time:
            try:
                messages_with_time.sort(key=lambda x: float(str(x['timestamp'])) if isinstance(x['timestamp'], (int, float, str)) else 0)
            except:
                print(f"{YELLOW}Warning: Could not sort some messages by timestamp{RESET}")
        
        # Combine sorted messages
        messages = messages_with_time + messages_without_time
        
        # Group into conversation sets
        current_set = []
        
        for msg in messages:
            current_set.append(msg)
            
            # If we have a user message followed by an assistant message, we have a complete set
            if len(current_set) >= 2:
                roles = [m['role'] for m in current_set[-2:]]
                if roles == ['user', 'assistant']:
                    conversation_sets.append(current_set[-2:])
                    current_set = []
        
        # Apply sample limit if specified
        if sample_limit > 0 and len(conversation_sets) > sample_limit:
            print(f"{YELLOW}Limiting to {sample_limit} conversation sets for testing{RESET}")
            conversation_sets = conversation_sets[:sample_limit]
        
        print(f"{GREEN}Extracted {len(conversation_sets)} complete conversation sets{RESET}")
        
    except Exception as e:
        print(f"{RED}Error extracting conversation sets: {e}{RESET}")
    finally:
        if 'conn' in locals():
            conn.close()
    
    return conversation_sets

def generate_markdown_from_sets(conversation_sets, log_results, output_file):
    """
    Generate a markdown file from conversation sets and log results
    """
    print(f"{BLUE}Generating markdown file: {output_file}{RESET}")
    
    markdown = f"# Cursor Chat History\n\n"
    markdown += f"Extracted from Cursor IDE on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    markdown += f"Found {len(conversation_sets)} complete conversation sets"
    if log_results:
        markdown += f" and {len(log_results)} additional items from logs"
    markdown += ".\n\n"
    
    # Write conversation sets
    markdown += "## Complete Conversations\n\n"
    
    for i, conv_set in enumerate(conversation_sets, 1):
        markdown += f"### Conversation {i}\n\n"
        
        for msg in conv_set:
            if msg['role'] == 'user':
                markdown += f"#### Human Message\n\n"
            else:
                markdown += f"#### LLM Response\n\n"
            
            markdown += f"```\n{msg['content']}\n```\n\n"
            
            if msg.get('timestamp'):
                markdown += f"*Timestamp: {msg['timestamp']}*\n\n"
            if msg.get('source'):
                markdown += f"*Source: {msg['source']}*\n\n"
        
        markdown += "---\n\n"
    
    # Add log results if any
    if log_results:
        markdown += "## Additional Content from Logs\n\n"
        
        for i, item in enumerate(log_results, 1):
            if item['type'] == 'prompt':
                markdown += f"### Human Message (Log #{i})\n\n"
            else:
                markdown += f"### LLM Response (Log #{i})\n\n"
            
            markdown += f"```\n{item['content']}\n```\n\n"
            markdown += f"*Source: {item['source']}*\n\n"
            markdown += "---\n\n"
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"{GREEN}Markdown file generated: {output_file}{RESET}")
    return True

def analyze_database(db_path):
    """
    Analyze database structure to help find relevant data
    """
    if not os.path.exists(db_path):
        print(f"{RED}Database file not found: {db_path}{RESET}")
        return
    
    try:
        print(f"{BLUE}Analyzing database structure: {db_path}{RESET}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"{GREEN}Found {len(tables)} tables:{RESET}")
        
        # Analyze each table
        for table_tuple in tqdm(tables, desc="Analyzing tables"):
            table = table_tuple[0]
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            
            print(f"\n{BLUE}Table: {table} ({row_count} rows){RESET}")
            print(f"  Columns: {', '.join(col[1] for col in columns)}")
            
            # Sample data if available
            if row_count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                sample = cursor.fetchone()
                
                # Check for JSON data
                json_columns = []
                for i, col in enumerate(columns):
                    col_name = col[1]
                    if sample[i] and isinstance(sample[i], str):
                        val = sample[i]
                        if val.startswith('{') and val.endswith('}'):
                            try:
                                json_data = json.loads(val)
                                json_columns.append(col_name)
                                print(f"  {YELLOW}JSON column: {col_name}{RESET}")
                                print(f"    Keys: {', '.join(json_data.keys())}")
                            except:
                                pass
                
                # If found JSON columns, analyze their content
                if json_columns:
                    print(f"  {GREEN}Analyzing JSON content...{RESET}")
                    
                    for col_name in json_columns:
                        # Check more rows for relevant content
                        cursor.execute(f"SELECT {col_name} FROM {table} LIMIT 10")
                        samples = cursor.fetchall()
                        
                        chat_related_found = False
                        for sample in samples:
                            if not sample[0] or not isinstance(sample[0], str):
                                continue
                                
                            try:
                                data = json.loads(sample[0])
                                if isinstance(data, dict):
                                    # Check for chat-related keys
                                    chat_keys = ['prompt', 'response', 'message', 'chat', 'query', 'answer']
                                    for key in chat_keys:
                                        if key in data:
                                            print(f"    {GREEN}Found chat-related key: {key}{RESET}")
                                            chat_related_found = True
                            except:
                                pass
                        
                        if chat_related_found:
                            print(f"  {GREEN}This column may contain chat data!{RESET}")
    
    except Exception as e:
        print(f"{RED}Error analyzing database: {e}{RESET}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    parser = argparse.ArgumentParser(description="Extract Chat History from Cursor")
    parser.add_argument("--db-path", help="Path to Cursor database file")
    parser.add_argument("--logs-dir", help="Path to Cursor logs directory")
    parser.add_argument("--output-file", help="Output markdown file", default="chat_history.md")
    parser.add_argument("--sample-limit", type=int, default=0, help="Limit number of conversation sets")
    parser.add_argument("--max-files", type=int, default=0, help="Limit number of log files to process")
    parser.add_argument("--test-mode", action="store_true", help="Run in test mode")
    parser.add_argument("--analyze", action="store_true", help="Analyze database structure")
    
    args = parser.parse_args()
    
    print(f"{BLUE}Cursor Chat History Extraction{RESET}")
    print(f"{BLUE}-----------------------------{RESET}")
    
    # Handle test mode defaults
    if args.test_mode and args.sample_limit == 0:
        args.sample_limit = 5  # Get at least 5 complete conversation sets
        args.max_files = 3
        print(f"{YELLOW}Running in test mode with sample limit {args.sample_limit} and max files {args.max_files}{RESET}")
    
    # Just analyze if that's all we're doing
    if args.analyze and args.db_path:
        analyze_database(args.db_path)
        return 0
    
    # Extract conversation sets from database
    conversation_sets = []
    if args.db_path:
        conversation_sets = extract_conversation_set(args.db_path, args.sample_limit)
    
    # Extract additional data from log files
    log_results = []
    if args.logs_dir:
        log_results = search_log_files(args.logs_dir, args.sample_limit, args.max_files)
    
    # Generate markdown
    if conversation_sets or log_results:
        generate_markdown_from_sets(conversation_sets, log_results, args.output_file)
        print(f"{GREEN}Extraction complete. Results saved to {args.output_file}{RESET}")
    else:
        print(f"{YELLOW}No data extracted. Please check your paths and try again.{RESET}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 