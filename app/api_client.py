import requests
import json

API_BASE_URL = "http://api:8000"

def analyze_query(query: str):
    """Sends a query to the /analyze endpoint."""
    return requests.post(f"{API_BASE_URL}/analyze", json={"query": query})
