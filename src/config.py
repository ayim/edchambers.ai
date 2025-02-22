"""
Configuration settings for the Ed Chambers AI application.
Loads environment variables and provides configuration for various services.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Application Settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Add other configuration settings as needed
