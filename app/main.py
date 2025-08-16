import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure import session  

PROJECT_NAME = os.getenv("PROJECT_NAME", "My FastAPI Project")
VERSION = os.getenv("VERSION", "1.0.0")
DESCRIPTION = os.getenv("DESCRIPTION", "Generic FastAPI Boilerplate API.")

app = FastAPI(
    title=PROJECT_NAME,
    version=VERSION,
    description=DESCRIPTION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """
    Endpoint básico de bienvenida.
    """
    return {
        "project": PROJECT_NAME,
        "version": VERSION,
        "status": "running",
        "db_type": os.getenv("DB_TYPE", "sqlite")
    }

# Incluir routers (ejemplo)
# from app.interfaces.api import some_router
# app.include_router(some_router, prefix="/api", tags=["Example"])

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload = os.getenv("RELOAD", "1") == "1",
        reload_dirs=[os.path.dirname(os.path.abspath(__file__))],
        reload_excludes=[
            "*/.git/*",
            "*/__pycache__/*",
            "*.pyc",
            "*/.pytest_cache/*",
            "*/.vscode/*",
            "*/.idea/*"
        ],
        reload_delay=1,
        reload_includes=["*.py", "*.html", "*.css", "*.js"]
    )
