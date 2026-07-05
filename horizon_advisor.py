"""
horizon_advisor.py
===================
Combina el Fibonacci INTRADIA (rang d'avui) amb el Fibonacci MENSUAL
(rang de fons) per respondre una pregunta diferent de "hi entro o no":
un cop dins, val la pena deixar-la correr mes enlla d'avui (swing) o
nomes te sentit operar-la intradia?

Logica (nomes dades objectives, no prediccio):

1. Si la direccio intradia i la direccio mensual coincideixen (les dues
   ALCISTA) I el preu actual no esta a prop d'un nivell mensual (possible
   sostre de fons) -> CANDIDATA A SWING: el moviment d'avui sembla
   alineat amb la tendencia de fons i encara hi ha marge fins al proper
   nivell "important" de mes amunt.

2. Si el preu esta a prop d'un nivell mensual (extensio o retroces),
   encara que la direccio intradia sigui bona, el marge de recorregut
   es mes curt de fons -> NOMES INTRADIA: millor no confiar que seguira
   pujant mes enlla d'avui, i tancar la posicio en acabar la sessio.

3. Si la direccio intradia i la mensual NO coincideixen (p.ex. avui puja
   pero el mes ha estat baixista de fons, o al reves) -> NOMES INTRADIA:
   el moviment d'avui pot ser nomes un rebot dins una tendencia de fons
   diferent, mes arriscat de mantenir mes d'un dia.
"""

from typing import Optional

from config import (
    MONTHLY_LEVEL_PROXIMITY_PCT,
    HORIZON_SWING_CANDIDATE,
    HORIZON_INTRADAY_ONLY,
    HORIZON_UNCLEAR,
)
from models import FibonacciLevels, HorizonAnalysis


def _price_near_any_monthly_level(last_price: float, monthly: FibonacciLevels) -> bool:
    """Comprova si el preu actual esta a prop (dins MONTHLY_LEVEL_PROXIMITY_PCT)
    d'algun dels nivells de retroces o extensio mensuals.

    Args:
        last_price: preu actual.
        monthly: FibonacciLevels (scope="MENSUAL") ja calculat.

    Returns:
        True si hi ha algun nivell mensual a prop, fals altrament.
    """
    if monthly.direction == "SENSE_DADES" or last_price <= 0:
        return False

    rang_ref = monthly.swing_high - monthly.swing_low
    if rang_ref <= 0:
        return False

    tolerance = rang_ref * (MONTHLY_LEVEL_PROXIMITY_PCT / 100.0)

    # El maxim i el minim del rang de referencia tambe compten com a nivells
    # importants (son el sostre/suport de fons en si, no nomes els retrocessos
    # o extensions calculats a partir d'ells).
    all_levels = (
        list(monthly.retracement_levels.values())
        + list(monthly.extension_levels.values())
        + [monthly.swing_high, monthly.swing_low]
    )
    for level in all_levels:
        if abs(last_price - level) <= tolerance:
            return True
    return False


def analyze_horizon(
    last_price: float,
    intraday_fibonacci: FibonacciLevels,
    monthly_fibonacci: Optional[FibonacciLevels],
) -> HorizonAnalysis:
    """Calcula la recomanacio d'horitzo temporal (intradia vs swing).

    Args:
        last_price: preu actual de l'accio.
        intraday_fibonacci: FibonacciLevels (scope="INTRADIA") ja calculat.
        monthly_fibonacci: FibonacciLevels (scope="MENSUAL") ja calculat, o
            None si no s'ha pogut descarregar (p.ex. accio amb poc historial).

    Returns:
        HorizonAnalysis amb l'horitzo recomanat i el motiu.
    """
    if monthly_fibonacci is None or monthly_fibonacci.direction == "SENSE_DADES":
        return HorizonAnalysis(
            horizon=HORIZON_UNCLEAR,
            intraday_direction=intraday_fibonacci.direction,
            monthly_direction="SENSE_DADES",
            near_monthly_level=False,
            notes="Sense prou historial mensual per contrastar amb la tendencia de fons.",
        )

    near_level = _price_near_any_monthly_level(last_price, monthly_fibonacci)
    aligned = intraday_fibonacci.direction == monthly_fibonacci.direction == "ALCISTA"

    if aligned and not near_level:
        horizon = HORIZON_SWING_CANDIDATE
        notes = (
            "El moviment d'avui va en la mateixa direccio que la tendencia de fons (ultim mes) "
            "i el preu encara no esta a prop de cap nivell mensual important. Hi ha marge per "
            "considerar mantenir la posicio mes enlla d'avui si la tesi es manté."
        )
    elif aligned and near_level:
        horizon = HORIZON_INTRADAY_ONLY
        notes = (
            "El moviment d'avui va a favor de la tendencia de fons, pero el preu ja esta a prop "
            "d'un nivell mensual important (possible sostre/suport de fons). Millor no donar per fet "
            "que seguira mes enlla d'avui: considera tancar la posicio en acabar la sessio."
        )
    else:
        horizon = HORIZON_INTRADAY_ONLY
        notes = (
            f"El moviment d'avui ({intraday_fibonacci.direction}) no coincideix amb la tendencia "
            f"de fons de l'ultim mes ({monthly_fibonacci.direction}). Podria ser nomes un rebot "
            "puntual: mes arriscat mantenir-la mes enlla d'avui."
        )

    return HorizonAnalysis(
        horizon=horizon,
        intraday_direction=intraday_fibonacci.direction,
        monthly_direction=monthly_fibonacci.direction,
        near_monthly_level=near_level,
        notes=notes,
    )
