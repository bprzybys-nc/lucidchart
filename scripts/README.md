# Cursor Chat History Extraction

This tool extracts chat history from the Cursor IDE, including both database and log files.

## Features

- Extracts complete conversation sets (request-response pairs)
- Supports both database and log file extraction
- Auto-detects database and log locations
- Progress bars and colorized output
- Test mode for quick validation
- Example data generation for testing
- Conda environment management

## Requirements

- Python 3.9 or higher
- Conda package manager
- SQLite3 support
- Required Python packages:
  - tqdm (for progress bars)
  - sqlite3 (usually included with Python)
  - json (usually included with Python)

## Installation

### Using Conda (Recommended)

The script will automatically create and manage a conda environment named `cursor-logs`:

```bash
./extract_chat_history.sh
```

### Manual Installation

If you prefer to manage dependencies yourself:

```bash
# Create and activate environment
conda create -n cursor-logs python=3.9
conda activate cursor-logs

# Install dependencies
pip install tqdm
```

## Usage

### Quick Start

```bash
# Basic extraction with auto-detection
./extract_chat_history.sh

# Run in test mode (limited samples)
./extract_chat_history.sh --test

# Analyze database structure
./extract_chat_history.sh --analyze
```

### Advanced Options

```bash
./extract_chat_history.sh [options]

Options:
  --db-path PATH      Specify database path
  --logs-dir PATH     Specify logs directory
  --output-file FILE  Set output file (default: chat_history.md)
  --sample-limit N    Limit number of conversation sets
  --max-files N       Limit number of log files to process
  --test             Run in test mode
  --analyze          Analyze database structure only
  --no-examples      Disable example generation
  --examples-only    Generate only example data
```

### Output Format

The extracted history is saved in markdown format with:
- Complete conversation sets from database
- Additional content from logs
- Timestamps and sources where available
- Code blocks for better readability

## Troubleshooting

1. If the script can't find the database or logs:
   - Check if Cursor is installed
   - Use --db-path and --logs-dir to specify locations manually

2. If no conversations are found:
   - Try running with --analyze to check database structure
   - Use --test mode to verify extraction works
   - Check if Cursor has any chat history

3. If environment issues occur:
   - Ensure conda is installed and in PATH
   - Try manual installation steps
   - Check Python version compatibility

## Development

The extraction process is split into several components:

1. `extract_chat_history.sh`: Main shell script
   - Environment management
   - Path detection
   - Command line parsing

2. `extract_responses.py`: Python extraction script
   - Database parsing
   - Log file processing
   - Markdown generation

3. `generate_example_data.py`: Example generation
   - Test data creation
   - Format validation

## Contributing

When contributing:
1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Test on both macOS and Linux

## License

MIT License - See LICENSE file for details 