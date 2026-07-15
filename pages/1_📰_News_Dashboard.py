"""
app.py
------
News & Fundamental Dashboard — thème Teal & Violet.
Accessible depuis n'importe quel appareil via Streamlit Cloud.
"""

import streamlit as st
from news_src.main import run_pipeline

st.set_page_config(
    page_title="News & Fundamental Dashboard",
    layout="wide",
    page_icon="📰",
)

# --- CSS thème Teal & Violet ---
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #0F6E56 0%, #534AB7 100%);
    padding: 14px 20px;
    border-radius: 12px;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.main-header h1 { color: #E1F5EE; font-size: 20px; margin: 0; }
.main-header p { color: #9FE1CB; font-size: 12px; margin: 2px 0 0; }

.section-title {
    font-size: 15px; font-weight: 500;
    color: #0F6E56; margin: 1rem 0 0.6rem;
    display: flex; align-items: center; gap: 6px;
}

.card {
    background: var(--background-color);
    border: 0.5px solid rgba(29,158,117,0.3);
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
}

.bias-haussier { color: #1D9E75; font-weight: 500; }
.bias-baissier { color: #E24B4A; font-weight: 500; }
.bias-neutre   { color: #BA7517; font-weight: 500; }

.impact-box {
    background: rgba(29,158,117,0.08);
    border-left: 3px solid #1D9E75;
    border-radius: 0 8px 8px 0;
    padding: 10px 12px;
    font-size: 13px;
    margin-top: 8px;
}
.impact-box-warning {
    background: rgba(186,117,23,0.08);
    border-left: 3px solid #BA7517;
}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="main-header">
  <div>
    <h1>📰 News & Fundamental Dashboard</h1>
    <p>SPX · Or · Nasdaq — Analyses fondamentales, calendrier macro, impact des news</p>
  </div>
</div>
""", unsafe_allow_html=True)

# --- Bouton Actualiser ---
col_btn, _ = st.columns([1, 4])
with col_btn:
    refresh = st.button("🔄 Actualiser", type="primary", use_container_width=True)

if refresh:
    with st.spinner("Récupération des données et analyses en cours..."):
        try:
            data = run_pipeline()
            st.session_state["data"] = data
        except Exception as e:
            st.error(f"Erreur : {e}")

if "data" not in st.session_state:
    st.info("Clique sur **🔄 Actualiser** pour lancer l'analyse.")
    st.stop()

data = st.session_state["data"]

# =============================================
# SECTION 1 : FEAR & GREED
# =============================================
st.markdown('<p class="section-title">😰 Indice Fear & Greed</p>', unsafe_allow_html=True)

fg = data.get("fear_greed")
if fg:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("Fear & Greed", f"{fg['value']} / 100")
        label_color = fg["color"]
        st.markdown(
            f'<div style="background:{fg["bg"]};color:{label_color};padding:4px 10px;'
            f'border-radius:6px;font-size:13px;font-weight:500;text-align:center;">'
            f'{fg["label"]}</div>',
            unsafe_allow_html=True,
        )
    with col2:
        # Jauge
        pct = fg["pct"]
        pct_normal = 25
        pct_neutre = 55
        st.markdown(f"""
<div style="margin:8px 0 4px;">
  <div style="display:flex;justify-content:space-between;font-size:11px;color:#888;margin-bottom:4px;">
    <span>Peur extrême</span><span>Peur</span><span>Neutre</span><span>Avidité</span><span>Avidité extrême</span>
  </div>
  <div style="height:10px;border-radius:5px;overflow:hidden;display:flex;">
    <div style="width:20%;background:#A32D2D;"></div>
    <div style="width:20%;background:#E24B4A;"></div>
    <div style="width:20%;background:#BA7517;"></div>
    <div style="width:20%;background:#3B6D11;"></div>
    <div style="width:20%;background:#085041;"></div>
  </div>
  <div style="position:relative;height:20px;margin-top:2px;">
    <div style="position:absolute;left:calc({pct}% - 1px);top:0;width:2px;height:14px;background:{fg['color']};border-radius:1px;"></div>
    <span style="position:absolute;left:calc({pct}% + 4px);top:1px;font-size:12px;font-weight:500;color:{fg['color']};">{pct} ←</span>
  </div>
</div>
<div class="impact-box" style="margin-top:6px;">
  <strong>Impact sur les marchés :</strong> {fg['impact']}
</div>
""", unsafe_allow_html=True)

st.divider()

# =============================================
# SECTION 2 : ANALYSE FONDAMENTALE
# =============================================
st.markdown('<p class="section-title">📈 Analyse fondamentale</p>', unsafe_allow_html=True)

prices = data.get("prices", {})
fundamental = data.get("fundamental", {})

ASSET_STYLE = {
    "SPX":    {"color": "#1D9E75", "bg": "#E1F5EE", "dark": "#085041"},
    "Gold":   {"color": "#BA7517", "bg": "#FAEEDA", "dark": "#633806"},
    "Nasdaq": {"color": "#534AB7", "bg": "#EEEDFE", "dark": "#26215C"},
}

cols = st.columns(3)
for i, (asset, style) in enumerate(ASSET_STYLE.items()):
    with cols[i]:
        price_info = prices.get(asset, {})
        fund = fundamental.get(asset, {})
        bias = fund.get("bias", "neutre")
        bias_icon = "⬆" if bias == "haussier" else ("⬇" if bias == "baissier" else "↔")
        bias_col = "#1D9E75" if bias == "haussier" else ("#E24B4A" if bias == "baissier" else "#BA7517")

        price_str = f"{price_info.get('price', 0):,.2f}" if price_info else "N/A"
        chg = price_info.get("change_pct", 0)
        chg_str = f"{chg:+.2f}%" if price_info else ""
        chg_col = "#1D9E75" if chg >= 0 else "#E24B4A"

        st.markdown(f"""
<div style="border:0.5px solid {style['color']};border-radius:10px;overflow:hidden;margin-bottom:8px;">
  <div style="background:{style['color']};padding:8px 12px;display:flex;align-items:center;justify-content:space-between;">
    <span style="font-size:14px;font-weight:500;color:{style['bg']};">{asset}</span>
    <span style="background:{style['bg']};color:{style['dark']};font-size:11px;padding:2px 8px;border-radius:4px;font-weight:500;">
      {bias_icon} {bias.capitalize()}
    </span>
  </div>
  <div style="padding:10px 12px;">
    <p style="margin:0 0 2px;font-size:20px;font-weight:500;color:{style['color']};">{price_str}</p>
    <p style="margin:0 0 8px;font-size:12px;color:{chg_col};">{chg_str}</p>
</div></div>""", unsafe_allow_html=True)

        if fund:
            with st.expander(f"Détail analyse {asset}"):
                pos = fund.get("facteurs_positifs", [])
                risks = fund.get("risques", [])
                verdict = fund.get("verdict", "")

                if pos:
                    st.markdown("**Facteurs positifs :**")
                    for p in pos:
                        st.markdown(f"• {p}")
                if risks:
                    st.markdown("**Risques :**")
                    for r in risks:
                        st.markdown(f"• {r}")
                if verdict:
                    st.markdown(
                        f'<div class="impact-box" style="margin-top:8px;">'
                        f'<strong>Verdict IA :</strong> {verdict}</div>',
                        unsafe_allow_html=True,
                    )

st.divider()

# =============================================
# SECTION 3 : CALENDRIER ÉCONOMIQUE
# =============================================
st.markdown('<p class="section-title">📅 Calendrier macro — événements ≥ ★★</p>', unsafe_allow_html=True)

events = data.get("events", [])
if not events:
    st.info("Aucun événement macro ≥ 2 étoiles dans les prochaines 48h, ou clé Finnhub non configurée.")
else:
    for ev in events:
        urgency = ev["urgency"]
        if urgency == "danger":
            border_col, bg_col, text_col = "#E24B4A", "#FCEBEB", "#501313"
        elif urgency == "warning":
            border_col, bg_col, text_col = "#BA7517", "#FAEEDA", "#633806"
        else:
            border_col, bg_col, text_col = "#1D9E75", "#E1F5EE", "#085041"

        actual_str = f" | **Résultat : {ev['actual']}**" if ev.get("actual") else ""
        estimate_str = f" | Consensus : {ev['estimate']}" if ev.get("estimate") else ""
        prev_str = f" | Précédent : {ev['prev']}" if ev.get("prev") else ""
        alert = " 🚨" if ev["countdown"] == "VIENT DE SORTIR" else ""

        st.markdown(f"""
<div style="padding:10px 14px;border-left:4px solid {border_col};background:{bg_col};
border-radius:0 8px 8px 0;margin-bottom:8px;display:flex;align-items:center;gap:12px;">
  <div style="min-width:70px;text-align:center;">
    <p style="margin:0;font-size:10px;color:{text_col};">{ev['date_str']} {ev['time_str']}</p>
    <p style="margin:0;font-size:15px;font-weight:500;color:{border_col};">{ev['countdown']}{alert}</p>
  </div>
  <div style="flex:1;">
    <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">
      <span style="font-size:13px;font-weight:500;color:{text_col};">{ev['name']}</span>
      <span style="font-size:12px;color:{border_col};">{ev['stars']}</span>
      <span style="font-size:10px;color:{text_col};background:rgba(0,0,0,0.08);padding:1px 6px;border-radius:3px;">{ev['currency']} {ev['country'].upper()}</span>
    </div>
    <p style="margin:0;font-size:11px;color:{text_col};">{actual_str}{estimate_str}{prev_str}</p>
  </div>
</div>""", unsafe_allow_html=True)

st.divider()


# =============================================
# SECTION : ALERTES MEGACAPS (earnings + profit warnings)
# =============================================
st.markdown('<p class="section-title">📅 Alertes Megacaps</p>', unsafe_allow_html=True)

earnings_today = data.get("earnings_today", [])
profit_warnings = data.get("profit_warnings", [])
impact_notes = data.get("impact_notes", {})

if earnings_today:
    st.markdown("**Earnings aujourd'hui :**")
    for e in earnings_today:
        st.markdown(
            f'<div style="border:0.5px solid #4B9FFF;border-radius:10px;padding:12px 14px;margin-bottom:10px;">'
            f'<p style="margin:0;font-size:14px;font-weight:600;">🔔 {e["ticker"]} — publie ses résultats aujourd\'hui</p>'
            f'<p style="margin:4px 0 0;font-size:12px;color:#888;">Clôture US {e["countdown"]}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        notes = impact_notes.get("earnings", {})
        col1, col2, col3 = st.columns(3)
        for col, asset in zip([col1, col2, col3], ["SPX", "Gold", "Nasdaq"]):
            with col:
                st.markdown(
                    f'<div style="background:var(--background-color);border:0.5px solid #4B9FFF;'
                    f'border-radius:8px;padding:8px;text-align:center;">'
                    f'<p style="margin:0;font-size:11px;color:#888;">{asset}</p>'
                    f'<p style="margin:4px 0 0;font-size:11px;color:#888;line-height:1.4;">{notes.get(asset, "—")}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
else:
    st.markdown("*Aucun earnings megacap aujourd'hui.*")

if profit_warnings:
    st.markdown("**⚠️ Profit warnings détectés :**")
    for w in profit_warnings:
        st.markdown(
            f'<div style="border:0.5px solid #E24B4A;border-radius:10px;padding:12px 14px;margin-bottom:10px;">'
            f'<p style="margin:0;font-size:13px;font-weight:600;color:#E24B4A;">🚨 {w["ticker"]}</p>'
            f'<p style="margin:4px 0 0;font-size:13px;">{w["title"]}</p>'
            f'<p style="margin:4px 0 0;font-size:11px;color:#888;">{w.get("source","")}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        notes = impact_notes.get("warning", {})
        col1, col2, col3 = st.columns(3)
        for col, asset in zip([col1, col2, col3], ["SPX", "Gold", "Nasdaq"]):
            with col:
                st.markdown(
                    f'<div style="background:var(--background-color);border:0.5px solid #E24B4A;'
                    f'border-radius:8px;padding:8px;text-align:center;">'
                    f'<p style="margin:0;font-size:11px;color:#888;">{asset}</p>'
                    f'<p style="margin:4px 0 0;font-size:11px;color:#888;line-height:1.4;">{notes.get(asset, "—")}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
else:
    st.markdown("*Aucun profit warning détecté.*")
