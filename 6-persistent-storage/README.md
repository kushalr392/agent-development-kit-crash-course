# Multi-Agent System with Persistent Storage in ADK

This example demonstrates a more complex ADK application featuring a **multi-agent system** that utilizes **persistent storage**. This allows multiple specialized agents to collaborate while remembering information and conversation history across sessions, application restarts, and deployments.

## What is Demonstrated?

This example showcases:
1.  **Orchestrated Multi-Agent Architecture with Mandatory Validation**:
    *   A `manager_agent` orchestrates a sequence: content generation by a sub-agent, then mandatory validation of that content by another sub-agent.
    *   **Content Sub-Agents** (invoked as tools by the manager):
        *   `reminder_agent`: Manages a user's to-do list.
        *   `joke_agent`: Tells jokes.
    *   **Validation Sub-Agent** (invoked as a tool by the manager):
        *   `validator_agent`: Reviews all responses from content agents for appropriateness, politeness, and correctness before they are sent to the user.
    *   **Retry Mechanism**: If validation fails, the manager attempts one retry with the content agent, providing feedback from the validator.
2.  **Persistent Storage with `DatabaseSessionService`**: Session data is stored in an SQLite database, ensuring:
    *   **Long-term Memory**: User details, reminders, joke history, and validation counts persist.
    *   **Consistent User Experiences**: Conversations can be resumed.
    *   **Shared State**: Agents access a common state pool (e.g., `reminders` list, `last_joke_topic`).
3.  **Session Management**: Standard ADK session finding or creation.
4.  **State Management within Tools**: Sub-agents update the shared state via `tool_context.state`.

## Project Structure

The key files have been reorganized to support the multi-agent setup:

```
6-persistent-storage/
│
├── multi_agent_persistent_storage/  # Main package for the multi-agent system
│   ├── __init__.py
│   ├── agent.py                     # Defines the manager_agent
│   └── sub_agents/                  # Package for sub-agents
│       ├── __init__.py
│       ├── joke/
│       │   ├── __init__.py
│       │   └── agent.py             # Defines joke_agent
│       ├── reminder/
│       │   ├── __init__.py
│       │   └── agent.py             # Defines reminder_agent
│       └── validator/
│           ├── __init__.py
│           └── agent.py             # Defines validator_agent
│
├── memory_agent/                    # Original single memory agent (kept for reference but not used by main.py anymore)
│   ├── __init__.py
│   └── agent.py
│
├── main.py                          # Application entry point: sets up and runs the multi-agent system
├── utils.py                         # Utility functions for terminal UI and agent interaction
├── AGENTS.md                        # Instructions and guidelines for AI developers working on these agents
├── .env                             # Environment variables (ensure GOOGLE_API_KEY is set)
├── my_multi_agent_data.db           # SQLite database file for the multi-agent system (created when first run)
└── README.md                        # This documentation
```

## Key Components

### 1. `DatabaseSessionService`

The foundation for persistence, initialized in `main.py`:
```python
from google.adk.sessions import DatabaseSessionService

db_url = "sqlite:///./my_multi_agent_data.db" # Note the new database filename
session_service = DatabaseSessionService(db_url=db_url)
```
This service manages storing and retrieving session data from the SQLite database.

### 2. `manager_agent`

Defined in `multi_agent_persistent_storage/agent.py`. This agent is the core orchestrator:
-   It uses `AgentTool` to call `joke_agent` or `reminder_agent` for content.
-   It then *always* calls `validator_agent` (also as an `AgentTool`) to review the generated content.
-   It handles a single retry attempt if validation fails, by re-prompting the content agent with feedback from the validator.
-   If validation fails after the retry, it issues a safe fallback response.
-   Its complex `instruction` field details this sequential workflow.

### 3. Sub-Agents (Used as Tools by the Manager)

-   **`reminder_agent`**: Generates responses related to reminder tasks. Its output is then validated.
-   **`joke_agent`**: Generates jokes. Its output is then validated.
-   **`validator_agent`**: Contains a tool (`review_and_approve_response`) with rules to check text for politeness, basic correctness, and appropriateness. It does not interact directly with the user.

Each sub-agent's tools primarily focus on their specific task, with the `validator_agent`'s tool being central to the new quality control process.

### 4. Session and State Management

-   **Session Creation/Continuation**: `main.py` checks for existing sessions for a user or creates a new one with an `initial_state` dictionary that includes `user_name`, `reminders`, `last_joke_topic`, and `validated_responses_count`.
-   **State Updates**: When a sub-agent's tool modifies `tool_context.state`, these changes are automatically persisted to the database by the `DatabaseSessionService`.

## Getting Started

### Prerequisites

-   Python 3.9+
-   Google API Key for Gemini models (set in `.env` file)
-   SQLite (typically included with Python)

### Setup

1.  **Activate Virtual Environment**: If you're navigating from the root of the repository, ensure your virtual environment is active:
    ```bash
    # Example for macOS/Linux from project root:
    # source .venv/bin/activate
    # (Adjust if your .venv is elsewhere or use appropriate command for Windows)
    ```
2.  **API Key**: Ensure your `GOOGLE_API_KEY` is correctly set in the `6-persistent-storage/.env` file (or an `.env` file at the root of your project that `load_dotenv()` can find).

### Running the Example

Navigate to the `6-persistent-storage` directory if you are not already there.
```bash
# If you are in the root of the repository:
# cd 6-persistent-storage

python main.py
```
This will:
1.  Connect to `my_multi_agent_data.db` (or create it).
2.  Check for previous sessions or create a new one.
3.  Start a conversation. The `manager_agent` will handle the internal workflow.
4.  Persist all interactions and state changes.

### Example Interactions

All user-facing responses are now subject to internal validation.
The `manager_agent` orchestrates this.

1.  **Reminders:**
    *   "Add a reminder: Call Mom tomorrow."
    *   "Show my reminders."
    *   (If a reminder response was initially phrased poorly by `reminder_agent`, the `validator_agent` would flag it, and `manager_agent` would attempt a retry with `reminder_agent` before you see a response.)

2.  **Jokes:**
    *   "Tell me a joke."
    *   (If `joke_agent`'s first attempt is, for example, not polite or uses flagged words, it will be internally retried after validation feedback.)

3.  **Observing Validation (Indirectly):**
    *   Try to elicit a response that might be borderline for politeness or appropriateness. The system will attempt to self-correct or provide a fallback.
    *   Check the console logs: You'll see more internal activity, including calls to `tool_validator_agent` and its `review_and_approve_response` tool, and potentially retry attempts. This is where the validation process is most visible.
    *   "How many responses have I validated?" (Manager might answer this from state, referring to `validated_responses_count` which is incremented by the validator tool).

4.  **Persistence Test:**
    *   Exit the program with "exit" or "quit".
    *   Run `python main.py` again.
    *   "What's my name?" (Should remember "Multi-Agent User" or what was set if a tool existed)
    *   "What are my reminders?" (Should list any remaining reminders)
    *   "What was the last joke topic?"

The system will remember your `user_name` (from initial state), reminders, last joke topic, and validation count across runs.

## Using Different Databases in Production

While this example uses SQLite, `DatabaseSessionService` supports various SQL databases via SQLAlchemy (e.g., PostgreSQL, MySQL, MS SQL Server). Refer to the ADK documentation and SQLAlchemy documentation for configuring different database backends for production environments.

## Additional Resources

-   [ADK Documentation](https://google.github.io/adk-docs/) (Especially Sessions, State Management, and Multi-Agent sections if available)
-   [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
-   `AGENTS.md` in this folder for AI developer-specific guidelines.
```
