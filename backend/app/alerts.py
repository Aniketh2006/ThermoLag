from __future__ import annotations
from datetime import datetime, timezone
from xml.sax.saxutils import escape
import uuid

STORE: dict[str, dict] = {}

def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def create_draft(ward: dict, day: dict) -> dict:
    aid = "TL-" + uuid.uuid4().hex[:8].upper()
    alert = {
        "id": aid, "status": "pending_approval", "created": _now(),
        "ward_id": ward["id"], "ward_name": ward["name"], "date": day["date"],
        "tier": day["risk"]["tier"], "tier_label": day["risk"]["tier_label"],
        "headline": f"{day['risk']['tier_label']} heat-health risk proxy — {ward['name']}",
        "reason": day["reason"], "utci": day["utci"], "wbgt": day["wbgt"],
        "score": day["risk"]["score"], "confidence": day["risk"]["confidence"],
        "actions": ward["recommended_actions"], "decided_by": None, "decided_at": None, "note": None,
    }
    alert["cap"] = build_cap(alert, status="Draft", scope="Restricted")
    STORE[aid] = alert
    return alert

def build_cap(a: dict, status="Draft", scope="Restricted") -> dict:
    return {
        "identifier": a["id"], "sender": "ThermoLag-Demo", "sent": a.get("decided_at") or a["created"],
        "status": status, "msgType": "Alert", "scope": scope,
        "info": {
            "language":"en-IN", "category":"Health", "event":"Heat-Health Risk Proxy",
            "responseType":"Prepare", "urgency":"Expected" if a["tier"] in ("high","extreme") else "Future",
            "severity":"Extreme" if a["tier"]=="extreme" else "Severe" if a["tier"]=="high" else "Moderate" if a["tier"]=="moderate" else "Minor",
            "certainty":"Likely" if a["confidence"]=="High" else "Possible",
            "effective":a["date"], "headline":a["headline"],
            "description":f"Heat-Health Risk Proxy score {a['score']}/100; UTCI {a['utci']} °C; WBGT {a['wbgt']} °C. {a['reason']}",
            "instruction":" ".join(a["actions"]), "area":{"areaDesc":a["ward_name"]+", Delhi","geocode":a["ward_id"]}
        }
    }

def list_alerts(): return sorted(STORE.values(), key=lambda x:x["created"], reverse=True)
def get(aid): return STORE.get(aid)

def decide(aid: str, approve: bool, official: str, note: str|None):
    a = STORE.get(aid)
    if not a: return None
    if a["status"] != "pending_approval": raise ValueError("Alert has already been decided")
    a["status"] = "released" if approve else "rejected"
    a["decided_by"] = official or "City official (demo)"
    a["decided_at"] = _now(); a["note"] = note
    a["cap"] = build_cap(a, status="Actual" if approve else "Cancelled", scope="Public" if approve else "Restricted")
    a["released_via"] = ["CAP feed (simulated)", "SMS/WhatsApp (simulated)", "NDMA Sachet (planned)"] if approve else []
    return a

def cap_xml(a: dict) -> str:
    c, i = a["cap"], a["cap"]["info"]
    e=escape
    return f'''<?xml version="1.0" encoding="UTF-8"?>\n<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">\n  <identifier>{e(c['identifier'])}</identifier>\n  <sender>{e(c['sender'])}</sender>\n  <sent>{e(c['sent'])}</sent>\n  <status>{e(c['status'])}</status>\n  <msgType>{e(c['msgType'])}</msgType>\n  <scope>{e(c['scope'])}</scope>\n  <info>\n    <language>{e(i['language'])}</language>\n    <category>{e(i['category'])}</category>\n    <event>{e(i['event'])}</event>\n    <responseType>{e(i['responseType'])}</responseType>\n    <urgency>{e(i['urgency'])}</urgency>\n    <severity>{e(i['severity'])}</severity>\n    <certainty>{e(i['certainty'])}</certainty>\n    <effective>{e(i['effective'])}</effective>\n    <headline>{e(i['headline'])}</headline>\n    <description>{e(i['description'])}</description>\n    <instruction>{e(i['instruction'])}</instruction>\n    <area><areaDesc>{e(i['area']['areaDesc'])}</areaDesc><geocode><valueName>WARD</valueName><value>{e(i['area']['geocode'])}</value></geocode></area>\n  </info>\n</alert>'''
