from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI

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
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    
    genai.configure(api_key=gemini_api_key)
    
    # Gemini 1.5 Flash モデルを使用
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    print(f"Received query: {request.query}")
    # 固定の JSON 応答を返す
    return AnalyzeResponse(
        data_json="{}",
        graph_code="",
        insights="OK"
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

@app.get("/catalog")
async def get_catalog():
    # このエンドポイントはそのまま残すか、必要に応じて削除
    return {"message": "Catalog endpoint - not implemented for this test."}
