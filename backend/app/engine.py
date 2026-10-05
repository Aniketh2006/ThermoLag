"""ThermoLag demo thermal-stress and heat-health risk engine.

The prototype follows the SIH proposal architecture: UTCI/WBGT -> lagged,
non-linear risk proxy -> uncertainty -> ward action. It is deliberately NOT a
fitted mortality model; the UI labels the result as a Heat-Health Risk Proxy.
"""
from __future__ import annotations
import math
import random
from datetime import date, timedelta

TIERS = [
    (75.0, "extreme", "Extreme", "Red"),
    (50.0, "high", "High", "Orange"),
    (25.0, "moderate", "Moderate", "Yellow"),
    (0.0, "low", "Low", "Green"),
]

LAG_WEIGHTS = [0.34, 0.24, 0.18, 0.12, 0.07]


def _sat_vapour_pressure(temp_c: float) -> float:
    return 6.112 * math.exp((17.62 * temp_c) / (temp_c + 243.12))


def _utci_demo(temp_c: float, rh: float, wind_ms: float, solar: float) -> float:
    """Dependency-free UTCI-style estimate for the demo.

    The production plan in the SIH deck calls for Bröde UTCI. This compact
    implementation preserves the same physical inputs (air temperature,
    humidity, wind and radiant load) without pulling NumPy/Numba into the
    free-tier deployment. It is intended for prototype demonstration only.
    """
    vapour = _sat_vapour_pressure(temp_c) * max(0.0, min(rh, 100.0)) / 100.0
    radiant = 0.00065 * max(solar, 0.0)
    humidity_penalty = 0.045 * max(vapour - 15.0, 0.0)
    wind_relief = 0.85 * max(min(wind_ms, 8.0) - 1.0, 0.0)
    return round(temp_c + humidity_penalty + radiant - wind_relief, 1)


def wbgt_outdoor(temp_c: float, rh: float, wind_ms: float, solar: float) -> float:
    vapour = _sat_vapour_pressure(temp_c) * max(0.0, min(rh, 100.0)) / 100.0
    globe = temp_c + 0.30 * max(solar, 0.0) / 100.0 - 0.35 * min(wind_ms, 6.0)
    wet_bulb = temp_c * 0.52 + vapour * 0.28
    return round(0.7 * wet_bulb + 0.2 * globe + 0.1 * temp_c, 1)


def tier_for_score(score: float):
    for threshold, key, label, colour in TIERS:
        if score >= threshold:
            return key, label, colour
    return "low", "Low", "Green"


def vulnerability_index(ward: dict) -> float:
    elderly = min(ward["elderly_percent"] / 20.0, 1.0)
    workers = min(ward["outdoor_workers_percent"] / 50.0, 1.0)
    green_protection = min(ward["green_cover_percent"] / 35.0, 1.0)
    health_protection = min(ward["healthcare_access"] / 10.0, 1.0)
    return max(0.0, min(1.0, 0.55 * elderly + 0.35 * workers + 0.10 * (1-green_protection) + 0.10 * (1-health_protection)))


def base_score(utci: float, wbgt: float, ward: dict, lagged_utci: list[float], day_index: int) -> float:
    series = [utci] + lagged_utci[:4]
    weights = LAG_WEIGHTS[:len(series)]
    weighted = sum(w * u for w, u in zip(weights, series)) / sum(weights)
    # Demo calibration: action thresholds are intentionally visible in the
    # prototype so a heatwave scenario produces a useful Low→Extreme gradient.
    heat_exposure = max(0.0, weighted - 28.0) / 15.0
    nonlinear = max(0.0, heat_exposure) ** 1.25
    wbgt_component = max(0.0, wbgt - 24.0) / 11.0
    vuln = vulnerability_index(ward)
    resilience = 0.55 * min(ward["healthcare_access"] / 10.0, 1.0) + 0.30 * min(ward["green_cover_percent"] / 35.0, 1.0) + 0.15 * min(ward["cooling_centers"] / 12.0, 1.0)
    score = 100 * (0.78 * min(nonlinear, 1.0) + 0.18 * min(wbgt_component, 1.0) + 0.28 * vuln - 0.10 * resilience)
    # Urban heat-island proxy: sparse green cover amplifies ward exposure.
    score += (15.0 - ward["green_cover_percent"]) * 0.9
    # Forecast uncertainty grows with lead time, represented here as a small spread.
    score *= 1.0 + 0.018 * day_index
    return max(0.0, min(100.0, score))


def confidence_for(score: float, day_index: int) -> str:
    if day_index >= 4 or 25 <= score <= 55:
        return "Medium"
    return "High"


def assess_day(ward: dict, weather: dict, lagged_utci: list[float], day_index: int) -> dict:
    utci = _utci_demo(weather["temp_c"], weather["humidity"], weather["wind_ms"], weather["solar_wm2"])
    wbgt = wbgt_outdoor(weather["temp_c"], weather["humidity"], weather["wind_ms"], weather["solar_wm2"])
    score = base_score(utci, wbgt, ward, lagged_utci, day_index)
    rng = random.Random(f"{ward['id']}-{weather['date']}")
    spread = 4.0 + day_index * 1.6 + rng.uniform(0.0, 2.5)
    low = max(0.0, round(score - spread, 1))
    high = min(100.0, round(score + spread, 1))
    tier, label, colour = tier_for_score(score)
    vuln = vulnerability_index(ward)
    reasons = []
    if utci >= 40: reasons.append(f"peak UTCI {utci:.1f} °C")
    elif utci >= 32: reasons.append(f"UTCI {utci:.1f} °C")
    if wbgt >= 28: reasons.append(f"WBGT {wbgt:.1f} °C")
    if vuln >= 0.55: reasons.append("high vulnerable-group exposure")
    if day_index >= 2 and lagged_utci: reasons.append("lagged heat effects included")
    if not reasons: reasons.append("thermal stress remains below action threshold")
    return {
        "date": weather["date"], "label": weather["label"], "temp_c": weather["temp_c"],
        "humidity": weather["humidity"], "wind_ms": weather["wind_ms"], "solar_wm2": weather["solar_wm2"],
        "utci": utci, "wbgt": wbgt, "risk": {
            "score": round(score, 1), "tier": tier, "tier_label": label, "colour": colour,
            "ci_low": low, "ci_high": high, "confidence": confidence_for(score, day_index)
        },
        "reason": "; ".join(reasons).capitalize(),
    }


def recommendations(tier: str) -> list[str]:
    return {
        "extreme": [
            "Shift outdoor work to early morning/evening; stop heavy labour at midday.",
            "Open cooling centres and extend operating hours.",
            "Pre-position ambulances and alert hospitals for heat-illness surge capacity.",
            "Check on elderly residents and people living alone.",
            "Prepare anticipatory power-grid load management.",
        ],
        "high": [
            "Enforce shaded rest and hydration breaks for outdoor workers.",
            "Open designated cooling centres and verify water availability.",
            "Alert nearby hospitals to expect heat-illness cases.",
            "Prepare vulnerable-group advisory for official approval.",
        ],
        "moderate": [
            "Issue public hydration and heat-avoidance advisory.",
            "Confirm cooling-centre readiness and routine health surveillance.",
        ],
        "low": ["Continue routine monitoring and watch the next forecast update."],
    }[tier]


def scenario_weather(scenario: str, start: date | None = None) -> list[dict]:
    start = start or date.today()
    profiles = {
        "heatwave": {
            "temp": [38, 39, 41, 43, 45, 42], "rh": [34, 35, 33, 31, 30, 34],
            "wind": [2.4, 2.1, 1.8, 1.6, 1.7, 2.2], "solar": [620, 690, 760, 820, 800, 700]
        },
        "humid": {
            "temp": [34, 35, 36, 37, 36, 35], "rh": [68, 70, 73, 75, 72, 69],
            "wind": [2.5, 2.2, 2.0, 1.8, 2.1, 2.5], "solar": [520, 560, 590, 600, 570, 540]
        },
        "mild": {
            "temp": [31, 32, 33, 33, 32, 31], "rh": [48, 50, 52, 49, 46, 45],
            "wind": [3.2, 3.5, 3.7, 3.8, 3.4, 3.2], "solar": [450, 480, 500, 490, 470, 440]
        },
    }
    p = profiles.get(scenario, profiles["heatwave"])
    # SIH deck: 3–5 day advance warning / 5-day ward trend.
    labels = ["Today", "Tomorrow"] + [(start + timedelta(days=i)).strftime("%a %d %b") for i in range(2, 5)]
    return [{"date": (start + timedelta(days=i)).isoformat(), "label": labels[i], "temp_c": p["temp"][i], "humidity": p["rh"][i], "wind_ms": p["wind"][i], "solar_wm2": p["solar"][i]} for i in range(5)]


def build_forecast(wards: list[dict], scenario: str) -> dict:
    weather = scenario_weather(scenario)
    results = []
    for ward in wards:
        days = []
        lag = []
        for i, w in enumerate(weather):
            d = assess_day(ward, w, lag, i)
            days.append(d)
            lag = [d["utci"]] + lag[:4]
        results.append({
            **ward,
            "days": days,
            "current": days[0],
            "peak": max(days, key=lambda x: x["risk"]["score"]),
            "vulnerability_index": round(vulnerability_index(ward), 2),
            "recommended_actions": recommendations(max(days, key=lambda x: x["risk"]["score"])["risk"]["tier"]),
        })
    return results
