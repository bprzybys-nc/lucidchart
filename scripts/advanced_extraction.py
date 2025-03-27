#!/usr/bin/env python3
"""
Advanced extraction techniques for Cursor chat logs.

This script implements more advanced methods to extract and match LLM responses
with user prompts, including parsing HTML/XML from logs, analyzing timestamps,
and attempting to reconstruct the conversation flow.
"""

import json
import os
import re
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict
from tqdm import tqdm
import sys
import glob

# Configure progress bar for better visibility in all terminals
tqdm.monitor_interval = 0

def extract_from_html_logs(logs_dir, max_files=None, sample_limit=None):
    """Extract chat data from HTML-formatted log files."""
    chat_data = []
    file_count = 0
    
    print(f"Searching for HTML-formatted messages in {logs_dir}")
    
    # First, collect all log files
    log_files = []
    for root, _, files in os.walk(logs_dir):
        for file in files:
            if file.endswith('.log'):
                log_files.append(os.path.join(root, file))
    
    # Apply max_files limit if specified
    if max_files and len(log_files) > max_files:
        print(f"Limiting HTML search to {max_files} of {len(log_files)} log files")
        log_files = log_files[:max_files]
    else:
        print(f"Searching through {len(log_files)} log files for HTML content")
    
    # Process log files with progress bar
    for log_file in tqdm(log_files, desc="Scanning log files for HTML"):
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                try:
                    content = f.read()
                    
                    # More comprehensive patterns for finding HTML-like fragments
                    html_patterns = [
                        r'<div.*?>.*?</div>',
                        r'<span.*?>.*?</span>',
                        r'<p.*?>.*?</p>'
                    ]
                    
                    for pattern in html_patterns:
                        try:
                            html_fragments = re.findall(pattern, content, re.DOTALL)
                            
                            if html_fragments:
                                tqdm.write(f"Found {len(html_fragments)} HTML fragments with pattern {pattern} in {os.path.basename(log_file)}")
                            
                            for fragment in tqdm(html_fragments, desc=f"Processing fragments in {os.path.basename(log_file)}", leave=False, disable=len(html_fragments) < 5):
                                try:
                                    soup = BeautifulSoup(fragment, 'lxml')
                                    # Look for user messages and AI responses with broader class and element matches
                                    message_elements = soup.find_all(['div', 'span', 'p', 'section', 'article'], 
                                                                  class_=lambda c: c and any(term in c for term in 
                                                                                          ['message', 'chat', 'user', 'human', 'ai', 'assistant', 'response', 'cursor', 'llm']))
                                    
                                    for element in message_elements:
                                        try:
                                            text = element.get_text(strip=True)
                                            if text and len(text) > 20:  # Filter out short fragments
                                                role = 'user' if any(cls in str(element).lower() for cls in ['user', 'human']) else 'assistant'
                                                timestamp = None
                                                
                                                # Try to extract timestamp
                                                time_element = element.find(['span', 'div', 'time'], class_=lambda c: c and 'time' in c)
                                                if time_element:
                                                    timestamp = time_element.get_text(strip=True)
                                                
                                                chat_data.append({
                                                    'role': role,
                                                    'content': text,
                                                    'timestamp': timestamp
                                                })
                                                
                                                if sample_limit and len(chat_data) >= sample_limit:
                                                    print(f"Reached sample limit ({sample_limit}) for testing")
                                                    return chat_data
                                        except Exception as e:
                                            # Skip this element if there's an error processing it
                                            continue
                                except Exception as e:
                                    tqdm.write(f"Error parsing HTML fragment: {e}")
                                    continue
                        except re.error:
                            tqdm.write(f"Error in regex pattern {pattern} for file {os.path.basename(log_file)}")
                            continue
                except Exception as e:
                    tqdm.write(f"Error processing content from {log_file}: {e}")
        except Exception as e:
            tqdm.write(f"Error reading log file {log_file}: {e}")
            continue
    
    print(f"Extracted {len(chat_data)} messages from HTML content")
    return chat_data

def extract_from_json_logs(logs_dir, max_files=None, sample_limit=None):
    """Extract chat data from JSON-formatted log entries."""
    chat_data = []
    file_count = 0
    
    print(f"Searching for JSON-formatted messages in {logs_dir}")
    
    # First, collect all log files
    log_files = []
    for root, _, files in os.walk(logs_dir):
        for file in files:
            if file.endswith('.log'):
                log_files.append(os.path.join(root, file))
    
    # Apply max_files limit if specified
    if max_files and len(log_files) > max_files:
        print(f"Limiting JSON search to {max_files} of {len(log_files)} log files")
        log_files = log_files[:max_files]
    else:
        print(f"Searching through {len(log_files)} log files for JSON content")
    
    # Improved patterns to find JSON-like structures
    json_patterns = [
        r'(\{.*?\})',  # Simple JSON objects
        r'"(?:message|prompt|response|content|chat)"\s*:\s*".*?"',  # Strings with chat-related keys
        r'"(?:user|assistant|ai|llm)"\s*:\s*".*?"'  # Role-based strings
    ]
    
    # Process log files with progress bar
    for log_file in tqdm(log_files, desc="Scanning log files for JSON"):
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                try:
                    content = f.read()
                    
                    # Apply all patterns
                    json_matches = []
                    for pattern in json_patterns:
                        try:
                            matches = list(re.finditer(pattern, content, re.DOTALL))
                            if matches:
                                tqdm.write(f"Found {len(matches)} potential JSON objects with pattern {pattern} in {os.path.basename(log_file)}")
                                json_matches.extend(matches)
                        except re.error:
                            tqdm.write(f"Error in regex pattern {pattern} for file {os.path.basename(log_file)}")
                            continue
                    
                    if json_matches:
                        tqdm.write(f"Found {len(json_matches)} total potential JSON objects in {os.path.basename(log_file)}")
                    
                    for match in tqdm(json_matches, desc=f"Processing JSON in {os.path.basename(log_file)}", leave=False, disable=len(json_matches) < 5):
                        try:
                            json_str = match.group(0)
                            # Check for and fix common JSON issues
                            if json_str.endswith(','):
                                json_str = json_str[:-1]
                            
                            # Try to parse the JSON
                            try:
                                data = json.loads(json_str)
                            except:
                                # Try with surrounding curly braces if it looks like a fragment
                                if not json_str.startswith('{'):
                                    try:
                                        data = json.loads('{' + json_str + '}')
                                    except:
                                        continue
                                else:
                                    continue
                            
                            # Check if this looks like chat data using a broader set of keys
                            chat_keys = ['message', 'prompt', 'response', 'content', 'chat', 
                                        'user', 'assistant', 'ai', 'llm', 'question', 'answer',
                                        'input', 'output', 'query', 'result', 'human']
                            
                            if isinstance(data, dict) and any(key in data for key in chat_keys):
                                # Determine the role
                                if any(key in data for key in ['prompt', 'user', 'human', 'question', 'input', 'query']):
                                    role = 'user'
                                else:
                                    role = 'assistant'
                                
                                # Extract content from various possible fields
                                for key in chat_keys:
                                    if key in data and isinstance(data[key], str) and len(data[key]) > 20:
                                        chat_data.append({
                                            'role': role,
                                            'content': data[key],
                                            'timestamp': data.get('timestamp') or data.get('time') or data.get('date')
                                        })
                                        break
                                
                                if sample_limit and len(chat_data) >= sample_limit:
                                    print(f"Reached sample limit ({sample_limit}) for testing")
                                    return chat_data
                        except Exception as e:
                            # Skip this match if there's an error processing it
                            continue
                except Exception as e:
                    tqdm.write(f"Error processing content from {log_file}: {e}")
        except Exception as e:
            tqdm.write(f"Error reading log file {log_file}: {e}")
            continue
    
    print(f"Extracted {len(chat_data)} messages from JSON content")
    return chat_data

def extract_from_conversation_history(db_path, sample_limit=None):
    """Extract conversation history from the database."""
    print(f"Extracting conversation history from database at {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    conversations = []
    table_count = 0
    
    try:
        # Check tables that might contain conversation history
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        chat_related_tables = [t[0] for t in tables if 'history' in t[0].lower() or 'conversation' in t[0].lower() or 'chat' in t[0].lower()]
        print(f"Found {len(chat_related_tables)} tables possibly containing conversation history")
        
        for table_name in tqdm(chat_related_tables, desc="Examining conversation tables"):
            try:
                limit_clause = f"LIMIT {sample_limit}" if sample_limit else ""
                cursor.execute(f"SELECT * FROM {table_name} {limit_clause}")
                rows = cursor.fetchall()
                
                # If we found some data, try to interpret it
                if rows:
                    # Get column names
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    # Convert to list of dicts for easier processing
                    data = []
                    for row in tqdm(rows, desc=f"Processing rows in {table_name}", leave=False, disable=len(rows) < 10):
                        data.append(dict(zip(columns, row)))
                    
                    tqdm.write(f"Extracted {len(data)} rows from {table_name}")
                    conversations.append({
                        'table': table_name,
                        'data': data,
                        'columns': columns
                    })
                    
                    table_count += 1
                    if sample_limit and table_count >= sample_limit:
                        print(f"Reached sample limit for tables ({sample_limit})")
                        break
            except Exception as e:
                tqdm.write(f"Error querying table {table_name}: {e}")
    
    except Exception as e:
        print(f"Error extracting conversation history: {e}")
    
    finally:
        conn.close()
    
    return conversations

def match_prompts_with_responses(prompts, responses, log_extracts):
    """Attempt to match prompts with responses using heuristics."""
    print("Matching prompts with responses...")
    matched_conversations = []
    
    # First, try direct matching by index if counts match
    if len(prompts) == len(responses):
        print(f"Direct matching possible: found {len(prompts)} prompts and {len(responses)} responses")
        for i, prompt in tqdm(enumerate(prompts), total=len(prompts), desc="Direct matching"):
            if isinstance(prompt, dict) and 'text' in prompt:
                prompt_text = prompt['text'].strip()
            else:
                prompt_text = str(prompt).strip()
                
            response = responses[i]
            if isinstance(response, dict) and ('response' in response or 'content' in response):
                response_text = response.get('response', response.get('content', ''))
            else:
                response_text = str(response)
                
            matched_conversations.append({
                'role': 'user',
                'content': prompt_text
            })
            
            matched_conversations.append({
                'role': 'assistant',
                'content': response_text
            })
    
    # If counts don't match or we have additional log extracts, try more advanced matching
    else:
        print(f"Using advanced matching: {len(prompts)} prompts, {len(responses)} responses, {len(log_extracts)} log extracts")
        # Create a combined dataset from all sources
        all_messages = []
        
        # Add prompts
        print("Adding prompts to matching pool...")
        for i, prompt in tqdm(enumerate(prompts), total=len(prompts), desc="Processing prompts"):
            if isinstance(prompt, dict) and 'text' in prompt:
                all_messages.append({
                    'role': 'user',
                    'content': prompt['text'].strip(),
                    'source': 'prompts',
                    'index': i
                })
        
        # Add responses
        print("Adding responses to matching pool...")
        for i, response in tqdm(enumerate(responses), total=len(responses), desc="Processing responses"):
            if isinstance(response, dict) and ('response' in response or 'content' in response):
                all_messages.append({
                    'role': 'assistant',
                    'content': response.get('response', response.get('content', '')),
                    'source': 'responses',
                    'index': i
                })
        
        # Add log extracts
        if log_extracts:
            print("Adding log extracts to matching pool...")
            for i, extract in tqdm(enumerate(log_extracts), total=len(log_extracts), desc="Processing log extracts"):
                role = 'user' if 'user' in extract.lower() or 'human' in extract.lower() else 'assistant'
                all_messages.append({
                    'role': role,
                    'content': extract,
                    'source': 'logs',
                    'index': i
                })
        
        # Sort and deduplicate messages
        print("Deduplicating and sorting messages...")
        # This is a simplistic approach; in reality, this would use more sophisticated 
        # NLP techniques to identify duplicates and establish conversation order
        seen_contents = set()
        sorted_messages = []
        
        for msg in tqdm(all_messages, desc="Deduplicating messages"):
            # Create a simplified representation for deduplication
            simplified = re.sub(r'\s+', ' ', msg['content']).lower()[:100]
            if simplified not in seen_contents:
                seen_contents.add(simplified)
                sorted_messages.append(msg)
        
        # Try to reconstruct conversation flow
        print("Reconstructing conversation flow...")
        current_role = None
        for msg in tqdm(sorted_messages, desc="Building conversation"):
            if msg['role'] != current_role:
                matched_conversations.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
                current_role = msg['role']
            else:
                # If same role appears twice in sequence, merge content
                matched_conversations[-1]['content'] += "\n\n" + msg['content']
    
    print(f"Created matched conversation with {len(matched_conversations)} messages")
    return matched_conversations

def generate_enhanced_markdown(conversations, output_file):
    """Generate a markdown file with enhanced formatting for the conversation."""
    print(f"Generating enhanced markdown file: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Lucidchart Project Chat History\n\n")
        f.write("This document contains the reconstructed chat history extracted from Cursor logs using advanced techniques.\n\n")
        
        f.write("## Extraction Method\n\n")
        f.write("The chat history was reconstructed using multiple data sources and matching algorithms to attempt to recreate the original conversation flow.\n\n")
        
        f.write("## Chat History\n\n")
        
        message_count = {'user': 0, 'assistant': 0}
        
        for i, message in tqdm(enumerate(conversations), total=len(conversations), desc="Writing conversation"):
            role = message.get('role', 'unknown')
            content = message.get('content', '').strip()
            
            if role == 'user':
                message_count['user'] += 1
                f.write(f"### Human (Message {message_count['user']}):\n\n")
                f.write(f"```\n{content}\n```\n\n")
            elif role == 'assistant':
                message_count['assistant'] += 1
                f.write(f"### LLM Response {message_count['assistant']}:\n\n")
                
                # Format code blocks properly in the assistant's response
                lines = content.split('\n')
                in_code_block = False
                formatted_lines = []
                
                for line in lines:
                    if line.strip().startswith('```'):
                        if in_code_block:
                            # End of code block
                            formatted_lines.append(line)
                            in_code_block = False
                        else:
                            # Start of code block
                            formatted_lines.append(line)
                            in_code_block = True
                    else:
                        formatted_lines.append(line)
                
                formatted_content = '\n'.join(formatted_lines)
                f.write(f"```\n{formatted_content}\n```\n\n")
                
                if i < len(conversations) - 1:  # Add separator except after the last message
                    f.write("---\n\n")
    
    print(f"Successfully generated {output_file} with {message_count['user']} human messages and {message_count['assistant']} LLM responses")

def extract_cursor_specific_data(logs_dir, max_files=None, sample_limit=None):
    """
    Extract data specific to Cursor chat interactions using targeted patterns
    """
    chat_data = []
    print(f"Searching for Cursor-specific chat data in {logs_dir}")
    
    # Collect all log files
    log_files = []
    for root, _, files in os.walk(logs_dir):
        for file in files:
            if file.endswith('.log'):
                log_files.append(os.path.join(root, file))
    
    # Apply max_files limit if specified
    if max_files and len(log_files) > max_files:
        print(f"Limiting Cursor-specific search to {max_files} of {len(log_files)} log files")
        log_files = log_files[:max_files]
    else:
        print(f"Searching through {len(log_files)} log files for Cursor chat data")
    
    # Cursor-specific patterns and keywords
    cursor_keywords = ['cursor', 'claude', 'ai chat', 'llm', 'gpt', 'anthropic']
    
    # Specifically target files that might contain relevant data
    relevant_files = []
    for log_file in tqdm(log_files, desc="Pre-filtering log files"):
        file_name = os.path.basename(log_file)
        if any(keyword in file_name.lower() for keyword in cursor_keywords):
            relevant_files.append(log_file)
            continue
            
        # Check parent directory names too
        parent_dir = os.path.basename(os.path.dirname(log_file))
        if any(keyword in parent_dir.lower() for keyword in cursor_keywords):
            relevant_files.append(log_file)
    
    print(f"Found {len(relevant_files)} potentially relevant files based on naming")
    
    # Process only the relevant files
    for log_file in tqdm(relevant_files or log_files, desc="Scanning for Cursor chat data"):
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                try:
                    content = f.read()
                    
                    # Look for specific Cursor chat patterns
                    cursor_chat_patterns = [
                        r'(human|user):\s*"(.+?)"\s+(assistant|ai|cursor):\s*"(.+?)"',
                        r'{"role"\s*:\s*"user"[^}]*"content"\s*:\s*"(.+?)"[^}]*}',
                        r'{"role"\s*:\s*"assistant"[^}]*"content"\s*:\s*"(.+?)"[^}]*}',
                        r'"prompt"\s*:\s*"(.+?)"[^}]*"response"\s*:\s*"(.+?)"',
                        r'"userMessage"\s*:\s*"(.+?)"[^}]*"aiMessage"\s*:\s*"(.+?)"',
                        r'"conversation":\s*\[(.*?)\]',
                        r'"messages":\s*\[(.*?)\]'
                    ]
                    
                    # Apply cursor-specific patterns
                    for pattern in cursor_chat_patterns:
                        try:
                            matches = list(re.finditer(pattern, content, re.DOTALL))
                            if matches:
                                tqdm.write(f"Found {len(matches)} cursor-specific matches with pattern '{pattern}' in {os.path.basename(log_file)}")
                                
                                for match in matches:
                                    try:
                                        groups = match.groups()
                                        if len(groups) == 4:  # Pattern like human: "..." assistant: "..."
                                            user_msg = groups[1]
                                            ai_msg = groups[3]
                                            
                                            if len(user_msg) > 20:
                                                chat_data.append({
                                                    'role': 'user',
                                                    'content': user_msg,
                                                    'source': f"cursor_{os.path.basename(log_file)}"
                                                })
                                            
                                            if len(ai_msg) > 20:
                                                chat_data.append({
                                                    'role': 'assistant',
                                                    'content': ai_msg,
                                                    'source': f"cursor_{os.path.basename(log_file)}"
                                                })
                                        elif len(groups) == 2:  # Patterns with two capturing groups
                                            user_msg = groups[0]
                                            ai_msg = groups[1]
                                            
                                            if len(user_msg) > 20:
                                                chat_data.append({
                                                    'role': 'user',
                                                    'content': user_msg,
                                                    'source': f"cursor_{os.path.basename(log_file)}"
                                                })
                                            
                                            if len(ai_msg) > 20:
                                                chat_data.append({
                                                    'role': 'assistant',
                                                    'content': ai_msg,
                                                    'source': f"cursor_{os.path.basename(log_file)}"
                                                })
                                        elif len(groups) == 1:  # Single group (likely a JSON array)
                                            array_content = groups[0]
                                            try:
                                                # Try to parse as JSON array
                                                if '[' not in array_content:
                                                    array_content = '[' + array_content + ']'
                                                messages = json.loads(array_content)
                                                
                                                if isinstance(messages, list):
                                                    for msg in messages:
                                                        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                                                            role = msg.get('role')
                                                            content = msg.get('content')
                                                            
                                                            if content and len(content) > 20:
                                                                chat_data.append({
                                                                    'role': role,
                                                                    'content': content,
                                                                    'source': f"cursor_json_{os.path.basename(log_file)}"
                                                                })
                                            except:
                                                # If not JSON, treat as text
                                                if len(array_content) > 50:
                                                    # Split by common role indicators
                                                    parts = re.split(r'(user:|human:|assistant:|ai:)', array_content)
                                                    for i in range(1, len(parts), 2):
                                                        role_indicator = parts[i].strip().lower()
                                                        content = parts[i+1] if i+1 < len(parts) else ""
                                                        
                                                        role = 'user' if role_indicator in ('user:', 'human:') else 'assistant'
                                                        
                                                        if content and len(content.strip()) > 20:
                                                            chat_data.append({
                                                                'role': role,
                                                                'content': content.strip(),
                                                                'source': f"cursor_text_{os.path.basename(log_file)}"
                                                            })
                                    except:
                                        pass
                        except re.error:
                            continue
                    
                    # Additional attempt to extract JSON-like objects specific to Cursor
                    cursor_json_pattern = r'(\{[^{}]*"cursor"[^{}]*\})'
                    try:
                        cursor_json_matches = re.finditer(cursor_json_pattern, content, re.DOTALL)
                        for match in cursor_json_matches:
                            try:
                                json_str = match.group(1)
                                data = json.loads(json_str)
                                
                                # Process cursor-specific JSON
                                if isinstance(data, dict) and any(key in data for key in ['prompt', 'response', 'userMessage', 'aiMessage']):
                                    # Extract user message
                                    user_msg = data.get('prompt') or data.get('userMessage') or data.get('user')
                                    if user_msg and isinstance(user_msg, str) and len(user_msg) > 20:
                                        chat_data.append({
                                            'role': 'user',
                                            'content': user_msg,
                                            'source': f"cursor_json_{os.path.basename(log_file)}"
                                        })
                                    
                                    # Extract AI response
                                    ai_msg = data.get('response') or data.get('aiMessage') or data.get('assistant')
                                    if ai_msg and isinstance(ai_msg, str) and len(ai_msg) > 20:
                                        chat_data.append({
                                            'role': 'assistant',
                                            'content': ai_msg,
                                            'source': f"cursor_json_{os.path.basename(log_file)}"
                                        })
                            except:
                                pass
                    except re.error:
                        pass
                    
                except Exception as e:
                    tqdm.write(f"Error processing content from {log_file}: {e}")
        except Exception as e:
            tqdm.write(f"Error reading log file {log_file}: {e}")
    
    print(f"Extracted {len(chat_data)} Cursor-specific chat messages")
    return chat_data

def main():
    # Ensure progress bars work properly in all terminals
    if sys.stdout.isatty():
        tqdm.write("Progress bars enabled for interactive terminal")
    else:
        print("Non-interactive terminal detected, configuring progress bars accordingly")
    
    parser = argparse.ArgumentParser(description='Advanced extraction of chat history from Cursor logs.')
    parser.add_argument('--logs-dir', help='Directory containing Cursor logs')
    parser.add_argument('--db-path', help='Path to Cursor SQLite database')
    parser.add_argument('--output', default='doc/enhanced_sessions.md', help='Output markdown file')
    parser.add_argument('--sample-limit', type=int, help='Limit the number of items processed (for testing)')
    parser.add_argument('--max-files', type=int, help='Limit the number of log files processed (for testing)')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode with reduced processing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Set sample limits for testing
    sample_limit = args.sample_limit
    max_files = args.max_files
    
    # If test mode is enabled, set reasonable defaults for testing
    if args.test_mode and not sample_limit:
        sample_limit = 5
        max_files = 3
        print(f"Test mode enabled: limiting to {sample_limit} samples and {max_files} log files")
    
    # Validation
    if not args.logs_dir and not args.db_path:
        print("Please provide either a logs directory or a database path.")
        return
    
    # Extract from database
    print("\n" + "="*60)
    print("STEP 1: DATABASE EXTRACTION")
    print("="*60)
    conversations = []
    prompts = []
    responses = []
    
    if args.db_path:
        print(f"Extracting data from database: {args.db_path}")
        # Extract prompts and responses using functions from extract_responses.py
        # For this script, these functions would need to be imported or reimplemented
        try:
            from extract_responses import extract_prompts, extract_responses
            prompts = extract_prompts(args.db_path, sample_limit)
            print(f"Extracted {len(prompts)} prompts from database.")
            
            responses = extract_responses(args.db_path, sample_limit)
            print(f"Extracted {len(responses)} responses from database.")
            
            # Also try to extract conversation history data
            print("\n" + "-"*40)
            print("Looking for conversation history tables...")
            print("-"*40)
            conv_history = extract_from_conversation_history(args.db_path, sample_limit)
            print(f"Found {len(conv_history)} potential conversation history tables.")
        except ImportError:
            print("Warning: extract_responses.py functions not available. Some extraction will be limited.")
    
    # Extract from log files
    print("\n" + "="*60)
    print("STEP 2: LOG FILE EXTRACTION")
    print("="*60)
    log_extracts = []
    cursor_extracts = []
    
    if args.logs_dir:
        print(f"Extracting data from log files in: {args.logs_dir}")
        # Extract from HTML-formatted logs
        print("\n" + "-"*40)
        print("Checking for HTML-formatted logs...")
        print("-"*40)
        html_data = extract_from_html_logs(args.logs_dir, max_files, sample_limit)
        print(f"Extracted {len(html_data)} messages from HTML-formatted logs.")
        
        # Extract from JSON-formatted logs
        print("\n" + "-"*40)
        print("Checking for JSON-formatted logs...")
        print("-"*40)
        json_data = extract_from_json_logs(args.logs_dir, max_files, sample_limit)
        print(f"Extracted {len(json_data)} messages from JSON-formatted logs.")
        
        # Use cursor-specific extraction as well
        print("\n" + "-"*40)
        print("Performing Cursor-specific extraction...")
        print("-"*40)
        cursor_extracts = extract_cursor_specific_data(args.logs_dir, max_files, sample_limit)
        print(f"Extracted {len(cursor_extracts)} messages with Cursor-specific extraction.")
        
        # Combine all log extracts
        all_extracts = html_data + json_data + cursor_extracts
        log_extracts = [msg['content'] for msg in all_extracts]
        
        # Directly add cursor extracts to organized conversations
        for extract in cursor_extracts:
            conversations.append({
                'role': extract['role'],
                'content': extract['content'],
                'source': extract['source']
            })
    
    # Match prompts with responses
    print("\n" + "="*60)
    print("STEP 3: MATCHING MESSAGES")
    print("="*60)
    matched_conversations = match_prompts_with_responses(prompts, responses, log_extracts)
    print(f"Matched {len(matched_conversations)} messages into conversation flow.")
    
    # Add cursor-specific extracts to matched conversations
    if cursor_extracts:
        print(f"Adding {len(cursor_extracts)} Cursor-specific extracts to conversation flow.")
        matched_conversations.extend(cursor_extracts)
    
    # Generate markdown
    print("\n" + "="*60)
    print("STEP 4: GENERATING OUTPUT")
    print("="*60)
    output_file = args.output
    generate_enhanced_markdown(matched_conversations, output_file)
    print(f"Enhanced extraction complete! Output saved to: {output_file}")

if __name__ == "__main__":
    main() 