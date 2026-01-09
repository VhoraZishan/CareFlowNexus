import traceback

from app.routers import admin, admission, auth, patients, tasks
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="CareFlow Nexus Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://careflow-nexus-nine.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(patients.router, prefix="/api/v1")
app.include_router(admission.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "CareFlow Nexus Backend is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "careflow-backend"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for debugging"""
    error_detail = {
        "error": str(exc),
        "type": type(exc).__name__,
        "path": request.url.path,
        "method": request.method,
    }

    # Print full traceback to logs
    print(f"Error handling request {request.method} {request.url.path}")
    print(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={"detail": error_detail},
    )
