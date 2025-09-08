from pydantic import BaseModel, Field, conlist, confloat
from typing import List


class AgentOutputModel(BaseModel):
    overview: str = Field(..., description="简短的概述，中文为主")
    recommendations: List[str] = Field(..., description="分步建议列表")
    risks: List[str] = Field(..., description="潜在风险点列表")
    confidence: confloat(ge=0.0, le=1.0) = Field(..., description="置信度 0-1")
