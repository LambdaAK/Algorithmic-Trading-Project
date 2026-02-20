"""Load bars from Parquet and download OHLCV from exchange."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Union

from src.core.types import Bar

try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore


def load_bars_df(path: Union[str, Path]):
    """
    Load Parquet file and return all bars as a pandas DataFrame.
    Columns: timestamp, open, high, low, close, volume. Sorted ascending by timestamp.
    """
    if pd is None:
        raise ImportError("pandas is required. Install with: pip install pandas pyarrow")
    df = pd.read_parquet(path)
    return df.sort_values("timestamp").reset_index(drop=True)


def load_bars(path: Union[str, Path]) -> list[Bar]:
    """
    Load Parquet file and return all bars as a list of Bar.
    No limit — every row in the file is returned. Sorted ascending by timestamp.
    """
    if pd is None:
        raise ImportError("pandas is required for load_bars. Install with: pip install pandas pyarrow")

    df = load_bars_df(path)

    bars: list[Bar] = []
    for _, row in df.iterrows():
        ts = row["timestamp"]
        if isinstance(ts, (int, float)):
            ts = datetime.utcfromtimestamp(int(ts) / 1000)
        elif hasattr(ts, "to_pydatetime"):
            ts = ts.to_pydatetime()
        bars.append(
            Bar(
                timestamp=ts,
                open=_to_decimal(row["open"]),
                high=_to_decimal(row["high"]),
                low=_to_decimal(row["low"]),
                close=_to_decimal(row["close"]),
                volume=_to_decimal(row["volume"]),
            )
        )
    return bars


def _to_decimal(x: Any) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def download_bars(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    path: Union[str, Path] = "data/BTCUSDT_1h.parquet",
    limit: int = 8760,
    base_url: str = "https://api.binance.com",
) -> Path:
    """
    Download klines and save as Parquet. Uses Binance by default.
    Fetches in chunks of 1000 when limit > 1000 (e.g. 8760 = 1 year of 1h bars).
    If you get HTTP 451 (region block), try base_url="https://api.binance.us" or install
    yfinance for fallback (fallback has limited history).
    interval: e.g. "1h", "1d". limit: max number of candles.
    """
    try:
        import requests
    except ImportError:
        raise ImportError("requests is required for download_bars. Install with: pip install requests")

    if pd is None:
        raise ImportError("pandas is required for download_bars. Install with: pip install pandas pyarrow")

    url = base_url.rstrip("/") + "/api/v3/klines"
    chunk_size = 1000  # Binance max per request
    try:
        all_raw = []
        end_time = None
        while len(all_raw) < limit:
            params = {"symbol": symbol, "interval": interval, "limit": chunk_size}
            if end_time is not None:
                params["endTime"] = end_time
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            raw = resp.json()
            if not raw:
                break
            # Binance returns oldest first; we're fetching backwards so prepend (new chunk is older)
            all_raw = raw + all_raw
            if len(raw) < chunk_size:
                break
            # Next request: get bars before the oldest we have
            end_time = raw[0][0] - 1
        # Keep only the most recent `limit` bars
        all_raw = all_raw[-limit:]
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 451:
            return _download_via_yfinance(path=path, limit=limit, symbol=symbol, interval=interval)
        raise
    except requests.exceptions.RequestException:
        return _download_via_yfinance(path=path, limit=limit, symbol=symbol, interval=interval)

    # Binance: [open_time, open, high, low, close, volume, close_time, ...]
    df = pd.DataFrame(
        all_raw,
        columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore",
        ],
    )
    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    for col in "open", "high", "low", "close", "volume":
        df[col] = df[col].astype(float)
    out = df[["timestamp", "open", "high", "low", "close", "volume"]]
    out = out.sort_values("timestamp").reset_index(drop=True)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(path, index=False)
    return path


def _download_via_yfinance(
    path: Union[str, Path],
    limit: int,
    symbol: str,
    interval: str,
) -> Path:
    """Fallback when Binance is blocked (e.g. 451). Uses Yahoo Finance. BTCUSDT -> BTC-USD."""
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError(
            "Binance returned 451 (region block). Install yfinance for fallback: pip install yfinance"
        ) from None

    yf_symbol = "BTC-USD" if symbol == "BTCUSDT" else symbol.replace("USDT", "-USD")
    period = "60d" if interval == "1h" else "730d"
    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(period=period, interval=interval, auto_adjust=True)
    if df.empty or len(df) < 2:
        df = ticker.history(period="60d", interval="1d", auto_adjust=True)
        df = df.reset_index()
        df.columns = [str(c).lower() for c in df.columns]
    else:
        df = df.reset_index()
        df.columns = [str(c).lower() for c in df.columns]
    if "date" in df.columns:
        df = df.rename(columns={"date": "timestamp"})
    elif "datetime" in df.columns:
        df = df.rename(columns={"datetime": "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    out = df[["timestamp", "open", "high", "low", "close", "volume"]].dropna()
    out = out.sort_values("timestamp").tail(limit).reset_index(drop=True)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(path, index=False)
    return path
