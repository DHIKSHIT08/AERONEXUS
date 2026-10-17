
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

app = FastAPI(
    title="AERONEX API",
    description="AERONEX educational aircraft systems simulator",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dhikshit08.github.io"
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
)

@app.get("/")
def home():
    return {
        "app": "AERONEX",
        "status": "online",
        "mode": "simulation_only"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/telemetry")
def telemetry():
    return {
        "flight": "AX-204-DEMO",
        "aircraft": "Boeing 757-style simulation",
        "altitude_ft": 35000,
        "airspeed_kts": 450,
        "engine_1_temp_c": 642,
        "engine_2_temp_c": 658,
        "hydraulic_pressure_psi": 3000,
        "source": "simulated",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/analysis")
def analysis():
    return {
        "result": "No demo anomalies detected",
        "mode": "rule_based_demo",
        "certified_diagnostic": False
    }
