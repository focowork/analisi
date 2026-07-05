"""
main.py
=======
Punt d'entrada de l'IBEX Intraday Decision Engine.

Executa aquest modul en qualsevol moment de la sessio (09:45, 11:30, 16:00...)
per obtenir una analisi instantania de l'univers d'accions, ordenada per
oportunitat.

Us a Google Colab:

    !pip install yfinance feedparser --quiet
    # (puja/importa config.py, models.py, data_loader.py, volume.py,
    #  relative_strength.py, news.py, energy.py, scoring.py, report.py, main.py)
    from main import run
    run()

IMPORTANT: aquest programa NO prediu abans de l'obertura. Nomes analitza
la situacio real en el moment exacte en que s'executa.
"""

from typing import Dict, List, Optional

from config import (
    STOCK_UNIVERSE,
    ACTIVE_MARKET,
    MARKET_STOCK_UNIVERSES,
    MARKET_CURRENCY,
    MARKETS_TO_RUN,
)
from models import StockReport, IndexSnapshot
import data_loader
import volume as volume_module
import relative_strength as rs_module
import news as news_module
import energy as energy_module
import regime as regime_module
import entry_signal as entry_module
import fibonacci as fibonacci_module
import horizon_advisor as horizon_module
import range_quality as range_quality_module
import scoring
import report as report_module


def analyze_stock(display_name: str, ticker: str, index_snapshot: IndexSnapshot) -> StockReport:
    """Executa el pipeline complet d'analisi per una sola accio.

    Args:
        display_name: nom llegible (p.ex. "INDRA").
        ticker: simbol de yfinance (p.ex. "IDR.MC").
        index_snapshot: IndexSnapshot de l'index de referencia, ja descarregat.

    Returns:
        StockReport complet d'aquesta accio.
    """
    price = data_loader.get_price_snapshot(display_name, ticker)

    vol_analysis = volume_module.analyze_volume(price)
    rs_analysis = rs_module.analyze_relative_strength(price, index_snapshot)
    news_analysis = news_module.analyze_news(display_name)
    energy_analysis = energy_module.analyze_energy(price)
    regime_analysis = regime_module.analyze_regime(price)
    entry_analysis = entry_module.analyze_entry(price, energy_analysis, regime_analysis)
    fibonacci_analysis = fibonacci_module.analyze_fibonacci(price)

    monthly_snapshot = data_loader.get_monthly_snapshot(ticker, price.last_price)
    monthly_fibonacci_analysis = fibonacci_module.analyze_fibonacci_monthly(monthly_snapshot)
    horizon_analysis = horizon_module.analyze_horizon(
        last_price=price.last_price,
        intraday_fibonacci=fibonacci_analysis,
        monthly_fibonacci=monthly_fibonacci_analysis,
    )
    range_quality_analysis = range_quality_module.analyze_range_quality(monthly_snapshot, news=news_analysis)

    score_breakdown = scoring.build_score_breakdown(
        volume=vol_analysis,
        relative_strength=rs_analysis,
        news=news_analysis,
        energy=energy_analysis,
    )
    # Filtre nomes-llargs: si la tendencia d'avui es BAIXISTA, sobreescriu
    # la recomanacio a EVITAR (veure config.LONG_ONLY_MODE).
    score_breakdown = scoring.apply_long_only_filter(score_breakdown, fibonacci_analysis)

    return report_module.build_stock_report(
        price=price,
        volume=vol_analysis,
        relative_strength=rs_analysis,
        news=news_analysis,
        energy=energy_analysis,
        scores=score_breakdown,
        entry=entry_analysis,
        regime=regime_analysis,
        fibonacci=fibonacci_analysis,
        monthly_fibonacci=monthly_fibonacci_analysis,
        horizon=horizon_analysis,
        range_quality=range_quality_analysis,
    )


def analyze_market(market: str = ACTIVE_MARKET, universe: Optional[Dict[str, str]] = None) -> List[StockReport]:
    """Executa el pipeline complet per UN mercat i retorna els StockReport crus
    (sense renderitzar), perque altres moduls (com compare.py) els puguin
    reutilitzar per fer snapshots i comparacions.

    Args:
        market: clau de config.MARKET_INDEX_TICKERS (p.ex. "IBEX35", "NASDAQ").
        universe: mapeig opcional nom_visible -> ticker per sobreescriure
            l'univers per defecte d'aquest mercat.

    Returns:
        Llista de StockReport (un per accio analitzada amb exit).
    """
    universe = universe or MARKET_STOCK_UNIVERSES.get(market, STOCK_UNIVERSE)
    index_snapshot = data_loader.get_index_snapshot(market)

    reports: List[StockReport] = []
    for display_name, ticker in universe.items():
        try:
            reports.append(analyze_stock(display_name, ticker, index_snapshot))
        except Exception as exc:
            print(f"[main] Avis: error analitzant {display_name}: {exc}")
    return reports


def run(market: str = ACTIVE_MARKET, universe: Optional[Dict[str, str]] = None) -> str:
    """Executa el pipeline complet per UN mercat i imprimeix l'informe.

    Args:
        market: clau de config.MARKET_INDEX_TICKERS (p.ex. "IBEX35", "NASDAQ").
            Per defecte, config.ACTIVE_MARKET.
        universe: mapeig opcional nom_visible -> ticker per sobreescriure
            l'univers per defecte d'aquest mercat (util per testejar amb
            menys accions).

    Returns:
        El text de l'informe renderitzat (tambe s'imprimeix per pantalla).
    """
    currency = MARKET_CURRENCY.get(market, "EUR")
    print(f"Analitzant mercat: {market} ...\n")

    reports = analyze_market(market=market, universe=universe)

    rendered = report_module.render_report(reports, market_name=market, currency=currency)
    print(rendered)
    return rendered


def watch_ticker(display_name: str, ticker: str, market: str = ACTIVE_MARKET) -> str:
    """Fa un seguiment EXHAUSTIU d'UN sol valor (p.ex. Grifols), amb tot el
    detall (VWAP, rang del dia, Efficiency Ratio, reversions, ATR), sense
    filtrar-lo per si surt o no al TOP N del mercat. Util per valors en
    regim lateral erratic que et preocupen especificament, encara que
    el seu score no sigui prou alt per sortir al rànquing general.

    Args:
        display_name: nom llegible (p.ex. "GRIFOLS").
        ticker: simbol de yfinance (p.ex. "GRF.MC").
        market: mercat de referencia per calcular la forca relativa
            (per defecte, config.ACTIVE_MARKET).

    Returns:
        El text del detall renderitzat (tambe s'imprimeix per pantalla).
    """
    currency = MARKET_CURRENCY.get(market, "EUR")
    index_snapshot = data_loader.get_index_snapshot(market)

    try:
        r = analyze_stock(display_name, ticker, index_snapshot)
    except Exception as exc:
        msg = f"[main] Error analitzant {display_name}: {exc}"
        print(msg)
        return msg

    lines = [f"SEGUIMENT DEDICAT — {display_name} ({ticker})"]
    lines.append("=" * 38)
    lines.extend(report_module.render_stock_detail(r, currency=currency, label=display_name))
    rendered = "\n".join(lines)
    print(rendered)
    return rendered


def run_multi_market(markets: Optional[List[str]] = None) -> str:
    """Executa el pipeline per DIVERSOS mercats en la mateixa crida i
    concatena els informes (p.ex. IBEX35 + NASDAQ alhora).

    Args:
        markets: llista de mercats (claus de config.MARKET_INDEX_TICKERS).
            Per defecte, config.MARKETS_TO_RUN (per defecte ["IBEX35", "NASDAQ"]).

    Returns:
        Text amb tots els informes concatenats, un darrere l'altre.
    """
    markets = markets or MARKETS_TO_RUN
    rendered_reports: List[str] = []

    for market in markets:
        rendered_reports.append(run(market=market))
        print("\n")

    return "\n\n".join(rendered_reports)


if __name__ == "__main__":
    run_multi_market()
