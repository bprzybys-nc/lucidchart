def extract_modern_chat_data(args, conn=None):
    """Extract data from modern chat format (messages array).
    
    Args:
        args: Command line arguments
        conn: Optional database connection
        
    Returns:
        List of conversations
    """
    print(f"Connecting to database: {args.db_path}")
    chat_conversations = []
    
    if conn is None:
        import sqlite3
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
        from tqdm import tqdm
        for key, value in tqdm(all_records, desc="Processing chat records", unit="record"):
            try:
                if not isinstance(value, str):
                    continue
                    
                import json
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
        
    return chat_conversations 