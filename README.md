# Cursor Chat History Extraction Project

A system for extracting and analyzing chat history from the Cursor IDE.

## Overview

This project provides tools and scripts for extracting complete conversations from Cursor IDE, preserving request-response pairs, and generating example data. It includes features for database parsing, log file processing, and HTML/JSON content extraction.

## Key Features

- Complete conversation extraction with request-response pair matching
- Timestamp-based sorting and source tracking
- Conda environment management and auto-dependency installation
- Cross-platform support
- Example data generation

## Documentation

- [Project Documentation](docs/extraction_project.md)
- [Mermaid Flowchart Examples](docs/mermaid_example.md)

## Command Line Interface

```bash
./extract_chat_history.sh [options]
# Key options:
#   --test             Run in test mode
#   --analyze          Analyze database structure
#   --with-examples    Enable example generation
#   --no-examples      Disable example generation
```

## Development

### Standardized Mermaid Diagrams

This project uses standardized Mermaid diagrams for process visualization. All diagrams follow a consistent style defined in the `.cursor/rules/mermaid.rules` file. 

Key style guidelines:
- Color-coded swimlanes by department/function
- Standardized node styles for different types of steps
- Consistent arrow formatting and text wrapping

For VSCode users, a settings file is available at `.cursor/rules/vscode_mermaid.json`.

### Project Rules

The project follows these standardized rules:

1. **Python Development**
   - Type hints for all functions
   - Google-style docstrings
   - Environment verification

2. **Code Organization**
   - Small, focused files
   - Consistent naming conventions
   - Clear separation of concerns

3. **Error Handling**
   - Specific exception types
   - Context-rich error messages
   - Proactive error detection

4. **Performance**
   - Optimized for large datasets
   - Cached results where appropriate
   - Progress tracking for long operations

See the `.cursor/rules/` directory for detailed rule definitions.

## Installation

1. Clone the repository
2. Run `./extract_chat_history.sh --setup` to create the environment
3. Install dependencies with `pip install -r requirements.txt`

## Usage Examples

### Basic Extraction
```bash
./extract_chat_history.sh
```

### With Analysis
```bash
./extract_chat_history.sh --analyze
```

### Testing Mode
```bash
./extract_chat_history.sh --test
``` 