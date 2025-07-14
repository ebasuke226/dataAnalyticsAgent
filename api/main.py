from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
from langchain_openai import ChatOpenAI
from typing import TypedDict
from langgraph.graph import StateGraph, END

# --- LangGraph State ---
class AgentState(TypedDict):
    user_query: str
    sql: str

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
        # ファイルが見つからない場合は、スキーマ情報なしで続行（またはエラー処理）
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
    # 先頭の ```sql とそれに続く改行を削除し、末尾の ``` を削除
    cleaned_sql = raw_sql.strip().removeprefix("```sql").removesuffix("```").strip()
    
    print(f"Generated SQL: {cleaned_sql}")
    
    state["sql"] = cleaned_sql
    return state

# --- LangGraph Definition ---
workflow = StateGraph(AgentState)
workflow.add_node("generate_sql", node_generate_sql)
workflow.set_entry_point("generate_sql")
workflow.add_edge("generate_sql", END)
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
    
    # GPT-4o-miniモデルを使用
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=openai_api_key)

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    print(f"Received query: {request.query}")
    
    # LangGraphを呼び出し
    initial_state = {"user_query": request.query, "sql": ""}
    final_state = app_graph.invoke(initial_state)
    
    # 生成されたSQLを返す（一時的な実装）
    return AnalyzeResponse(
        data_json=json.dumps({"sql": final_state.get("sql")}),
        graph_code="",
        insights="SQL Generated"
    )

@app.get("/test_llm", response_model=LLMTestResponse)
async def test_llm():
    try:
        print("Attempting to get LLM...")
        llm = get_llm()
        print("Successfully got LLM.")
        
        prompt = "Hello"
        print(f"Invoking LLM with prompt: {prompt}")
        response = llm.invoke(prompt)
        print(f"LLM Test Response: {response.content}")
        
        return LLMTestResponse(llm_response=response.content)
    except Exception as e:
        print(f"An error occurred in /test_llm: {e}") # エラーをコンソールに出力
        raise HTTPException(status_code=500, detail=f"LLM test failed: {e}")

@app.get("/graph_test")
async def graph_test():
    """Endpoint to test the LangGraph workflow."""
    try:
        print("Testing LangGraph workflow...")
        initial_state = {"user_query": "foo", "sql": ""}
        result = app_graph.invoke(initial_state)
        print(f"LangGraph result: {result}")
        return result
    except Exception as e:
        print(f"An error occurred in /graph_test: {e}")
        raise HTTPException(status_code=500, detail=f"LangGraph test failed: {e}")

@app.get("/catalog")
async def get_catalog():
    # このエンドポイントはそのまま残すか、必要に応じて削除
    return {"message": "Catalog endpoint - not implemented for this test."}
