"""
data_loader.py
==============
Responsable de TOTA la descarrega de dades de mercat (yfinance / Yahoo
Finance). Aquest modul nomes descarrega i dona forma lleugera a les dades
(PriceSnapshot / IndexSnapshot). Cap logica de scoring viu aqui.
"""

import datetime as dt
from typing import Dict, List

import pandas as pd
import yfinance as yf

from config import (
    STOCK_UNIVERSE,
    MARKET_INDEX_TICKERS,
    ACTIVE_MARKET,
    INTRADAY_INTERVAL,
    INTRADAY_PERIOD,
    HISTORICAL_PERIOD_FOR_AVG_VOLUME,
    HISTORICAL_INTERVAL_FOR_AVG_VOLUME,
    ENERGY_LOOKBACK_BARS,
    REGIME_LOOKBACK_BARS,
    MONTHLY_LOOKBACK_PERIOD,
    MONTHLY_LOOKBACK_INTERVAL,
)
from models import PriceSnapshot, IndexSnapshot, MonthlySnapshot


def _download_intraday(ticker: str) -> pd.DataFrame:
    """Descarrega les barres intradia d'avui per un ticker.

    Args:
        ticker: simbol de yfinance.

    Returns:
        DataFrame indexat per datetime amb columnes Open, High, Low, Close,
        Volume. DataFrame buit si no hi ha dades (mercat tancat, festiu...).
    """
    data = yf.download(
        tickers=ticker,
        period=INTRADAY_PERIOD,
        interval=INTRADAY_INTERVAL,
        progress=False,
        auto_adjust=False,
    )
    if isinstance(data.columns, pd.MultiIndex):
        # yfinance a vegades retorna columnes multi-index encara que nomes
        # es demani un ticker.
        data.columns = [c[0] for c in data.columns]
    return data


def _historical_average_volume_at_time(ticker: str, current_time: dt.time) -> float:
    """Estima el volum mitja acumulat fins `current_time` en un dia tipic.

    Aixo dona un "volum relatiu" mes just que comparar amb la mitjana de tot
    el dia, ja que p.ex. les 10:00 tenen naturalment menys volum que les 16:00.

    Args:
        ticker: simbol de yfinance.
        current_time: hora del dia amb la qual comparar l'historic.

    Returns:
        Volum mitja acumulat fins aquesta hora, basat en els ultims
        HISTORICAL_PERIOD_FOR_AVG_VOLUME dies. Retorna 0.0 si no hi ha dades.
    """
    try:
        hist = yf.download(
            tickers=ticker,
            period=HISTORICAL_PERIOD_FOR_AVG_VOLUME,
            interval=HISTORICAL_INTERVAL_FOR_AVG_VOLUME,
            progress=False,
            auto_adjust=False,
        )
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = [c[0] for c in hist.columns]
        if hist.empty:
            return 0.0

        hist = hist.copy()
        hist["date"] = hist.index.date
        hist["time"] = hist.index.time

        daily_cumsum_at_time = []
        for _, day_df in hist.groupby("date"):
            day_df = day_df[day_df["time"] <= current_time]
            if not day_df.empty:
                daily_cumsum_at_time.append(day_df["Volume"].sum())

        if not daily_cumsum_at_time:
            return 0.0
        return float(sum(daily_cumsum_at_time) / len(daily_cumsum_at_time))
    except Exception:
        # Problema puntual de la font de dades: degradem amb gracia,
        # l'score de volum quedara neutre.
        return 0.0


def get_index_snapshot(market: str = ACTIVE_MARKET) -> IndexSnapshot:
    """Descarrega la variacio % actual de l'index de referencia del mercat actiu.

    Args:
        market: clau de MARKET_INDEX_TICKERS.

    Returns:
        IndexSnapshot amb el ticker de l'index i la seva variacio % avui.
    """
    ticker = MARKET_INDEX_TICKERS[market]
    df = _download_intraday(ticker)
    if df.empty:
        return IndexSnapshot(ticker=ticker, change_pct=0.0)

    open_price = float(df["Open"].iloc[0])
    last_price = float(df["Close"].iloc[-1])
    change_pct = ((last_price - open_price) / open_price) * 100.0 if open_price else 0.0
    return IndexSnapshot(ticker=ticker, change_pct=change_pct)


def get_price_snapshot(display_name: str, ticker: str) -> PriceSnapshot:
    """Descarrega les dades intradia actuals d'una accio.

    Args:
        display_name: nom llegible (p.ex. "INDRA").
        ticker: simbol de yfinance (p.ex. "IDR.MC").

    Returns:
        PriceSnapshot amb preu, volum i barres recents per l'analisi d'energia.
    """
    df = _download_intraday(ticker)
    if df.empty:
        # Mercat probablement tancat o encara sense dades: snapshot neutre.
        return PriceSnapshot(
            ticker=ticker,
            display_name=display_name,
            last_price=0.0,
            open_price=0.0,
            change_pct=0.0,
            current_volume=0.0,
            average_volume_at_this_time=0.0,
        )

    open_price = float(df["Open"].iloc[0])
    last_price = float(df["Close"].iloc[-1])
    change_pct = ((last_price - open_price) / open_price) * 100.0 if open_price else 0.0
    current_volume = float(df["Volume"].sum())

    day_high = float(df["High"].max())
    day_low = float(df["Low"].min())

    # VWAP = suma(preu_tipic * volum) / suma(volum), amb preu_tipic = (H+L+C)/3
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
    total_volume = df["Volume"].sum()
    vwap = float((typical_price * df["Volume"]).sum() / total_volume) if total_volume else last_price

    current_time = df.index[-1].time()
    avg_volume = _historical_average_volume_at_time(ticker, current_time)

    recent = df.tail(ENERGY_LOOKBACK_BARS)
    recent_closes = [float(x) for x in recent["Close"].tolist()]
    recent_volumes = [float(x) for x in recent["Volume"].tolist()]
    recent_highs = [float(x) for x in recent["High"].tolist()]
    recent_lows = [float(x) for x in recent["Low"].tolist()]

    regime_window = df.tail(REGIME_LOOKBACK_BARS)
    regime_closes = [float(x) for x in regime_window["Close"].tolist()]
    regime_highs = [float(x) for x in regime_window["High"].tolist()]
    regime_lows = [float(x) for x in regime_window["Low"].tolist()]

    return PriceSnapshot(
        ticker=ticker,
        display_name=display_name,
        last_price=last_price,
        open_price=open_price,
        change_pct=change_pct,
        current_volume=current_volume,
        average_volume_at_this_time=avg_volume,
        day_high=day_high,
        day_low=day_low,
        vwap=vwap,
        recent_closes=recent_closes,
        recent_volumes=recent_volumes,
        recent_highs=recent_highs,
        recent_lows=recent_lows,
        regime_closes=regime_closes,
        regime_highs=regime_highs,
        regime_lows=regime_lows,
    )


def get_monthly_snapshot(ticker: str, last_price: float) -> MonthlySnapshot:
    """Descarrega el rang de fons (per defecte, ultim mes, barres diaries)
    d'un ticker, per calcular Fibonacci mensual com a dada complementaria.

    A mes del maxim/minim, calcula tambe algunes metriques nomes per
    detectar si el rang pot estar distorsionat per un esdeveniment
    excepcional (veure range_quality.py): quants dies de cotitzacio hi ha
    disponibles, quin es el salt mes gran d'un sol dia, i si aquest salt
    coincideix amb el maxim o el minim actual del rang.

    Args:
        ticker: simbol de yfinance.
        last_price: preu actual ja obtingut de l'intradia (evita una altra
            crida nomes per saber el preu; el rang mensual nomes aporta
            maxim/minim de fons).

    Returns:
        MonthlySnapshot amb monthly_high, monthly_low i last_price. Si no
        hi ha dades disponibles, monthly_high/low queden a 0.0 (Fibonacci
        mensual ho detectara com "SENSE_DADES").
    """
    try:
        hist = yf.download(
            tickers=ticker,
            period=MONTHLY_LOOKBACK_PERIOD,
            interval=MONTHLY_LOOKBACK_INTERVAL,
            progress=False,
            auto_adjust=False,
        )
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = [c[0] for c in hist.columns]
        if hist.empty:
            return MonthlySnapshot(ticker=ticker, monthly_high=0.0, monthly_low=0.0, last_price=last_price)

        monthly_high = float(hist["High"].max())
        monthly_low = float(hist["Low"].min())
        trading_days_available = int(len(hist))

        # Salt mes gran d'un sol dia (variacio % de tancament a tancament).
        daily_returns_pct = hist["Close"].pct_change().dropna() * 100.0
        if daily_returns_pct.empty:
            max_daily_move_pct = 0.0
            high_set_by_extreme_day = False
            low_set_by_extreme_day = False
        else:
            max_move_idx = daily_returns_pct.abs().idxmax()
            max_daily_move_pct = float(abs(daily_returns_pct.loc[max_move_idx]))

            # Comprova si el dia del salt es tambe el dia que marca el
            # maxim o el minim actual del rang mensual.
            extreme_day_high = float(hist.loc[max_move_idx, "High"])
            extreme_day_low = float(hist.loc[max_move_idx, "Low"])
            high_set_by_extreme_day = abs(extreme_day_high - monthly_high) < 1e-6
            low_set_by_extreme_day = abs(extreme_day_low - monthly_low) < 1e-6

        return MonthlySnapshot(
            ticker=ticker,
            monthly_high=monthly_high,
            monthly_low=monthly_low,
            last_price=last_price,
            trading_days_available=trading_days_available,
            max_daily_move_pct=max_daily_move_pct,
            high_set_by_extreme_day=high_set_by_extreme_day,
            low_set_by_extreme_day=low_set_by_extreme_day,
        )
    except Exception:
        # Problema puntual de la font de dades: degradem amb gracia,
        # el Fibonacci mensual sortira com "SENSE_DADES".
        return MonthlySnapshot(ticker=ticker, monthly_high=0.0, monthly_low=0.0, last_price=last_price)


def get_all_price_snapshots(universe: Dict[str, str] = None) -> List[PriceSnapshot]:
    """Descarrega el PriceSnapshot de totes les accions de l'univers.

    Args:
        universe: mapeig nom_visible -> ticker. Per defecte config.STOCK_UNIVERSE.

    Returns:
        Llista de PriceSnapshot, un per accio. Continua encara que una accio falli.
    """
    universe = universe or STOCK_UNIVERSE
    snapshots: List[PriceSnapshot] = []
    for display_name, ticker in universe.items():
        try:
            snapshots.append(get_price_snapshot(display_name, ticker))
        except Exception as exc:
            print(f"[data_loader] Avis: no s'ha pogut carregar {display_name} ({ticker}): {exc}")
    return snapshots
