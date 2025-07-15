import os
from langchain_openai import ChatOpenAI

def get_llm():
    openai_api_key = os.getenv("GPT_API_KEY")
    if not openai_api_key:
        raise ValueError("GPT_API_KEY environment variable not set.")
    
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=openai_api_key)
