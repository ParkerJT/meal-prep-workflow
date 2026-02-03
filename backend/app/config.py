from dotenv import load_dotenv
import os

# Loading .env file
load_dotenv()

class Settings:
    """Cleanly loads environment variables as app setings"""

    # Access Token
    ACCESS_TOKEN: str = os.getenv("ACCESS_TOKEN", "")

    # OpenAI API Key
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # OpenAI Model
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini") 

    # Azure Cosmos DB
    COSMOS_DB_CONNECTION_STRING: str = os.getenv("COSMOS_DB_CONNECTION_STRING", "")
    COSMOS_DB_NAME: str = os.getenv("COSMOS_DB_NAME", "")
    COSMOS_DB_CONTAINER: str = os.getenv("COSMOS_DB_CONTAINER", "")