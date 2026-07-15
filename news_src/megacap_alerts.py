"""
megacap_alerts.py
------------------
Detection des earnings programmes et profit warnings pour une watchlist
de mega caps US, avec interpretation de l'impact sur SPX, Gold, Nasdaq.
"""
from __future__ import annotations
from datetime import datetime

MEGACAPS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

COMPANY_NAMES = {
    "AAPL": ["apple"],
    "MSFT": ["microsoft"],
    "GOOGL": ["google", "alphabet"],
    "AMZN": ["amazon"],
    "NVDA": ["nvidia"],
    "META": ["meta", "facebook"],
    "TSLA": ["tesla"],
}

WARNING_KEYWORDS = [
    "profit warning", "guidance cut", "lowers guidance", "lowers outlook",
    "cuts forecast", "misses estimates", "warns on", "slashes forecast",
    "below expectations", "disappointing results",
]

IMPACT_NOTES = {
    "earnings": {
        "SPX": "impact modere, poids dilue dans le S&P 500",
        "Gold": "impact quasi nul, sauf choc de risk-off generalise",
        "Nasdaq": "impact direct, poids important dans le Nasdaq-100",
    },
    "warning": {
        "SPX": "impact limite si l'entreprise pese peu dans l'indice",
        "Gold": "aucun lien direct sauf mouvement de risk-off large",
        "Nasdaq": "pression baissiere probable si le titre est pondere",
    },
}


def compute_countdown_to_us_close() -> str:
    now = datetime.now()
    close_today = now.replace(hour=22, minute=0, second=0, microsecond=0)
    if now >= close_today:
        return "cloture US passee"
    delta = close_today - now
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return f"dans {hours}h {minutes:02d}min"


def get_todays_earnings() -> list[dict]:
    results = []
    try:
        import yfinance as yf
        today = datetime.now().date()
        for ticker in MEGACAPS:
            try:
                cal = yf.Ticker(ticker).get_earnings_dates(limit=4)
                if cal is None or cal.empty:
                    continue
                for idx in cal.index:
                    if idx.date() == today:
                        results.append({
                            "ticker": ticker,
                            "date": idx.date(),
                            "countdown": compute_countdown_to_us_close(),
                        })
                        break
            except Exception:
                continue
    except Exception:
        pass
    return results


def detect_profit_warnings(news_list: list[dict]) -> list[dict]:
    warnings_found = []
    for n in news_list:
        title_lower = n.get("title", "").lower()
        has_warning_kw = any(kw in title_lower for kw in WARNING_KEYWORDS)
        if not has_warning_kw:
            continue
        for ticker, names in COMPANY_NAMES.items():
            if any(name in title_lower for name in names):
                warnings_found.append({
                    "ticker": ticker,
                    "title": n.get("title", ""),
                    "time": n.get("time", ""),
                    "source": n.get("source", ""),
                })
                break
    return warnings_found


def get_megacap_alerts(news_list: list[dict]) -> dict:
    return {
        "earnings_today": get_todays_earnings(),
        "profit_warnings": detect_profit_warnings(news_list),
        "impact_notes": IMPACT_NOTES,
    }
