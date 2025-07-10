# Agent Instructions for Multi-Agent Persistent Storage System

This document provides guidance for interacting with and modifying the multi-agent system within the `6-persistent-storage` example.

## System Overview

The system now uses a `manager_agent` that delegates tasks to two specialized sub-agents:
1.  `joke_agent`: Responsible for telling jokes.
2.  `validator_agent`: Responsible for validating text, for example, checking for politeness.

All agents in this system share a persistent session state managed by `DatabaseSessionService`. This state includes:
-   `user_name`: The name of the user.
-   `last_joke_topic`: The topic of the last joke told by `joke_agent`.
-   `validated_responses_count`: A counter for how many times `validator_agent` has performed a validation.

## Interacting with the System

When running `main.py`:
-   You can ask the `manager_agent` to tell you a joke. It should delegate this to the `joke_agent`.
    -   Example: "Tell me a joke about programming."
    -   Example: "Can you tell me another joke?"
-   You can ask the `manager_agent` to validate a piece of text. It should delegate this to the `validator_agent`.
    -   Example: "Validate this sentence: Thank you for your help."
    -   Example: "Is 'be quiet' a polite phrase?"
-   The `manager_agent` can also access shared state directly.
    -   Example: "What was the last joke about?"
    -   Example: "How many responses have I asked you to validate?"
    -   Example: "What is my name?" (It will use the `user_name` from the state).

## Modifying Agents

-   **Manager Agent (`multi_agent_persistent_storage/agent.py`):**
    -   This agent is responsible for routing. Its `instruction` field is crucial for correct delegation.
    -   If adding new sub-agents, update the `sub_agents` list and the `instruction` to include them.
-   **Joke Agent (`multi_agent_persistent_storage/sub_agents/joke/agent.py`):**
    -   Its primary tool is `get_simple_joke`.
    -   It reads and writes `last_joke_topic` to the session state.
-   **Validator Agent (`multi_agent_persistent_storage/sub_agents/validator/agent.py`):**
    -   Its primary tool is `validate_response_politeness`.
    -   It reads and writes `validated_responses_count` to the session state.
-   **Session State:**
    -   The initial state is defined in `main.py`.
    -   All agents can access the shared state via `tool_context.state` within their tools. Ensure that state keys are used consistently.
    -   When adding new state variables, update `initial_state` in `main.py` and the `display_state` function in `utils.py` for better debugging.

## Code Conventions and Checks (For AI Agent Developers)

1.  **State Management:**
    -   When a sub-agent modifies the state, ensure it's a part of the shared state that the `manager_agent` is also aware of if the manager needs to report on it.
    -   Tools that modify state should clearly document which state keys they affect.
2.  **Delegation:**
    -   The `manager_agent`'s instructions should be very clear about which types of queries go to which sub-agent. Test delegation thoroughly if you change these instructions.
3.  **Tool Design:**
    -   Tools within sub-agents should be focused on the agent's specific task.
    -   Tool responses should be dictionaries providing clear information about the action taken.
4.  **Testing:**
    -   After any modification, run `main.py` and test the interaction flow:
        -   Does the manager delegate correctly?
        -   Do sub-agents use their tools as expected?
        -   Is the session state updated and read correctly by all relevant agents?
        -   Is the state persisted across multiple interactions (i.e., after stopping and restarting, if a session already exists)?
    -   Check the console output for any errors or unexpected behavior in `display_state` or tool execution logs.

This `AGENTS.md` file should be updated if the architecture or core functionalities of the agents within `6-persistent-storage` change significantly.
