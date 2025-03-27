#!/bin/bash
# Test script for different extraction configurations

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default to medium test
TEST_MODE="medium"
OUTPUT_DIR="../doc/test_results"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --quick)
      TEST_MODE="quick"
      shift
      ;;
    --medium)
      TEST_MODE="medium"
      shift
      ;;
    --custom)
      TEST_MODE="custom"
      shift
      ;;
    --sample-limit)
      SAMPLE_LIMIT="$2"
      shift 2
      ;;
    --max-files)
      MAX_FILES="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Set test parameters based on mode
if [ "$TEST_MODE" = "quick" ]; then
  SAMPLE_LIMIT=5
  MAX_FILES=5
  OUTPUT_DIR="${OUTPUT_DIR}/quick"
  echo -e "${YELLOW}Running QUICK test with ${SAMPLE_LIMIT} samples and ${MAX_FILES} files${NC}"
elif [ "$TEST_MODE" = "medium" ]; then
  SAMPLE_LIMIT=20
  MAX_FILES=50
  OUTPUT_DIR="${OUTPUT_DIR}/medium"
  echo -e "${YELLOW}Running MEDIUM test with ${SAMPLE_LIMIT} samples and ${MAX_FILES} files${NC}"
elif [ "$TEST_MODE" = "custom" ]; then
  # Custom uses the provided sample limit and max files
  if [ -z "$SAMPLE_LIMIT" ]; then
    SAMPLE_LIMIT=10
  fi
  if [ -z "$MAX_FILES" ]; then
    MAX_FILES=20
  fi
  OUTPUT_DIR="${OUTPUT_DIR}/custom"
  echo -e "${YELLOW}Running CUSTOM test with ${SAMPLE_LIMIT} samples and ${MAX_FILES} files${NC}"
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run the extraction with parameters
echo -e "${CYAN}==================================================================${NC}"
echo -e "${CYAN}         CURSOR CHAT EXTRACTION TEST                              ${NC}"
echo -e "${CYAN}==================================================================${NC}"
echo -e "Starting test run at $(date)"
echo -e "Output directory: ${BLUE}$OUTPUT_DIR${NC}"
echo -e "Sample limit: ${BLUE}$SAMPLE_LIMIT${NC}"
echo -e "Max files: ${BLUE}$MAX_FILES${NC}"

# Launch the extraction script with the appropriate settings
./extract_chat_history.sh --sample-limit "$SAMPLE_LIMIT" --max-files "$MAX_FILES" --output-dir "$OUTPUT_DIR"

# Check extraction results
RESULT_FILE="$OUTPUT_DIR/complete_sessions.md"
if [ -f "$RESULT_FILE" ]; then
  LINE_COUNT=$(wc -l < "$RESULT_FILE")
  HUMAN_COUNT=$(grep -c "Human (Message" "$RESULT_FILE")
  LLM_COUNT=$(grep -c "LLM Response" "$RESULT_FILE")
  
  echo -e "\n${CYAN}==================================================================${NC}"
  echo -e "${CYAN}         TEST RESULTS                                             ${NC}"
  echo -e "${CYAN}==================================================================${NC}"
  echo -e "Test completed at $(date)"
  echo -e "Output file: ${BLUE}$RESULT_FILE${NC}"
  echo -e "File size: ${BLUE}$(ls -lh "$RESULT_FILE" | awk '{print $5}')${NC}"
  echo -e "Line count: ${BLUE}$LINE_COUNT${NC}"
  echo -e "Human messages: ${BLUE}$HUMAN_COUNT${NC}"
  echo -e "LLM responses: ${BLUE}$LLM_COUNT${NC}"
  
  if [ "$HUMAN_COUNT" -eq 0 ] && [ "$LLM_COUNT" -eq 0 ]; then
    echo -e "${RED}No messages extracted. Test failed.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}Test completed successfully.${NC}"
  exit 0
else
  echo -e "${RED}Output file not found. Test failed.${NC}"
  exit 1
fi 