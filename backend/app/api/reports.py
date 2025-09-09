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

# Simple in-memory job store for asynchronous processing (suitable for dev; replace with Redis/RQ in prod)
from uuid import uuid4
from typing import Dict
import asyncio

JOB_STORE: Dict[str, Dict[str, Any]] = {}


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



class StartReportResponse(BaseModel):
    job_id: str


@router.post('/reports/start', response_model=StartReportResponse)
async def start_report(payload: FinancialStatement):
    """Start an analysis job and return a job_id for polling.
    The actual analysis runs in the event loop's executor to avoid blocking.
    """
    job_id = str(uuid4())
    JOB_STORE[job_id] = {"status": "queued", "result": None}

    async def _run():
        JOB_STORE[job_id]["status"] = "running"
        try:
            model_client = create_gemini_client_from_env()
            agent = CFPAgent(model_client=model_client)
            res = await agent.analyze_async(payload)
            JOB_STORE[job_id]["status"] = "done"
            JOB_STORE[job_id]["result"] = {
                "summary": "已接收",
                "debt_ratio": float(payload.debt_ratio()),
                "analysis": res,
            }
        except Exception as e:
            JOB_STORE[job_id]["status"] = "error"
            JOB_STORE[job_id]["result"] = {"error": str(e)}

    # schedule the job
    asyncio.create_task(_run())
    return {"job_id": job_id}


@router.get('/reports/{job_id}')
async def get_report_status(job_id: str):
    job = JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job
