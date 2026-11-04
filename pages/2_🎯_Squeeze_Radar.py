"""
app.py - SqueezeRadar (version coloree)
Dashboard de detection de gamma squeeze sur NQ, ES, GC.
"""

import streamlit as st

from squeeze_src.loader import load_yf_options
from squeeze_src.gex import gamma_profile
from squeeze_src.squeeze_detector import detect_squeeze_setup
from squeeze_src.technical_levels import compute_technical_levels
from squeeze_src.oi_history import load_oi_history, append_daily_snapshot

st.set_page_config(page_title="SqueezeRadar", page_icon="🎯", layout="wide")

ASSET_CONFIG = {
    "NQ": {"proxy_ticker": "QQQ", "label": "Nasdaq Futures (NQ)"},
    "ES": {"proxy_ticker": "SPY", "label": "S&P 500 Futures (ES)"},
    "GC": {"proxy_ticker": "GLD", "label": "Gold Futures (GC)"},
}

TREND_LABELS = {
    "up": "en hausse - le mur grossit",
    "down": "en baisse - les gens sortent",
    "flat": "stable",
    "insuffisant": "historique insuffisant",
}

URGENCY_LABELS = {
    "haute": "haute - tres peu de marge",
    "moderee": "moderee - encore un peu de marge",
    "faible": "marge confortable",
    "N/A": "non disponible",
}

SCORE_COLORS = {3: "#ff4b4b", 2: "#ffa500", 1: "#4b9fff", 0: "#6c6c6c"}
SCORE_BG = {
    3: "rgba(255,75,75,0.12)",
    2: "rgba(255,165,0,0.12)",
    1: "rgba(75,159,255,0.10)",
    0: "rgba(108,108,108,0.10)",
}
SCORE_ICON = {3: "🔥", 2: "⚠️", 1: "🔵", 0: "⚪"}

st.markdown("""
<style>
.stApp { background-color: #0d1117; }
.metric-box {
    background: rgba(255,255,255,0.03);
    border-radius: 10px;
    padding: 12px 16px;
    text-align: center;
}
.metric-label {
    font-size: 12px;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}
.metric-value {
    font-size: 26px;
    font-weight: 700;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)


def render_header():
    st.title("🎯 SqueezeRadar")
    st.caption("NQ · ES · GC — mis a jour quotidiennement")
    with st.expander("Comment lire ce dashboard"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**🔥 Score**")
            st.caption("Combien de feux sont au vert sur 3. Rouge = fort, orange = modere, bleu = faible, gris = neutre.")
        with col2:
            st.markdown("**📈 Tendance OI**")
            st.caption("Le mur grossit ou retrecit.")
        with col3:
            st.markdown("**⏱️ Urgence**")
            st.caption("La marge qu'il reste aux vendeurs.")

@st.cache_data(ttl=3600, show_spinner=False)
def load_asset_data(proxy_ticker: str):
    return load_yf_options(proxy_ticker)


@st.cache_data(ttl=3600, show_spinner=False)
def load_technical_levels_cached(proxy_ticker: str):
    return compute_technical_levels(proxy_ticker)


def render_asset(asset_key: str, config: dict):
    proxy = config["proxy_ticker"]
    try:
        spot, df_options = load_asset_data(proxy)
    except ValueError as e:
        st.error(f"{config['label']} : {e}")
        return

    _, _, zero_gamma = gamma_profile(df_options, spot)
    tech_levels = load_technical_levels_cached(proxy)
    oi_hist = load_oi_history(asset_key)
    result = detect_squeeze_setup(df_options, oi_hist, spot, zero_gamma, tech_levels)
    append_daily_snapshot(asset_key, df_options)
    return spot, zero_gamma, result

def display_asset_card(asset_key: str, config: dict, spot, zero_gamma, result):
    score = result["detection_score"]
    color = SCORE_COLORS.get(score, "#6c6c6c")
    bg = SCORE_BG.get(score, "rgba(108,108,108,0.10)")
    icon = SCORE_ICON.get(score, "⚪")

    zg_display = f"{zero_gamma:.2f}" if zero_gamma else "N/A"
    urgency_text = URGENCY_LABELS.get(result["urgency_label"], "N/A")
    trend_text = TREND_LABELS.get(result["oi_trend_status"], "N/A")

    st.markdown(f"""
    <div style="border-left: 5px solid {color}; background: {bg};
                border-radius: 12px; padding: 20px 24px; margin-bottom: 20px;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
            <span style="font-size:20px; font-weight:700; color:#ffffff;">
                {icon} {config['label']}
            </span>
            <span style="background:{color}; color:#0d1117; font-weight:700;
                         padding:4px 14px; border-radius:20px; font-size:13px;">
                {result['alert_level']} ({score}/3)
            </span>
        </div>
        <div style="display:flex; gap:16px; margin-bottom:12px;">
            <div class="metric-box" style="flex:1;">
                <div class="metric-label">Spot</div>
                <div class="metric-value">{spot:.2f}</div>
            </div>
            <div class="metric-box" style="flex:1;">
                <div class="metric-label">Zero Gamma</div>
                <div class="metric-value">{zg_display}</div>
            </div>
            <div class="metric-box" style="flex:1;">
                <div class="metric-label">Urgence</div>
                <div class="metric-value" style="font-size:16px;">{urgency_text}</div>
            </div>
        </div>
        <div style="color:#9ca3af; font-size:13px;">
            Tendance OI : {trend_text}
        </div>
    </div>
    """, unsafe_allow_html=True)


render_header()

for asset_key, config in ASSET_CONFIG.items():
    data = render_asset(asset_key, config)
    if data:
        spot, zero_gamma, result = data
        display_asset_card(asset_key, config, spot, zero_gamma, result)

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# --- Setup Optimal Haussier / Baissier ---
st.subheader("🎯 Setup optimal — Conditions de marché")
st.caption("Confluence des signaux volatilité, gamma et flux pour valider un biais directionnel")

_sq_col1, _sq_col2 = st.columns(2)

with _sq_col1:
    st.markdown("""
<div style="background:rgba(63,185,80,0.08);border:1px solid #3FB950;border-radius:12px;padding:20px">
  <div style="font-size:1.05rem;font-weight:700;color:#3FB950;margin-bottom:14px">🟢 Setup HAUSSIER optimal</div>
  <div style="font-size:0.84rem;line-height:1.9;color:#E6EDF3">
    ✅ <b>VPIN &gt; 0.60</b> <span style="color:#8B949E">— flux informé côté acheteur</span><br>
    ✅ <b>GEX positif</b> <span style="color:#8B949E">— dealers long gamma, marché stabilisé</span><br>
    ✅ <b>VIX term structure en contango</b> <span style="color:#8B949E">— VIX1M &lt; VIX3M</span><br>
    ✅ <b>Skew baissier (&lt; −10)</b> <span style="color:#8B949E">— peu de protection achetée</span><br>
    ✅ <b>VVIX stable ou en baisse</b> <span style="color:#8B949E">— vol de vol contenue</span>
  </div>
  <div style="margin-top:14px;padding-top:12px;border-top:1px solid #30363D;font-size:0.82rem;font-weight:600;color:#3FB950">
    → Momentum Pinball LONG confirmé
  </div>
</div>""", unsafe_allow_html=True)

with _sq_col2:
    st.markdown("""
<div style="background:rgba(248,81,73,0.08);border:1px solid #F85149;border-radius:12px;padding:20px">
  <div style="font-size:1.05rem;font-weight:700;color:#F85149;margin-bottom:14px">🔴 Setup BAISSIER optimal</div>
  <div style="font-size:0.84rem;line-height:1.9;color:#E6EDF3">
    ✅ <b>VPIN &gt; 0.60</b> <span style="color:#8B949E">— flux informé côté vendeur</span><br>
    ✅ <b>GEX négatif</b> <span style="color:#8B949E">— dealers short gamma, mouvements amplifiés</span><br>
    ✅ <b>VIX term structure inversée</b> <span style="color:#8B949E">— VIX1M &gt; VIX3M</span><br>
    ✅ <b>Skew haussier (&gt; 0)</b> <span style="color:#8B949E">— protection institutionnelle achetée</span><br>
    ✅ <b>VVIX en hausse</b> <span style="color:#8B949E">— incertitude sur vol future</span>
  </div>
  <div style="margin-top:14px;padding-top:12px;border-top:1px solid #30363D;font-size:0.82rem;font-weight:600;color:#F85149">
    → Momentum Pinball SHORT confirmé
  </div>
</div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.expander("📖 Analyse détaillée des indicateurs", expanded=False):
    st.markdown("""
**VPIN — Volume-synchronized Probability of Informed Trading**  
Mesure le déséquilibre buy/sell sur des buckets de volume synchronisé (non temporel).  
`VPIN = |V_buy − V_sell| / V_total` sur N buckets  
• `> 0.70` → flux informé dominant  
• `0.40–0.60` → marché équilibré, faible conviction  
• `< 0.30` → peu de directionnalité  
⚠️ VPIN seul n'indique pas la direction — combiner avec OBI ou le régime gamma pour qualifier le biais.

**VVIX — Volatilité de la volatilité**  
Signal *avancé* de 1 à 2 jours sur les mouvements du VIX.  
• `VVIX > 100` → instabilité de régime imminente  
• VVIX stable/↓ dans un setup haussier = confirmation de la stabilité du régime  
• VVIX ↑ fort = prudence, même si les autres signaux sont bullish

**SKEW — Protection institutionnelle**  
Coût relatif des puts OTM vs calls OTM sur SPX. Un Skew élevé = les institutionnels achètent de la couverture tail-risk.  
• `< 110` → peu de protection = environnement bull  
• `> 140` → protection achetée = méfiance institutionnelle  
Combiné à GEX négatif, un Skew élevé renforce fortement la conviction baissière.

**VIX Term Structure — Contango vs Inversion**  
• **Contango** (VIX1M < VIX3M) → régime normal, favorable aux setups longs  
• **Inversion** (VIX1M > VIX3M) → stress immédiat, confirme les setups courts  
Une inversion soudaine après une période de contango est souvent précurseur d'un sell-off.

**Score de confluence**  
✅✅✅ (3/5) → setup de qualité  
✅✅✅✅✅ (5/5) → confluence maximale → conviction élevée pour Momentum Pinball  
< 3/5 → signal ambigu → ne pas forcer le trade
""")
