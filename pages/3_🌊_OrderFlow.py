import streamlit as st
import scipy.stats as _scipy_stats

st.set_page_config(page_title="OrderFlow — OBI & Kyle Lambda", page_icon="🌊", layout="wide")
st.title("🌊 OrderFlow — OBI & Kyle Lambda")
st.caption("Pression d'ordre temps réel · NQ · ES · RTY · 1h & 4h")

_OF_OBI_WIN    = 5
_OF_OBI_THRESH = 0.05
_OF_KL_WIN     = 20
_OF_KL_PCTILE  = 0.60

_OF_TICKERS = {"NQ": "NQ=F", "ES": "ES=F", "RTY": "RTY=F"}
_OF_TFS     = ["4h", "1h"]

_OF_WR_REF = {
    ("NQ","4h"): 55.1, ("NQ","1h"): 51.6,
    ("ES","4h"): 50.4, ("ES","1h"): 50.1,
    ("RTY","4h"): 49.8, ("RTY","1h"): 49.5,
}

@st.cache_data(ttl=900, show_spinner=False)
def _load_of_data(ticker, tf):
    try:
        import yfinance as _yf
        from datetime import datetime as _dt, timedelta as _td
        start = (_dt.today() - _td(days=720)).strftime("%Y-%m-%d")
        df = _yf.download(ticker, start=start, interval=tf,
                          progress=False, auto_adjust=True)
        if df.empty:
            return None
        if isinstance(df.columns, __import__('pandas').MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df[['Open','High','Low','Close','Volume']].dropna()
    except Exception:
        return None

def _compute_obi(df):
    import numpy as _np
    hl  = (df['High'] - df['Low']).replace(0, _np.nan)
    bp  = ((df['Close'] - df['Open']) / hl).fillna(0)
    return bp.rolling(_OF_OBI_WIN, min_periods=2).mean()

def _compute_kl_pct(df):
    import numpy as _np
    dp    = df['Close'].diff().abs()
    vol   = df['Volume'].replace(0, _np.nan)
    lam   = (dp / vol).fillna(0)
    lam_s = lam.rolling(_OF_KL_WIN, min_periods=5).mean()
    pct   = lam_s.rolling(60, min_periods=20).apply(
        lambda x: _scipy_stats.percentileofscore(x, x.iloc[-1]) / 100.0,
        raw=False
    )
    direc = df['Close'].diff().apply(_np.sign).fillna(0)
    return lam_s, pct, direc

def _of_signal(obi_val, kl_pct_val, kl_dir_val):
    bull = obi_val >  _OF_OBI_THRESH and kl_pct_val > _OF_KL_PCTILE and kl_dir_val > 0
    bear = obi_val < -_OF_OBI_THRESH and kl_pct_val > _OF_KL_PCTILE and kl_dir_val < 0
    if bull: return "HAUSSIER", "🟢", "#3FB950"
    if bear: return "BAISSIER", "🔴", "#F85149"
    return "NEUTRE", "⚪", "#8B949E"

_of_results = {}
with st.spinner("Chargement données OrderFlow…"):
    for instr, ticker in _OF_TICKERS.items():
        for tf in _OF_TFS:
            df_of = _load_of_data(ticker, tf)
            if df_of is None or len(df_of) < 80:
                _of_results[(instr, tf)] = None
                continue
            try:
                obi               = _compute_obi(df_of)
                lam_s, kl_pct, kl_dir = _compute_kl_pct(df_of)
                obi_val  = float(obi.iloc[-1])
                kl_pct_v = float(kl_pct.iloc[-1]) if not __import__('math').isnan(float(kl_pct.iloc[-1])) else 0.0
                kl_dir_v = float(kl_dir.iloc[-1])
                kl_raw   = float(lam_s.iloc[-1])
                sig, emoji, color = _of_signal(obi_val, kl_pct_v, kl_dir_v)
                _of_results[(instr, tf)] = {
                    "obi": obi_val, "kl_pct": kl_pct_v,
                    "kl_dir": kl_dir_v, "kl_raw": kl_raw,
                    "signal": sig, "emoji": emoji, "color": color,
                    "wr_ref": _OF_WR_REF.get((instr, tf), 0.0),
                }
            except Exception:
                _of_results[(instr, tf)] = None

st.subheader("📊 Biais directionnel actuel — 4h")
_cols_of = st.columns(3)
for _ci, instr in enumerate(["NQ","ES","RTY"]):
    r = _of_results.get((instr, "4h"))
    with _cols_of[_ci]:
        if r is None:
            st.warning(f"{instr} — données indisponibles")
            continue
        obi_str = f"+{r['obi']:.3f}" if r['obi'] >= 0 else f"{r['obi']:.3f}"
        kl_str  = f"{r['kl_pct']*100:.0f}%"
        of_dir  = "OF +" if r['kl_dir'] > 0 else ("OF −" if r['kl_dir'] < 0 else "OF ≈")
        wr_str  = f"{r['wr_ref']:.1f}%" if r['wr_ref'] > 0 else "—"
        st.markdown(f"""<div style="background:#161B22;border:1px solid {r['color']};border-radius:10px;padding:16px;text-align:center">
  <div style="font-size:1.5rem;font-weight:700;color:{r['color']}">{r['emoji']} {instr}</div>
  <div style="font-size:1.1rem;color:{r['color']};margin:6px 0">{r['signal']}</div>
  <div style="color:#8B949E;font-size:0.85rem;margin-top:8px">
    OBI&nbsp;(5b)&nbsp;<span style="color:#E6EDF3;font-weight:600">{obi_str}</span> &nbsp;|&nbsp;
    λ&nbsp;<span style="color:#BC8CFF;font-weight:600">{kl_str}</span> &nbsp;|&nbsp;
    <span style="color:#58A6FF">{of_dir}</span>
  </div>
  <div style="color:#8B949E;font-size:0.78rem;margin-top:6px">WR backtest&nbsp;<b style="color:#3FB950">{wr_str}</b></div>
</div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.subheader("🔥 Heatmap Kyle Lambda — Sensibilité au flux")
_hm_cols = st.columns([1,1,1,1])
_hm_cols[0].markdown("**TF**")
for _ci, instr in enumerate(["NQ","ES","RTY"]):
    _hm_cols[_ci+1].markdown(f"**{instr}**")

for tf in _OF_TFS:
    _row = st.columns([1,1,1,1])
    _row[0].markdown(f"**{tf.upper()}**")
    for _ci, instr in enumerate(["NQ","ES","RTY"]):
        r = _of_results.get((instr, tf))
        with _row[_ci+1]:
            if r is None:
                st.markdown("—")
                continue
            pct   = r['kl_pct']
            alpha = max(0.15, min(1.0, pct))
            r_hex = int(155 * alpha); b_hex = int(255 * alpha)
            bg    = f"#{r_hex:02x}00{b_hex:02x}"
            fg    = "#E6EDF3" if pct > 0.4 else "#8B949E"
            st.markdown(
                f'<div style="background:{bg};border-radius:6px;padding:8px 4px;'
                f'text-align:center;font-weight:700;font-size:0.9rem;color:{fg}">'
                f'{pct*100:.0f}e</div>',
                unsafe_allow_html=True
            )

st.markdown("<br>", unsafe_allow_html=True)

with st.expander("📖 Comment lire ces indicateurs", expanded=False):
    st.markdown("""
**OBI — Order Book Imbalance (5 barres)**  
Mesure la pression acheteuse/vendeuse sur les 5 dernières bougies.  
`OBI = moyenne( (Close − Open) / (High − Low) )`  
• `> +0.05` → pression acheteuse dominante 🟢  
• `< −0.05` → pression vendeuse dominante 🔴  
• Entre les deux → marché indécis ⚪  

**Kyle λ — Sensibilité du marché au flux d'ordre**  
Plus λ est élevé, plus le marché est fin (thin) et réactif aux ordres institutionnels.  
`λ ≈ ΔPrix / Volume` (rolling 20 barres)  
Le **percentile rolling** compare λ actuel aux 60 dernières barres.  
• `> 60e percentile` = marché particulièrement sensible au flux → signal renforcé  

**Signal HAUSSIER** ✅ si OBI > +0.05 **ET** λ > 60e pct **ET** flow directionnel positif  
**Signal BAISSIER** ✅ si OBI < −0.05 **ET** λ > 60e pct **ET** flow directionnel négatif  

**WR backtest** = win rate historique de la stratégie Momentum Pinball filtré OBI+Kyle Lambda  
(NQ 4h : **55.1%**, NQ 1h : **51.6%** — seuil break-even R:R 1:2 = 33.3%)
""")
