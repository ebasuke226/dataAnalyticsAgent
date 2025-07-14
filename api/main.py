from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
from langchain_openai import ChatOpenAI
from typing import TypedDict
from langgraph.graph import StateGraph, END
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO

# --- LangGraph State ---
class AgentState(TypedDict):
    user_query: str
    sql: str
    df: pd.DataFrame
    graph_metadata: dict

# --- Dummy DB Function ---
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
"""
## SQLクエリ

    response = llm.invoke(prompt)
    raw_sql = response.content
    cleaned_sql = raw_sql.strip().removeprefix("```sql").removesuffix("```").strip()
    
    print(f"Generated SQL: {cleaned_sql}")
    
    state["sql"] = cleaned_sql
    return state

# --- Dummy DB Function ---
def fetch_data(sql: str) -> pd.DataFrame:
    """Executes the SQL query on the SQLite DB and returns a DataFrame."""
    print(f"Executing SQL: {sql}")
    db_path = "data/odoo_test_data.db"
    try:
        with sqlite3.connect(db_path) as con:
            df = pd.read_sql_query(sql, con)
            print(f"DataFrame loaded in fetch_data:\n{df.head()}") # 追加
            # 日付カラムをdatetime型に変換（例: 'date_order'カラムがある場合）
            if 'date_order' in df.columns:
                df['date_order'] = pd.to_datetime(df['date_order'])
            return df
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        # エラーが発生した場合は空のDataFrameを返すか、例外を再発生させる
        return pd.DataFrame()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return pd.DataFrame()

def node_execute_sql(state: AgentState) -> AgentState:
    """Executes the SQL query and stores the result in the state."""
    print("Executing node: execute_sql")
    sql_query = state["sql"]
    df = fetch_data(sql_query)
    state["df"] = df
    print(f"DataFrame dtypes after SQL execution:\n{df.dtypes}")
    print(f"DataFrame empty status after SQL execution: {df.empty}") # 追加
    print(f"DataFrame head after SQL execution:\n{df.head()}") # 追加
    return state


def node_generate_graph_metadata(state: AgentState) -> AgentState:
    """Generates graph metadata (type, columns, etc.) using LLM."""
    print("Executing node: generate_graph_metadata")
    user_query = state["user_query"]
    df = state["df"]

    if df.empty:
        state["graph_metadata"] = {"type": "none", "message": "データがありません。グラフを生成できません。"}
        return state

    # データフレームの情報をプロンプトに含める
    df_info = f"DataFrame columns: {df.columns.tolist()}\nDataFrame head:\n{df.head().to_markdown(index=False)}"

    llm = get_llm()
    prompt = f"""以下のユーザーの要求とデータフレームの情報に基づいて、最適なグラフの種類と描画に必要なカラム情報をJSON形式で生成してください。
JSONのみを返し、他の説明やテキストは一切含めないでください。

利用可能なグラフの種類:
- line (折れ線グラフ): 時系列データや連続的な変化の表示に適しています。
- bar (棒グラフ): カテゴリごとの比較や数量の表示に適しています。
- scatter (散布図): 2つの数値変数の関係性の表示に適しています。

JSONの形式:
{{"type": "[グラフの種類]", "x_col": "[X軸のカラム名]", "y_col": "[Y軸のカラム名]", "title": "[グラフのタイトル]"}}

例:
{{"type": "line", "x_col": "date", "y_col": "sales", "title": "日別売上推移"}}
{{"type": "bar", "x_col": "category", "y_col": "count", "title": "カテゴリ別商品数"}}

## データフレーム情報
{df_info}

## ユーザーの要求
{user_query}

## グラフメタデータ (JSON)
"""
    response = llm.invoke(prompt)
    raw_metadata = response.content.strip()

    try:
        graph_metadata = json.loads(raw_metadata)
        state["graph_metadata"] = graph_metadata
        print(f"Generated Graph Metadata: {graph_metadata}")
    except json.JSONDecodeError as e:
        print(f"Error decoding graph metadata JSON: {e}\nRaw metadata: {raw_metadata}")
        state["graph_metadata"] = {"type": "none", "message": f"グラフメタデータの生成に失敗しました: {e}"}

    return state

# --- LangGraph Definition ---
workflow = StateGraph(AgentState)
workflow.add_node("generate_sql", node_generate_sql)
workflow.add_node("execute_sql", node_execute_sql)
workflow.add_node("generate_graph_metadata", node_generate_graph_metadata)
workflow.set_entry_point("generate_sql")
workflow.add_edge("generate_sql", "execute_sql")
workflow.add_edge("execute_sql", "generate_graph_metadata")
workflow.add_edge("generate_graph_metadata", END)
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
    
    initial_state = {"user_query": request.query, "sql": "", "df": pd.DataFrame(), "graph_metadata": {}}
    final_state = app_graph.invoke(initial_state)
    
    df = final_state.get("df")
    df_json = df.to_json(orient="split", index=False) if df is not None and not df.empty else "{}"
    print(f"Returning df_json: {df_json}") # 追加
    graph_metadata = final_state.get("graph_metadata", {})

    return AnalyzeResponse(
        data_json=df_json,
        graph_code=json.dumps(graph_metadata),
        insights="Graph Metadata Generated"
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
        initial_state = {"user_query": "foo", "sql": "", "df": pd.DataFrame(), "graph_metadata": {}}
        result = app_graph.invoke(initial_state)
        if 'df' in result and isinstance(result['df'], pd.DataFrame):
            result['df'] = result['df'].to_dict(orient='records')
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LangGraph test failed: {e}")

@app.get("/catalog")
async def get_catalog():
    return {"message": "Catalog endpoint - not implemented for this test."}
