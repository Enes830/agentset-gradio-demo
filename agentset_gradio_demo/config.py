"""
Configuration file for RAG System
Contains default settings and API credentials
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Logging Configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# API Configuration
AGENTSET_NAMESPACE_ID = ""
AGENTSET_API_KEY = os.getenv("AGENTSET_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# RAG Settings
TOP_K = 10  # Number of documents to retrieve
MIN_SCORE = 0.6  # Minimum relevance score (0-1)

# OpenAI Model Configuration
OPENAI_MODEL = "gpt-4o-mini"  # Default model
AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
    "o1",
    "o1-mini",
    "o3-mini",
]

# System Prompt for RAG responses
SYSTEM_PROMPT = """You are a helpful assistant. Answer questions based on the following context.
If you cannot find the answer in the context, say so clearly.

Context:
{context}"""
