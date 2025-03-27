# Extracting Cursor Chat History - Instructions

This document provides instructions for extracting and processing Cursor IDE chat history. The scripts in this directory can extract both user prompts and (where possible) LLM responses, combining them into comprehensive markdown files.

## Prerequisites

1. **Python Environment**: 
   - The scripts require Python 3.6+ with several dependencies
   - Use the included conda environment for the simplest setup

2. **Cursor Log Files**:
   - Access to Cursor log files (SQLite database and log files)
   - The scripts will attempt to auto-detect these locations

## Setting Up the Environment

### Using Conda (Recommended)

```bash
# Create and activate the environment
conda env create -f environment.yml
conda activate cursor-logs
```

### Manual Installation

If you don't use conda, install the required packages:

```bash
pip install sqlite pandas beautifulsoup4 markdown lxml
```

## Extraction Methods

The toolkit provides several approaches to extract chat history:

1. **Basic Extraction** (`extract_responses.py`):
   - Extracts user prompts from SQLite database
   - Attempts to find LLM responses in database records
   - Creates a markdown file with the conversation

2. **Advanced Extraction** (`advanced_extraction.py`):
   - Uses more sophisticated techniques to find chat data
   - Parses HTML/XML fragments in log files
   - Attempts to match prompts with responses using heuristics

3. **Combined Approach** (`extract_chat_history.sh`):
   - Shell script that runs both extraction methods
   - Auto-detects log locations
   - Handles conda environment setup

## Running the Extraction

### Quickest Method (Recommended)

Simply run the shell script with no arguments to use automatic detection:

```bash
./extract_chat_history.sh
```

### Specifying Custom Paths

```bash
./extract_chat_history.sh --logs-dir /path/to/logs --db-path /path/to/database.vscdb --output-dir /path/to/save
```

### Running Python Scripts Directly

```bash
# Basic extraction
python extract_responses.py --db-path /path/to/database.vscdb --output doc/complete_sessions.md

# Advanced extraction
python advanced_extraction.py --logs-dir /path/to/logs --output doc/enhanced_sessions.md

# Analyze database structure
python extract_responses.py --db-path /path/to/database.vscdb --analyze
```

## Understanding the Results

The extraction process creates markdown files with the following structure:

1. **complete_sessions.md**:
   - Basic extraction of user prompts with placeholders or extracted LLM responses
   - Organized chronologically

2. **enhanced_sessions.md**:
   - More advanced extraction attempting to recover the full conversation
   - May include responses extracted from log files
   - Tries to preserve conversation flow

## Troubleshooting

If the extraction fails to find logs or responses:

1. **Verify Log Locations**:
   - macOS: `~/Library/Application Support/Cursor`
   - Linux: `~/.config/Cursor`
   - Windows: `%APPDATA%\Cursor`

2. **Database Analysis**:
   - Run `python extract_responses.py --db-path /path/to/database.vscdb --analyze` to inspect the database structure
   - This can help identify where chat data might be stored

3. **Manual Exploration**:
   - If automated extraction fails, use SQLite Browser to explore the database
   - Look for tables with names like 'chat', 'message', 'conversation', etc.

## Lessons Learned

From our exploration of Cursor logs, we've discovered:

1. User prompts are consistently stored in the SQLite database under the key `aiService.prompts` in the `ItemTable`
2. LLM responses are more challenging to extract consistently
3. Different Cursor versions may store chat data in different locations
4. Some response data may be stored in log files rather than the database
5. HTML/XML fragments in log files sometimes contain chat data
6. The database schema can vary between Cursor versions

These insights have shaped our extraction approach, which focuses on finding user prompts first, then trying multiple methods to locate corresponding LLM responses.

## Future Improvements

Potential enhancements to the extraction process:

1. Add support for extracting context information (active files, cursor positions)
2. Implement more sophisticated prompt-response matching algorithms
3. Support conversation threading and branched conversations
4. Extract and include timestamps for all messages
5. Create a web-based viewer for exploring the extracted conversations
6. Add NLP-based analysis of chat content

## Incremental Testing

To ensure efficient development and testing of the extraction process, the scripts include parametrization options for incremental testing:

### Parametrization Options

1. **Sample Limiting**:
   - `--sample-limit N`: Limit the number of records processed
   - `--max-files N`: Limit the number of log files searched

2. **Test Modes**:
   - `--test-mode`: Use reasonable defaults for testing
   - `--quick-test`: Run minimal extraction for rapid testing
   - `--medium-test`: Run medium-sized test with more data

### Incremental Testing Approach

For a successful testing workflow, follow this incremental approach:

1. **Start with Quick Tests**:
   ```bash
   ./extract_chat_history.sh --quick-test
   ```
   - Processes minimal data (3 records, 2 files)
   - Output saved to `doc/test_quick` directory
   - Fastest execution time

2. **Progress to Medium Tests**:
   ```bash
   ./extract_chat_history.sh --medium-test
   ```
   - Processes moderate data (10 records, 5 files)
   - Output saved to `doc/test_medium` directory
   - Validates on a larger sample

3. **Custom Test Parameters**:
   ```bash
   ./extract_chat_history.sh --sample-limit 20 --max-files 8 --output-dir doc/test_custom
   ```
   - Precise control over test scope
   - Good for testing specific extraction issues

4. **Full Extraction**:
   ```bash
   ./extract_chat_history.sh
   ```
   - Processes all available data
   - Output saved to default `doc` directory
   - Only run after successful incremental tests

### Benefits of Incremental Testing

- **Rapid Development**: Quick feedback loop for code changes
- **Early Bug Detection**: Find issues with minimal data before scaling up
- **Resource Efficiency**: Save time and computing resources during development
- **Targeted Testing**: Focus on specific components or test cases

When adding new extraction features, always start with quick tests to validate the basic functionality, then gradually increase the data size as confidence in the implementation grows. 