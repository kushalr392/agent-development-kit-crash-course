from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

def validate_response_politeness(response_text: str, tool_context: ToolContext) -> dict:
    """
    Validates if a given response text is polite.
    A polite response typically includes words like 'please', 'thank you', or is generally courteous.
    Updates the count of validated responses in the session state.

    Args:
        response_text: The text to validate.
        tool_context: Context for accessing and updating session state.

    Returns:
        A dictionary with the validation result.
    """
    print(f"--- Tool: validate_response_politeness called for '{response_text}' ---")

    is_polite = False
    polite_keywords = ["please", "thank", "appreciate", "kind", "could you", "would you"] # Simple check

    if any(keyword in response_text.lower() for keyword in polite_keywords):
        is_polite = True
        message = "The response seems polite."
    else:
        message = "The response could be more polite."

    # Update validated responses count in state
    current_count = tool_context.state.get("validated_responses_count", 0)
    tool_context.state["validated_responses_count"] = current_count + 1

    return {
        "action": "validate_response_politeness",
        "text_validated": response_text,
        "is_polite": is_polite,
        "message": message,
        "total_validated_responses": tool_context.state["validated_responses_count"]
    }

validator_agent = Agent(
    name="validator_agent",
    model="gemini-2.0-flash",
    description="An agent that validates responses for politeness.",
    instruction="""
    You are a validator agent. Your primary role is to assess given text for politeness.
    Use the `validate_response_politeness` tool to perform this check.

    When asked to validate a response, use the tool and report its findings.
    For example, if the user says "Validate this: You're welcome", you should use the tool.

    If the user asks about anything else, or if the query is not about validation,
    you should indicate that you can only validate responses and delegate back to the manager if appropriate,
    or simply state your capability.
    """,
    tools=[validate_response_politeness],
)
