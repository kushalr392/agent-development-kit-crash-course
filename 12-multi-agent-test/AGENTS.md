# Agent Instructions for Multi-Agent Persistent Storage System with Mandatory Response Validation

This document provides guidance for interacting with and modifying the multi-agent system within the `6-persistent-storage` example. This system now features a **mandatory validation step for all agent-generated responses** before they are sent to the user.

## System Overview

The system uses a `manager_agent` that orchestrates a sequential workflow:
1.  **Content Generation**: Based on user input, the `manager_agent` invokes either `joke_agent` or `reminder_agent` (as tools) to generate a response.
2.  **Mandatory Validation**: The response from the content agent is then *always* passed to `validator_agent` (as a tool).
3.  **Retry Logic**: If `validator_agent` disapproves the response, `manager_agent` instructs the original content agent to retry once, providing feedback from the validator. The retried response is also validated.
4.  **Final Output**: Only approved responses are sent to the user. If validation fails after a retry, a generic safe fallback message is provided.

**Sub-Agents (invoked as tools by the Manager):**
-   `joke_agent`: Responsible for telling jokes.
-   `reminder_agent`: Responsible for managing a list of reminders.
-   `validator_agent`: Responsible for reviewing all generated content for politeness, appropriateness, and basic correctness. Its decision (`approved: True/False`) is final for that attempt.

**Persistent Session State:**
Managed by `DatabaseSessionService` (SQLite). Includes:
-   `user_name`: The name of the user.
-   `reminders`: A list of reminder strings.
-   `last_joke_topic`: The topic of the last joke told by `joke_agent`.
-   `validated_responses_count`: A counter for how many responses `validator_agent` has reviewed.

## Interacting with the System

When running `main.py`:
-   The `manager_agent` handles your requests. You will interact with it normally.
-   **Behind the scenes, every response you receive (unless it's a direct, simple lookup from session state by the manager) will have gone through the `validator_agent`.**
-   You typically won't ask the manager to "validate text" anymore, as this is an automatic internal process.

**Example Interactions:**
-   "Tell me a joke about programming."
    -   *Flow: You -> Manager -> Joke Agent -> Validator Agent -> Manager (possibly retries) -> You*
-   "Add a reminder: Buy milk."
    -   *Flow: You -> Manager -> Reminder Agent -> Validator Agent -> Manager (possibly retries) -> You*
-   The `manager_agent` can still answer simple queries about state directly (e.g., "What is my name?", "How many reminders?"). These direct state retrievals might bypass the generation/validation sequence if they don't involve new content generation.

## Modifying Agents

-   **Manager Agent (`multi_agent_persistent_storage/agent.py`):**
    -   **Core Orchestrator**: Its `instruction` field is extremely detailed and defines the sequential workflow (Content Tool -> Validator Tool -> Retry Logic -> Final Response).
    -   It uses `AgentTool` wrappers around `joke_agent`, `reminder_agent`, and `validator_agent` to call them.
    -   Modifying its instruction requires careful attention to maintain the sequence and retry logic.
    -   `SAFE_FALLBACK_RESPONSE` and `MAX_RETRIES` are defined here.

-   **Joke Agent (`multi_agent_persistent_storage/sub_agents/joke/agent.py`):**
    -   Focuses purely on joke generation via its `get_simple_joke` tool.
    -   If it receives feedback for a retry, it should attempt to generate a new, improved joke.
    -   Interacts with `last_joke_topic` in session state.

-   **Reminder Agent (`multi_agent_persistent_storage/sub_agents/reminder/agent.py`):**
    -   Focuses on reminder tasks via its tools (`add_reminder`, etc.).
    -   Its responses (e.g., "Reminder added: ...") are subject to validation.
    -   If it receives feedback for a retry, it should try to rephrase or ensure its response is compliant.
    -   Interacts with the `reminders` list in session state.

-   **Validator Agent (`multi_agent_persistent_storage/sub_agents/validator/agent.py`):**
    -   Its primary tool is `review_and_approve_response`. This tool contains the rules for validation.
    -   **IMPORTANT**: This agent's tool is called by the `manager_agent`, not directly by user delegation.
    -   Its `instruction` emphasizes its role as a mandatory reviewer.
    -   It updates `validated_responses_count` in session state. Modifying its validation rules directly impacts what responses are allowed.

-   **Session State (`main.py` - `initial_state`, `utils.py` - `display_state`):**
    -   Ensure consistency if adding new state variables.

## Code Conventions and Checks (For AI Agent Developers)

1.  **Manager's Prompt is Key:** The reliability of the sequential validation and retry heavily depends on the `manager_agent`'s detailed prompt. Small changes there can have big impacts.
2.  **Validator Agent's Tool (`review_and_approve_response`):**
    -   This is where you define what constitutes an "acceptable" response.
    -   The `feedback` string from this tool is crucial for the retry mechanism. It should be actionable for the content agents.
3.  **Content Agent Retries:** Content agents (`joke_agent`, `reminder_agent`) should ideally be prompted or designed so they can understand and act upon the feedback provided by the `validator_agent` during a retry.
4.  **Tool Design within Sub-Agents:**
    -   Tools in `joke_agent` and `reminder_agent` should return clear textual responses that the `validator_agent` can then process.
    -   The `validator_agent`'s tool must return the `approved` (boolean) and `feedback` (string) structure expected by the `manager_agent`.
5.  **Testing the Flow:**
    -   Test scenarios where validation should pass.
    -   Test scenarios where validation should fail (e.g., a joke agent that initially tells an inappropriate joke). Verify that:
        -   The `validator_agent` disapproves it.
        -   The `manager_agent` attempts a retry with the content agent.
        -   The content agent attempts to provide a new response.
        -   The new response is re-validated.
        -   The `SAFE_FALLBACK_RESPONSE` is used if retries are exhausted and validation still fails.
    -   Monitor `display_state` and console logs to trace the multi-step process. Pay attention to which agent is active and what tool outputs are.

This `AGENTS.md` file should be updated if the architecture or core functionalities, especially the validation and retry logic, change significantly.
```
