# Workflow Process Analysis: Transform to Certinia

## Overview
This document analyzes the current workflow process depicted in the swimlane flowchart. The chart shows a resource/demand management process that starts with a Demand Plan and flows through various approval stages and checks across different organizational roles.

## Chart Header Information
- **Blue**: Decision/Approval processes
- **Green**: Ticket status indicators
- **Orange**: Interim tool
- **Pink/Purple**: Desired/target tool (Certinia)

## Swimlanes and Participants
The flowchart is organized into vertical swimlanes representing different roles:
- LT (Leadership Team)
- WPM (Work/Project Management)
- Demand Owner
- CBDRF
- IBM WFM
- Subcontractors
- TA (Talent Acquisition)

## Status Indicators (from header)
- **Forecasted**: Initial ticket status
- **New**: Early stage in the process
- **Internal Check**: Verification stage
- **Proposal**: When offering to Demand Owner
- **CBDRF/IBM WFM/Subcontractors**: All have three possible statuses:
  - In progress
  - Accepted
  - Onboarded
- **External Search Approval Pending**: Waiting for approval
- **External Search**: Active external search
- **Softbooked**: Resource tentatively assigned
- **Assigned**: Resource fully assigned
- **Cancelled**: Process terminated
- **Case Lost**: Opportunity not pursued

## Process Flow

### Cross-Swimlane Workflow
1. Process begins with **Demand Plan** in the Demand Owner swimlane
2. Moves to **Opportunity Evaluation** in the WPM swimlane for initial assessment
3. Decision point in WPM: **Opportunity Qualified (>20%)**
   - If Yes: Proceeds to **Mandatory descriptive data quality check** in WPM
   - If No: Process returns or terminates
4. **Quality Check** decision point in WPM swimlane
5. Moves back to Demand Owner swimlane for **RR Update** (Resource Request Update)
6. Continues to **RR Role Classification Update** in Demand Owner swimlane
7. Moves to **Internal Check** in WPM swimlane
8. Decision point in WPM: **Expert(s) Found**
   - If Yes: Moves to **Expert(s) Proposed** in Demand Owner
   - If No: Proceeds to **Gap Analysis** in WPM
9. After **Gap Analysis** or from **Expert(s) Proposed**, moves to **Staffing Recommendations** in WPM
10. Decision point in Demand Owner: **Staffing Recommendation**
    - If Yes: Proceeds to **Job Description**
    - If No: Returns to earlier stages
11. Multiple **Approval** stages across different stakeholders following the Job Description
12. If approvals are successful, process branches to handle different resource types (internal vs. external)
13. For external resources: **NC hiring approval flow** in WPM swimlane
14. **Inform TA** in TA swimlane when applicable
15. **Expert(s) Softbooked** near the end of the process
16. **Assignment** as the final stage of the process

### Resource Pool Integration
The CBDRF, IBM WFM, and Subcontractors swimlanes show specialized processes that integrate with the main workflow when these resource pools are involved in staffing decisions.

## Current System State
- **Interim Tool**: Shown in orange at the top
- **Desired Tool**: Certinia (shown in pink/purple)
- **NC WFM Strategy** appears at the bottom of the chart in the LT swimlane

## Key Decision Points
Multiple approval steps are required throughout the process, with checks at various stages to ensure proper qualification, resource matching, and stakeholder agreement. The workflow frequently crosses between swimlanes, indicating collaboration between different organizational roles throughout the process. 