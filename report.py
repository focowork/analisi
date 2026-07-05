"""
report.py
=========
Construeix les explicacions i renderitza l'informe final, net i llegible
des del mobil, amb nomes les cinc millors accions.
"""

from typing import List

from config import TOP_N_RESULTS, RECOMMENDATION_BUY, RECOMMENDATION_WATCH, RECOMMENDATION_AVOID
from models import (
    PriceSnapshot,
    VolumeAnalysis,
    RelativeStrengthAnalysis,
    NewsAnalysis,
    EnergyAnalysis,
    ScoreBreakdown,
    EntrySignal,
    RegimeAnalysis,
    FibonacciLevels,
    StockReport,
)

# Llindars nomes per triar la frase descriptiva (no afecten el score,
# que ja s'ha calculat als moduls corresponents).
VOLUME_PHRASE_HIGH: float = 2.0
VOLUME_PHRASE_MEDIUM: float = 1.5
VOLUME_PHRASE_NORMAL: float = 1.0

STRENGTH_PHRASE_STRONG: float = 1.0
STRENGTH_PHRASE_POSITIVE: float = 0.0


def _volume_phrase(volume: VolumeAnalysis) -> str:
    """Frase curta que descriu el volum relatiu."""
    if volume.relative_volume >= VOLUME_PHRASE_HIGH:
        return "Volum molt alt"
    if volume.relative_volume >= VOLUME_PHRASE_MEDIUM:
        return "Volum alt"
    if volume.relative_volume >= VOLUME_PHRASE_NORMAL:
        return "Volum normal"
    return "Volum baix"


def _strength_phrase(rs: RelativeStrengthAnalysis) -> str:
    """Frase curta que descriu la forca relativa vs l'index."""
    if rs.relative_strength_pct >= STRENGTH_PHRASE_STRONG:
        return "Molt mes forta que l'index"
    if rs.relative_strength_pct >= STRENGTH_PHRASE_POSITIVE:
        return "Mes forta que l'index"
    return "Mes debil que l'index"


def build_explanation(
    volume: VolumeAnalysis,
    relative_strength: RelativeStrengthAnalysis,
    news: NewsAnalysis,
    energy: EnergyAnalysis,
) -> str:
    """Construeix una explicacio curta que justifica el score/recomanacio.

    Cada accio ha d'entendre's SEMPRE: mai es dona una recomanacio sense
    els motius que la sustenten.

    Args:
        volume: VolumeAnalysis.
        relative_strength: RelativeStrengthAnalysis.
        news: NewsAnalysis.
        energy: EnergyAnalysis.

    Returns:
        Text multi-linia amb un motiu per pilar.
    """
    lines = [
        f"- {_volume_phrase(volume)}",
        f"- {_strength_phrase(relative_strength)}",
        f"- {news.summary}",
        f"- {energy.detail}",
    ]
    return "\n".join(lines)


def build_stock_report(
    price: PriceSnapshot,
    volume: VolumeAnalysis,
    relative_strength: RelativeStrengthAnalysis,
    news: NewsAnalysis,
    energy: EnergyAnalysis,
    scores: ScoreBreakdown,
    entry: EntrySignal,
    regime: RegimeAnalysis,
    fibonacci: FibonacciLevels,
    monthly_fibonacci: FibonacciLevels = None,
    horizon: "HorizonAnalysis" = None,
    range_quality: "RangeQualityAssessment" = None,
) -> StockReport:
    """Munta l'objecte StockReport complet d'una accio.

    Args:
        price: PriceSnapshot.
        volume: VolumeAnalysis.
        relative_strength: RelativeStrengthAnalysis.
        news: NewsAnalysis.
        energy: EnergyAnalysis.
        scores: ScoreBreakdown.
        entry: EntrySignal (qualitat del punt d'entrada ara mateix).
        regime: RegimeAnalysis (tendencia / lateral tranquil / lateral caotic).
        fibonacci: FibonacciLevels (retrocessos i extensions) intradia.
        monthly_fibonacci: FibonacciLevels (opcional) calculat sobre el rang
            de fons (ultim mes), com a dada complementaria.
        horizon: HorizonAnalysis (opcional) amb la recomanacio d'horitzo
            temporal (intradia vs swing).

    Returns:
        StockReport llest per renderitzar.
    """
    explanation = build_explanation(volume, relative_strength, news, energy)
    return StockReport(
        display_name=price.display_name,
        ticker=price.ticker,
        price=price,
        volume=volume,
        relative_strength=relative_strength,
        news=news,
        energy=energy,
        scores=scores,
        entry=entry,
        regime=regime,
        fibonacci=fibonacci,
        explanation=explanation,
        monthly_fibonacci=monthly_fibonacci,
        horizon=horizon,
        range_quality=range_quality,
    )


def build_short_reason(
    volume: VolumeAnalysis,
    relative_strength: RelativeStrengthAnalysis,
    news: NewsAnalysis,
) -> str:
    """Construeix UNA sola frase amb el motiu mes rellevant, per un resum
    directe (no una llista de 4 bullets). Prioritza la noticia si n'hi ha
    una de rellevant; si no, combina volum + forca relativa.

    Args:
        volume: VolumeAnalysis.
        relative_strength: RelativeStrengthAnalysis.
        news: NewsAnalysis.

    Returns:
        Frase curta, en minuscules excepte la primera lletra.
    """
    if news.best_category not in ("Sense noticia",) and news.score >= 65:
        return news.summary
    return f"{_volume_phrase(volume).lower()} i {_strength_phrase(relative_strength).lower()}"


# Veredicte directe: combina la recomanacio (COMPRAR/VIGILAR/EVITAR) amb la
# qualitat del punt d'entrada (RUPTURA/MARGE_RECORREGUT/SOBREESTES/LATERAL)
# per donar UNA frase d'accio, en lloc de deixar que la persona hagi de
# creuar dues dades per treure la conclusio ella mateixa.
_VERDICTS = {
    ("COMPRAR", "RUPTURA"):          ("🟢", "ENTRA ARA"),
    ("COMPRAR", "MARGE_RECORREGUT"): ("🟢", "COMPRA — encara hi ha marge"),
    ("COMPRAR", "SOBREESTES"):       ("🟡", "ESPERA UN RECULL — ja ha pujat molt"),
    ("COMPRAR", "LATERAL"):          ("🟢", "COMPRAR"),
    ("COMPRAR", "SENSE_DADES"):      ("🟢", "COMPRAR (verifica dades)"),
    ("COMPRAR", "ALT_RISC_WHIPSAW"): ("⚠️", "COMPTE — whipsaw, no fiquis stop ajustat"),
    ("VIGILAR", "RUPTURA"):          ("🟡", "VIGILA'L DE PROP — pot trencar"),
    ("VIGILAR", "MARGE_RECORREGUT"): ("🟡", "VIGILAR"),
    ("VIGILAR", "SOBREESTES"):       ("🟡", "VIGILAR — sembla esgotat"),
    ("VIGILAR", "LATERAL"):          ("🟡", "VIGILAR"),
    ("VIGILAR", "SENSE_DADES"):      ("🟡", "VIGILAR"),
    ("VIGILAR", "ALT_RISC_WHIPSAW"): ("⚠️", "EVITA ENTRAR ARA — lateral erratic"),
    ("EVITAR", "RUPTURA"):           ("🔴", "EVITAR — encara feble de fons"),
    ("EVITAR", "MARGE_RECORREGUT"):  ("🔴", "EVITAR"),
    ("EVITAR", "SOBREESTES"):        ("🔴", "EVITAR"),
    ("EVITAR", "LATERAL"):           ("🔴", "EVITAR"),
    ("EVITAR", "SENSE_DADES"):       ("🔴", "EVITAR"),
    ("EVITAR", "ALT_RISC_WHIPSAW"):  ("⚠️", "EVITAR — lateral erratic"),
}


def build_verdict(recommendation: str, entry_quality: str) -> str:
    """Retorna un emoji + una frase d'accio directa combinant recomanacio i entrada.

    Args:
        recommendation: "COMPRAR" / "VIGILAR" / "EVITAR".
        entry_quality: qualitat d'entrada de EntrySignal.quality.

    Returns:
        Text tipus "🟢 ENTRA ARA".
    """
    emoji, phrase = _VERDICTS.get((recommendation, entry_quality), ("⚪", recommendation))
    return f"{emoji} {phrase}"


ENTRY_LABELS = {
    "RUPTURA": "RUPTURA (possible entrada, confirma amb volum)",
    "MARGE_RECORREGUT": "MARGE DE RECORREGUT (encara no toca sostre)",
    "SOBREESTES": "SOBREESTES (compte, ja allunyat / esgotant-se)",
    "LATERAL": "LATERAL (sense senyal clar d'entrada)",
    "ALT_RISC_WHIPSAW": "ALT RISC DE WHIPSAW (lateral erratic, veure nota de regim)",
    "SENSE_DADES": "SENSE DADES SUFICIENTS",
}

REGIME_LABELS = {
    "TENDENCIA": "TENDENCIA",
    "LATERAL_TRANQUIL": "LATERAL TRANQUIL",
    "LATERAL_CAOTIC": "LATERAL CAOTIC (whipsaw)",
    "SENSE_DADES": "SENSE DADES",
}


def render_fibonacci_section(fib: FibonacciLevels, currency: str = "EUR") -> List[str]:
    """Renderitza els nivells de Fibonacci (retrocessos i extensions) d'una accio.

    Args:
        fib: FibonacciLevels ja calculats.
        currency: codi de moneda per mostrar els preus.

    Returns:
        Llista de linies de text.
    """
    lines: List[str] = []
    scope_label = "intradia" if fib.scope == "INTRADIA" else "mensual"
    if fib.direction == "SENSE_DADES":
        lines.append(f"   Fibonacci ({scope_label}): {fib.notes}")
        return lines

    lines.append(f"   Fibonacci {scope_label} ({fib.direction}, rang {fib.swing_low:.2f}-{fib.swing_high:.2f} {currency}):")
    retro_str = "  ".join(f"{label} {price:.2f}" for label, price in fib.retracement_levels.items())
    lines.append(f"     Retrocessos (possibles entrades): {retro_str}")
    ext_str = "  ".join(f"{label} {price:.2f}" for label, price in fib.extension_levels.items())
    lines.append(f"     Extensions (possibles objectius): {ext_str}")
    lines.append(
        f"     Zona d'entrada suggerida: {fib.suggested_entry_zone[0]:.2f} - "
        f"{fib.suggested_entry_zone[1]:.2f} {currency}"
    )
    return lines


def render_stock_detail(r: StockReport, currency: str = "EUR", label: str = None) -> List[str]:
    """Renderitza el bloc de detall complet d'UNA accio (recomanacio, entrada,
    regim, motiu). Reutilitzat tant pel detall del TOP N com per la 'lupa'
    de seguiment dedicat d'un ticker concret (veure watch_ticker a main.py).

    Args:
        r: StockReport de l'accio.
        currency: codi de moneda per mostrar el preu.
        label: text opcional per la capcalera (per defecte, el nom de l'accio).

    Returns:
        Llista de linies de text (sense fer join, per poder-les combinar
        amb altres blocs).
    """
    entry_label = ENTRY_LABELS.get(r.entry.quality, r.entry.quality)
    regime_label = REGIME_LABELS.get(r.regime.regime, r.regime.regime)
    header = label or r.display_name

    lines: List[str] = []
    lines.append(f"--- {header} ---")
    lines.append(f"   Recomanacio: {r.scores.recommendation}   |   Punt d'entrada: {entry_label}")
    if r.scores.filter_note:
        lines.append(f"   🚫 {r.scores.filter_note}")
    lines.append(f"   Preu: {r.price.last_price:.2f} {currency}  ({r.price.change_pct:+.2f}%)")
    lines.append(f"   Volum relatiu: {r.volume.relative_volume:.2f}x")
    lines.append(f"   Forca relativa vs index: {r.relative_strength.relative_strength_pct:+.2f} p.p.")
    lines.append(f"   vs VWAP: {r.entry.position_vs_vwap_pct:+.2f}%   "
                 f"al maxim del dia: -{r.entry.distance_to_high_pct:.2f}%   "
                 f"al minim del dia: +{r.entry.distance_to_low_pct:.2f}%")
    lines.append(f"   Referencia de risc (no es consell): {r.entry.suggested_stop_reference:.2f} {currency}")
    lines.append(f"   Regim: {regime_label}   |   Efficiency Ratio: {r.regime.efficiency_ratio:.2f}   "
                 f"|   Reversions: {r.regime.reversals_count}   |   ATR: {r.regime.atr:.2f} {currency}")
    lines.append(f"   {r.regime.notes}")
    if r.regime.regime == "LATERAL_CAOTIC":
        lines.append(f"     ⚠️ {r.entry.notes}")
    lines.extend(render_fibonacci_section(r.fibonacci, currency=currency))
    if r.monthly_fibonacci is not None:
        lines.extend(render_fibonacci_section(r.monthly_fibonacci, currency=currency))
    if r.horizon is not None:
        lines.append(f"   Horitzo suggerit: {r.horizon.horizon}")
        lines.append(f"     {r.horizon.notes}")
    if r.range_quality is not None and r.range_quality.flags:
        lines.append(f"   ⚠️ Fiabilitat del rang mensual: {r.range_quality.confidence}")
        for flag in r.range_quality.flags:
            lines.append(f"     - {flag}")
    lines.append(f"   Noticia: {r.news.summary}")
    lines.append("   Motiu complet:")
    for line in r.explanation.split("\n"):
        lines.append(f"     {line}")
    lines.append("-" * 38)
    return lines


def render_report(
    reports: List[StockReport],
    top_n: int = TOP_N_RESULTS,
    market_name: str = "IBEX35",
    currency: str = "EUR",
) -> str:
    """Renderitza les top N accions com un bloc de text DIRECTE i clar,
    llegible d'un sol cop d'ull des del mobil.

    Args:
        reports: llista de StockReport, en qualsevol ordre.
        top_n: quantes mostrar (per defecte, config.TOP_N_RESULTS).
        market_name: nom del mercat analitzat, per al titol de l'informe.
        currency: codi de moneda (EUR, USD...) per mostrar el preu correctament.

    Returns:
        Text formatat, llest per fer print() a Colab.
    """
    # Prioritzem primer la recomanacio (COMPRAR > VIGILAR > EVITAR) i despres
    # el score dins de cada grup. Aixo evita que una accio bloquejada pel
    # filtre nomes-llargs (EVITAR per tendencia BAIXISTA, encara que el
    # score cru fos alt) ocupi un lloc del TOP N desplaçant oportunitats
    # realment operables.
    recommendation_priority = {
        RECOMMENDATION_BUY: 0,
        RECOMMENDATION_WATCH: 1,
        RECOMMENDATION_AVOID: 2,
    }
    sorted_reports = sorted(
        reports,
        key=lambda r: (recommendation_priority.get(r.scores.recommendation, 3), -r.scores.final_score),
    )
    top = sorted_reports[:top_n]

    lines: List[str] = []
    lines.append("=" * 38)
    lines.append(f"{market_name} — {len(top)} millors oportunitats")
    lines.append("=" * 38)
    lines.append("")

    if not top:
        lines.append("No hi ha dades disponibles en aquest moment.")
        return "\n".join(lines)

    for rank, r in enumerate(top, start=1):
        verdict = build_verdict(r.scores.recommendation, r.entry.quality)
        reason = build_short_reason(r.volume, r.relative_strength, r.news)

        lines.append(f"{rank}. {verdict}  —  {r.display_name}  ({r.scores.final_score:.0f}/100)")
        lines.append(f"   {reason.capitalize()}.")
        lines.append(
            f"   {r.price.last_price:.2f} {currency} ({r.price.change_pct:+.2f}%)   "
            f"vol {r.volume.relative_volume:.2f}x   vs VWAP {r.entry.position_vs_vwap_pct:+.2f}%"
        )
        if r.entry.extreme_move_warning:
            lines.append(
                f"   ⚠️ Moviment molt gran avui ({r.price.change_pct:+.2f}%) — "
                "mes risc de correccio tecnica els propers dies."
            )
        lines.append("-" * 38)

    lines.append("")
    lines.append("Detall complet de cada accio a sota (motius, VWAP, rang del dia).")
    lines.append("")

    for rank, r in enumerate(top, start=1):
        lines.extend(render_stock_detail(r, currency=currency, label=f"{rank}. {r.display_name}"))

    return "\n".join(lines)
