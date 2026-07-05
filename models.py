"""
models.py
=========
Dataclasses compartides per tots els moduls de l'IBEX Intraday Decision
Engine. Centralitzar el model de dades permet que cada modul rebi i
retorni aquests tipus en lloc de diccionaris solts, la qual cosa fa el
projecte molt mes facil de mantenir i ampliar (Fase 2: backtesting,
estadistica, ML, altres mercats...).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PriceSnapshot:
    """Dades cru de preu/volum intradia d'una accio en el moment de l'analisi."""
    ticker: str
    display_name: str
    last_price: float
    open_price: float
    change_pct: float                    # % variacio vs tancament anterior
    current_volume: float                # volum acumulat avui fins ara
    average_volume_at_this_time: float   # mitjana historica de volum a aquesta hora
    day_high: float = 0.0                # maxim intradia fins ara
    day_low: float = 0.0                 # minim intradia fins ara
    vwap: float = 0.0                    # preu mitja ponderat per volum del dia
    recent_closes: List[float] = field(default_factory=list)   # ultimes N barres (energia)
    recent_volumes: List[float] = field(default_factory=list)  # ultimes N barres (energia)
    recent_highs: List[float] = field(default_factory=list)    # ultimes N barres (energia, per ATR)
    recent_lows: List[float] = field(default_factory=list)     # ultimes N barres (energia, per ATR)
    regime_closes: List[float] = field(default_factory=list)   # finestra mes llarga (regim/whipsaw)
    regime_highs: List[float] = field(default_factory=list)    # finestra mes llarga (regim/whipsaw)
    regime_lows: List[float] = field(default_factory=list)     # finestra mes llarga (regim/whipsaw)


@dataclass
class IndexSnapshot:
    """Dades intradia de l'index de referencia (p.ex. IBEX 35)."""
    ticker: str
    change_pct: float


@dataclass
class NewsItem:
    """Un titular de noticia ja classificat."""
    headline: str
    source: str
    category: str
    link: Optional[str] = None


@dataclass
class NewsAnalysis:
    """Resultat agregat de l'analisi de noticies d'una accio."""
    items: List[NewsItem]
    best_category: str
    summary: str
    score: float


@dataclass
class VolumeAnalysis:
    """Resultat de l'analisi de volum."""
    relative_volume: float
    score: float


@dataclass
class RelativeStrengthAnalysis:
    """Resultat de l'analisi de forca relativa vs l'index."""
    stock_change_pct: float
    index_change_pct: float
    relative_strength_pct: float
    score: float


@dataclass
class EnergyAnalysis:
    """Resultat de l'analisi d'energia del moviment."""
    state: str
    score: float
    detail: str


@dataclass
class ScoreBreakdown:
    """Desglossament complet del score final d'una accio."""
    volume_score: float
    relative_strength_score: float
    news_score: float
    energy_score: float
    final_score: float
    recommendation: str
    filter_note: str = ""  # explicacio si un filtre posterior (p.ex. long-only) ha sobreescrit la recomanacio


@dataclass
class EntrySignal:
    """Analisi de QUALITAT DEL PUNT D'ENTRADA (no nomes si l'accio esta forta,
    sino si ARA es un bon moment o si ja s'ha perdut el millor moment).

    Aixo NO es un consell d'inversio: nomes descriu, amb dades objectives,
    la posicio del preu actual respecte al VWAP i al rang del dia.
    """
    position_vs_vwap_pct: float   # % de distancia del preu actual al VWAP (+ = per sobre)
    distance_to_high_pct: float   # % de distancia al maxim del dia (0 = som al maxim)
    distance_to_low_pct: float    # % de distancia al minim del dia
    quality: str                  # "RUPTURA", "MARGE_RECORREGUT", "SOBREESTES", "LATERAL", "SENSE_DADES"
    suggested_stop_reference: float  # nivell de referencia (VWAP o minim del dia)
    extreme_move_warning: bool = False  # True si el moviment d'avui es tan gran que hi ha risc de correccio
    notes: str = ""                    # explicacio curta en llenguatge natural


@dataclass
class RegimeAnalysis:
    """Analisi del 'regim' de mercat d'una accio: si es mou amb tendencia
    neta o si nomes esta oscil·lant sense rumb (lateral erratic / whipsaw).

    Aixo es clau per decidir si val la pena operar-la ara mateix: en un
    regim lateral caotic, els stops ajustats salten sovint per soroll
    (falses ruptures amunt i avall), no perque la tesi d'entrada fos
    incorrecta.
    """
    efficiency_ratio: float   # 0-1. Prop d'1 = tendencia neta. Prop de 0 = soroll pur.
    reversals_count: int      # nombre de canvis de direccio en les ultimes barres
    atr: float                # rang mitja per barra (volatilitat absoluta)
    regime: str                # "TENDENCIA", "LATERAL_TRANQUIL", "LATERAL_CAOTIC", "SENSE_DADES"
    suggested_stop_distance: float  # distancia de stop suggerida (en unitats de preu) basada en ATR
    notes: str


@dataclass
class FibonacciLevels:
    """Projeccio de nivells de Fibonacci a partir d'un rang de referencia
    (per defecte, el rang del dia), per identificar possibles zones
    d'entrada (retrocessos) i possibles objectius de sortida (extensions).

    IMPORTANT: aixo NO prediu res ni es un consell d'inversio. Nomes
    aplica una formula matematica estandard (proporcions de Fibonacci)
    sobre un rang de preus, perque la persona tingui referencies
    objectives de nivells.
    """
    direction: str                        # "ALCISTA" o "BAIXISTA" (segons el moviment dominant del rang)
    swing_low: float                      # minim de referencia
    swing_high: float                     # maxim de referencia
    scope: str = "INTRADIA"               # "INTRADIA" (rang d'avui) o "MENSUAL" (rang de fons)
    retracement_levels: Dict[str, float] = field(default_factory=dict)   # possibles zones d'entrada
    extension_levels: Dict[str, float] = field(default_factory=dict)     # possibles objectius de sortida
    suggested_entry_zone: tuple = (0.0, 0.0)   # rang de preu (50%-61.8%) mes vigilat pels traders
    notes: str = ""


@dataclass
class MonthlySnapshot:
    """Dades de rang de fons (per defecte, ultim mes) d'una accio, per
    calcular Fibonacci mensual com a dada complementaria al Fibonacci
    intradia. Independent de PriceSnapshot perque ve d'una descarrega
    de yfinance diferent (barres diaries, no de 5 minuts).

    Els camps trading_days_available, max_daily_move_pct i els dos
    high/low_set_by_extreme_day existeixen nomes per detectar si el rang
    esta distorsionat per un esdeveniment excepcional (veure range_quality.py)."""
    ticker: str
    monthly_high: float
    monthly_low: float
    last_price: float
    trading_days_available: int = 0
    max_daily_move_pct: float = 0.0
    high_set_by_extreme_day: bool = False
    low_set_by_extreme_day: bool = False


@dataclass
class RangeQualityAssessment:
    """Resultat de contrastar si el rang mensual (maxim/minim) es fiable
    o si pot estar distorsionat per un esdeveniment excepcional (sortida
    a borsa recent, OPA, ampliacio de capital, resultat extraordinari).

    Aixo NO desqualifica el Fibonacci mensual, nomes avisa de quant de
    fiar-se'n abans de fer-lo servir per decidir un horitzo de swing."""
    reliable: bool
    confidence: str    # config.RANGE_QUALITY_HIGH / MEDIUM / LOW
    flags: List[str]   # llista de motius concrets detectats (buida si tot ok)
    notes: str = ""


@dataclass
class HorizonAnalysis:
    """Recomanacio d'HORITZO temporal: si val la pena deixar una posicio
    corre mes enlla d'avui (swing) o si nomes te sentit operar-la intradia.

    Es calcula combinant la direccio intradia (fibonacci.py) amb la
    direccio mensual (fibonacci_monthly.py) i la proximitat del preu
    actual a un nivell mensual (possible sostre/suport de fons)."""
    horizon: str          # config.HORIZON_SWING_CANDIDATE / HORIZON_INTRADAY_ONLY / HORIZON_UNCLEAR
    intraday_direction: str
    monthly_direction: str
    near_monthly_level: bool
    notes: str = ""


@dataclass
class StockReport:
    """Informe complet d'una accio, llest per ser renderitzat."""
    display_name: str
    ticker: str
    price: PriceSnapshot
    volume: VolumeAnalysis
    relative_strength: RelativeStrengthAnalysis
    news: NewsAnalysis
    energy: EnergyAnalysis
    scores: ScoreBreakdown
    entry: "EntrySignal"
    regime: "RegimeAnalysis"
    fibonacci: "FibonacciLevels"
    explanation: str
    monthly_fibonacci: Optional["FibonacciLevels"] = None
    horizon: Optional["HorizonAnalysis"] = None
    range_quality: Optional["RangeQualityAssessment"] = None
