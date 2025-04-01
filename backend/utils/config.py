import os
from dotenv import load_dotenv
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent.parent

# Load environment variables from .env file
load_dotenv(project_root / ".env")

class Config:
    """Configuration class to manage environment variables"""
    
    @staticmethod
    def get_openai_api_key() -> str:
        """Get OpenAI API key from environment variables"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        return api_key
