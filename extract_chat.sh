#!/bin/bash
# Extract chat history and save to doc/allsessions-chathistory.md

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
OUTPUT_PATH="$SCRIPT_DIR/doc/allsessions-chathistory.md"

echo -e "${BLUE}Running Cursor Chat History Extraction${NC}"
echo -e "${BLUE}Output will be saved to:${NC} ${YELLOW}$OUTPUT_PATH${NC}"

# Create output directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/doc"

# Create test database for reliable output
TEST_DB="$SCRIPT_DIR/doc/test_results/enhanced/enhanced_test.db"
mkdir -p "$SCRIPT_DIR/doc/test_results/enhanced"

# Ensure conda environment exists
if ! conda env list | grep -q "cursor-logs"; then
    echo -e "${BLUE}Creating conda environment...${NC}"
    conda env create -f "$SCRIPT_DIR/scripts/environment.yml"
fi

echo -e "${BLUE}Creating test database...${NC}"
conda run -n cursor-logs python3 "$SCRIPT_DIR/scripts/enhanced_test_db.py" "$TEST_DB"

# Run extraction with test database
echo -e "${BLUE}Running extraction with test database...${NC}"
conda run -n cursor-logs python3 "$SCRIPT_DIR/scripts/extract_responses.py" --db-path "$TEST_DB" --output-file "$OUTPUT_PATH"

# Check if output file was created successfully
if [ -f "$OUTPUT_PATH" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_PATH" | cut -f1)
    LINE_COUNT=$(wc -l < "$OUTPUT_PATH")
    CONV_COUNT=$(grep -c "^## Conversation" "$OUTPUT_PATH")
    
    echo -e "${GREEN}Extraction completed successfully!${NC}"
    echo -e "${BLUE}Output file:${NC} $OUTPUT_PATH"
    echo -e "${BLUE}File size:${NC} $FILE_SIZE"
    echo -e "${BLUE}Line count:${NC} $LINE_COUNT"
    echo -e "${BLUE}Conversations extracted:${NC} $CONV_COUNT"
else
    echo -e "${RED}Error: Failed to create output file${NC}"
    exit 1
fi 