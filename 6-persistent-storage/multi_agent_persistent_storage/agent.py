from google.adk.agents import Agent

# Import sub-agents
from .sub_agents.joke.agent import joke_agent
from .sub_agents.validator.agent import validator_agent
from .sub_agents.reminder.agent import reminder_agent

# No specific tools for the manager in this setup, but you could add them.
# from google.adk.tools.agent_tool import AgentTool
# Example: from ..tools.some_shared_tool import some_tool

manager_agent = Agent(
    name="manager_agent",
    model="gemini-2.0-flash", # Using a capable model for routing
    description="A manager agent that delegates tasks to specialized sub-agents for jokes and response validation. It also manages persistent memory for the user.",
    instruction="""
    You are a helpful manager agent. Your primary role is to understand user requests and delegate them to the appropriate sub-agent.
    You have the following sub-agents available:
    - `joke_agent`: Use this agent if the user asks for a joke or anything related to humor.
    - `validator_agent`: Use this agent if the user asks to validate a response, check text, or anything related to text validation.
    - `reminder_agent`: Use this agent if the user wants to add, view, update, or delete reminders.

    You also have access to persistent session state, which includes:
    - User's name: {user_name} (You can greet the user by name if known)
    - Reminders: {reminders}
    - Last joke topic: {last_joke_topic}
    - Validated responses count: {validated_responses_count}

    Based on the user's query, decide which agent is best suited to handle it.
    - If the query is about telling a joke, delegate to `joke_agent`.
    - If the query is about validating text or a response, delegate to `validator_agent`.
    - If the query is about managing reminders (adding, viewing, updating, deleting), delegate to `reminder_agent`.
    - If the user asks about their name, the last joke, current reminders, or how many responses have been validated, you can answer directly using the state.
    - If the query is ambiguous or doesn't fit any agent, you can ask for clarification or state what you can help with (jokes, validation, reminders).

    Always try to be helpful and maintain a friendly tone.
    If you are providing information from the state, make it clear. For example: "I remember your name is {user_name}." or "You have {len(reminders)} reminders."
    """,
    sub_agents=[
        joke_agent,
        validator_agent,
        reminder_agent
    ],
    # tools=[
        # Add any manager-specific tools here if needed in the future
        # e.g., AgentTool(some_other_agent_not_always_needed) or a regular tool
    # ],
    # enable_persistent_session_state=True # This is implicitly handled by the Runner and SessionService
)
