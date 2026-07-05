"""
range_quality.py
=================
Contrasta si el rang mensual (maxim/minim) que fa servir fibonacci.py per
calcular el Fibonacci MENSUAL es fiable, o si pot estar distorsionat per
un esdeveniment excepcional:

- SORTIDA A BORSA RECENT: si hi ha poques sessions de cotitzacio
  disponibles, el "rang de l'ultim mes" pot incloure el dia de debut
  (moviments molt bruscos que no son tendencia real).
- SALT D'UN SOL DIA: una OPA, una ampliacio de capital o un resultat
  extraordinari poden disparar el preu un 20-40% en una sola sessio.
  Si aquest salt es precisament el que marca el maxim o el minim actual,
  el "nivell important" que fem servir es en realitat soroll d'un dia,
  no un nivell tecnic real.
- NOTICIES: si la categoria de noticia mes rellevant d'avui es "OPA",
  es un senyal addicional que el rang de fons pot estar condicionat per
  aquest event (es reutilitza news.py, no es torna a cercar res).

IMPORTANT: aquest modul NO desqualifica el Fibonacci mensual ni el
sobreescriu. Nomes li posa una etiqueta de confiança (ALTA/MITJANA/BAIXA)
i explica per que, perque la persona decideixi quant fiar-se'n.
"""

from typing import List, Optional

from config import (
    RANGE_QUALITY_MIN_TRADING_DAYS,
    RANGE_QUALITY_GAP_WARNING_PCT,
    RANGE_QUALITY_HIGH,
    RANGE_QUALITY_MEDIUM,
    RANGE_QUALITY_LOW,
)
from models import MonthlySnapshot, NewsAnalysis, RangeQualityAssessment

OPA_NEWS_CATEGORY: str = "OPA"


def analyze_range_quality(monthly: MonthlySnapshot, news: Optional[NewsAnalysis] = None) -> RangeQualityAssessment:
    """Avalua la fiabilitat del rang mensual (maxim/minim) fent servir
    nomes dades objectives ja calculades (no torna a descarregar res).

    Args:
        monthly: MonthlySnapshot ja calculat (inclou trading_days_available,
            max_daily_move_pct i els flags high/low_set_by_extreme_day).
        news: NewsAnalysis (opcional) d'aquesta accio, per contrastar si la
            categoria de noticia mes rellevant d'avui es "OPA".

    Returns:
        RangeQualityAssessment amb reliable, confidence, flags i notes.
    """
    flags: List[str] = []

    if monthly.trading_days_available == 0:
        return RangeQualityAssessment(
            reliable=False,
            confidence=RANGE_QUALITY_LOW,
            flags=["Sense dades mensuals disponibles."],
            notes="No s'ha pogut descarregar historial mensual per aquesta accio.",
        )

    if monthly.trading_days_available < RANGE_QUALITY_MIN_TRADING_DAYS:
        flags.append(
            f"Nomes {monthly.trading_days_available} sessions de cotitzacio disponibles "
            f"(per sota de {RANGE_QUALITY_MIN_TRADING_DAYS}): historial curt, possible sortida "
            "a borsa recent. El rang mensual pot no ser representatiu encara."
        )

    if monthly.max_daily_move_pct >= RANGE_QUALITY_GAP_WARNING_PCT:
        if monthly.high_set_by_extreme_day or monthly.low_set_by_extreme_day:
            extrem = "el maxim" if monthly.high_set_by_extreme_day else "el minim"
            flags.append(
                f"{extrem.capitalize()} del rang mensual coincideix amb un salt d'un sol dia "
                f"de {monthly.max_daily_move_pct:.1f}%: pot ser una OPA, ampliacio de capital o "
                "resultat extraordinari, no un nivell tecnic real."
            )
        else:
            flags.append(
                f"Hi ha hagut un salt d'un sol dia de {monthly.max_daily_move_pct:.1f}% aquest mes "
                "(event puntual), encara que no marca el maxim/minim actual del rang."
            )

    if news is not None and news.best_category == OPA_NEWS_CATEGORY:
        flags.append(
            "Les noticies d'avui classifiquen la categoria OPA per aquesta accio: el rang "
            "mensual pot estar condicionat per aquest event."
        )

    if not flags:
        return RangeQualityAssessment(
            reliable=True,
            confidence=RANGE_QUALITY_HIGH,
            flags=[],
            notes="Sense senyals d'esdeveniments excepcionals detectats: el rang mensual sembla representatiu.",
        )

    confidence = RANGE_QUALITY_MEDIUM if len(flags) == 1 else RANGE_QUALITY_LOW
    reliable = confidence == RANGE_QUALITY_HIGH  # amb 1+ flags, mai es HIGH; queda False
    notes = " ".join(flags)

    return RangeQualityAssessment(reliable=reliable, confidence=confidence, flags=flags, notes=notes)
