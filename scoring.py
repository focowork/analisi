"""
scoring.py
==========
Combina els quatre scores pilar (volum, forca relativa, noticies, energia)
en un score final unic i una recomanacio. Els pesos venen de config.py
perque es puguin ajustar sense tocar aquesta logica.
"""

from config import (
    WEIGHT_VOLUME,
    WEIGHT_RELATIVE_STRENGTH,
    WEIGHT_NEWS,
    WEIGHT_ENERGY,
    THRESHOLD_BUY,
    THRESHOLD_WATCH,
    RECOMMENDATION_BUY,
    RECOMMENDATION_WATCH,
    RECOMMENDATION_AVOID,
    LONG_ONLY_MODE,
    LONG_ONLY_BLOCKED_DIRECTION,
    LONG_ONLY_BLOCK_NOTE,
)
from models import (
    VolumeAnalysis,
    RelativeStrengthAnalysis,
    NewsAnalysis,
    EnergyAnalysis,
    ScoreBreakdown,
    FibonacciLevels,
)


def compute_final_score(
    volume_score: float,
    relative_strength_score: float,
    news_score: float,
    energy_score: float,
) -> float:
    """Calcula el score final ponderat a partir dels quatre scores pilar.

    Args:
        volume_score: 0-100.
        relative_strength_score: 0-100.
        news_score: 0-100.
        energy_score: 0-100.

    Returns:
        Score final ponderat, 0-100.
    """
    return (
        volume_score * WEIGHT_VOLUME
        + relative_strength_score * WEIGHT_RELATIVE_STRENGTH
        + news_score * WEIGHT_NEWS
        + energy_score * WEIGHT_ENERGY
    )


def determine_recommendation(final_score: float) -> str:
    """Mapeja el score final a una etiqueta de recomanacio.

    Args:
        final_score: 0-100.

    Returns:
        RECOMMENDATION_BUY / RECOMMENDATION_WATCH / RECOMMENDATION_AVOID.
    """
    if final_score >= THRESHOLD_BUY:
        return RECOMMENDATION_BUY
    if final_score >= THRESHOLD_WATCH:
        return RECOMMENDATION_WATCH
    return RECOMMENDATION_AVOID


def build_score_breakdown(
    volume: VolumeAnalysis,
    relative_strength: RelativeStrengthAnalysis,
    news: NewsAnalysis,
    energy: EnergyAnalysis,
) -> ScoreBreakdown:
    """Construeix el ScoreBreakdown complet d'una accio a partir de les 4 analisis.

    Args:
        volume: resultat de volume.analyze_volume.
        relative_strength: resultat de relative_strength.analyze_relative_strength.
        news: resultat de news.analyze_news.
        energy: resultat de energy.analyze_energy.

    Returns:
        ScoreBreakdown amb tots els scores pilar, el score final i la recomanacio.
    """
    final_score = compute_final_score(
        volume_score=volume.score,
        relative_strength_score=relative_strength.score,
        news_score=news.score,
        energy_score=energy.score,
    )
    recommendation = determine_recommendation(final_score)
    return ScoreBreakdown(
        volume_score=volume.score,
        relative_strength_score=relative_strength.score,
        news_score=news.score,
        energy_score=energy.score,
        final_score=final_score,
        recommendation=recommendation,
    )


def apply_long_only_filter(scores: ScoreBreakdown, fibonacci: FibonacciLevels) -> ScoreBreakdown:
    """Aplica el filtre "nomes llargs": si la tendencia dominant d'avui es
    BAIXISTA, sobreescriu la recomanacio a EVITAR, independentment de com
    de alt fos el score dels 4 pilars.

    Motiu: l'usuari nomes opera al alça i busca tancar la sessio en positiu.
    Entrar llarg en una accio que avui domina a la baixa vol dir operar en
    contra de la tendencia intradia, cosa que redueix les probabilitats
    d'exit encara que el volum/forca/noticies/energia siguin bons.

    Args:
        scores: ScoreBreakdown ja calculat pels 4 pilars.
        fibonacci: FibonacciLevels ja calculat (conte la direccio del dia).

    Returns:
        El mateix ScoreBreakdown si no aplica el filtre, o una copia amb
        la recomanacio sobreescrita i `filter_note` omplert si aplica.
    """
    if not LONG_ONLY_MODE:
        return scores
    if fibonacci.direction != LONG_ONLY_BLOCKED_DIRECTION:
        return scores

    return ScoreBreakdown(
        volume_score=scores.volume_score,
        relative_strength_score=scores.relative_strength_score,
        news_score=scores.news_score,
        energy_score=scores.energy_score,
        final_score=scores.final_score,
        recommendation=RECOMMENDATION_AVOID,
        filter_note=LONG_ONLY_BLOCK_NOTE,
    )
