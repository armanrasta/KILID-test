import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import analysis
from src.api.middleware.error_handler import catch_exceptions_middleware
from src.api.config import settings

app = FastAPI(
    title=settings.app_name,
    description="API for real estate property analysis",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(catch_exceptions_middleware)

app.include_router(analysis.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Real Estate Analysis API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
