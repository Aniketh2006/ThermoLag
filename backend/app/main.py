from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from .data import WARDS
from .engine import build_forecast, recommendations, _utci_demo, wbgt_outdoor
from .alerts import create_draft, list_alerts, get, decide, cap_xml

app = FastAPI(title="ThermoLag Demo API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

class AlertDraft(BaseModel):
    ward_id: str
    date: str
    scenario: str = "heatwave"

class AlertDecision(BaseModel):
    approve: bool
    official: str = Field(default="City official (demo)", max_length=80)
    note: str | None = Field(default=None, max_length=300)

class ThermalInput(BaseModel):
    temp_c: float
    humidity: float
    wind_ms: float
    solar_wm2: float = 600

@app.get("/")
def root():
    return {"name":"ThermoLag", "status":"ok", "mode":"prototype", "risk_model":"Heat-Health Risk Proxy"}

@app.get("/health")
def health(): return {"status":"healthy"}

@app.get("/api/dashboard")
def dashboard(scenario: str = Query("heatwave", pattern="^(heatwave|humid|mild)$")):
    wards = build_forecast(WARDS, scenario)
    current = [w["current"] for w in wards]
    high = sum(1 for d in current if d["risk"]["tier"] in ("high","extreme"))
    extreme = sum(1 for d in current if d["risk"]["tier"] == "extreme")
    peak = max((d for w in wards for d in w["days"]), key=lambda d:d["risk"]["score"])
    return {
        "scenario": scenario, "model_note":"Demo-phase Heat-Health Risk Proxy; not a mortality estimate. Calibrated MRI requires local de-identified ward-day health data.",
        "wards": wards,
        "summary": {"ward_count":len(wards),"high_or_extreme_now":high,"extreme_now":extreme,"peak_score":peak["risk"]["score"],"peak_date":peak["date"],"peak_utci":peak["utci"]},
        "brief":[
            f"{high} of {len(wards)} wards are High or Extreme today.",
            f"Forecast peak reaches {peak['risk']['score']}/100 on {peak['label']} with UTCI {peak['utci']:.1f} °C.",
            "Risk uses lagged, non-linear thermal exposure, vulnerability and resilience with an uncertainty band.",
            "Alerts remain in draft until a city official approves them; CAP/SMS/WhatsApp release is simulated in this prototype.",
        ]
    }

@app.get("/api/wards")
def wards(): return {"wards":WARDS}

@app.get("/api/wards/{ward_id}")
def ward_detail(ward_id: str, scenario: str = Query("heatwave", pattern="^(heatwave|humid|mild)$")):
    for w in build_forecast(WARDS, scenario):
        if w["id"] == ward_id: return w
    raise HTTPException(404,"Ward not found")

@app.post("/api/thermal")
def thermal(payload: ThermalInput):
    if not 20 <= payload.temp_c <= 55: raise HTTPException(400,"Temperature outside demo range")
    utci = _utci_demo(payload.temp_c,payload.humidity,payload.wind_ms,payload.solar_wm2)
    wbgt = wbgt_outdoor(payload.temp_c,payload.humidity,payload.wind_ms,payload.solar_wm2)
    return {"utci":utci,"wbgt":wbgt,"note":"Prototype thermal engine using the UTCI physical inputs; production calibration should use the validated Bröde implementation."}

@app.get("/api/alerts")
def alerts(): return {"alerts":list_alerts()}

@app.post("/api/alerts/draft")
def draft(payload: AlertDraft):
    data = next((w for w in build_forecast(WARDS,payload.scenario) if w["id"]==payload.ward_id),None)
    if not data: raise HTTPException(404,"Ward not found")
    day = next((d for d in data["days"] if d["date"]==payload.date),None)
    if not day: raise HTTPException(404,"Forecast day not found")
    return create_draft(data,day)

@app.post("/api/alerts/{alert_id}/decision")
def decision(alert_id: str, payload: AlertDecision):
    try: result=decide(alert_id,payload.approve,payload.official,payload.note)
    except ValueError as e: raise HTTPException(409,str(e))
    if not result: raise HTTPException(404,"Alert not found")
    return result

@app.get("/api/alerts/{alert_id}/cap.xml")
def cap(alert_id: str):
    a=get(alert_id)
    if not a: raise HTTPException(404,"Alert not found")
    return Response(cap_xml(a),media_type="application/xml")
