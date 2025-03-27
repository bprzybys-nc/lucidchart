#!/bin/bash
# Comprehensive script to extract Cursor IDE chat history
# This script provides various options for testing and full extraction

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Initialize variables
QUICK_TEST=false
MEDIUM_TEST=false
TEST_MODE=false
CUSTOM_TEST=false
EXAMPLES_ONLY=false
FORCE_EXAMPLE=false
EXAMPLE_GENERATED=false
NO_EXAMPLES=true  # Default to not generating examples

# Default values
SAMPLE_LIMIT=0
MAX_FILES=0
OUTPUT_DIR="../doc"

# Function to check if conda is available
check_conda() {
    if ! command -v conda &> /dev/null; then
        echo -e "${RED}Error: conda is not installed or not in PATH${NC}"
        return 1
    fi
    return 0
}

# Function to check if environment exists
check_env() {
    if ! conda env list | grep -q "cursor-logs"; then
        echo -e "${YELLOW}Warning: cursor-logs environment not found${NC}"
        echo -e "${BLUE}Creating cursor-logs environment...${NC}"
        conda create -n cursor-logs python=3.9 -y
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to create cursor-logs environment${NC}"
            return 1
        fi
    fi
    return 0
}

# Function to activate environment
activate_env() {
    echo -e "${BLUE}Activating cursor-logs environment...${NC}"
    eval "$(conda shell.bash hook)"
    conda activate cursor-logs
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to activate cursor-logs environment${NC}"
        return 1
    fi
    return 0
}

# Function to check Python dependencies
check_dependencies() {
    echo -e "${BLUE}Checking Python dependencies...${NC}"
    python -c "import sqlite3, json, tqdm" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Installing required Python packages...${NC}"
        pip install tqdm
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install dependencies${NC}"
            return 1
        fi
    fi
    return 0
}

# Function to find database path
find_db_path() {
    local os_type=$(uname)
    local home_dir=$HOME
    local db_path=""
    
    case $os_type in
        "Darwin")  # macOS
            db_path="$home_dir/Library/Application Support/Cursor/User/workspaceStorage"
            ;;
        "Linux")
            db_path="$home_dir/.config/Cursor/User/workspaceStorage"
            ;;
        *)
            echo -e "${RED}Unsupported operating system: $os_type${NC}"
            return 1
            ;;
    esac
    
    if [ -d "$db_path" ]; then
        # Find the most recently modified state.vscdb file
        local latest_db=$(find "$db_path" -name "state.vscdb" -type f -print0 | xargs -0 ls -t | head -n 1)
        if [ -n "$latest_db" ]; then
            echo "$latest_db"
            return 0
        fi
    fi
    
    echo -e "${RED}Could not find Cursor database${NC}"
    return 1
}

# Function to find logs directory
find_logs_dir() {
    local os_type=$(uname)
    local home_dir=$HOME
    local logs_dir=""
    
    case $os_type in
        "Darwin")  # macOS
            logs_dir="$home_dir/Library/Application Support/Cursor/logs"
            ;;
        "Linux")
            logs_dir="$home_dir/.config/Cursor/logs"
            ;;
        *)
            echo -e "${RED}Unsupported operating system: $os_type${NC}"
            return 1
            ;;
    esac
    
    if [ -d "$logs_dir" ]; then
        echo "$logs_dir"
        return 0
    fi
    
    echo -e "${RED}Could not find Cursor logs directory${NC}"
    return 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --quick)
      QUICK_TEST=true
      TEST_MODE=true
      shift
      ;;
    --medium)
      MEDIUM_TEST=true
      TEST_MODE=true
      shift
      ;;
    --test)
      TEST_MODE=true
      shift
      ;;
    --custom)
      CUSTOM_TEST=true
      TEST_MODE=true
      shift
      ;;
    --examples-only)
      EXAMPLES_ONLY=true
      shift
      ;;
    --force-example)
      FORCE_EXAMPLE=true
      shift
      ;;
    --with-examples)
      NO_EXAMPLES=false
      shift
      ;;
    --samples=*)
      SAMPLE_LIMIT="${1#*=}"
      shift
      ;;
    --max-files=*)
      MAX_FILES="${1#*=}"
      shift
      ;;
    --output=*)
      OUTPUT_DIR="${1#*=}"
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --quick                Run a quick test with minimal samples"
      echo "  --medium               Run a medium test with moderate samples"
      echo "  --test                 Run in test mode with custom parameters"
      echo "  --custom               Run with custom test parameters"
      echo "  --examples-only        Skip extraction and only generate example data"
      echo "  --force-example        Force example generation even if real data exists"
      echo "  --with-examples        Generate example data as a fallback if no real data is found"
      echo "  --samples=N            Limit extraction to N samples"
      echo "  --max-files=N          Limit the number of log files to process to N"
      echo "  --output=DIR           Set output directory (default: ../doc)"
      echo "  --help, -h             Show this help message"
      exit 0
      ;;
    --db-path)
      DB_PATH="$2"
      shift 2
      ;;
    --logs-dir)
      LOGS_DIR="$2"
      shift 2
      ;;
    --output-file)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --analyze)
      ANALYZE_ONLY=true
      shift
      ;;
    --no-examples)
      NO_EXAMPLES=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Set up test mode parameters
if [ "$QUICK_TEST" = true ]; then
  SAMPLE_LIMIT=3
  MAX_FILES=2
  OUTPUT_DIR="../doc/test_results/quick"
  echo -e "${YELLOW}Running in QUICK TEST mode${NC}"
  echo -e "  Samples: ${BLUE}$SAMPLE_LIMIT${NC}"
  echo -e "  Max files: ${BLUE}$MAX_FILES${NC}"
  echo -e "  Output directory: ${BLUE}$OUTPUT_DIR${NC}"
elif [ "$MEDIUM_TEST" = true ]; then
  SAMPLE_LIMIT=20
  MAX_FILES=50
  OUTPUT_DIR="../doc/test_results/medium"
  echo -e "${YELLOW}Running in MEDIUM TEST mode${NC}"
  echo -e "  Samples: ${BLUE}$SAMPLE_LIMIT${NC}"
  echo -e "  Max files: ${BLUE}$MAX_FILES${NC}"
  echo -e "  Output directory: ${BLUE}$OUTPUT_DIR${NC}"
elif [ "$CUSTOM_TEST" = true ]; then
  if [ "$SAMPLE_LIMIT" -eq 0 ]; then
    SAMPLE_LIMIT=10
  fi
  if [ "$MAX_FILES" -eq 0 ]; then
    MAX_FILES=20
  fi
  OUTPUT_DIR="../doc/test_results/custom"
  echo -e "${YELLOW}Running in CUSTOM TEST mode${NC}"
  echo -e "  Samples: ${BLUE}$SAMPLE_LIMIT${NC}"
  echo -e "  Max files: ${BLUE}$MAX_FILES${NC}"
  echo -e "  Output directory: ${BLUE}$OUTPUT_DIR${NC}"
elif [ "$TEST_MODE" = true ]; then
  if [ "$SAMPLE_LIMIT" -eq 0 ]; then
    SAMPLE_LIMIT=5
  fi
  if [ "$MAX_FILES" -eq 0 ]; then
    MAX_FILES=10
  fi
  OUTPUT_DIR="../doc/test_results/default"
  echo -e "${YELLOW}Running in TEST mode${NC}"
  echo -e "  Samples: ${BLUE}$SAMPLE_LIMIT${NC}"
  echo -e "  Max files: ${BLUE}$MAX_FILES${NC}"
  echo -e "  Output directory: ${BLUE}$OUTPUT_DIR${NC}"
fi

# Check if examples only mode
if [ "$EXAMPLES_ONLY" = true ]; then
  # Check if example generation is disabled
  if [ "$NO_EXAMPLES" = true ]; then
    echo -e "${RED}Error: Examples only mode requested but example generation is disabled.${NC}"
    echo -e "${YELLOW}Please use --with-examples to enable example generation.${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Running in EXAMPLES ONLY mode (skipping extraction)${NC}"
  
  # Create output directory if it doesn't exist
  mkdir -p "$OUTPUT_DIR"
  
  # Determine complexity level
  COMPLEXITY="medium"
  CONVERSATIONS=3
  EXCHANGES=5
  
  if [ "$QUICK_TEST" = true ]; then
    COMPLEXITY="simple"
    CONVERSATIONS=2
    EXCHANGES=3
  elif [ "$MEDIUM_TEST" = true ]; then
    COMPLEXITY="medium"
    CONVERSATIONS=3
    EXCHANGES=5
  else
    COMPLEXITY="complex"
    CONVERSATIONS=5
    EXCHANGES=7
  fi
  
  # Generate example data
  echo -e "\n${YELLOW}Generating example data...${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  
  $PYTHON_CMD generate_example_data.py \
    --output "$OUTPUT_DIR/complete_sessions.md" \
    --conversations $CONVERSATIONS \
    --exchanges $EXCHANGES \
    --complexity $COMPLEXITY
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Example data generated successfully${NC}"
    echo -e "  Output file: ${BLUE}$OUTPUT_DIR/complete_sessions.md${NC}"
    echo -e "\n${BLUE}NOTE: This is example data demonstrating the format of extracted chat history.${NC}"
    echo -e "${BLUE}No real extraction was performed.${NC}"
  else
    echo -e "${RED}✗ Failed to generate example data${NC}"
    exit 1
  fi
  
  # Exit early since we're only generating examples
  exit 0
fi

# Begin normal extraction process
echo -e "${GREEN}Starting chat history extraction...${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Print header with configuration details
echo -e "${CYAN}==================================================================${NC}"
echo -e "${CYAN}         CURSOR CHAT EXTRACTION UTILITY                           ${NC}"
echo -e "${CYAN}==================================================================${NC}"
echo -e "Starting extraction at $(date)"
echo -e "\n${YELLOW}Configuration:${NC}"
echo -e "  Output directory: ${BLUE}$OUTPUT_DIR${NC}"

if [ "$TEST_MODE" = true ] || [ "$QUICK_TEST" = true ] || [ "$MEDIUM_TEST" = true ]; then
  echo -e "  ${YELLOW}RUNNING IN TEST MODE${NC}"
  echo -e "  Sample limit: ${BLUE}$SAMPLE_LIMIT${NC}"
  echo -e "  Max log files: ${BLUE}$MAX_FILES${NC}"
else
  echo -e "  ${GREEN}RUNNING IN FULL EXTRACTION MODE${NC}"
fi

if [ "$ANALYZE_ONLY" = true ]; then
  echo -e "  ${BLUE}Database analysis enabled${NC}"
fi

echo -e "\n${YELLOW}Checking environment...${NC}"

# Check for Python
if command -v python3 &>/dev/null; then
  PYTHON_CMD="python3"
  echo -e "${GREEN}✓ Python found: $(python3 --version)${NC}"
elif command -v python &>/dev/null; then
  PYTHON_CMD="python"
  echo -e "${GREEN}✓ Python found: $(python --version)${NC}"
else
  echo -e "${RED}✗ Python not found. Please install Python 3.${NC}"
  exit 1
fi

# Check for required modules
echo -e "\n${YELLOW}Checking required Python modules...${NC}"
$PYTHON_CMD -c "import sqlite3" 2>/dev/null
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ sqlite3 module available${NC}"
else
  echo -e "${RED}✗ sqlite3 module not found${NC}"
fi

$PYTHON_CMD -c "import tqdm" 2>/dev/null
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ tqdm module available${NC}"
else
  echo -e "${YELLOW}⚠ tqdm module not found, progress bars won't be displayed${NC}"
  echo -e "  You can install it with: pip install tqdm"
fi

# Auto-detect operating system and set paths
echo -e "\n${YELLOW}Auto-detecting OS and paths...${NC}"
case "$(uname -s)" in
  Darwin*)
    echo -e "${GREEN}✓ macOS detected${NC}"
    CURSOR_LOGS_DIR="$HOME/Library/Application Support/Cursor/logs"
    CURSOR_DB_PATH="$HOME/Library/Application Support/Cursor/User/workspaceStorage"
    ;;
  Linux*)
    echo -e "${GREEN}✓ Linux detected${NC}"
    CURSOR_LOGS_DIR="$HOME/.config/Cursor/logs"
    CURSOR_DB_PATH="$HOME/.config/Cursor/User/workspaceStorage"
    ;;
  CYGWIN*|MINGW*|MSYS*)
    echo -e "${GREEN}✓ Windows detected${NC}"
    CURSOR_LOGS_DIR="$APPDATA/Cursor/logs"
    CURSOR_DB_PATH="$APPDATA/Cursor/User/workspaceStorage"
    ;;
  *)
    echo -e "${RED}✗ Unknown operating system: $(uname -s)${NC}"
    echo -e "${YELLOW}Please specify log directories manually:${NC}"
    read -p "Cursor logs directory: " CURSOR_LOGS_DIR
    read -p "Cursor database path: " CURSOR_DB_PATH
    ;;
esac

echo -e "  Logs directory: ${BLUE}$CURSOR_LOGS_DIR${NC}"
echo -e "  Database directory: ${BLUE}$CURSOR_DB_PATH${NC}"

# Find actual database files
if [ -d "$CURSOR_DB_PATH" ]; then
  echo -e "${YELLOW}Searching for database files...${NC}"
  # Look for state.vscdb files
  DB_FILES=$(find "$CURSOR_DB_PATH" -name "state.vscdb" | head -3)
  
  if [ -n "$DB_FILES" ]; then
    # Use the first file as the primary database
    CURSOR_DB_FILE=$(echo "$DB_FILES" | head -1)
    echo -e "${GREEN}✓ Found database file: $CURSOR_DB_FILE${NC}"
    CURSOR_DB_PATH="$CURSOR_DB_FILE"
  else
    echo -e "${YELLOW}⚠ No .vscdb database files found in workspaceStorage.${NC}"
  fi
fi

echo -e "  Using database: ${BLUE}$CURSOR_DB_PATH${NC}"

# Verify paths exist
if [ ! -d "$CURSOR_LOGS_DIR" ]; then
  echo -e "${RED}✗ Logs directory not found: $CURSOR_LOGS_DIR${NC}"
  echo -e "${YELLOW}Please check if Cursor is installed and has been run at least once.${NC}"
  exit 1
fi

if [ ! -f "$CURSOR_DB_PATH" ] && [ -d "$(dirname "$CURSOR_DB_PATH")" ]; then
  echo -e "${YELLOW}⚠ Primary database file not found at expected path.${NC}"
  echo -e "${YELLOW}Looking for alternative database files...${NC}"
  
  # Find an alternative database file
  ALT_DB_PATH=$(find "$(dirname "$CURSOR_DB_PATH")" -name "*.log" | head -1)
  if [ -n "$ALT_DB_PATH" ]; then
    CURSOR_DB_PATH="$ALT_DB_PATH"
    echo -e "${GREEN}✓ Alternative database file found: $CURSOR_DB_PATH${NC}"
  else
    echo -e "${RED}✗ No database files found in $(dirname "$CURSOR_DB_PATH")${NC}"
    echo -e "${YELLOW}Continuing with log file extraction only.${NC}"
  fi
fi

# Build command arguments
CMD_ARGS=""

if [ "$SAMPLE_LIMIT" -gt 0 ]; then
  CMD_ARGS="$CMD_ARGS --sample-limit $SAMPLE_LIMIT"
fi

if [ "$MAX_FILES" -gt 0 ]; then
  CMD_ARGS="$CMD_ARGS --max-files $MAX_FILES"
fi

if [ "$TEST_MODE" = true ]; then
  CMD_ARGS="$CMD_ARGS --test-mode"
fi

if [ "$ANALYZE_ONLY" = true ]; then
  CMD_ARGS="$CMD_ARGS --analyze"
fi

# Run basic extraction
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 1: Running basic extraction...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

$PYTHON_CMD extract_responses.py \
  --db-path "$CURSOR_DB_PATH" \
  --logs-dir "$CURSOR_LOGS_DIR" \
  --output-file "$OUTPUT_DIR/basic_sessions.md" \
  $CMD_ARGS

BASIC_STATUS=$?

if [ $BASIC_STATUS -eq 0 ]; then
  echo -e "${GREEN}✓ Basic extraction completed successfully${NC}"
else
  echo -e "${RED}✗ Basic extraction failed with status $BASIC_STATUS${NC}"
fi

# Run advanced extraction
echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 2: Running advanced extraction...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

$PYTHON_CMD advanced_extraction.py \
  --db-path "$CURSOR_DB_PATH" \
  --logs-dir "$CURSOR_LOGS_DIR" \
  --output "$OUTPUT_DIR/complete_sessions.md" \
  $CMD_ARGS

ADVANCED_STATUS=$?

if [ $ADVANCED_STATUS -eq 0 ]; then
  echo -e "${GREEN}✓ Advanced extraction completed successfully${NC}"
else
  echo -e "${RED}✗ Advanced extraction failed with status $ADVANCED_STATUS${NC}"
fi

# Final step - Verify output file exists and has content
echo -e "\n${GREEN}Verifying output...${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check for force example flag
if [ "$FORCE_EXAMPLE" = true ] && [ "$NO_EXAMPLES" = false ]; then
  echo -e "${YELLOW}Force example flag is set. Generating example data regardless of extraction results.${NC}"
  
  # Determine complexity level
  COMPLEXITY="medium"
  CONVERSATIONS=3
  EXCHANGES=5
  
  if [ "$QUICK_TEST" = true ]; then
    COMPLEXITY="simple"
    CONVERSATIONS=2
    EXCHANGES=3
  elif [ "$MEDIUM_TEST" = true ]; then
    COMPLEXITY="medium"
    CONVERSATIONS=3
    EXCHANGES=5
  else
    COMPLEXITY="complex"
    CONVERSATIONS=5
    EXCHANGES=7
  fi
  
  # Generate example data
  echo -e "\n${YELLOW}Generating example data...${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  
  $PYTHON_CMD generate_example_data.py \
    --output "$OUTPUT_DIR/complete_sessions.md" \
    --conversations $CONVERSATIONS \
    --exchanges $EXCHANGES \
    --complexity $COMPLEXITY
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Example data generated successfully${NC}"
    echo -e "  Output file: ${BLUE}$OUTPUT_DIR/complete_sessions.md${NC}"
    EXAMPLE_GENERATED=true
  else
    echo -e "${RED}✗ Failed to generate example data${NC}"
  fi
  
  # Exit with success since we forced example generation
  if [ "$EXAMPLE_GENERATED" = true ]; then
    echo -e "\n${BLUE}NOTE: Example data was generated as requested with --force-example flag.${NC}"
    echo -e "${BLUE}This demonstrates the format of what real extracted chat would look like.${NC}"
    exit 0
  fi
fi

# Continue with normal verification
if [ -f "$OUTPUT_DIR/complete_sessions.md" ]; then
  # Count lines in the output file
  LINE_COUNT=$(wc -l < "$OUTPUT_DIR/complete_sessions.md")
  HUMAN_COUNT=$(grep -c "Human (Message" "$OUTPUT_DIR/complete_sessions.md" || echo 0)
  LLM_COUNT=$(grep -c "LLM Response" "$OUTPUT_DIR/complete_sessions.md" || echo 0)
  
  echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${GREEN}Extraction completed at $(date)!${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "Summary:"
  echo -e "  Total lines: ${BLUE}$LINE_COUNT${NC}"
  echo -e "  Human messages: ${BLUE}$HUMAN_COUNT${NC}"
  echo -e "  LLM responses: ${BLUE}$LLM_COUNT${NC}"
  echo -e "  Output file: ${BLUE}$OUTPUT_DIR/complete_sessions.md${NC}"
  
  if [ "$LLM_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠ No LLM responses found. This might indicate an issue with the extraction process.${NC}"
    
    # Generate example data if no real data was found (unless NO_EXAMPLES is true)
    if [ "$NO_EXAMPLES" = false ]; then
      echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
      echo -e "${YELLOW}Generating example data as fallback...${NC}"
      echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
      
      # Set example complexity based on test mode
      COMPLEXITY="medium"
      CONVERSATIONS=3
      EXCHANGES=5
      
      if [ "$QUICK_TEST" = true ]; then
        COMPLEXITY="simple"
        CONVERSATIONS=2
        EXCHANGES=3
      elif [ "$MEDIUM_TEST" = true ]; then
        COMPLEXITY="medium"
        CONVERSATIONS=3
        EXCHANGES=5
      else
        COMPLEXITY="complex"
        CONVERSATIONS=5
        EXCHANGES=7
      fi
      
      $PYTHON_CMD generate_example_data.py \
        --output "$OUTPUT_DIR/complete_sessions.md" \
        --conversations $CONVERSATIONS \
        --exchanges $EXCHANGES \
        --complexity $COMPLEXITY
      
      if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Example data generated successfully${NC}"
        EXAMPLE_GENERATED=true
      else
        echo -e "${RED}✗ Failed to generate example data${NC}"
      fi
    else
      echo -e "${BLUE}Skipping example data generation as requested.${NC}"
      echo -e "${BLUE}To generate example data, use the --with-examples flag.${NC}"
    fi
  elif [ "$LLM_COUNT" -lt "$HUMAN_COUNT" ]; then
    echo -e "${YELLOW}⚠ Fewer LLM responses than human messages. Some responses might be missing.${NC}"
  fi
  
  if [ "$TEST_MODE" = true ] || [ "$QUICK_TEST" = true ] || [ "$MEDIUM_TEST" = true ]; then
    echo -e "\n${YELLOW}This was a test run. For full extraction, run:${NC}"
    echo -e "${CYAN}./extract_chat_history.sh${NC}"
  fi
else
  echo -e "\n${RED}✗ Output file not found: $OUTPUT_DIR/complete_sessions.md${NC}"
  echo -e "${RED}Extraction may have failed to complete.${NC}"
  
  # Generate example data if output file was not created (unless NO_EXAMPLES is true)
  if [ "$NO_EXAMPLES" = false ]; then
    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Generating example data as fallback...${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Set example complexity based on test mode
    COMPLEXITY="medium"
    CONVERSATIONS=3
    EXCHANGES=5
    
    if [ "$QUICK_TEST" = true ]; then
      COMPLEXITY="simple"
      CONVERSATIONS=2
      EXCHANGES=3
    elif [ "$MEDIUM_TEST" = true ]; then
      COMPLEXITY="medium"
      CONVERSATIONS=3
      EXCHANGES=5
    else
      COMPLEXITY="complex"
      CONVERSATIONS=5
      EXCHANGES=7
    fi
    
    $PYTHON_CMD generate_example_data.py \
      --output "$OUTPUT_DIR/complete_sessions.md" \
      --conversations $CONVERSATIONS \
      --exchanges $EXCHANGES \
      --complexity $COMPLEXITY
    
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✓ Example data generated successfully${NC}"
      EXAMPLE_GENERATED=true
    else
      echo -e "${RED}✗ Failed to generate example data${NC}"
    fi
  else
    echo -e "${BLUE}Skipping example data generation as requested.${NC}"
    echo -e "${BLUE}To generate example data, use the --with-examples flag.${NC}"
  fi
fi

# Final message if example data was generated
if [ "$EXAMPLE_GENERATED" = true ]; then
  echo -e "\n${BLUE}NOTE: Example data was generated because no real chat history was found.${NC}"
  echo -e "${BLUE}This demonstrates the format of what real extracted chat would look like.${NC}"
  echo -e "${BLUE}To extract real chat data, ensure Cursor has been used for chat and try again.${NC}"
fi 