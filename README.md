
# SLM-Based Suggestion Engine for Complex Alerts

An AI/ML-assisted system for analyzing Windows Event Viewer alerts, identifying probable root causes, and suggesting appropriate remediation actions.

This project was developed as a campus research collaboration with **Unisys India** and **BMS Institute of Technology and Management (BMSIT)**.

> **Publication note:** Before making this repository public, confirm that the project materials are authorized for publication. Remove confidential information, internal logs, credentials, API keys, machine-specific paths, and sensitive event data.

## Overview

Windows systems can generate large volumes of warnings and errors. Reviewing events individually can make it difficult to identify related issues and determine what action to take.

This project combines alert collection, machine-learning-based classification, incident correlation, root cause analysis (RCA), confidence scoring, and a human-approved remediation workflow. Results are presented through a Flask-based dashboard.

The system is designed to assist incident investigation and remediation. Suggested actions are subject to the configured approval workflow rather than being unrestricted autonomous fixes.

## Key Features

- **Incremental alert collection:** Collects relevant Windows Event Viewer events and uses a checkpoint to avoid repeatedly processing the same time range.
- **Alert classification:** Uses a Random Forest classifier to distinguish simple and complex alerts.
- **Incident correlation:** Groups related alerts using event attributes and a time-based correlation window.
- **Root cause analysis:** Uses a small language model (SLM) to help analyze complex incidents and produce probable root-cause explanations.
- **Explainable confidence scoring:** Calculates an RCA confidence score using five factors:
  - Severity
  - Correlation strength
  - Event frequency
  - Alert diversity
  - Stability
- **Human-in-the-loop remediation:** Maps identified issues to predefined PowerShell remediation scripts and requires administrator approval before execution.
- **Execution tracking and audit history:** Records remediation status and execution history.
- **Flask dashboard:** Presents incident information, RCA results, confidence scores, suggested actions, and remediation status.

## System Workflow

1. **Alert collection:** A PowerShell script collects selected Windows Event Viewer alerts and stores the results in JSON.
2. **Alert classification:** A machine-learning model classifies alerts as simple or complex.
3. **Incident correlation:** Related alerts are grouped into incidents based on their attributes and time proximity.
4. **Root cause analysis:** The RCA component analyzes complex incidents and generates a probable explanation.
5. **Confidence scoring:** A five-factor heuristic calculates a confidence score to communicate the strength of the RCA result.
6. **Remediation suggestion and approval:** The system maps an incident to a predefined remediation action. An administrator reviews and approves the action before execution.
7. **Execution and dashboard update:** The approved PowerShell script is executed, and the result is recorded and displayed on the dashboard.

## Technology Stack

| Area                             | Technologies                |
| -------------------------------- | --------------------------- |
| Programming                      | Python                      |
| Alert collection and remediation | PowerShell                  |
| Machine learning                 | Scikit-learn, Random Forest |
| Text processing                  | TF-IDF                      |
| Small language model             | Phi-3 Mini                  |
| Local model runtime              | Ollama                      |
| Backend and dashboard            | Flask                       |
| Data exchange                    | JSON                        |

## Main Components

| Component            | Responsibility                                                                                               |
| -------------------- | ------------------------------------------------------------------------------------------------------------ |
| Alert Collection     | Collects Windows Event Viewer alerts and maintains an incremental collection checkpoint.                     |
| Alert Classification | Classifies incoming alerts into simple and complex categories.                                               |
| Incident Correlation | Groups related alerts using event attributes and a time-based window.                                        |
| RCA Engine           | Analyzes complex incidents and generates probable root-cause explanations.                                   |
| Confidence Scoring   | Computes an explainable score from five heuristic factors.                                                   |
| Action Executor      | Connects incidents to predefined PowerShell remediation scripts and manages approval and execution tracking. |
| Dashboard            | Displays incidents, RCA findings, suggested actions, statuses, and execution history.                        |

## Human-in-the-Loop Execution

The remediation workflow is designed to retain human oversight:

1. The system identifies a probable issue and suggests a mapped action.
2. The proposed action is presented for review.
3. An administrator approves or rejects the action.
4. Only an approved action proceeds to the configured execution workflow.
5. The execution outcome is recorded for tracking and audit purposes.

Review remediation scripts in a safe test environment before running them on a production machine. PowerShell scripts can make system-level changes.

## Repository Structure

The exact directory layout may vary by project version. A typical separation of responsibilities is:

```text
.
├── alert_collection/       # Windows Event Viewer collection scripts
├── classification/         # Alert classification code and model assets
├── incident_correlation/   # Alert grouping logic
├── rca/                    # Root cause analysis and confidence scoring
├── action_executor/        # Approval workflow and remediation scripts
├── dashboard/              # Flask dashboard
├── data/                   # Sanitized sample data only
├── models/                 # Model artifacts, if approved for publication
├── requirements.txt        # Python dependencies, if provided
└── README.md
```

Update this tree to match the files and folders actually included in the repository. Do not upload private event logs, machine-specific output files, or model/data artifacts unless you have permission to share them.

## Setup and Execution

The exact setup commands depend on the project configuration and Windows environment. Before publishing, add the verified commands for:

1. Creating and activating the Python virtual environment.
2. Installing the dependencies listed in `requirements.txt`.
3. Installing and starting Ollama, if the SLM component is included.
4. Downloading or making the approved model available locally.
5. Configuring alert collection and application paths.
6. Running the alert collection, classification, RCA, and dashboard components.

Do not add real credentials or machine-specific paths to this README. Use a sanitized `.env.example` or configuration template where required, and keep actual secrets out of Git.

## Safety and Responsible Use

- Run collection and remediation components only on systems you own or are authorized to administer.
- Review every remediation script before execution.
- Keep administrator approval enabled for actions that can modify a system.
- Test scripts in a controlled environment before using them on production systems.
- Do not commit credentials, private logs, personal information, or confidential organizational data.

## Project Context

- **Project:** SLM-Based Suggestion Engine for Complex Alerts
- **Type:** Campus research project
- **Collaboration:** Unisys India and BMS Institute of Technology and Management (BMSIT)
- **Project period:** November 2025 – August 2026

## Acknowledgements

Thank you to the project mentors from BMSIT and Unisys for their guidance and feedback, and to the project teammates for their collaboration throughout the research project.

---

*This README describes the system at a high level. Update the setup instructions, repository structure, and component details to reflect the exact files and functionality included in the published repository.*
===============================================================================================================================================================================================================

# SLM-Based-Complex-Alert-RCA-Engine-UNISYS-

An AI/ML-powered system for Windows Event Viewer alert classification, incident correlation, root cause analysis, confidence scoring, and human-approved automated remediation using SLMs.

>>>>>>> 33bf6caa431399296ccf0db2f3bbc4194b34f588
>>>>>>>
>>>>>>
>>>>>
>>>>
>>>
>>
