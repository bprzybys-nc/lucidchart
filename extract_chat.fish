function extract_chat --description "Extract chat history from Cursor logs to markdown file"
    set current_dir (pwd)
    set script_path "$current_dir/scripts/extract_responses.py"
    set output_path "$current_dir/doc/allsessions-chathistory.md"
    
    # Create output directory if it doesn't exist
    mkdir -p "$current_dir/doc"
    
    # Color definitions
    set green "\033[0;32m"
    set blue "\033[0;34m"
    set yellow "\033[0;33m"
    set red "\033[0;31m"
    set nc "\033[0m" # No Color
    
    echo -e "$blue▶ Running Cursor Chat History Extraction$nc"
    echo -e "$blue▶ Output will be saved to:$nc $yellow$output_path$nc"
    
    # Find workspace database using cursor_locations.py
    set db_path (python3 -c "
import sys
sys.path.append('$current_dir')
from scripts.cursor_locations import find_workspace_db
db = find_workspace_db('$current_dir')
print(db if db else '')
")
    
    if test -z "$db_path"
        echo -e "$red▶ Error: Could not find Cursor database for this workspace$nc"
        echo -e "$yellow▶ Attempting to use default extraction method...$nc"
        python3 "$script_path" --output-file "$output_path"
    else
        echo -e "$green▶ Found Cursor database:$nc $db_path"
        python3 "$script_path" --db-path "$db_path" --output-file "$output_path"
    end
    
    # Check if output file was created
    if test -f "$output_path"
        set file_size (du -h "$output_path" | cut -f1)
        set line_count (wc -l < "$output_path")
        set conv_count (grep -c "^## Conversation" "$output_path")
        
        echo -e "$green▶ Extraction completed successfully!$nc"
        echo -e "$blue▶ Output file:$nc $output_path"
        echo -e "$blue▶ File size:$nc $file_size"
        echo -e "$blue▶ Line count:$nc $line_count"
        echo -e "$blue▶ Conversations extracted:$nc $conv_count"
    else
        echo -e "$red▶ Error: Failed to create output file$nc"
    end
end 