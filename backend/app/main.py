# app/main.py
from fastapi import FastAPI
from app.routers import patients, beds, tasks, admissions, agent,discharge, debug

app = FastAPI(title="CareFlowNexus - Backend (DB aligned)")

app.include_router(patients.router, prefix="/patients")
app.include_router(beds.router, prefix="/beds")
app.include_router(tasks.router, prefix="/tasks")
app.include_router(admissions.router, prefix="/admissions")
app.include_router(agent.router, prefix="/agent")
app.include_router(discharge.router, prefix="/discharge")
app.include_router(debug.router, prefix="/debug")

@app.get("/")
def root():
    return {"status": "backend running"}
