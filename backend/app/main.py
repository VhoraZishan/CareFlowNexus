from fastapi import FastAPI
from app.routers import auth, patients, admission, tasks

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1")
app.include_router(patients.router, prefix="/api/v1")
app.include_router(admission.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
