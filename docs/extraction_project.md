# Cursor Chat History Extraction Project

## Overview

This project provides a system for extracting and analyzing chat history from the Cursor IDE. It includes tools for extracting complete conversations, preserving request-response pairs, and generating example data.

## Project Architecture

```mermaid
flowchart TD
    %% Style Definitions
    classDef defaultStyle fill:white,stroke:#333,stroke-width:1px;
    classDef startStyle fill:#d8eae6,stroke:#333,stroke-width:1px,color:black;
    classDef endStyle fill:#f7d9ea,stroke:#333,stroke-width:1px,color:black;
    classDef stateStyle fill:#d8eae6,stroke:#333,stroke-width:1px,color:black;
    classDef decisionStyle fill:black,stroke:#333,stroke-width:1px,color:white;
    classDef processStyle fill:#d8eae6,stroke:#333,stroke-width:1px,color:black;
    classDef dataStyle fill:#eae6d8,stroke:#333,stroke-width:1px,color:black;
    classDef outputStyle fill:#f7d9ea,stroke:#333,stroke-width:1px,color:black;
    
    %% Main Components
    start[Start Extraction] --> scriptExecution
    scriptExecution[Execute<br/>extract_chat_history.sh] --> envCheck
    
    %% Environment Check
    envCheck{Environment<br/>Ready?} -- No --> setupEnv
    envCheck{Environment<br/>Ready?} -- Yes --> sourceSelection
    setupEnv[Setup Conda<br/>Environment] --> sourceSelection
    
    %% Data Sources
    subgraph dataSources [Data Sources]
        sourceSelection{Select Data<br/>Source} -- Database --> dbExtraction
        sourceSelection{Select Data<br/>Source} -- Logs --> logExtraction
        dbExtraction[Extract from<br/>SQLite DB]
        logExtraction[Process<br/>Log Files]
    end
    
    %% Processing
    subgraph processing [Processing]
        dbExtraction --> matchPairs
        logExtraction --> matchPairs
        matchPairs[Match Request-<br/>Response Pairs]
        matchPairs --> sortTimestamp
        sortTimestamp[Sort by<br/>Timestamp]
        sortTimestamp --> trackSource
        trackSource[Track<br/>Source Info]
    end
    
    %% Output Generation
    subgraph output [Output Generation]
        trackSource --> exampleGen
        exampleGen{Generate<br/>Examples?} -- Yes --> createExamples
        exampleGen{Generate<br/>Examples?} -- No --> finalOutput
        createExamples[Create Example<br/>Data]
        createExamples --> finalOutput
        finalOutput[Generate Final<br/>Output]
    end
    
    finalOutput --> end[Extraction<br/>Complete]
    
    %% Apply Styles
    class start,end startStyle;
    class scriptExecution,setupEnv processStyle;
    class dbExtraction,logExtraction,matchPairs,sortTimestamp,trackSource processStyle;
    class sourceSelection,envCheck,exampleGen decisionStyle;
    class createExamples,finalOutput outputStyle;
```

## Key Components

1. **Core Scripts**
   - `extract_responses.py`: Main extraction logic
   - `extract_chat_history.sh`: Shell script wrapper

2. **Environment Management**
   - Conda environment: `cursor-logs`
   - Auto-dependency installation
   - Cross-platform compatibility

3. **Extraction Features**
   - Complete conversation sets
   - Request-response pairing
   - Timestamp-based sorting
   - Source tracking

4. **CLI Options**
```bash
./extract_chat_history.sh [options]
# Key options:
#   --test             Run in test mode
#   --analyze          Analyze database structure
#   --with-examples    Enable example generation
#   --no-examples      Disable example generation
```

## Current Focus Areas

- Complete conversation set extraction reliability
- Data source detection improvements
- Cross-platform compatibility
- Optimizing large dataset processing

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