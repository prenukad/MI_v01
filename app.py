# app.py

from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import asyncio
from llm.mi_agent import MIDetectionAgent
from models.model import Incident
from datetime import datetime
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace * with your domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

class IncidentInput(BaseModel):
    incident_id: str
    summary: str
    description: str
    service_ci_name: str
    priority: int
    created_at: str
    status: str
    assigned_to: str
    affected_users: List[str]

@app.post("/analyze")
async def analyze_incident(incident_data: IncidentInput):
    print("Received incident:", incident_data.dict())
    incident = Incident(**incident_data.dict())
    agent = MIDetectionAgent()
    
    try:
        result = await agent.detect_major_incident(incident)
        return {
            "incident_id": incident.incident_id,
            "is_major_incident": result.is_major_incident
        }
    except Exception as e:
        return {"error": str(e)}

#@app.get("/", response_class=HTMLResponse)
#async def root():
#    return "<h2>MI Detection API is running.</h2><p>Use POST /analyze to detect incidents.</p>"


@app.get("/")
def read_root():
    return {"message": "It works!"}