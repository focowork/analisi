"""
config.py
=========
Constants i configuracio central de l'IBEX Intraday Decision Engine.

REGLA D'OR: cap altre modul ha de contenir "numeros magics". Tot valor
ajustable (pesos, llindars, finestres temporals...) viu aqui, perque es
pugui afinar el sistema sense tocar la logica de negoci.
"""

from typing import Dict, List

# ---------------------------------------------------------------------------
# MERCATS
# ---------------------------------------------------------------------------
# Ticker de yfinance que representa l'index de referencia de cada mercat.
# Afegir un mercat nou en el futur (NASDAQ, SP500, DAX, CAC...) es tan facil
# com afegir una entrada aqui.
MARKET_INDEX_TICKERS: Dict[str, str] = {
    "IBEX35": "^IBEX",
    "NASDAQ": "^IXIC",
    # "SP500": "^GSPC",
    # "DAX": "^GDAXI",
    # "CAC40": "^FCHI",
}

# Mercat actiu per aquesta execucio. Per canviar de mercat nomes cal
# modificar aquesta linia.
ACTIVE_MARKET: str = "NASDAQ"

# ---------------------------------------------------------------------------
# UNIVERS D'ACCIONS
# ---------------------------------------------------------------------------
# Mapeja un nom llegible al seu ticker de yfinance.
# Cada mercat te el seu propi univers d'accions.
IBEX_STOCK_UNIVERSE: Dict[str, str] = {
    "INDRA": "IDR.MC",
    "GRIFOLS": "GRF.MC",
    "BBVA": "BBVA.MC",
    "BANKINTER": "BKT.MC",
    "CAIXABANK": "CABK.MC",
}

# Univers per defecte de NASDAQ (grans tecnologiques molt liquides).
# Amplia aquesta llista amb qualsevol ticker de NASDAQ que vulguis seguir.
NASDAQ_STOCK_UNIVERSE: Dict[str, str] = {
    "APPLE": "AAPL",
    "MICROSOFT": "MSFT",
    "NVIDIA": "NVDA",
    "AMAZON": "AMZN",
    "ALPHABET": "GOOGL",
    "META": "META",
    "TESLA": "TSLA",
    "NETFLIX": "NFLX",
    "AMD": "AMD",
    "BROADCOM": "AVGO",
    "SPACEX": "SPCX",
}

# Univers actiu que fara servir main.py quan nomes s'analitza UN mercat
# (canvia junt amb ACTIVE_MARKET). Per tornar a l'IBEX: STOCK_UNIVERSE = IBEX_STOCK_UNIVERSE.
STOCK_UNIVERSE: Dict[str, str] = NASDAQ_STOCK_UNIVERSE

# Mapeig mercat -> univers d'accions. Necessari per poder analitzar
# diversos mercats en la mateixa execucio (run_multi_market).
MARKET_STOCK_UNIVERSES: Dict[str, Dict[str, str]] = {
    "IBEX35": IBEX_STOCK_UNIVERSE,
    "NASDAQ": NASDAQ_STOCK_UNIVERSE,
}

# Moneda de cotitzacio de cada mercat, nomes per mostrar-la correctament
# a l'informe (EUR per IBEX, USD per NASDAQ...).
MARKET_CURRENCY: Dict[str, str] = {
    "IBEX35": "EUR",
    "NASDAQ": "USD",
}

# Mercats que s'analitzaran quan es fa servir run_multi_market() sense
# arguments. Per defecte, tots dos alhora.
MARKETS_TO_RUN: List[str] = ["IBEX35", "NASDAQ"]

# ---------------------------------------------------------------------------
# DADES / TEMPS
# ---------------------------------------------------------------------------
INTRADAY_INTERVAL: str = "5m"              # granularitat intradia de yfinance
INTRADAY_PERIOD: str = "1d"                # historial a descarregar per "avui"
HISTORICAL_PERIOD_FOR_AVG_VOLUME: str = "20d"     # finestra per calcular volum mitja
HISTORICAL_INTERVAL_FOR_AVG_VOLUME: str = "5m"

# ---------------------------------------------------------------------------
# PESOS DEL SCORE (han de sumar 1.0)
# ---------------------------------------------------------------------------
WEIGHT_VOLUME: float = 0.30
WEIGHT_RELATIVE_STRENGTH: float = 0.30
WEIGHT_NEWS: float = 0.20
WEIGHT_ENERGY: float = 0.20

SCORE_WEIGHTS: Dict[str, float] = {
    "volume": WEIGHT_VOLUME,
    "relative_strength": WEIGHT_RELATIVE_STRENGTH,
    "news": WEIGHT_NEWS,
    "energy": WEIGHT_ENERGY,
}

# ---------------------------------------------------------------------------
# ESCALA DE SCORE
# ---------------------------------------------------------------------------
SCORE_MIN: float = 0.0
SCORE_MAX: float = 100.0

# ---------------------------------------------------------------------------
# LLINDARS DE RECOMANACIO
# ---------------------------------------------------------------------------
THRESHOLD_BUY: float = 75.0
THRESHOLD_WATCH: float = 55.0
# Per sota de THRESHOLD_WATCH => evitar / sense oportunitat clara

RECOMMENDATION_BUY: str = "COMPRAR"
RECOMMENDATION_WATCH: str = "VIGILAR"
RECOMMENDATION_AVOID: str = "EVITAR"

# ---------------------------------------------------------------------------
# FILTRE "NOMES LLARGS" (long-only)
# ---------------------------------------------------------------------------
# L'usuari nomes opera al alça. Si el moviment dominant d'avui en una accio
# es BAIXISTA (segons fibonacci.py, basat en la posicio del preu dins el
# rang del dia), entrar-hi llarg vol dir anar en contra de la tendencia
# intradia d'avui: mes risc de NO tancar la sessio en positiu, que es
# l'objectiu declarat. Per aixo, si LONG_ONLY_MODE esta actiu, es sobreescriu
# la recomanacio a EVITAR encara que el score dels 4 pilars fos alt.
LONG_ONLY_MODE: bool = True
LONG_ONLY_BLOCKED_DIRECTION: str = "BAIXISTA"
LONG_ONLY_BLOCK_NOTE: str = (
    "Filtre nomes-llargs: la tendencia dominant d'avui en aquesta accio es BAIXISTA "
    "(el preu esta mes a prop del minim del dia que del maxim). Entrar-hi llarg ara "
    "aniria en contra del moviment d'avui. Recomanacio sobreescrita a EVITAR."
)

# ---------------------------------------------------------------------------
# FIBONACCI MENSUAL (dada complementaria: intradia vs mantenir dies)
# ---------------------------------------------------------------------------
# Rang de referencia per calcular els nivells de Fibonacci "de fons": no es
# el rang d'avui, sino el rang dels ultims N dies. Serveix per decidir si
# val la pena deixar correr una posicio mes enlla d'avui (swing) o si nomes
# te sentit operar-la intradia.
MONTHLY_LOOKBACK_PERIOD: str = "1mo"     # periode de yfinance (1 mes)
MONTHLY_LOOKBACK_INTERVAL: str = "1d"    # una barra per dia

# Marge (en % del rang mensual) per considerar que el preu esta "a prop"
# d'un nivell d'extensio o retroces mensual (zona de possible sostre/suport
# de fons, no nomes d'avui).
MONTHLY_LEVEL_PROXIMITY_PCT: float = 2.0

HORIZON_SWING_CANDIDATE: str = "CANDIDATA A SWING (pot aguantar mes d'un dia)"
HORIZON_INTRADAY_ONLY: str = "NOMES INTRADIA (tancar avui)"
HORIZON_UNCLEAR: str = "SENSE CLAREDAT (dades insuficients)"

# ---------------------------------------------------------------------------
# QUALITAT DEL RANG MENSUAL (range_quality.py)
# ---------------------------------------------------------------------------
# Contrasta si el rang mensual (maxim/minim) es fiable, o si pot estar
# distorsionat per un esdeveniment excepcional (sortida a borsa recent,
# OPA, ampliacio de capital, resultat extraordinari). No desqualifica el
# Fibonacci mensual, nomes indica quant fiar-se'n.
RANGE_QUALITY_MIN_TRADING_DAYS: int = 15   # per sota d'aixo, historial curt (possible IPO recent)
RANGE_QUALITY_GAP_WARNING_PCT: float = 8.0  # variacio d'un sol dia per sobre d'aixo, "salt" a investigar

RANGE_QUALITY_HIGH: str = "ALTA"
RANGE_QUALITY_MEDIUM: str = "MITJANA"
RANGE_QUALITY_LOW: str = "BAIXA"

# ---------------------------------------------------------------------------
# SCORE DE VOLUM
# ---------------------------------------------------------------------------
# Volum relatiu = volum acumulat avui / volum mitja historic a la mateixa hora.
RELATIVE_VOLUME_EXCELLENT: float = 2.0   # >= 2x la mitjana => score maxim
RELATIVE_VOLUME_HIGH: float = 1.5
RELATIVE_VOLUME_NORMAL: float = 1.0
RELATIVE_VOLUME_LOW: float = 0.5

# ---------------------------------------------------------------------------
# SCORE DE FORCA RELATIVA
# ---------------------------------------------------------------------------
# Diferencia en punts percentuals entre la variacio de l'accio i la de l'index.
RS_EXCELLENT_DIFF: float = 2.0
RS_GOOD_DIFF: float = 1.0
RS_NEUTRAL_DIFF: float = 0.0
RS_NEGATIVE_DIFF: float = -1.0

# ---------------------------------------------------------------------------
# NOTICIES
# ---------------------------------------------------------------------------
NEWS_MAX_HEADLINES: int = 8
# Per NASDAQ (empreses USA) les noticies es cerquen en angles/US per obtenir
# millors resultats a Google News. Per tornar a l'IBEX: "es"/"ES".
NEWS_LANGUAGE: str = "en"
NEWS_REGION: str = "US"

# Categories de noticia i la seva puntuacio base d'impacte (0-100).
NEWS_CATEGORY_SCORES: Dict[str, float] = {
    "OPA": 100.0,
    "Resultats": 90.0,
    "Contracte": 85.0,
    "Recomanacio": 70.0,
    "Canvi de previsio": 65.0,
    "Rumor": 50.0,
    "Sectorial": 40.0,
    "Sense noticia": 0.0,
}

# Paraules clau (en minuscules) per classificar cada titular en una categoria.
# Inclou termes en castella (IBEX) i en angles (NASDAQ) perque el motor
# funcioni amb qualsevol dels dos mercats sense tocar mes codi.
NEWS_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "OPA": [
        "opa", "oferta publica de adquisicion", "takeover bid",
        "acquisition", "acquires", "merger", "buyout", "tender offer",
    ],
    "Resultats": [
        "resultados", "beneficio", "beneficios", "ebitda", "ingresos", "cuentas",
        "earnings", "quarterly results", "revenue", "profit", "eps beat", "eps miss",
    ],
    "Contracte": [
        "contrato", "adjudicacion", "acuerdo", "alianza",
        "contract", "deal", "partnership", "agreement",
    ],
    "Recomanacio": [
        "recomienda", "sobreponderar", "infraponderar", "precio objetivo", "eleva", "rebaja",
        "upgrades", "downgrades", "price target", "overweight", "underweight", "outperform",
    ],
    "Canvi de previsio": [
        "revisa", "prevision", "guidance", "actualiza objetivo",
        "raises guidance", "cuts guidance", "forecast",
    ],
    "Rumor": [
        "rumor", "fuentes", "podria", "negocia",
        "sources say", "reportedly", "in talks",
    ],
    "Sectorial": ["sector", "industry"],
}

# Frases que indiquen un article de tipus "roundup" promocional (llistat
# d'ofertes/descomptes que esmenta moltes marques de passada), NO una
# noticia real sobre l'empresa. Si el titular en conte alguna, es forca
# a "Sense noticia" independentment de si tambe conte alguna paraula clau
# de les categories normals (p.ex. "deal").
NEWS_ROUNDUP_BLOCKLIST: List[str] = [
    "% off", "off from", "deals up to", "shop deals", "shop the best deals",
    "best deals", "top deals", "gift guide", "black friday", "cyber monday",
    "prime day", "prime day deals", "holiday deals", "deals of the day",
    "rebajas", "chollos", "ofertas de",
]

# Si un titular te moltes comes seguides (llista de marques/productes),
# es un indici mes de "roundup" generic i no de noticia especifica de
# l'empresa. A partir d'aquest nombre de comes, es tracta com a roundup.
NEWS_ROUNDUP_COMMA_THRESHOLD: int = 3

# ---------------------------------------------------------------------------
# ENERGIA DEL MOVIMENT (continuitat del momentum)
# ---------------------------------------------------------------------------
ENERGY_LOOKBACK_BARS: int = 6  # barres intradia recents a analitzar

# Finestra mes llarga que ENERGY_LOOKBACK_BARS, nomes per detectar si l'accio
# esta en tendencia neta o en regim lateral erratic (whipsaw). Amb interval
# de 5 min, 20 barres = ~100 minuts de sessio.
REGIME_LOOKBACK_BARS: int = 20

# A partir d'aquest % de variacio intradia (en valor absolut), s'afegeix un
# avis de "moviment extrem": un moviment tan gran en una sola sessio te mes
# risc estadistic de correccio tecnica els dies seguents, independentment
# de si l'score diu COMPRAR. No es una prediccio, nomes un avis de prudencia.
EXTREME_MOVE_WARNING_PCT: float = 4.0

ENERGY_STATE_STRONG_CONTINUATION: str = "Mante maxims / entra volum"
ENERGY_STATE_MODERATE_CONTINUATION: str = "Mante forca"
ENERGY_STATE_WEAKENING: str = "Perd forca"
ENERGY_STATE_EXHAUSTED: str = "Esgota moviment"
ENERGY_STATE_DECREASING_VOLUME: str = "Disminueix volum"

ENERGY_SCORE_MAP: Dict[str, float] = {
    ENERGY_STATE_STRONG_CONTINUATION: 95.0,
    ENERGY_STATE_MODERATE_CONTINUATION: 75.0,
    ENERGY_STATE_DECREASING_VOLUME: 50.0,
    ENERGY_STATE_WEAKENING: 30.0,
    ENERGY_STATE_EXHAUSTED: 10.0,
}

# ---------------------------------------------------------------------------
# INFORME
# ---------------------------------------------------------------------------
TOP_N_RESULTS: int = 5
