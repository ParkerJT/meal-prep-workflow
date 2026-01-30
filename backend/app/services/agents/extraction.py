from agents import Agent

def firecrawl_api(url: str) -> str:
    """
    Uses the Firecrawl API to parse and clean HTML content
    """
    return

SYSTEM_PROMPT_WEB = """

"""

SYSTEM_PROMPT_YOUTUBE = """

"""

extraction_agent_youtube = Agent(
    name="Extraction Agent - YouTube",
    description="Extracts recipe information from YouTube videos",
    system_prompt=SYSTEM_PROMPT_YOUTUBE,
    model="gpt-4o-mini",
)

extraction_agent_web: Agent(
    name="Extraction Agent - Web",
    description="Extracts recipe information from web pages",
    system_prompt=SYSTEM_PROMPT_WEB,
    model="gpt-4o-mini",
)