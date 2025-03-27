# Mermaid Flowchart Example

This document demonstrates how to use the standardized Mermaid flowchart styles.

## Process Workflow Example

```mermaid
flowchart TD
    %% Style Definitions
    classDef defaultStyle fill:white,stroke:#333,stroke-width:1px;
    classDef startStyle fill:#d8eae6,stroke:#333,stroke-width:1px,color:black;
    classDef endStyle fill:#f7d9ea,stroke:#333,stroke-width:1px,color:black;
    classDef stateStyle fill:#d8eae6,stroke:#333,stroke-width:1px,color:black;
    classDef decisionStyle fill:black,stroke:#333,stroke-width:1px,color:white;
    classDef demandLeadStyle fill:#eae6d8,stroke:#333,stroke-width:1px,color:black;
    classDef wfmStyle fill:#d8eae6,stroke:#333,stroke-width:1px,color:black;
    classDef approvalStyle fill:#f7d9ea,stroke:#333,stroke-width:1px,color:black;
    classDef cioStyle fill:#d9eaf7,stroke:#333,stroke-width:1px,color:black;
    classDef ibmStyle fill:#e6d8ea,stroke:#333,stroke-width:1px,color:black;
    classDef subStyle fill:#e6d8ea,stroke:#333,stroke-width:1px,color:black;
    classDef taStyle fill:#d9eaf7,stroke:#333,stroke-width:1px,color:black;
    
    %% Start and End Nodes
    start[Start Process] --> requestCreation
    end[End Process]
    
    %% Demand Lead Swimlane
    subgraph demandLead [Demand Lead]
        requestCreation[Create Resource<br/>Request] --> initialReview
        initialReview[Review<br/>Requirements]
    end
    
    %% Decision Point
    initialReview --> isComplete{Complete<br/>Request?}
    isComplete{Complete<br/>Request?} -- Yes --> wfmReview
    isComplete{Complete<br/>Request?} -- No --> requestUpdates
    
    %% WFM Swimlane
    subgraph wfm [WFM]
        wfmReview[Review Resource<br/>Request] --> resourceEvaluation
        resourceEvaluation[Evaluate<br/>Resources]
        resourceAssignment[Assign<br/>Resources]
    end
    
    %% Approval Swimlane
    subgraph approval [Decision/Approval]
        requestUpdates[Request<br/>Updates] --> requestCreation
        approvalCheck{Approved?}
    end
    
    %% Process Flow
    resourceEvaluation --> approvalCheck
    approvalCheck -- Yes --> resourceAssignment
    approvalCheck -- No --> requestUpdates
    resourceAssignment --> end
    
    %% Apply Styles
    class start startStyle;
    class end endStyle;
    class requestCreation,initialReview demandLeadStyle;
    class wfmReview,resourceEvaluation,resourceAssignment wfmStyle;
    class requestUpdates,approvalCheck approvalStyle;
    class isComplete decisionStyle;
```

## Key Style Features

- **Swimlanes**: Color-coded by department/function
- **Decision Points**: Black background with white text
- **State Boxes**: Light blue with black text
- **Arrow Styles**: Standard black for flow, colored for Yes/No paths
- **Text Formatting**: Line breaks for readability

## Usage Guidelines

1. Copy the style definitions section to maintain consistency
2. Use descriptive node IDs instead of numbers
3. Group related nodes in appropriate swimlanes
4. Apply styles using class definitions at the end
5. Use standardized colors for each department/function 