"""
fear_greed.py
-------------
Récupère l'indice Fear & Greed via l'API gratuite Alternative.me.
Pas de clé API nécessaire.
"""
from __future__ import annotations
import requests


def fetch_fear_greed() -> dict | None:
    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        resp.raise_for_status()
        data = resp.json()["data"][0]
        value = int(data["value"])
        label = data["value_classification"]

        if value <= 25:
            color = "#A32D2D"
            bg = "#FCEBEB"
            impact = (
                "Peur extrême — signal contrarian haussier à moyen terme historiquement. "
                "Volatilité élevée sur SPX et Nasdaq. L'or bénéficie de la fuite vers la valeur refuge."
            )
        elif value <= 45:
            color = "#E24B4A"
            bg = "#FCEBEB"
            impact = (
                "Peur dominante — les marchés sont sous pression vendeur. "
                "SPX et Nasdaq vulnérables à court terme. L'or soutenu. "
                "Historiquement, les niveaux de peur précèdent souvent des rebonds."
            )
        elif value <= 55:
            color = "#BA7517"
            bg = "#FAEEDA"
            impact = (
                "Sentiment neutre — pas de signal directionnel fort. "
                "Les marchés attendent un catalyseur. Surveille les prochaines publications macro."
            )
        elif value <= 75:
            color = "#3B6D11"
            bg = "#EAF3DE"
            impact = (
                "Avidité — appétit au risque présent. SPX et Nasdaq soutenus. "
                "L'or sous légère pression (rotation vers les actifs risqués). "
                "Attention aux excès de valorisation."
            )
        else:
            color = "#085041"
            bg = "#E1F5EE"
            impact = (
                "Avidité extrême — signal de prudence. Les marchés sont euphoriques, "
                "ce qui précède souvent une correction. Réduction d'exposition conseillée "
                "et renforcement de l'or comme protection."
            )

        return {
            "value": value,
            "label": label,
            "color": color,
            "bg": bg,
            "impact": impact,
            "pct": min(100, max(0, value)),
        }
    except Exception:
        return None


def interpret_fear_greed(data: dict) -> str:
    lines = ["## 😰 Indice Fear & Greed", ""]
    lines.append(f"**Valeur : {data['value']}/100 — {data['label']}**")
    lines.append("")
    lines.append(f"→ {data['impact']}")
    return "\n".join(lines)
