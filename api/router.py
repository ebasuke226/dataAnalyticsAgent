from fastapi import APIRouter, HTTPException
import pandas as pd
import json
from .models import AnalyzeRequest, AnalyzeResponse, LLMTestResponse
from .graph import app_graph
from .llm import get_llm

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    print(f"Received query: {request.query}")
    
    initial_state = {"user_query": request.query, "sql": "", "df": pd.DataFrame(), "graph_metadata": {}, "insights_text": ""}
    final_state = app_graph.invoke(initial_state)
    
    df = final_state.get("df")
    df_json = df.to_json(orient="split", index=False) if df is not None and not df.empty else "{}"
    print(f"Returning df_json: {df_json}") # 追加
    graph_metadata = final_state.get("graph_metadata", {})

    return AnalyzeResponse(
        data_json=df_json,
        graph_code=json.dumps(graph_metadata),
        insights=final_state.get("insights_text", "")
    )

@router.get("/test_llm", response_model=LLMTestResponse)
async def test_llm():
    try:
        llm = get_llm()
        prompt = "Hello"
        response = llm.invoke(prompt)
        return LLMTestResponse(llm_response=response.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM test failed: {e}")

@router.get("/graph_test")
async def graph_test():
    """Endpoint to test the LangGraph workflow."""
    try:
        initial_state = {"user_query": "foo", "sql": "", "df": pd.DataFrame(), "graph_metadata": {}, "insights_text": ""}
        result = app_graph.invoke(initial_state)
        if 'df' in result and isinstance(result['df'], pd.DataFrame):
            result['df'] = result['df'].to_dict(orient='records')
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LangGraph test failed: {e}")

@router.get("/catalog")
async def get_catalog():
    return {"message": "Catalog endpoint - not implemented for this test."}
