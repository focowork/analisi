"""
streamlit_app.py
================
App mobil-friendly per l'IBEX Intraday Decision Engine.

Substitueix l'us via Google Colab per una app web senzilla que pots
obrir des del navegador del mobil (i afegir a la pantalla d'inici perque
es comporti com una app).

Us local:
    pip install -r requirements.txt
    streamlit run streamlit_app.py

Desplegament gratuit (recomanat, per accedir-hi des del mobil sense
tenir l'ordinador ences):
    Veure DEPLOY.md en aquesta mateixa carpeta.
"""

from datetime import datetime

import streamlit as st

from config import MARKETS_TO_RUN, MARKET_CURRENCY, MARKET_STOCK_UNIVERSES
import main
import compare as compare_module

st.set_page_config(
    page_title="IBEX Intraday Engine",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# CSS lleuger per fer els botons mes grans i comodes al mobil.
st.markdown(
    """
    <style>
    div.stButton > button {
        width: 100%;
        padding: 0.9em 0.5em;
        font-size: 1.05em;
        border-radius: 10px;
    }
    pre, code {
        font-size: 0.78em !important;
        white-space: pre-wrap !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "snapshots" not in st.session_state:
    st.session_state.snapshots = []  # llista de compare.Snapshot d'aquesta sessio de navegador
if "last_report" not in st.session_state:
    st.session_state.last_report = ""

st.title("📊 IBEX Intraday Engine")
st.caption("Eina de suport a la decisio. No prediu res, nomes fotografia la sessio real en el moment que l'executes.")

tab_analisi, tab_snapshots, tab_seguiment = st.tabs(["🔍 Analisi", "🕒 Snapshots", "👁️ Seguiment"])

# ---------------------------------------------------------------------------
# TAB 1 — Analisi general (equivalent a run_multi_market / run)
# ---------------------------------------------------------------------------
with tab_analisi:
    st.subheader("Foto de mercat ara mateix")

    market_options = ["Tots (" + " + ".join(MARKETS_TO_RUN) + ")"] + list(MARKET_STOCK_UNIVERSES.keys())
    choice = st.radio("Mercat a analitzar", market_options, horizontal=False)

    if st.button("▶️ Analitzar ara", type="primary"):
        with st.spinner("Descarregant dades i analitzant... (pot trigar uns segons)"):
            try:
                if choice.startswith("Tots"):
                    rendered = main.run_multi_market()
                else:
                    rendered = main.run(market=choice)
                st.session_state.last_report = rendered
                st.session_state.last_report_time = datetime.now().strftime("%H:%M:%S")
            except Exception as exc:
                st.error(f"Error durant l'analisi: {exc}")

    if st.session_state.last_report:
        st.caption(f"Ultima analisi: {st.session_state.get('last_report_time', '')}")
        st.code(st.session_state.last_report, language=None)

# ---------------------------------------------------------------------------
# TAB 2 — Snapshots i comparativa (equivalent a compare.py)
# ---------------------------------------------------------------------------
with tab_snapshots:
    st.subheader("Compara dues fotos en el temps")
    st.write(
        "Pren una foto ara, espera uns minuts, pren-ne una altra i compara-les "
        "per veure si l'oportunitat guanya o perd forca."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📸 Prendre snapshot ara"):
            with st.spinner("Capturant snapshot..."):
                try:
                    label = datetime.now().strftime("%H:%M:%S")
                    snap = compare_module.Snapshot(label=label)
                    for market in MARKETS_TO_RUN:
                        snap.markets[market] = main.analyze_market(market=market)
                    st.session_state.snapshots.append(snap)
                    st.success(f"Snapshot '{label}' guardada ({len(st.session_state.snapshots)} en total).")
                except Exception as exc:
                    st.error(f"Error capturant snapshot: {exc}")

    with col2:
        only_changed = st.checkbox("Nomes canvis", value=True)

    if len(st.session_state.snapshots) >= 1:
        st.write("**Snapshots d'aquesta sessio:**")
        for s in st.session_state.snapshots:
            st.write(f"- {s.label}")

    if st.button("🔁 Comparar les 2 ultimes"):
        if len(st.session_state.snapshots) < 2:
            st.warning(
                f"Nomes hi ha {len(st.session_state.snapshots)} snapshot(s). "
                "Cal prendre'n almenys 2 abans de comparar."
            )
        else:
            older, newer = st.session_state.snapshots[-2], st.session_state.snapshots[-1]
            comparison = compare_module.compare_snapshots(older, newer, only_changed=only_changed)
            st.code(comparison, language=None)

    if st.session_state.snapshots and st.button("🗑️ Esborrar snapshots d'aquesta sessio"):
        st.session_state.snapshots = []
        st.rerun()

# ---------------------------------------------------------------------------
# TAB 3 — Seguiment dedicat d'un valor (equivalent a watch_ticker)
# ---------------------------------------------------------------------------
with tab_seguiment:
    st.subheader("Seguiment dedicat d'un valor concret")
    st.write("Analitza a fons un valor concret encara que no surti al TOP del rànquing general.")

    name_input = st.text_input("Nom (p.ex. GRIFOLS)")
    ticker_input = st.text_input("Ticker de yfinance (p.ex. GRF.MC)")
    market_for_watch = st.selectbox("Mercat de referencia", list(MARKET_STOCK_UNIVERSES.keys()))

    if st.button("👁️ Vigilar aquest valor"):
        if not name_input or not ticker_input:
            st.warning("Cal indicar nom i ticker.")
        else:
            with st.spinner(f"Analitzant {name_input}..."):
                try:
                    rendered = main.watch_ticker(name_input.upper(), ticker_input.upper(), market=market_for_watch)
                    st.code(rendered, language=None)
                except Exception as exc:
                    st.error(f"Error analitzant {name_input}: {exc}")

st.divider()
st.caption(
    "Recorda: eina de suport a la decisio, no un bot. No executa ordres. "
    "Si yfinance no respon o el mercat esta tancat, els scores es degraden amb gracia."
)
