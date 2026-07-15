"""
news_analysis.py
----------------
Récupère les news financières via RSS (Yahoo Finance, Reuters) — sans restriction IP.
Analyse l'impact sur SPX, Gold et Nasdaq via Groq (gratuit, Llama 3).
"""
from __future__ import annotations
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ASSETS = ["SPX", "Gold", "Nasdaq"]
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

RSS_FEEDS = [
    ("Yahoo Finance Markets", "https://finance.yahoo.com/news/rssindex"),
    ("Yahoo Finance SPX", "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US"),
    ("Yahoo Finance Gold", "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F&region=US&lang=en-US"),
    ("Yahoo Finance NDX", "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^NDX&region=US&lang=en-US"),
]

TICKERS = {
    "SPX":    "SPY",
    "Gold":   "GLD",
    "Nasdaq": "QQQ",
}


def fetch_news(av_key: str = "", limit: int = 10) -> list[dict]:
    """
    Récupère les dernières news financières via RSS Yahoo Finance.
    Le paramètre av_key est conservé pour compatibilité mais non utilisé.
    """
    news = []
    seen_titles = set()

    for source_name, url in RSS_FEEDS:
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                continue
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")
            for item in items[:5]:
                title = item.findtext("title", "").strip()
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)
                desc = item.findtext("description", "").strip()
                pub_date = item.findtext("pubDate", "")
                link = item.findtext("link", "")
                news.append({
                    "title": title,
                    "summary": desc[:400] if desc else "",
                    "source": source_name,
                    "url": link,
                    "time": pub_date,
                    "sentiment": "Neutral",
                    "sentiment_score": 0.0,
                })
        except Exception:
            continue

    return news[:limit]


def analyze_with_groq(groq_key: str, prompt: str) -> str:
    """Envoie un prompt à Groq et retourne la réponse texte."""
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 700,
        "temperature": 0.3,
    }
    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=body, timeout=30)
        if resp.status_code != 200:
            return f"ERREUR Groq {resp.status_code}: {resp.text[:200]}"
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"ERREUR connexion Groq: {str(e)[:200]}"


def analyze_fundamental(groq_key: str, news_list: list[dict]) -> dict:
    """Génère une analyse fondamentale pour SPX, Gold et Nasdaq."""
    news_text = "\n".join(
        f"- {n['title']}" for n in news_list[:8]
    )

    prompt = f"""Tu es un analyste financier expert. Voici les dernières news des marchés financiers :

{news_text}

Pour chaque actif ci-dessous, donne en JSON (UNIQUEMENT du JSON, pas de texte autour) :
- "bias" : "haussier", "baissier" ou "neutre"
- "facteurs_positifs" : liste de 2-3 points courts
- "risques" : liste de 2-3 points courts  
- "verdict" : 1 phrase de synthèse concrète pour le trader

Format exact attendu :
{{
  "SPX": {{"bias": "...", "facteurs_positifs": ["...", "..."], "risques": ["...", "..."], "verdict": "..."}},
  "Gold": {{"bias": "...", "facteurs_positifs": ["...", "..."], "risques": ["...", "..."], "verdict": "..."}},
  "Nasdaq": {{"bias": "...", "facteurs_positifs": ["...", "..."], "risques": ["...", "..."], "verdict": "..."}}
}}"""

    raw = analyze_with_groq(groq_key, prompt)

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception:
        pass

    return {
        asset: {
            "bias": "neutre",
            "facteurs_positifs": [raw[:100] if raw.startswith("ERREUR") else "Analyse en cours"],
            "risques": ["—"],
            "verdict": raw[:200] if raw.startswith("ERREUR") else "Réessaie dans quelques instants.",
        }
        for asset in ASSETS
    }


def analyze_news_impact(groq_key: str, news_title: str, news_summary: str) -> dict:
    """Analyse l'impact d'une news spécifique sur SPX, Gold et Nasdaq."""
    prompt = f"""Tu es un analyste financier expert. Analyse l'impact de cette news sur les marchés :

Titre : {news_title}
Résumé : {news_summary[:300] if news_summary else "Non disponible"}

Réponds UNIQUEMENT en JSON au format exact suivant :
{{
  "SPX": {{"direction": "haussier", "explication": "1 phrase"}},
  "Gold": {{"direction": "neutre", "explication": "1 phrase"}},
  "Nasdaq": {{"direction": "baissier", "explication": "1 phrase"}},
  "interpretation": "2-3 phrases d'analyse globale"
}}
Les valeurs de direction doivent être exactement : "haussier", "baissier" ou "neutre"."""

    raw = analyze_with_groq(groq_key, prompt)

    if raw.startswith("ERREUR"):
        return {
            "SPX": {"direction": "neutre", "explication": "—"},
            "Gold": {"direction": "neutre", "explication": "—"},
            "Nasdaq": {"direction": "neutre", "explication": "—"},
            "interpretation": f"Erreur API : {raw[:200]}",
        }

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception as e:
        return {
            "SPX": {"direction": "neutre", "explication": "—"},
            "Gold": {"direction": "neutre", "explication": "—"},
            "Nasdaq": {"direction": "neutre", "explication": "—"},
            "interpretation": f"Réponse Groq reçue mais JSON invalide. Réessaie.",
        }

    return {
        "SPX": {"direction": "neutre", "explication": "—"},
        "Gold": {"direction": "neutre", "explication": "—"},
        "Nasdaq": {"direction": "neutre", "explication": "—"},
        "interpretation": f"Analyse indisponible.",
    }


def get_prices() -> dict:
    """Récupère les prix actuels de SPY, GLD, QQQ via yfinance."""
    try:
        import yfinance as yf
        result = {}
        for asset, ticker in TICKERS.items():
            hist = yf.Ticker(ticker).history(period="2d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
                chg_pct = (price - prev) / prev * 100
                result[asset] = {"price": price, "change_pct": chg_pct, "ticker": ticker}
        return result
    except Exception:
        return {}
