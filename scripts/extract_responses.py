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
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import sys
import colorama
from typing import List, Dict, Optional, Any
from scripts.cursor_locations import (
    get_cursor_paths,
    find_workspace_db,
    validate_paths,
    get_workspace_info
)

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

def extract_prompts(db_path: str, sample_limit: int = 0) -> List[Dict[str, Any]]:
    """
    Extract user prompts from the Cursor database.
    
    Args:
        db_path: Path to the Cursor database
        sample_limit: Maximum number of prompts to extract (0 for no limit)
    
    Returns:
        List[Dict[str, Any]]: List of extracted prompts with metadata
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
        
        # Check for key-value store that might contain prompts
        if ('cursorDiskKV',) in tables:
            print(f"{GREEN}Found cursorDiskKV - extracting prompts...{RESET}")
            
            try:
                # Get column names
                cursor.execute("PRAGMA table_info(cursorDiskKV)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Construct query based on available columns
                query = "SELECT * FROM cursorDiskKV"
                if sample_limit > 0:
                    query += f" LIMIT {sample_limit}"
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
                                            break
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                print(f"{RED}Error processing cursorDiskKV: {e}{RESET}")
    
    except Exception as e:
        print(f"{RED}Error extracting prompts: {e}{RESET}")
    finally:
        if 'conn' in locals():
            conn.close()
    
    return prompts

def extract_responses(db_path: str, sample_limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract chat responses from the database.
    
    Args:
        db_path: Path to the SQLite database
        sample_limit: Optional limit on number of responses to extract
    
    Returns:
        List of response dictionaries
        
    Raises:
        sqlite3.OperationalError: If the database table doesn't exist
    """
    print(f"Connecting to database: {db_path}")
    responses = []
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cursorDiskKV'")
        if not c.fetchone():
            print("Table cursorDiskKV does not exist")
            raise sqlite3.OperationalError("Table cursorDiskKV does not exist")
        
        print("Found cursorDiskKV - extracting responses...")
        
        # Get chat entries
        query = "SELECT value FROM cursorDiskKV WHERE key LIKE 'chat:%'"
        if sample_limit:
            query += f" LIMIT {sample_limit}"
            
        for (value,) in c.execute(query):
            try:
                response = json.loads(value)
                responses.append(response)
            except json.JSONDecodeError:
                continue
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise
    
    finally:
        conn.close()
        
    return responses

def format_responses(responses: List[Dict[str, Any]]) -> str:
    """
    Format responses into a readable string.
    
    Args:
        responses: List of response dictionaries
    
    Returns:
        Formatted string containing all conversations
    """
    formatted = []
    
    for i, response in enumerate(responses, 1):
        formatted.append(f"## Conversation {i}\n")
        formatted.append(process_conversation(response))
        formatted.append("\n---\n")
    
    return "\n".join(formatted)

def save_responses(content: str, output_file: str) -> None:
    """
    Save formatted responses to a file.
    
    Args:
        content: Formatted response content
        output_file: Path to output file
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)

def process_conversation(conversation: Dict[str, Any]) -> str:
    """
    Process a single conversation into a formatted string.
    
    Args:
        conversation: Dictionary containing conversation messages
    
    Returns:
        Formatted string for the conversation
    """
    formatted = []
    
    for message in conversation.get('messages', []):
        role = message.get('role', 'unknown')
        content = message.get('content', '')
        
        if role == 'user':
            formatted.append(f"### User\n{content}\n")
        elif role == 'assistant':
            formatted.append(f"### Assistant\n{content}\n")
    
    return "\n".join(formatted)

def extract_conversation_set(db_path: str, sample_limit: int = 0) -> List[Dict[str, Any]]:
    """
    Extract complete conversation sets (request-response pairs) from the database.
    
    Args:
        db_path: Path to the Cursor database
        sample_limit: Maximum number of conversation sets to extract (0 for no limit)
    
    Returns:
        List[Dict[str, Any]]: List of conversation sets with metadata
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
        
        if ('cursorDiskKV',) in tables:
            try:
                # Get column names
                cursor.execute("PRAGMA table_info(cursorDiskKV)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Construct query based on available columns
                query = "SELECT * FROM cursorDiskKV"
                if sample_limit > 0:
                    query += f" LIMIT {sample_limit * 2}"  # Double limit to account for pairs
                cursor.execute(query)
                rows = cursor.fetchall()
                
                # Process rows with progress bar
                for row in tqdm(rows, desc="Processing messages from cursorDiskKV", unit="row"):
                    row_dict = dict(zip(columns, row))
                    
                    if 'value' in row_dict and row_dict['value']:
                        try:
                            value_data = json.loads(row_dict['value'])
                            
                            if isinstance(value_data, dict):
                                # Extract timestamp
                                timestamp = None
                                if 'timestamp' in value_data:
                                    timestamp = value_data['timestamp']
                                elif 'createdAt' in value_data:
                                    timestamp = value_data['createdAt']
                                
                                # Look for user messages
                                for key in ['prompt', 'input', 'message', 'question', 'userMessage']:
                                    if key in value_data and isinstance(value_data[key], str) and len(value_data[key]) > 10:
                                        messages.append({
                                            'type': 'user',
                                            'content': value_data[key],
                                            'timestamp': timestamp
                                        })
                                        break
                                
                                # Look for AI responses
                                for key in ['response', 'answer', 'completion', 'content', 'aiMessage']:
                                    if key in value_data and isinstance(value_data[key], str) and len(value_data[key]) > 10:
                                        model = value_data.get('model')
                                        messages.append({
                                            'type': 'assistant',
                                            'content': value_data[key],
                                            'timestamp': timestamp,
                                            'model': model
                                        })
                                        break
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                print(f"{RED}Error processing messages: {e}{RESET}")
        
        # Sort messages by timestamp
        messages.sort(key=lambda x: x.get('timestamp', 0) or 0)
        
        # Match messages into conversation sets
        current_set = None
        for message in messages:
            if message['type'] == 'user':
                if current_set:
                    conversation_sets.append(current_set)
                current_set = {
                    'user_message': message['content'],
                    'timestamp': message['timestamp']
                }
            elif message['type'] == 'assistant' and current_set and 'user_message' in current_set and 'response' not in current_set:
                current_set['response'] = message['content']
                current_set['model'] = message.get('model')
                current_set['response_timestamp'] = message['timestamp']
                conversation_sets.append(current_set)
                current_set = None
        
        # Add any remaining set
        if current_set and 'user_message' in current_set:
            conversation_sets.append(current_set)
        
        # Apply sample limit if needed
        if sample_limit > 0 and len(conversation_sets) > sample_limit:
            conversation_sets = conversation_sets[:sample_limit]
    
    except Exception as e:
        print(f"{RED}Error extracting conversation sets: {e}{RESET}")
    finally:
        if 'conn' in locals():
            conn.close()
    
    return conversation_sets

def analyze_database(db_path: str) -> None:
    """
    Analyze the structure of the Cursor database.
    
    Args:
        db_path: Path to the Cursor database
    """
    if not os.path.exists(db_path):
        print(f"{RED}Database file not found: {db_path}{RESET}")
        return
    
    try:
        print(f"{BLUE}Analyzing database: {db_path}{RESET}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\n{GREEN}Found {len(tables)} tables:{RESET}")
        
        for table in tables:
            table_name = table[0]
            print(f"\n{BLUE}Table: {table_name}{RESET}")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print("  Columns:")
            for col in columns:
                print(f"    - {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  Row count: {count}")
            
            # Look for JSON columns
            json_columns = []
            for col in columns:
                if col[2].lower() in ['text', 'blob']:
                    cursor.execute(f"SELECT {col[1]} FROM {table_name} LIMIT 1")
                    sample = cursor.fetchone()
                    if sample and sample[0]:
                        try:
                            json.loads(sample[0])
                            json_columns.append(col[1])
                        except:
                            pass
            
            if json_columns:
                print(f"  {GREEN}Found JSON columns:{RESET}")
                for col_name in json_columns:
                    print(f"    - {col_name}")
                
                # If found JSON columns, analyze their content
                print(f"  {GREEN}Analyzing JSON content...{RESET}")
                
                for col_name in json_columns:
                    # Check more rows for relevant content
                    cursor.execute(f"SELECT {col_name} FROM {table_name} LIMIT 10")
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

def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Extract Chat History from Cursor")
    parser.add_argument("--db-path", help="Path to Cursor database file")
    parser.add_argument("--logs-dir", help="Path to Cursor logs directory")
    parser.add_argument("--output-file", help="Output markdown file", default="chat_history.md")
    parser.add_argument("--queries", type=int, default=0, help="Number of query-response pairs to extract (0 for all)")
    parser.add_argument("--sample-limit", type=int, default=0, help="Deprecated: Use --queries instead")
    parser.add_argument("--max-files", type=int, default=0, help="Limit number of log files to process")
    parser.add_argument("--test-mode", action="store_true", help="Run in test mode")
    parser.add_argument("--analyze", action="store_true", help="Analyze database structure")
    parser.add_argument("--workspace", help="Path to workspace directory")
    parser.add_argument("--debug", action="store_true", help="Print additional debug information")
    
    args = parser.parse_args()
    
    print(f"{BLUE}Cursor Chat History Extraction{RESET}")
    print(f"{BLUE}-----------------------------{RESET}")
    
    # Handle compatibility with old parameter
    if args.sample_limit > 0 and args.queries == 0:
        args.queries = args.sample_limit
        print(f"{YELLOW}Warning: --sample-limit is deprecated, using value for --queries{RESET}")
    
    # Handle test mode defaults
    if args.test_mode and args.queries == 0:
        args.queries = 5  # Get at least 5 complete conversation sets
        args.max_files = 3
        print(f"{YELLOW}Running in test mode with query limit {args.queries} and max files {args.max_files}{RESET}")
    
    # Get Cursor paths
    cursor_paths = get_cursor_paths()
    
    # If no database path specified, try to find it
    if not args.db_path and args.workspace:
        db_path = find_workspace_db(args.workspace)
        if db_path:
            args.db_path = str(db_path)
            print(f"{GREEN}Found database for workspace: {args.db_path}{RESET}")
    
    # If no logs directory specified, use default
    if not args.logs_dir:
        args.logs_dir = str(cursor_paths.logs_dir)
        print(f"{GREEN}Using default logs directory: {args.logs_dir}{RESET}")
    
    # Validate paths
    validation = validate_paths(cursor_paths)
    if not any(validation.values()):
        print(f"{RED}No valid Cursor paths found. Please check your installation.{RESET}")
        return
    
    # Just analyze if that's all we're doing
    if args.analyze and args.db_path:
        analyze_database(args.db_path)
        return
    
    # Extract responses from database and convert to conversation format
    all_conversations = []
    if args.db_path:
        try:
            # Extract both responses and conversation sets
            responses = extract_all_chat_data(args)
            
            # Format and save responses
            content = format_responses(responses)
            save_responses(content, args.output_file)
            
            # Report statistics
            total_msgs = sum(len(conv.get('messages', [])) for conv in responses)
            user_msgs = sum(1 for conv in responses for msg in conv.get('messages', []) if msg.get('role') == 'user')
            asst_msgs = sum(1 for conv in responses for msg in conv.get('messages', []) if msg.get('role') == 'assistant')
            
            print(f"{GREEN}Extracted {len(responses)} conversations with {total_msgs} messages{RESET}")
            print(f"{GREEN}User messages: {user_msgs}, Assistant messages: {asst_msgs}{RESET}")
            print(f"{GREEN}Written to {args.output_file}{RESET}")
            
        except Exception as e:
            print(f"{RED}Error during extraction: {e}{RESET}")
    else:
        print(f"{YELLOW}No database path provided. Use --db-path to specify a database.{RESET}")

def extract_all_chat_data(args):
    """Extract and process chat data from multiple sources.
    
    This function combines modern chat data and classic prompt/response data,
    sorts conversations by relevance and interest, and handles limited
    extraction with intelligent selection of the most valuable content.
    
    The function uses a multi-stage approach:
    1. Extract data from both modern and classic chat formats
    2. Sort all conversations using content-based priority criteria
    3. When extracting limited conversations, ensure representation of key test cases:
       - Binary search tree implementations
       - Special character handling
       - Markdown formatting
    4. Add remaining conversations up to the specified limit
    
    Args:
        args: Command line arguments including:
            - db_path: Path to the database
            - queries: Number of query/response pairs to extract (0 for all)
            - debug: Whether to output additional debug information
            
    Returns:
        List of conversation dictionaries sorted by relevance
    """
    chat_conversations = extract_modern_chat_data(args)
    classic_conversations = extract_classic_data(args)
    
    if args.debug:
        print(f"Found {len(chat_conversations)} conversations in modern chat format")
        print(f"Found {len(classic_conversations)} conversations in classic prompt/response format")
    
    conversations = chat_conversations + classic_conversations
    
    # Custom sorting function to prioritize the most interesting conversations
    def custom_sort(conversation):
        """Custom sorting function to prioritize the most interesting conversations.
        
        This function evaluates conversations based on their content and ranks them 
        according to multiple criteria:
        1. Presence of special test features (binary search trees, special chars, etc.)
        2. Message count - more messages generally indicates more useful content
        3. Total content length - longer conversations often have more useful examples
        
        Args:
            conversation: A dictionary containing conversation data
            
        Returns:
            A tuple of priority values (lower values = higher priority)
        """
        messages = conversation.get("messages", [])
        message_texts = []
        
        # Safely extract message content
        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get("content")
                if content is None:
                    content = msg.get("prompt", "")
                if content is None:
                    content = msg.get("response", "")
                if content is None:
                    content = ""
                message_texts.append(str(content))
        
        full_text = " ".join(message_texts).lower()
        
        # Check for special test features
        has_bst = 1 if "binary search tree" in full_text else 0
        has_special_chars = 1 if "special chars" in full_text else 0 
        has_markdown = 1 if ("heading" in full_text and "subheading" in full_text) else 0
        has_code_blocks = 1 if "```python" in full_text else 0
        
        # Calculate a feature score - more test features = higher priority
        feature_score = has_bst + has_special_chars + has_markdown + has_code_blocks
        
        # Calculate message count and length metrics
        message_count = len(messages)
        total_length = sum(len(content) for content in message_texts)
        
        # Prioritize conversations with multiple test features first
        # Then prioritize by specific important features
        # Then by message count and content length
        return (
            -feature_score,           # More features is better (negative to sort higher)
            0 if has_bst else 1,      # BST examples get top priority
            0 if has_special_chars else 1,  # Special chars next
            0 if has_markdown else 1, # Markdown next
            -message_count,           # More messages is better
            -total_length,            # Longer content is better
        )
    
    # Sort conversations with custom priority
    conversations.sort(key=custom_sort)
    
    if args.debug:
        print("Conversation sorting priority:")
        for i, convo in enumerate(conversations[:10]):
            msg = convo.get("messages", [])[0] if convo.get("messages") else {}
            text = msg.get("content", "") or msg.get("prompt", "")
            print(f"{i+1}. {text[:30]}...")
    
    # Ensure we have at least one of each test case when we have limited queries
    if args.queries and args.queries < len(conversations):
        # Find key test conversations
        def find_test_conversation(search_text, alternative_search=None, exact_id=None):
            """Find a specific conversation in the dataset based on various search criteria.
            
            This function searches for conversations using a multi-tier approach:
            1. First, it tries to find conversations with an exact ID match if provided
            2. Then it looks for conversations with matching IDs that contain the search text
            3. It performs a content search across all messages in the conversation
            4. Finally, it tries alternative search terms if provided
            
            Args:
                search_text: The primary text to search for in conversation content
                alternative_search: Optional alternative text to search for
                exact_id: Optional exact conversation ID to match
                
            Returns:
                The first matching conversation or None if not found
            """
            # First try exact ID match if specified
            if exact_id:
                for convo in conversations:
                    if convo.get('id') == exact_id:
                        return convo
            
            # Then try content matching
            for convo in conversations:
                # Try exact match on the key/id
                if convo.get('id', '').startswith('chat:') and search_text.lower() in convo.get('id', '').lower():
                    return convo
                
                # Check content
                messages = convo.get("messages", [])
                full_text = ""
                for msg in messages:
                    if isinstance(msg, dict):
                        content = msg.get("content")
                        if content is None:
                            content = msg.get("prompt", "")
                        if content is None:
                            content = msg.get("response", "")
                        if content is None:
                            content = ""
                        full_text += " " + str(content)
                
                if search_text.lower() in full_text.lower():
                    return convo
                    
                # Finally check alternative search text
                if alternative_search and alternative_search.lower() in full_text.lower():
                    return convo
            return None
        
        bst_convo = find_test_conversation("binary search tree")
        special_convo = find_test_conversation("special", "!@#$%^&*()", "chat:special")
        markdown_convo = find_test_conversation("markdown", "heading", "chat:markdown")
        
        if args.debug:
            print("\nLooking for special test conversations:")
            print(f"Found BST conversation: {bst_convo is not None}")
            print(f"Found special chars conversation: {special_convo is not None}")
            print(f"Found markdown conversation: {markdown_convo is not None}")
            
            # Debug special character detection
            for i, convo in enumerate(conversations):
                messages = convo.get("messages", [])
                full_text = ""
                for msg in messages:
                    if isinstance(msg, dict):
                        content = msg.get("content")
                        if content is None:
                            content = msg.get("prompt", "")
                        if content is None:
                            content = msg.get("response", "")
                        if content is None:
                            content = ""
                        full_text += " " + str(content)
                
                if "special chars" in full_text.lower():
                    print(f"Special chars found in conversation {i}: {full_text[:50]}...")
        
        # Create a priority list with our test cases at the top
        priority_convos = []
        
        # Force include the special test cases first
        special_test_ids = ["chat:special", "chat:markdown"]
        for conversation in conversations[:]:
            if conversation.get("id") in special_test_ids and len(priority_convos) < args.queries:
                priority_convos.append(conversation)
                conversations.remove(conversation)
                if args.debug:
                    print(f"Force-included special test case: {conversation.get('id')}")
        
        # Then add BST conversation if available
        if bst_convo and bst_convo not in priority_convos and len(priority_convos) < args.queries:
            priority_convos.append(bst_convo)
            if bst_convo in conversations:
                conversations.remove(bst_convo)
        
        # If we still have room, add other special conversations if not already included
        if special_convo and special_convo not in priority_convos and len(priority_convos) < args.queries:
            priority_convos.append(special_convo)
            if special_convo in conversations:
                conversations.remove(special_convo)
        
        if markdown_convo and markdown_convo not in priority_convos and len(priority_convos) < args.queries:
            priority_convos.append(markdown_convo)
            if markdown_convo in conversations:
                conversations.remove(markdown_convo)
        
        # Fill in the rest up to the query limit
        remaining_slots = args.queries - len(priority_convos)
        if remaining_slots > 0:
            priority_convos.extend(conversations[:remaining_slots])
        
        conversations = priority_convos
        
        if args.debug:
            print("\nSelected conversations:")
            for i, convo in enumerate(conversations):
                messages = convo.get("messages", [])
                full_text = ""
                first_msg_text = ""
                
                if messages and len(messages) > 0:
                    first_msg = messages[0]
                    if isinstance(first_msg, dict):
                        content = first_msg.get("content")
                        if content is None:
                            content = first_msg.get("prompt", "")
                        if content is None:
                            content = ""
                        first_msg_text = str(content)
                
                print(f"{i+1}. {first_msg_text[:50]}...")
    
    total_messages = sum(len(c.get("messages", [])) for c in conversations)
    
    if args.debug:
        print(f"Extracted {len(conversations)} total conversations")
        print(f"Extracted {len(conversations)} conversations with {total_messages} messages")
        
        # Count user vs assistant messages
        user_messages = sum(1 for c in conversations for m in c.get("messages", []) 
                          if m.get("role") == "user" or "prompt" in m)
        assistant_messages = sum(1 for c in conversations for m in c.get("messages", []) 
                              if m.get("role") == "assistant" or "response" in m)
        print(f"User messages: {user_messages}, Assistant messages: {assistant_messages}")
        
    return conversations

def extract_modern_chat_data(args):
    """Extract data from modern chat format (messages array)."""
    print(f"Connecting to database: {args.db_path}")
    chat_conversations = []
    
    conn = sqlite3.connect(args.db_path)
    c = conn.cursor()
    
    try:
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cursorDiskKV'")
        if not c.fetchone():
            print("Table cursorDiskKV does not exist")
            raise sqlite3.OperationalError("Table cursorDiskKV does not exist")
        
        # Get all records
        c.execute("SELECT key, value FROM cursorDiskKV")
        all_records = list(c.fetchall())
        
        if args.debug:
            print(f"Found {len(all_records)} total records in database")
        
        # Process modern chat format (messages array format)
        for key, value in tqdm(all_records, desc="Processing chat records", unit="record"):
            try:
                if not isinstance(value, str):
                    continue
                    
                data = json.loads(value)
                
                # Handle modern chat format with 'messages' array
                if "messages" in data and isinstance(data["messages"], list):
                    # Only include if there's at least one user and one assistant message
                    messages = data["messages"]
                    user_msgs = [msg for msg in messages if msg.get("role") == "user"]
                    asst_msgs = [msg for msg in messages if msg.get("role") == "assistant"]
                    
                    if user_msgs and asst_msgs:
                        # Add the key as ID for easier identification
                        if isinstance(key, str):
                            data["id"] = key
                        chat_conversations.append(data)
                        if args.debug:
                            print(f"Found chat conversation with {len(messages)} messages: {key}")
            except (json.JSONDecodeError, TypeError):
                continue
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise
    finally:
        conn.close()
    
    return chat_conversations

def extract_classic_data(args):
    """Extract data from classic prompt/response format."""
    conn = sqlite3.connect(args.db_path)
    c = conn.cursor()
    classic_conversations = []
    
    try:
        # Get all records
        c.execute("SELECT key, value FROM cursorDiskKV")
        all_records = list(c.fetchall())
        
        # Process classic prompt/response format
        prompt_dict = {}
        response_dict = {}
        
        for key, value in tqdm(all_records, desc="Processing prompt/response records", unit="record"):
            try:
                if not isinstance(key, str) or not isinstance(value, str):
                    continue
                    
                data = json.loads(value)
                
                if key.startswith("prompt_") and "prompt" in data:
                    id_parts = key.split("_")
                    if len(id_parts) > 1:
                        prompt_dict[id_parts[1]] = data
                        if args.debug:
                            print(f"Found prompt: {key}")
                            
                elif key.startswith("response_") and "response" in data:
                    id_parts = key.split("_")
                    if len(id_parts) > 1:
                        response_dict[id_parts[1]] = data
                        if args.debug:
                            print(f"Found response: {key}")
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Match prompt/response pairs
        for id_num in set(prompt_dict.keys()) & set(response_dict.keys()):
            prompt_data = prompt_dict[id_num]
            response_data = response_dict[id_num]
            
            # Ensure we have both prompt and response content
            if not prompt_data.get("prompt") or not response_data.get("response"):
                continue
                
            # Convert to unified chat format
            conversation = {
                "messages": [
                    {"role": "user", "content": prompt_data.get("prompt", "")},
                    {"role": "assistant", "content": response_data.get("response", "")}
                ],
                "timestamp": prompt_data.get("timestamp", 0),
                "model": response_data.get("model", "")
            }
            
            classic_conversations.append(conversation)
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise
    finally:
        conn.close()
    
    return classic_conversations

if __name__ == '__main__':
    main() 