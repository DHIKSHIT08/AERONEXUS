from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

DATABASE = Path(__file__).with_name("aeronexus.db")

app = FastAPI(
    title="AERONEXUS Demo API",
    description="Local API for an isolated, fictional aircraft systems simulator.",
    version="1.0.0",
)

# Allow a local browser preview to call the local API.
# The public GitHub Pages site will be connected separately later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

DEFAULTS = {
    "altitude_ft": 35000,
    "airspeed_kts": 450,
    "heading_deg": 89,
    "throttle_pct": 72,
    "flaps_deg": 0,
    "fuel_pct": 76,
}

state = {**DEFAULTS, "anomalies": set()}


class ControlUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    altitude_ft: int | None = Field(default=None, ge=10000, le=41000)
    airspeed_kts: int | None = Field(default=None, ge=200, le=500)
    heading_deg: int | None = Field(default=None, ge=0, le=359)
    throttle_pct: int | None = Field(default=None, ge=35, le=90)
    flaps_deg: int | None = Field(default=None, ge=0, le=30)


def initialize_database():
    with sqlite3.connect(DATABASE) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_utc TEXT NOT NULL,
                category TEXT NOT NULL,
                message TEXT NOT NULL
            )
            """
        )


def record_event(category: str, message: str):
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(DATABASE) as connection:
        connection.execute(
            "INSERT INTO events (time_utc, category, message) VALUES (?, ?, ?)",
            (timestamp, category, message),
        )


def snapshot():
    anomalies = state["anomalies"]
    engine1_temp = 570 + state["throttle_pct"] + (130 if "engine" in anomalies else 0)
    engine2_temp = 586 + state["throttle_pct"] + (125 if "engine" in anomalies else 0)
    hydraulic_psi = 1800 if "hydraulic" in anomalies else 3000
    electrical_volts = 20.4 if "electrical" in anomalies else 28.0
    fuel_pct = 18 if "fuel" in anomalies else state["fuel_pct"]

    return {
        "aircraft_profile": "B757-style fictional demo",
        "simulation_only": True,
        "altitude_ft": state["altitude_ft"],
        "airspeed_kts": state["airspeed_kts"],
        "heading_deg": state["heading_deg"],
        "throttle_pct": state["throttle_pct"],
        "flaps_deg": state["flaps_deg"],
        "fuel_pct": fuel_pct,
        "engine1_egt_c": engine1_temp,
        "engine2_egt_c": engine2_temp,
        "hydraulic_pressure_psi": hydraulic_psi,
        "electrical_bus_volts": electrical_volts,
        "active_demo_scenarios": sorted(anomalies),
        "real_aircraft_connected": False,
    }


def analyze():
    data = snapshot()
    findings = []

    if data["engine1_egt_c"] >= 760 or data["engine2_egt_c"] >= 760:
        findings.append("Example engine temperature crossed the demo review threshold.")
    if data["hydraulic_pressure_psi"] < 2300:
        findings.append("Example hydraulic pressure crossed the demo review threshold.")
    if data["fuel_pct"] < 25:
        findings.append("Example fuel quantity crossed the demo review threshold.")
    if data["electrical_bus_volts"] < 24:
        findings.append("Example electrical value crossed the demo review threshold.")
    if not findings:
        findings.append("All fictional values are within the demo thresholds.")

    return {
        "analysis_type": "local rule-based demonstration",
        "read_only": True,
        "findings": findings,
        "operational_guidance": False,
        "real_aircraft_connected": False,
    }


initialize_database()
record_event("system", "AERONEXUS local demo API started.")


@app.get("/")
def home():
    return {
        "name": "AERONEXUS Demo API",
        "message": "Fictional simulator data only.",
        "documentation": "/docs",
        "real_aircraft_connected": False,
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "simulation_only": True}


@app.get("/api/state")
def get_state():
    return snapshot()


@app.post("/api/controls")
def update_controls(update: ControlUpdate):
    changes = {
        key: value
        for key, value in update.model_dump(exclude_unset=True).items()
        if value is not None
    }

    if not changes:
        raise HTTPException(status_code=400, detail="Provide at least one demo value.")

    state.update(changes)
    record_event("control", "Virtual demo values updated: " + ", ".join(changes.keys()))
    return snapshot()


@app.post("/api/scenarios/{scenario}")
def activate_scenario(scenario: str):
    allowed = {"engine", "hydraulic", "fuel", "electrical"}

    if scenario not in allowed:
        raise HTTPException(
            status_code=404,
            detail="Choose engine, hydraulic, fuel, or electrical.",
        )

    state["anomalies"].add(scenario)
    record_event("scenario", "Fictional " + scenario + " scenario activated.")
    return snapshot()


@app.post("/api/reset")
def reset_simulation():
    state.update(DEFAULTS)
    state["anomalies"] = set()
    record_event("system", "Fictional simulator values reset.")
    return snapshot()


@app.get("/api/analysis")
def get_analysis():
    return analyze()


@app.get("/api/events")
def get_events(limit: int = Query(default=50, ge=1, le=200)):
    with sqlite3.connect(DATABASE) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, time_utc, category, message
            FROM events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return {"events": [dict(row) for row in rows]}
