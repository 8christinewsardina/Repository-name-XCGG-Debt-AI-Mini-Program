from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, List
from app.models.financials import FinancialStatement
from app.services.cfp_agent import CFPAgent
from app.services.model_clients import create_gemini_client_from_env


class AnalysisModel(BaseModel):
    overview: str
    recommendations: List[str]
    risks: List[str]
    confidence: float


class ReportResponse(BaseModel):
    summary: str
    debt_ratio: float
    analysis: AnalysisModel


router = APIRouter(prefix="/api/v1")


@router.post('/reports', response_model=ReportResponse)
async def create_report(payload: FinancialStatement):
    try:
        # create a model client from environment (Gemini gated by GEMINI_ENABLED and GEMINI_API_KEY)
        model_client = create_gemini_client_from_env()
        agent = CFPAgent(model_client=model_client)
        result = await agent.analyze_async(payload)
        # 确保返回字段完整，若缺失则抛错或补全
        analysis = {
            "overview": result.get("overview", ""),
            "recommendations": result.get("recommendations", []),
            "risks": result.get("risks", []),
            "confidence": float(result.get("confidence", 0.0)),
        }
        # Validate analysis strictly with Pydantic model
        analysis_model = AnalysisModel.parse_obj(analysis)
        return {"summary": "已接收", "debt_ratio": float(payload.debt_ratio()), "analysis": analysis_model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
