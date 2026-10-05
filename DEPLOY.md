# ThermoLag deployment — easiest free prototype setup

## Recommended architecture

**Frontend → Vercel**  
**Backend API → Render Free Web Service**

This is the cleanest prototype split: Vercel serves the fast static dashboard, while Render runs the Python FastAPI API. Render currently offers free web services for testing/hobby/prototype use, but free services spin down after 15 minutes without traffic, so the first request after idle can be slow. Vercel also supports FastAPI directly, but keeping the API on Render makes this package easier to understand and debug.

---

## PART 1 — Put the ZIP on GitHub

1. Create a GitHub repository, for example `thermolag-sih2026`.
2. Extract this ZIP.
3. Upload the **contents of `ThermoLag-SIH2026-Prototype`** to the repository root.
4. Commit and push.

Your GitHub repository should show:

```text
backend/
frontend/
DEPLOY.md
README.md
```

---

## PART 2 — Deploy the backend on Render

1. Open Render and sign in with GitHub.
2. Click **New → Web Service**.
3. Select your `thermolag-sih2026` repository.
4. Use these settings:

| Setting | Value |
|---|---|
| Name | `thermolag-api` |
| Root Directory | `backend` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Plan | `Free` |
| Health Check Path | `/health` |

5. Click **Create Web Service**.
6. Wait for the deploy to finish.
7. Copy the Render URL, for example:

```text
https://thermolag-api.onrender.com
```

8. Test it in your browser:

```text
https://YOUR-RENDER-URL/health
```

You should see:

```json
{"status":"healthy"}
```

Also test:

```text
https://YOUR-RENDER-URL/docs
```

You should see the FastAPI Swagger page.

> If the first request takes a while, wait. Render's free service can sleep after inactivity and needs to wake up again.

---

## PART 3 — Connect the Vercel frontend to Render

Open:

```text
frontend/config.js
```

Change:

```js
window.THERMOLAG_API = "http://localhost:8000";
```

to:

```js
window.THERMOLAG_API = "https://YOUR-RENDER-URL";
```

Do **not** add a trailing `/`.

Commit and push the change to GitHub.

---

## PART 4 — Deploy the frontend on Vercel

1. Open Vercel and sign in with GitHub.
2. Click **Add New → Project**.
3. Import your `thermolag-sih2026` repository.
4. Set **Root Directory** to:

```text
frontend
```

5. Framework Preset: **Other** (this is a static HTML/CSS/JS dashboard).
6. Build Command: leave empty.
7. Output Directory: leave empty.
8. Click **Deploy**.

Vercel will give you a URL such as:

```text
https://thermolag-sih2026.vercel.app
```

Open it.

---

## PART 5 — Demo flow for SIH

Use this exact flow during the presentation:

### 1. Start on the dashboard

Show:

- Ward count
- High/Extreme wards
- Peak risk proxy
- Delhi ward map

### 2. Click a red/orange ward

Show:

- Risk score
- UTCI
- WBGT
- Humidity
- Wind
- Vulnerability
- Plain-language reason

### 3. Change scenario

Top-right:

- **Heatwave** → strongest escalation
- **Humid heat** → demonstrates humidity contribution
- **Mild baseline** → shows lower risk

### 4. Show the 5-day forecast

Point out that ThermoLag is designed around a **3–5 day warning horizon** and shows the risk trajectory rather than only today's temperature.

### 5. Create an alert

Click:

**Create approval-gated alert**

This creates a draft in the Approval Queue.

### 6. Approve it

Click **Approve**.

The UI changes the alert to a simulated released state and provides a **CAP** view.

Important: this prototype does **not** send SMS, WhatsApp or NDMA Sachet alerts. The release is simulated so you can safely demonstrate the workflow.

---

## PART 6 — What to say if judges ask “Is this the actual mortality model?”

Say:

> “For the prototype we deliberately label the output as a Heat-Health Risk Proxy. The production architecture is SB-DLNM-based, but we will only calibrate a Mortality Risk Index after a city pilot provides de-identified ward-day health outcomes. This avoids false precision.”

That matches the boundary stated in the SIH solution.

---

## Troubleshooting

### Frontend says API not reachable

Check `frontend/config.js` and make sure the Render URL is correct.

Then open the Render URL directly:

```text
https://YOUR-RENDER-URL/health
```

### Render build fails

Confirm:

```text
Root Directory: backend
Build: pip install -r requirements.txt
Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Vercel shows an old API URL

Push the updated `frontend/config.js` to GitHub and redeploy the Vercel project.

### Map tiles do not appear

The map uses OpenStreetMap tiles. The application itself can still load if the tile provider is temporarily unavailable.
