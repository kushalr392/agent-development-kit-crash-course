from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

# --- Tool Functions (Copied and adapted from original memory_agent) ---
def add_reminder(reminder: str, tool_context: ToolContext) -> dict:
    """Add a new reminder to the user's reminder list.

    Args:
        reminder: The reminder text to add
        tool_context: Context for accessing and updating session state

    Returns:
        A confirmation message
    """
    print(f"--- Tool (reminder_agent): add_reminder called for '{reminder}' ---")
    reminders = tool_context.state.get("reminders", [])
    reminders.append(reminder)
    tool_context.state["reminders"] = reminders
    return {
        "action": "add_reminder",
        "reminder": reminder,
        "message": f"Added reminder: {reminder}",
    }

def view_reminders(tool_context: ToolContext) -> dict:
    """View all current reminders.

    Args:
        tool_context: Context for accessing session state

    Returns:
        The list of reminders
    """
    print("--- Tool (reminder_agent): view_reminders called ---")
    reminders = tool_context.state.get("reminders", [])
    return {"action": "view_reminders", "reminders": reminders, "count": len(reminders)}

def update_reminder(index: int, updated_text: str, tool_context: ToolContext) -> dict:
    """Update an existing reminder.

    Args:
        index: The 1-based index of the reminder to update
        updated_text: The new text for the reminder
        tool_context: Context for accessing and updating session state

    Returns:
        A confirmation message
    """
    print(
        f"--- Tool (reminder_agent): update_reminder called for index {index} with '{updated_text}' ---"
    )
    reminders = tool_context.state.get("reminders", [])
    if not reminders or index < 1 or index > len(reminders):
        return {
            "action": "update_reminder",
            "status": "error",
            "message": f"Could not find reminder at position {index}. Currently there are {len(reminders)} reminders.",
        }
    old_reminder = reminders[index - 1]
    reminders[index - 1] = updated_text
    tool_context.state["reminders"] = reminders
    return {
        "action": "update_reminder",
        "index": index,
        "old_text": old_reminder,
        "updated_text": updated_text,
        "message": f"Updated reminder {index} from '{old_reminder}' to '{updated_text}'",
    }

def delete_reminder(index: int, tool_context: ToolContext) -> dict:
    """Delete a reminder.

    Args:
        index: The 1-based index of the reminder to delete
        tool_context: Context for accessing and updating session state

    Returns:
        A confirmation message
    """
    print(f"--- Tool (reminder_agent): delete_reminder called for index {index} ---")
    reminders = tool_context.state.get("reminders", [])
    if not reminders or index < 1 or index > len(reminders):
        return {
            "action": "delete_reminder",
            "status": "error",
            "message": f"Could not find reminder at position {index}. Currently there are {len(reminders)} reminders.",
        }
    deleted_reminder = reminders.pop(index - 1)
    tool_context.state["reminders"] = reminders
    return {
        "action": "delete_reminder",
        "index": index,
        "deleted_reminder": deleted_reminder,
        "message": f"Deleted reminder {index}: '{deleted_reminder}'",
    }

# Note: update_user_name tool is not included here as user name management
# can be a general manager_agent concern or a dedicated user_profile_agent if complexity grows.
# For now, manager_agent can read {user_name} from state. If it needs to be updated,
# a new tool could be added to manager_agent or a dedicated agent.

# --- Reminder Agent Definition ---
reminder_agent = Agent(
    name="reminder_agent",
    model="gemini-2.0-flash",
    description="A sub-agent specialized in managing a user's list of reminders. It can add, view, update, and delete reminders.",
    instruction="""
    You are a specialized reminder management assistant.
    Your sole focus is to help the user manage their reminders using the available tools.
    The user's reminders are stored in a list in the session state: {reminders}.
    The user's name is: {user_name}. You can use this to personalize responses if appropriate.

    You have the following capabilities:
    1.  **Add new reminders:** Use the `add_reminder` tool.
        -   Extract the core reminder text (e.g., "buy milk" from "remind me to buy milk").
    2.  **View existing reminders:** Use the `view_reminders` tool.
        -   Format the output as a numbered list. If no reminders, state that.
    3.  **Update reminders:** Use the `update_reminder` tool.
        -   Identify the index (1-based) and the new text.
    4.  **Delete reminders:** Use the `delete_reminder` tool.
        -   Identify the index (1-based).

    **Guidelines for identifying reminder index for update/delete:**
    -   If the user provides a number (e.g., "delete reminder 2"), use that as the index.
    -   If they mention content (e.g., "delete my 'call mom' reminder"), try to find a match in the {reminders} list. If multiple matches, you can use the first one or state ambiguity if necessary (though the original agent preferred picking first match). For this version, let's try to be precise: if an exact match is found, use its index. If not, or if ambiguous, you can list reminders and ask for an index, or state you couldn't find it.
    -   Handle relative positions like "first", "last", "second".

    If the user asks about anything not related to managing reminders (e.g., jokes, validation, general chit-chat),
    you should state that your function is only to manage reminders and that they might need to ask the main assistant (manager) for other tasks.
    """,
    tools=[
        add_reminder,
        view_reminders,
        update_reminder,
        delete_reminder,
    ],
)
