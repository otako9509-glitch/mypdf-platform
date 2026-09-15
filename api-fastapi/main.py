import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers.upload import router as upload_router
from routers.jobs import router as jobs_router
from routers.health import router as health_router

app = FastAPI(
    title="MyPDF API",
    version="1.0.0",
    description="PDF processing API for MyPDF",
)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["Health"],
)

app.include_router(
    upload_router,
    prefix="/api/v1",
    tags=["Upload"],
)

app.include_router(
    jobs_router,
    prefix="/api/v1",
    tags=["Jobs"],
)

# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    return {
        "success": True,
        "name": "MyPDF API",
        "version": "1.0.0",
        "status": "running",
    }

# ============================================================
# GLOBAL ERROR HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"[API ERROR] {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)