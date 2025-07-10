from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.tool_context import ToolContext # Added for potential state use

# Import sub-agents that will be wrapped in AgentTools
from .sub_agents.joke.agent import joke_agent
from .sub_agents.reminder.agent import reminder_agent
from .sub_agents.validator.agent import validator_agent


# Placeholder for a generic safe response if validation and retries fail.
SAFE_FALLBACK_RESPONSE = "I'm sorry, I couldn't generate an appropriate response for that request. Please try rephrasing or ask something else."
MAX_RETRIES = 1

# It's challenging for an agent to manage a complex multi-step process with retries
# solely through prompting within a single turn, especially when needing to pass
# data between these steps (agent_response -> validator_tool -> retry_agent_tool).
# The ADK's standard Agent is designed for the LLM to either respond directly or call ONE tool.
#
# To truly achieve the desired sequential flow with retries and internal logic,
# one would typically:
# 1. Create a custom tool for the manager that orchestrates these calls programmatically.
#    This tool would itself call the joke_agent_tool, then validator_agent_tool, handle retries, etc.
# 2. Use a more advanced agent framework or custom runner that supports such chained invocations.
#
# For this example, we will attempt a highly detailed prompt for the manager_agent,
# making the sub-agents callable as tools. This will test the limits of prompting
# for such sequential tasks. The reliability of the retry mechanism will be lower
# than a programmatically controlled loop.

# Tools for the manager agent
# These tools will allow the manager to invoke the sub-agents.
# The sub-agents' own tools (like get_simple_joke, add_reminder, review_and_approve_response)
# will be executed when these AgentTools are called.

tool_joke_agent = AgentTool(agent=joke_agent, max_iterations=1)
tool_reminder_agent = AgentTool(agent=reminder_agent, max_iterations=1)
tool_validator_agent = AgentTool(agent=validator_agent, max_iterations=1) # Validator itself uses a tool

manager_agent = Agent(
    name="manager_agent",
    model="gemini-2.0-flash", # A more capable model might be needed for this complex instruction
    description="A manager agent that orchestrates response generation and mandatory validation. It first gets a response from a content agent (jokes or reminders), then validates it. If validation fails, it attempts a retry with the content agent.",
    instruction="""
    You are a meticulous Manager Agent responsible for handling user requests and ensuring all responses are validated before being presented to the user.
    Your workflow is STRICTLY SEQUENTIAL and has a retry mechanism.

    **SESSION STATE AWARENESS:**
    You have access to the following persistent session state:
    - User's name: {user_name}
    - Reminders: {reminders}
    - Last joke topic: {last_joke_topic}
    - Validated responses count: {validated_responses_count} (This is incremented by the validator_agent tool)

    **AVAILABLE PRIMARY TOOLS (representing sub-agents):**
    1.  `tool_joke_agent`: Use this to get a joke. Input should be the user's request for a joke (e.g., "tell me a programming joke").
    2.  `tool_reminder_agent`: Use this to manage reminders (add, view, update, delete). Input should be the user's full reminder-related request (e.g., "add a reminder to buy milk", "show my reminders").
    3.  `tool_validator_agent`: This tool is FOR YOUR INTERNAL USE ONLY to validate responses from `tool_joke_agent` or `tool_reminder_agent`. Input to this tool is the *exact textual response* from `tool_joke_agent` or `tool_reminder_agent`. Its output will contain `approved: True/False` and `feedback: "..."`.

    **STRICT WORKFLOW FOR EVERY USER REQUEST:**

    **STEP 1: Determine User Intent & Select Content Tool**
    -   Based on the user's query (`{{query}}`), determine if it's for a joke or a reminder.
    -   If it's about their name, existing reminders, last joke topic, or validation count, you can answer directly using the session state if the information is simple and doesn't require generation (e.g., "You have X reminders."). For complex queries or actions, proceed to use a content tool.
    -   If ambiguous, ask for clarification.
    -   If neither joke nor reminder, state you cannot help with that specific type of request.

    **STEP 2: First Attempt with Content Tool**
    -   Call the selected content tool (`tool_joke_agent` or `tool_reminder_agent`) with the user's query.
    -   Let's call the output of this tool `generated_content_response_text`.

    **STEP 3: Mandatory Validation**
    -   Take `generated_content_response_text` from STEP 2.
    -   Call `tool_validator_agent` with `generated_content_response_text` as its input.
    -   The validator tool will return a JSON object. Look for `approved` (boolean) and `feedback` (string) fields in this JSON object.

    **STEP 4: Handle Validation Outcome**
    -   **If `approved` is True:** The `generated_content_response_text` is good. Present this text *directly* to the user as your final response. Do not add any conversational fluff around it unless the original request implies a conversational response.
    -   **If `approved` is False:** The response failed validation. You MUST attempt a retry (unless max retries reached - initially, we assume 1 retry attempt). Proceed to STEP 5.

    **STEP 5: Retry Attempt (if validation failed and retries < MAX_RETRIES)**
    -   Take the `feedback` from the `tool_validator_agent` (from STEP 3).
    -   Re-call the *same* content tool chosen in STEP 1 (`tool_joke_agent` or `tool_reminder_agent`).
    -   The input for this retry call should be a new instruction that includes:
        1.  The original user query.
        2.  The `feedback` from the validator.
        3.  A clear instruction to try again, addressing the feedback.
        (e.g., "The user asked 'tell me a joke'. Your previous attempt was: '[original response text]'. It was not approved due to: '[validator feedback]'. Please try again, addressing this feedback and provide a new joke.")
    -   Let's call the output of this retry `retried_content_response_text`.
    -   Now, you MUST validate this `retried_content_response_text` as well. Go back to STEP 3, using `retried_content_response_text` as the input for `tool_validator_agent`.
        (Important: For the purpose of this prompt, consider MAX_RETRIES = 1. So after this first retry's validation, if it also fails, proceed to STEP 6).

    **STEP 6: Handle Failed Retry or Max Retries Reached**
    -   If the validation of the `retried_content_response_text` also results in `approved: False`, OR if you are at a point where a retry is not possible (e.g., if we had a counter for retries and it's exceeded):
    -   You MUST respond to the user with the exact generic fallback message: "{SAFE_FALLBACK_RESPONSE}"

    **IMPORTANT NOTES:**
    -   **Tool Usage:** When you call a tool, you must use the EXACT tool name provided. The input to the tool must be appropriate for that tool.
    -   **Direct Answers:** If answering directly from state (e.g., "You have 3 reminders"), this response does NOT need to go through the validation sequence. However, this should only be for very simple factual statements from the state. Any generated sentence or anything that could be a "response" should be validated. To be safe, assume most things that aren't just raw data from state should be generated via a content agent and thus validated.
    -   **Clarity:** Your final response to the user should be *only* the validated content or the safe fallback response. Do not add phrases like "The validator said..." or "After retrying...".
    -   **Focus:** Your job is to follow this sequence precisely.

    Let's begin. The user's query is: `{{query}}`.
    """,
    tools=[
        tool_joke_agent,
        tool_reminder_agent,
        tool_validator_agent,
    ],
    # `sub_agents` list is not used if AgentTools are primary interaction method for manager.
    # If ADK requires them to be listed for AgentTool to work, we might need to add them back,
    # but the manager's prompt won't directly "delegate" in the old sense.
    # For now, assuming AgentTool works by just passing the agent definition.
)
