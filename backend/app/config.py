from dotenv import load_dotenv
import os

# Loading .env file
load_dotenv()

class Settings:
    """Cleanly loads environment variables as app settings"""

    # OpenAI API Key
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # OpenAI Model
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")