# SkillProtocol

SkillProtocol is an AI-powered verification platform that analyzes GitHub repositories to validate developer skills. It uses a multi-agent workflow to clone repositories, calculate complexity metrics (NCrF), and assess competency levels based on the SFIA framework.

## Overview

The system provides an objective, data-driven way to verify coding ability. Instead of relying on self-reported skills, it examines the actual codebase to determine:
* **Complexity:** Code structure, architectural patterns, and depth.
* **Competency:** Use of industry standards (CI/CD, Testing, Docker, Async).
* **Consistency:** Verified history of code contributions.

## Key Features

* **Multi-Language Analysis:** Supports Python, JavaScript, TypeScript, Go, Rust, Java, PowerShell, Shell, and Jupyter Notebooks.
* **Agentic Workflow:** Orchestrates five specialized AI agents (Validator, Scanner, Grader, Auditor, Reporter) to perform deep analysis.
* **Dynamic Context Switching:** Automatically detects the repository owner and switches the dashboard context, isolating data per user.
* **Smart Deduplication:** Tracks Git commit hashes to prevent duplicate scoring of the same code version while allowing credit for legitimate updates.
* **Full Observability:** Integrated with Opik to provide immutable audit trails for every credit awarded.

## Architecture

The application is built as a decoupled full-stack system:

1.  **Frontend (React + Vite):** A responsive interface that handles user input, visualizes the analysis process in real-time, and displays the user's skill topology.
2.  **Backend (FastAPI + LangGraph):** The core engine that manages the agent state machine. It handles:
    * **Validator Agent:** Verifies repository access and metadata.
    * **Scanner Agent:** Securely clones code and parses ASTs (Abstract Syntax Trees) for metrics.
    * **Grader Agent:** Evaluates code quality against the SFIA rubric.
    * **Reporter Agent:** Finalizes scores and commits data to the persistent ledger.
3.  **Database (PostgreSQL):** Stores user profiles, analysis history, and the immutable credit ledger.

## Getting Started

### Prerequisites
* Node.js (v18+)
* Python (v3.10+)
* PostgreSQL
* Git (Required on the host machine for cloning)

### Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/your-username/skill-protocol.git](https://github.com/your-username/skill-protocol.git)
    cd skill-protocol
    ```

2.  **Backend Setup**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    
    # Configure environment
    cp .env.example .env
    # Add your DATABASE_URL, OPENAI/GROQ_API_KEY, and OPIK_API_KEY
    ```

3.  **Frontend Setup**
    ```bash
    cd ../frontend
    npm install
    ```

### Running the System

1.  **Start Backend**
    ```bash
    uvicorn app.main:app --reload
    ```

2.  **Start Frontend**
    ```bash
    npm run dev
    ```

3.  Open `http://localhost:5173` to start an analysis.

## Usage

1.  **Input:** Enter any public GitHub repository URL (e.g., `github.com/torvalds/linux`).
2.  **Analysis:** The agents will validate the repo, clone it to a secure temp directory, and analyze the code.
3.  **Result:** You receive a verified certificate with a credit score and SFIA level.
4.  **Dashboard:** The dashboard updates to show the history and metrics for that specific GitHub user.

## License

MIT License
