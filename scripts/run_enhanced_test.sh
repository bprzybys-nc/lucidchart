#!/bin/bash
# Test script for enhanced extraction test with challenging test cases

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Set up output directory
OUTPUT_DIR="../doc/test_results/enhanced"
mkdir -p "$OUTPUT_DIR"

# Create enhanced test database
TEST_DB="$OUTPUT_DIR/enhanced_test.db"
echo -e "${BLUE}Creating enhanced test database: ${TEST_DB}${NC}"

# Run the enhanced test database creation script
PYTHONPATH="$PROJECT_ROOT" python3 "$SCRIPT_DIR/enhanced_test_db.py" "$TEST_DB"

# Run the extraction with the enhanced test data
echo -e "${CYAN}==================================================================${NC}"
echo -e "${CYAN}       ENHANCED CURSOR CHAT EXTRACTION TEST                       ${NC}"
echo -e "${CYAN}==================================================================${NC}"
echo -e "Starting enhanced test run at $(date)"
echo -e "Output directory: ${BLUE}$OUTPUT_DIR${NC}"

# Extract with various configurations to test different aspects
echo -e "${YELLOW}Testing default extraction mode:${NC}"
PYTHONPATH="$PROJECT_ROOT" python3 "$SCRIPT_DIR/extract_responses.py" --db-path "$TEST_DB" --output-file "$OUTPUT_DIR/default_output.md" --debug

echo -e "${YELLOW}Testing limited query extraction:${NC}"
PYTHONPATH="$PROJECT_ROOT" python3 "$SCRIPT_DIR/extract_responses.py" --db-path "$TEST_DB" --output-file "$OUTPUT_DIR/limited_output.md" --queries 5 --debug

# Check extraction results
for FILE in "$OUTPUT_DIR/default_output.md" "$OUTPUT_DIR/limited_output.md"; do
  if [ -f "$FILE" ]; then
    # Count actual conversation elements
    CONV_COUNT=$(grep -c "^## Conversation" "$FILE")
    USER_COUNT=$(grep -c "### User" "$FILE")
    LLM_COUNT=$(grep -c "### Assistant" "$FILE")
    
    echo -e "\n${CYAN}==================================================================${NC}"
    echo -e "${CYAN}         TEST RESULTS: $(basename "$FILE")                        ${NC}"
    echo -e "${CYAN}==================================================================${NC}"
    echo -e "Test completed at $(date)"
    echo -e "Output file: ${BLUE}$FILE${NC}"
    echo -e "File size: ${BLUE}$(ls -lh "$FILE" | awk '{print $5}')${NC}"
    echo -e "Number of conversations: ${BLUE}$CONV_COUNT${NC}"
    echo -e "User messages: ${BLUE}$USER_COUNT${NC}"
    echo -e "Assistant responses: ${BLUE}$LLM_COUNT${NC}"
    
    # Check for special test cases
    echo -e "\n${YELLOW}Checking for supported features:${NC}"
    
    # Check for binary search tree content
    if grep -q "binary search tree" "$FILE"; then
      echo -e "${GREEN}✓ Chat format extracted correctly${NC}"
      CHAT_FORMAT_SUPPORTED=1
    else
      echo -e "${YELLOW}? Chat format not found in this file${NC}"
      CHAT_FORMAT_SUPPORTED=0
    fi
    
    # Check for special characters
    if grep -q "Special chars: \\!@#" "$FILE" || grep -q "More special chars:" "$FILE"; then
      echo -e "${GREEN}✓ Special characters handled correctly${NC}"
      SPECIAL_CHARS_SUPPORTED=1
    else
      echo -e "${YELLOW}? Special characters not found in this file${NC}"
      SPECIAL_CHARS_SUPPORTED=0
    fi
    
    # Check for markdown
    if grep -q "Heading" "$FILE" && grep -q "Subheading" "$FILE"; then
      echo -e "${GREEN}✓ Markdown formatting preserved${NC}"
      MARKDOWN_SUPPORTED=1
    else
      echo -e "${YELLOW}? Markdown formatting not found in this file${NC}"
      MARKDOWN_SUPPORTED=0
    fi
    
    # Check for code blocks
    if grep -q '```python' "$FILE"; then
      echo -e "${GREEN}✓ Code blocks preserved${NC}"
      CODE_BLOCKS_SUPPORTED=1
    else
      echo -e "${YELLOW}? Code blocks not found in this file${NC}"
      CODE_BLOCKS_SUPPORTED=0
    fi
    
    # If limited output, only check for binary search tree which should be prioritized
    if [[ "$FILE" == *"limited_output.md" ]]; then
      if [ $CHAT_FORMAT_SUPPORTED -eq 1 ]; then
        echo -e "${GREEN}✓ Limited output correctly prioritized important content${NC}"
      else
        echo -e "${RED}✗ Limited output failed to prioritize important content${NC}"
      fi
    # For full output, check that all features are supported
    else
      TOTAL_FEATURES=$(($CHAT_FORMAT_SUPPORTED + $SPECIAL_CHARS_SUPPORTED + $MARKDOWN_SUPPORTED + $CODE_BLOCKS_SUPPORTED))
      if [ $TOTAL_FEATURES -eq 4 ]; then
        echo -e "${GREEN}✓ Full output supports all test features${NC}"
      else
        echo -e "${RED}✗ Full output missing some test features ($TOTAL_FEATURES/4)${NC}"
      fi
    fi
    
    # Verify query/response pairs
    if [ "$USER_COUNT" -eq "$LLM_COUNT" ] && [ "$USER_COUNT" -gt 0 ]; then
      echo -e "${GREEN}✓ Balanced query/response pairs: $USER_COUNT pairs extracted${NC}"
    else
      echo -e "${RED}✗ Unbalanced query/response pairs: $USER_COUNT user messages, $LLM_COUNT assistant responses${NC}"
    fi
    
    # Check if limited version has correct count
    if [[ "$FILE" == *"limited_output.md" ]] && [ "$CONV_COUNT" -eq 5 ]; then
      echo -e "${GREEN}✓ Query limit correctly applied${NC}"
    elif [[ "$FILE" == *"limited_output.md" ]]; then
      echo -e "${RED}✗ Query limit not correctly applied: expected 5 conversations, got $CONV_COUNT${NC}"
    fi
    
    # Overall test result
    if [ "$USER_COUNT" -gt 0 ] && [ "$LLM_COUNT" -gt 0 ]; then
      echo -e "\n${GREEN}Test completed successfully.${NC}"
    else
      echo -e "\n${RED}Test failed: No complete conversations extracted.${NC}"
    fi
  else
    echo -e "${RED}Output file not found: $FILE. Test failed.${NC}"
  fi
done 