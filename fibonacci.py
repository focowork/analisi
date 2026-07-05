"""
fibonacci.py
============
Projecta nivells de Fibonacci a partir d'un rang de preu de referencia,
per identificar:

- RETROCESSOS (23.6% / 38.2% / 50% / 61.8% / 78.6%): possibles zones on
  el preu podria "descansar" abans de continuar el moviment. La zona
  entre el 50% i el 61.8% es la mes vigilada pels traders tecnics i es
  marca com a "zona d'entrada suggerida".
- EXTENSIONS (127.2% / 161.8% / 200%): possibles objectius de sortida
  si el moviment continua mes enlla del rang actual.

La direccio (ALCISTA/BAIXISTA) es determina a partir de si el preu
actual esta mes a prop del maxim o del minim del rang de referencia.

Aquest modul calcula DOS ambits (scope), reutilitzant el mateix nucli
matematic:
- INTRADIA: rang del dia d'avui (maxim/minim intradia). Analyze_fibonacci().
- MENSUAL: rang de fons (per defecte, ultim mes). Dada complementaria per
  decidir si val la pena deixar correr una posicio mes enlla d'avui (swing)
  o si nomes te sentit operar-la intradia. Analyze_fibonacci_monthly().

IMPORTANT: aixo es una tecnica d'analisi tecnica estandard basada en
proporcions matematiques (la seqüencia de Fibonacci), NO una prediccio.
Els nivells son referencies que molts altres traders tambe vigilen,
cosa que els dona relleváncia estadistica, pero no garanteixen res.
"""

from typing import Dict

from models import PriceSnapshot, MonthlySnapshot, FibonacciLevels


# Percentatges estandard de Fibonacci (com a fraccio, no %).
RETRACEMENT_RATIOS: Dict[str, float] = {
    "23.6%": 0.236,
    "38.2%": 0.382,
    "50.0%": 0.500,
    "61.8%": 0.618,
    "78.6%": 0.786,
}

EXTENSION_RATIOS: Dict[str, float] = {
    "127.2%": 1.272,
    "161.8%": 1.618,
    "200.0%": 2.000,
}


def _compute_fibonacci_levels(
    swing_high: float, swing_low: float, last_price: float, scope: str
) -> FibonacciLevels:
    """Nucli de calcul de nivells de Fibonacci, independent de si el rang
    ve d'avui (intradia) o d'un periode mes llarg (mensual). Reutilitzat
    per analyze_fibonacci() i analyze_fibonacci_monthly().

    Args:
        swing_high: maxim del rang de referencia.
        swing_low: minim del rang de referencia.
        last_price: preu actual.
        scope: "INTRADIA" o "MENSUAL", nomes per etiquetar el resultat.

    Returns:
        FibonacciLevels amb retrocessos, extensions i direccio dominant.
    """
    if swing_high <= 0 or swing_low <= 0 or swing_high == swing_low:
        return FibonacciLevels(
            direction="SENSE_DADES",
            swing_low=swing_low,
            swing_high=swing_high,
            scope=scope,
            notes=f"Sense prou rang de preu ({scope.lower()}) per calcular nivells de Fibonacci.",
        )

    rang = swing_high - swing_low

    # Direccio: si el preu actual esta mes a prop del maxim, el moviment
    # dominant del rang ha estat alcista (i viceversa).
    dist_to_high = swing_high - last_price
    dist_to_low = last_price - swing_low
    direction = "ALCISTA" if dist_to_high <= dist_to_low else "BAIXISTA"

    retracement_levels: Dict[str, float] = {}
    extension_levels: Dict[str, float] = {}

    scope_label = "avui" if scope == "INTRADIA" else "del periode de fons"

    if direction == "ALCISTA":
        for label, ratio in RETRACEMENT_RATIOS.items():
            retracement_levels[label] = swing_high - (rang * ratio)
        for label, ratio in EXTENSION_RATIOS.items():
            extension_levels[label] = swing_low + (rang * ratio)
        suggested_entry_zone = (retracement_levels["61.8%"], retracement_levels["50.0%"])
        notes = (
            f"Moviment dominant {scope_label} a l'alça. Els retrocessos son possibles zones on "
            "el preu podria descansar abans de continuar pujant; les extensions son "
            "possibles objectius de sortida si segueix la pujada."
        )
    else:
        for label, ratio in RETRACEMENT_RATIOS.items():
            retracement_levels[label] = swing_low + (rang * ratio)
        for label, ratio in EXTENSION_RATIOS.items():
            extension_levels[label] = swing_high - (rang * ratio)
        suggested_entry_zone = (retracement_levels["50.0%"], retracement_levels["61.8%"])
        notes = (
            f"Moviment dominant {scope_label} a la baixa. Els retrocessos son possibles zones on "
            "el preu podria descansar abans de continuar baixant; les extensions son "
            "possibles objectius si segueix la baixada."
        )

    return FibonacciLevels(
        direction=direction,
        swing_low=swing_low,
        swing_high=swing_high,
        scope=scope,
        retracement_levels=retracement_levels,
        extension_levels=extension_levels,
        suggested_entry_zone=suggested_entry_zone,
        notes=notes,
    )


def analyze_fibonacci(price: PriceSnapshot) -> FibonacciLevels:
    """Calcula els nivells de Fibonacci INTRADIA a partir del rang de preu
    del dia d'una accio (maxim/minim d'avui).

    Args:
        price: PriceSnapshot amb day_high, day_low i last_price ja calculats.

    Returns:
        FibonacciLevels (scope="INTRADIA") amb els nivells de retroces
        (possibles entrades), els nivells d'extensio (possibles objectius
        de sortida) i la zona d'entrada suggerida (banda 50%-61.8%).
    """
    return _compute_fibonacci_levels(
        swing_high=price.day_high, swing_low=price.day_low, last_price=price.last_price, scope="INTRADIA"
    )


def analyze_fibonacci_monthly(monthly: MonthlySnapshot) -> FibonacciLevels:
    """Calcula els nivells de Fibonacci MENSUAL (rang de fons), com a dada
    complementaria al Fibonacci intradia: serveix per veure si el preu
    actual esta a prop d'un sostre/suport de fons (no nomes d'avui).

    Args:
        monthly: MonthlySnapshot amb monthly_high, monthly_low i last_price.

    Returns:
        FibonacciLevels (scope="MENSUAL").
    """
    return _compute_fibonacci_levels(
        swing_high=monthly.monthly_high,
        swing_low=monthly.monthly_low,
        last_price=monthly.last_price,
        scope="MENSUAL",
    )
