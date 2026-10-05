# ThermoLag — SIH 2026 Working Prototype

**Team Aikyam · SIH26083 · Team ID 119828**

This package is intentionally a **prototype**, not a production public-health system. It demonstrates the architecture from the SIH presentation:

- Ward-level UTCI/WBGT thermal stress (UTCI primary; WBGT for outdoor-labour module)
- Lagged, non-linear Heat-Health Risk Proxy with uncertainty (SB-DLNM-inspired demo; not a fitted local mortality model)
- Vulnerability-aware ward map
- 5-day forecast/timeline
- Plain-language “why this ward?” explanation
- Approval-gated CAP-style alert workflow
- CAP-compatible alert payload with simulated SMS/WhatsApp release; no real public alert is sent

The SIH deck explicitly positions the demo output as a **Heat-Health Risk Proxy** until local health-outcome data validates a calibrated Mortality Risk Index (MRI).

## Folder structure

```text
ThermoLag-SIH2026-Prototype/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── engine.py
│   │   ├── data.py
│   │   ├── alerts.py
│   │   └── __init__.py
│   ├── requirements.txt
│   ├── Procfile
│   └── render.yaml
└── frontend/
    ├── index.html
    ├── styles.css
    ├── app.js
    ├── config.js
    └── vercel.json
```

## Local run

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs to see the API.

### Frontend

Open a second terminal:

```bash
cd frontend
python -m http.server 5500
```

Open http://localhost:5500.

Before opening the frontend, `frontend/config.js` should contain:

```js
window.THERMOLAG_API = "http://localhost:8000";
```

## Prototype boundary

The risk engine is deliberately labelled a **Heat-Health Risk Proxy**. It is not fitted to local mortality/admission outcomes. The production pathway in the SIH proposal is to replace the proxy with a calibrated SB-DLNM/MRI after a city pilot supplies de-identified ward-day health counts.

## Alignment with SIH presentation

The prototype uses the presentation terminology: UTCI as the primary ward metric, WBGT for the outdoor-labour module, a lagged/non-linear Heat-Health Risk Proxy with uncertainty, a 5-day ward trend, vulnerability-aware GIS, and approval-gated CAP-compatible actions. It intentionally does **not** claim a calibrated Mortality Risk Index (MRI); that is a later pilot stage requiring de-identified ward-day health counts and city-approved thresholds.

The weather values and ward attributes are **demo scenario inputs** for the SIH prototype, not live IMD/ECMWF measurements. The deck describes IMD/ECMWF as the planned data-input layer.
