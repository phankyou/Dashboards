"""
main.py
-------
Orchestre tout le pipeline du News & Fundamental Dashboard :
1. Fear & Greed Index
2. Calendrier économique (Finnhub)
3. News financières + analyse fondamentale (Alpha Vantage + Groq)
4. Analyse d'impact des news (Groq)
5. Prix en direct (yfinance)
"""
from __future__ import annotations
import os

from news_src import fear_greed, calendar_events, news_analysis, megacap_alerts


def _get_secrets() -> dict:
    """
    Récupère les clés API depuis :
    - st.secrets (Streamlit Cloud)
    - Variables d'environnement (local avec .env ou export)
    """
    try:
        import streamlit as st
        return {
            "finnhub": st.secrets.get("FINNHUB_KEY", os.getenv("FINNHUB_KEY", "")),
            "alphavantage": st.secrets.get("AV_KEY", os.getenv("AV_KEY", "")),
            "groq": st.secrets.get("GROQ_KEY", os.getenv("GROQ_KEY", "")),
        }
    except Exception:
        return {
            "finnhub": os.getenv("FINNHUB_KEY", ""),
            "alphavantage": os.getenv("AV_KEY", ""),
            "groq": os.getenv("GROQ_KEY", ""),
        }


def run_pipeline() -> dict:
    """
    Exécute tout le pipeline et retourne un dict avec toutes les données
    nécessaires à l'affichage dans app.py.
    """
    secrets = _get_secrets()
    finnhub_key = secrets["finnhub"]
    av_key = secrets["alphavantage"]
    groq_key = secrets["groq"]

    results = {}

    # 1. Fear & Greed
    fg_data = fear_greed.fetch_fear_greed()
    results["fear_greed"] = fg_data

    # 2. Calendrier économique
    events = calendar_events.fetch_calendar(finnhub_key) if finnhub_key else []
    results["events"] = events

    # 3. Prix en direct
    prices = news_analysis.get_prices()
    results["prices"] = prices

    # 4. News financières
    news = news_analysis.fetch_news(av_key) if av_key else []
    results["news"] = news

    # 5. Analyse fondamentale (nécessite Groq + news)
    if groq_key and news:
        fundamental = news_analysis.analyze_fundamental(groq_key, news)
    else:
        fundamental = {}
    results["fundamental"] = fundamental

    # 6. Analyse d'impact sur les 3 premières news importantes
    impacts = []
    if groq_key:
        for n in news[:3]:
            impact = news_analysis.analyze_news_impact(
                groq_key, n["title"], n.get("summary", "")
            )
            impacts.append({"news": n, "impact": impact})
    results["impacts"] = impacts

    # 7. Alertes megacaps (earnings + profit warnings)
    megacap_data = megacap_alerts.get_megacap_alerts(news)
    results["earnings_today"] = megacap_data["earnings_today"]
    results["profit_warnings"] = megacap_data["profit_warnings"]
    results["impact_notes"] = megacap_data["impact_notes"]

    return results
