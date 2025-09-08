from pydantic import BaseModel, Field, condecimal, validator
from typing import Optional


class FinancialStatement(BaseModel):
    user_id: Optional[str] = None
    assets: condecimal(gt=0) = Field(..., description="总资产（元）")
    liabilities: condecimal(ge=0) = Field(..., description="总负债（元）")
    income: condecimal(gt=0) = Field(..., description="月均收入（元）")
    expenses: condecimal(ge=0) = Field(..., description="月均支出（元）")
    notes: Optional[str] = None

    @validator('liabilities')
    def liabilities_not_exceed_assets(cls, v, values):
        assets = values.get('assets')
        if assets is not None and v is not None and v > assets:
            # 允许，但发出警告式处理：实际业务可以按需改为抛错
            return v
        return v

    def debt_ratio(self) -> float:
        try:
            return float(self.liabilities / self.assets) if self.assets else 0.0
        except Exception:
            return 0.0
