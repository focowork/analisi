"""
compare.py
==========
Permet capturar "fotografies" (snapshots) de l'analisi en diferents
moments de la sessio (p.ex. a les 09:45 i despres a les 09:55, deu
minuts mes tard) i comparar-les per veure com evoluciona el score, el
preu i la recomanacio de cada accio. Util per decidir un punt d'entrada:
no nomes mirar una foto fixa, sino veure la tendencia entre dues.

Us a Colab:

    from compare import take_snapshot, compare_latest

    snap1 = take_snapshot()      # primera foto (p.ex. 09:45)
    # ... espera 10 minuts ...
    snap2 = take_snapshot()      # segona foto (p.ex. 09:55)

    print(compare_latest())      # taula de diferencies, llesta per llegir
                                  # o enganxar a un altre assistent (ChatGPT...)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from config import MARKETS_TO_RUN
from models import StockReport
import main


@dataclass
class Snapshot:
    """Una fotografia completa de tots els mercats analitzats en un instant."""
    label: str                                   # p.ex. "09:45:12"
    markets: Dict[str, List[StockReport]] = field(default_factory=dict)


# Historial de snapshots preses durant la sessio de Colab (en memoria,
# es perd si reinicies el runtime).
SNAPSHOTS: List[Snapshot] = []


def take_snapshot(markets: Optional[List[str]] = None, label: Optional[str] = None) -> Snapshot:
    """Executa l'analisi ara mateix per un o mes mercats i guarda el resultat
    com a nova entrada a SNAPSHOTS.

    Args:
        markets: llista de mercats a analitzar (per defecte, config.MARKETS_TO_RUN).
        label: etiqueta opcional per identificar la foto (per defecte, l'hora actual).

    Returns:
        El Snapshot acabat de crear (tambe queda guardat a SNAPSHOTS).
    """
    markets = markets or MARKETS_TO_RUN
    label = label or datetime.now().strftime("%H:%M:%S")

    snap = Snapshot(label=label)
    for market in markets:
        print(f"[compare] Capturant {market} a les {label} ...")
        snap.markets[market] = main.analyze_market(market=market)

    SNAPSHOTS.append(snap)
    print(f"[compare] Snapshot '{label}' guardat ({len(SNAPSHOTS)} en total aquesta sessio).\n")
    return snap


def _index_by_ticker(reports: List[StockReport]) -> Dict[str, StockReport]:
    return {r.ticker: r for r in reports}


def compare_snapshots(older: Snapshot, newer: Snapshot, only_changed: bool = False) -> str:
    """Compara dues snapshots i genera un text amb els canvis de cada accio:
    delta de score, delta de preu, delta de volum relatiu i si ha canviat
    la recomanacio (p.ex. de VIGILAR a COMPRAR).

    Args:
        older: snapshot mes antiga.
        newer: snapshot mes recent.
        only_changed: si True, nomes mostra accions on el score s'ha mogut
            almenys 1 punt (per centrar-se en el que realment es mou).

    Returns:
        Text formatat, llest per llegir a Colab o enganxar a un altre
        assistent (ChatGPT, etc.) per demanar una segona opinio.
    """
    lines: List[str] = []
    lines.append("=" * 42)
    lines.append(f"COMPARATIVA  {older.label}  ->  {newer.label}")
    lines.append("=" * 42)

    common_markets = [m for m in older.markets if m in newer.markets]
    if not common_markets:
        return "No hi ha mercats en comu entre les dues snapshots."

    for market in common_markets:
        old_by_ticker = _index_by_ticker(older.markets[market])
        new_by_ticker = _index_by_ticker(newer.markets[market])
        common_tickers = [t for t in new_by_ticker if t in old_by_ticker]

        rows = []
        for ticker in common_tickers:
            old_r = old_by_ticker[ticker]
            new_r = new_by_ticker[ticker]

            delta_score = new_r.scores.final_score - old_r.scores.final_score
            delta_price_pct = new_r.price.change_pct - old_r.price.change_pct
            delta_rel_vol = new_r.volume.relative_volume - old_r.volume.relative_volume
            rec_changed = old_r.scores.recommendation != new_r.scores.recommendation
            entry_changed = old_r.entry.quality != new_r.entry.quality
            regime_changed = old_r.regime.regime != new_r.regime.regime

            if only_changed and abs(delta_score) < 1 and not rec_changed and not entry_changed and not regime_changed:
                continue

            rows.append({
                "ticker": ticker,
                "name": new_r.display_name,
                "old_score": old_r.scores.final_score,
                "new_score": new_r.scores.final_score,
                "delta_score": delta_score,
                "old_rec": old_r.scores.recommendation,
                "new_rec": new_r.scores.recommendation,
                "rec_changed": rec_changed,
                "old_entry": old_r.entry.quality,
                "new_entry": new_r.entry.quality,
                "entry_changed": entry_changed,
                "old_regime": old_r.regime.regime,
                "new_regime": new_r.regime.regime,
                "regime_changed": regime_changed,
                "delta_price_pct": delta_price_pct,
                "delta_rel_vol": delta_rel_vol,
            })

        rows.sort(key=lambda r: r["delta_score"], reverse=True)

        lines.append("")
        lines.append(f"--- {market} ---")
        if not rows:
            lines.append("  (cap canvi rellevant)")
            continue

        for r in rows:
            arrow = "->" if r["rec_changed"] else "  "
            flag = " *** CANVI DE RECOMANACIO ***" if r["rec_changed"] else ""
            entry_flag = f"   entrada: {r['old_entry']} -> {r['new_entry']}" if r["entry_changed"] else f"   entrada: {r['new_entry']}"
            regime_flag = f"   regim: {r['old_regime']} -> {r['new_regime']}" if r["regime_changed"] else f"   regim: {r['new_regime']}"
            lines.append(
                f"  {r['name']:<10} score {r['old_score']:.0f} {arrow} {r['new_score']:.0f} "
                f"({r['delta_score']:+.0f})   "
                f"preu {r['delta_price_pct']:+.2f} p.p.   "
                f"vol.rel {r['delta_rel_vol']:+.2f}x   "
                f"[{r['old_rec']} {arrow} {r['new_rec']}]{flag}"
                f"{entry_flag}"
                f"{regime_flag}"
            )

    lines.append("")
    lines.append("=" * 42)
    return "\n".join(lines)


def compare_latest(only_changed: bool = False) -> str:
    """Compara automaticament les DUES ultimes snapshots preses aquesta sessio.

    Args:
        only_changed: veure compare_snapshots().

    Returns:
        Text de la comparativa, o un avis si encara no hi ha 2 snapshots.
    """
    if len(SNAPSHOTS) < 2:
        return (
            f"Nomes hi ha {len(SNAPSHOTS)} snapshot(s) guardada(es) aquesta sessio. "
            "Cal fer take_snapshot() almenys dues vegades abans de comparar."
        )
    rendered = compare_snapshots(SNAPSHOTS[-2], SNAPSHOTS[-1], only_changed=only_changed)
    print(rendered)
    return rendered
