from pydantic import BaseModel
from typing import TypedDict
import pandas as pd

class AgentState(TypedDict):
    user_query: str
    sql: str
    df: pd.DataFrame
    graph_metadata: dict
    insights_text: str

class AnalyzeRequest(BaseModel):
    query: str

class AnalyzeResponse(BaseModel):
    data_json: str
    graph_code: str
    insights: str

class LLMTestResponse(BaseModel):
    llm_response: str
