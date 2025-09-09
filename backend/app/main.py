from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI 财务顾问 API")

# Allow CORS for frontend (development-friendly). In production narrow this list to your miniprogram proxy/origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """
    一个简单的测试接口，用于验证服务器是否成功运行。
    """
    return {"message": "欢迎使用 AI 财务顾问 API"}

# include api routers
try:
    from app.api import reports
    app.include_router(reports.router)
except Exception:
    # 报错时保守处理，避免导入时报错影响根接口
    pass
