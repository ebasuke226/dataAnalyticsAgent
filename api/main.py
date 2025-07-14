from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
from langchain_openai import ChatOpenAI
from typing import TypedDict
from langgraph.graph import StateGraph, END
import pandas as pd
import sqlite3

# --- LangGraph State ---
class AgentState(TypedDict):
    user_query: str
    sql: str
    df: pd.DataFrame

# --- Dummy DB Function ---
def fetch_data(sql: str) -> pd.DataFrame:
    """Executes the SQL query on the SQLite DB and returns a DataFrame."""
    print(f"Executing SQL: {sql}")
    db_path = "data/odoo_test_data.db"
    try:
        with sqlite3.connect(db_path) as con:
            df = pd.read_sql_query(sql, con)
        return df
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        # エラーが発生した場合は空のDataFrameを返すか、例外を再発生させる
        return pd.DataFrame()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return pd.DataFrame()

# --- LangGraph Nodes ---
def node_generate_sql(state: AgentState):
    """Generates SQL from the user query based on the provided schema."""
    print("Executing node: generate_sql")
    user_query = state["user_query"]

    # スキーマファイルを読み込む
    try:
        with open("data/odoo_schema.json", "r") as f:
            schema = json.load(f)
    except FileNotFoundError:
        schema = {}
        print("Warning: schema file not found at data/odoo_schema.json")

    schema_str = json.dumps(schema, indent=2, ensure_ascii=False)

    # LLMを呼び出してSQLを生成
    llm = get_llm()
    prompt = f"""以下のデータベーススキーマ情報を参考にして、ユーザーの要求を満たすSQLクエリを生成してください。
SQLクエリのみを返し、他の説明やテキストは一切含めないでください。

## データベーススキーマ
{schema_str}

## ユーザーの要求
{user_query}

## SQLクエリ
"""
    response = llm.invoke(prompt)
    raw_sql = response.content
    cleaned_sql = raw_sql.strip().removeprefix("```sql").removesuffix("```").strip()
    
    print(f"Generated SQL: {cleaned_sql}")
    
    state["sql"] = cleaned_sql
    return state

def node_execute_sql(state: AgentState) -> AgentState:
    """Executes the SQL query and stores the result in the state."""
    print("Executing node: execute_sql")
    sql_query = state["sql"]
    df = fetch_data(sql_query)
    state["df"] = df
    return state

# --- LangGraph Definition ---
workflow = StateGraph(AgentState)
workflow.add_node("generate_sql", node_generate_sql)
workflow.add_node("execute_sql", node_execute_sql)
workflow.set_entry_point("generate_sql")
workflow.add_edge("generate_sql", "execute_sql")
workflow.add_edge("execute_sql", END)
app_graph = workflow.compile()

# --- FastAPI Models ---
class AnalyzeRequest(BaseModel):
    query: str

class AnalyzeResponse(BaseModel):
    data_json: str
    graph_code: str
    insights: str

class LLMTestResponse(BaseModel):
    llm_response: str

# --- FastAPI App ---
app = FastAPI()

# LLM 初期化関数
def get_llm():
    openai_api_key = os.getenv("GPT_API_KEY")
    if not openai_api_key:
        raise ValueError("GPT_API_KEY environment variable not set.")
    
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=openai_api_key)

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    print(f"Received query: {request.query}")
    
    initial_state = {"user_query": request.query, "sql": "", "df": pd.DataFrame()}
    final_state = app_graph.invoke(initial_state)
    
    df = final_state.get("df")
    df_json = df.to_json(orient="split", index=False) if df is not None and not df.empty else "{}"

    return AnalyzeResponse(
        data_json=df_json,
        graph_code="",
        insights="SQL Executed"
    )

@app.get("/test_llm", response_model=LLMTestResponse)
async def test_llm():
    try:
        llm = get_llm()
        prompt = "Hello"
        response = llm.invoke(prompt)
        return LLMTestResponse(llm_response=response.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM test failed: {e}")

@app.get("/graph_test")
async def graph_test():
    """Endpoint to test the LangGraph workflow."""
    try:
        initial_state = {"user_query": "foo", "sql": "", "df": pd.DataFrame()}
        result = app_graph.invoke(initial_state)
        if 'df' in result and isinstance(result['df'], pd.DataFrame):
            result['df'] = result['df'].to_dict(orient='records')
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LangGraph test failed: {e}")

@app.get("/catalog")
async def get_catalog():
    return {"message": "Catalog endpoint - not implemented for this test."}
