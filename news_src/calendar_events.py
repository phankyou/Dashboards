"""
calendar_events.py
------------------
Récupère les événements macro du calendrier économique via Finnhub.
Filtre les événements >= 2 étoiles et calcule le décompte avant chaque événement.
"""
from __future__ import annotations
import os
import requests
from datetime import datetime, timedelta, timezone


IMPACT_MAP = {"high": 3, "medium": 2, "low": 1}
MIN_IMPACT = 2  # on garde medium (2 étoiles) et high (3 étoiles)


def fetch_calendar(api_key: str, days_ahead: int = 2) -> list[dict]:
    today = datetime.now(timezone.utc)
    date_from = today.strftime("%Y-%m-%d")
    date_to = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    try:
        url = f"https://finnhub.io/api/v1/calendar/economic?from={date_from}&to={date_to}&token={api_key}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        raw = resp.json().get("economicCalendar", [])
    except Exception:
        return []

    events = []
    for ev in raw:
        impact_str = ev.get("impact", "low").lower()
        impact = IMPACT_MAP.get(impact_str, 1)
        if impact < MIN_IMPACT:
            continue

        time_str = ev.get("time", "")
        event_dt = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                event_dt = datetime.strptime(time_str, fmt).replace(tzinfo=timezone.utc)
                break
            except ValueError:
                continue

        if event_dt is None:
            continue

        delta = event_dt - today
        total_seconds = int(delta.total_seconds())
        if total_seconds < -3600:  # ignore les events passés depuis plus d'1h
            continue

        if total_seconds <= 0:
            countdown = "VIENT DE SORTIR"
            urgency = "danger"
        elif total_seconds < 3600:
            mins = total_seconds // 60
            countdown = f"{mins} min"
            urgency = "danger"
        elif total_seconds < 7200:
            hrs = total_seconds // 3600
            mins = (total_seconds % 3600) // 60
            countdown = f"{hrs}h{mins:02d}"
            urgency = "warning"
        else:
            hrs = total_seconds // 3600
            countdown = f"{hrs}h"
            urgency = "normal"

        events.append({
            "name": ev.get("event", "Événement inconnu"),
            "country": ev.get("country", ""),
            "currency": ev.get("currency", ""),
            "impact": impact,
            "stars": "★" * impact,
            "actual": ev.get("actual", ""),
            "estimate": ev.get("estimate", ""),
            "prev": ev.get("prev", ""),
            "event_dt": event_dt,
            "countdown": countdown,
            "urgency": urgency,
            "time_str": event_dt.strftime("%H:%M"),
            "date_str": event_dt.strftime("%d/%m"),
        })

    events.sort(key=lambda x: x["event_dt"])
    return events
