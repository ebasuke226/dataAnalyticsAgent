import json
from langgraph.graph import StateGraph, END
from .models import AgentState
from .llm import get_llm
from .db import fetch_data

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

def node_generate_insights(state: AgentState) -> AgentState:
    """Analyzes the data and generates insights using an LLM."""
    print("Executing node: generate_insights")
    user_query = state["user_query"]
    df = state["df"]

    if df.empty:
        state["insights_text"] = "データがありません。分析できません。"
        return state

    # データフレームの情報をプロンプトに含める
    df_info = f"DataFrame columns: {df.columns.tolist()}\nDataFrame head:\n{df.head().to_markdown(index=False)}"

    llm = get_llm()
    prompt = f"""以下のユーザーの要求とデータフレームの情報に基づいて、データから読み取れる傾向や特徴を分析し、日本語で簡潔なインサイトを生成してください。
インサイトのみを返し、他の説明やテキストは一切含めないでください。

## データフレーム情報
{df_info}

## ユーザーの要求
{user_query}

## インサイト
"""
    response = llm.invoke(prompt)
    insights = response.content.strip()
    
    print(f"Generated Insights: {insights}")
    
    state["insights_text"] = insights
    return state

workflow = StateGraph(AgentState)
workflow.add_node("generate_sql", node_generate_sql)
workflow.add_node("execute_sql", node_execute_sql)
workflow.add_node("generate_graph_metadata", node_generate_graph_metadata)
workflow.add_node("generate_insights", node_generate_insights)
workflow.set_entry_point("generate_sql")
workflow.add_edge("generate_sql", "execute_sql")
workflow.add_edge("execute_sql", "generate_graph_metadata")
workflow.add_edge("generate_graph_metadata", "generate_insights")
workflow.add_edge("generate_insights", END)
app_graph = workflow.compile()
