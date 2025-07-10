from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

def get_simple_joke(topic: str = "general", tool_context: ToolContext) -> dict:
    """
    Provides a simple joke, optionally related to a topic.
    Updates the session state with the last joke topic.

    Args:
        topic: The topic for the joke (e.g., "programming", "animals"). Defaults to "general".
        tool_context: Context for accessing and updating session state.

    Returns:
        A dictionary containing the joke.
    """
    print(f"--- Tool: get_simple_joke called for topic: {topic} ---")

    jokes = {
        "programming": "Why do programmers prefer dark mode? Because light attracts bugs!",
        "animals": "What do you call a fish with no eyes? Fsh!",
        "space": "Why did the sun go to school? To get brighter!",
        "general": "Why don't scientists trust atoms? Because they make up everything!",
        "food": "Why did the tomato turn red? Because it saw the salad dressing!"
    }

    chosen_joke = jokes.get(topic.lower(), jokes["general"])

    # Update state with the last joke topic
    tool_context.state["last_joke_topic"] = topic

    return {
        "action": "get_simple_joke",
        "topic": topic,
        "joke": chosen_joke,
        "message": f"Here's a {topic} joke for you: {chosen_joke}"
    }

joke_agent = Agent(
    name="joke_agent",
    model="gemini-2.0-flash",
    description="An agent that tells simple jokes on various topics.",
    instruction="""
    You are a friendly joke-telling agent.
    Your main function is to tell jokes using the `get_simple_joke` tool.

    When the user asks for a joke:
    1. Use the `get_simple_joke` tool. You can specify a topic if the user provides one (e.g., "Tell me a programming joke").
    2. If no topic is mentioned, you can pick a general joke or ask if they have a preferred topic.
    3. Present the joke clearly.

    Remember the last topic a joke was told about from the session state: {last_joke_topic}. You can use this to suggest variety or if the user asks for "another one".

    If the user asks about something other than jokes,
    indicate that your specialty is telling jokes and you can't help with other requests.
    """,
    tools=[get_simple_joke],
)
