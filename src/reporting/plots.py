"""Plot equity curve and drawdown from backtest recorder."""

from pathlib import Path
from typing import List, Optional, Tuple, Union

from src.backtest.recorder import Recorder


def _equity_and_drawdown(recorder: Recorder) -> Tuple[List[Optional[object]], List[float], List[float]]:
    """Return (timestamps, equity, drawdown_pct) for plotting."""
    states = recorder.states
    if not states:
        return [], [], []
    timestamps = [s.timestamp for s in states]
    equity = [float(s.equity) for s in states]
    peak = equity[0]
    drawdown_pct = []
    for e in equity:
        if e > peak:
            peak = e
        dd = (peak - e) / peak * 100 if peak > 0 else 0.0
        drawdown_pct.append(dd)
    return timestamps, equity, drawdown_pct


def plot_equity_and_drawdown(
    recorder: Recorder,
    save_path: Optional[Union[str, Path]] = None,
    show: bool = True,
) -> None:
    """
    Plot equity curve and drawdown in two subplots. Optionally save to file.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        raise ImportError("matplotlib is required for plots. Install with: pip install matplotlib")

    ts, equity, dd = _equity_and_drawdown(recorder)
    if not ts or not equity:
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 6))
    ax1.plot(ts, equity, color="steelblue", linewidth=1)
    ax1.set_ylabel("Equity")
    ax1.set_title("Equity curve")
    ax1.grid(True, alpha=0.3)

    ax2.fill_between(ts, 0, dd, color="coral", alpha=0.6)
    ax2.set_ylabel("Drawdown (%)")
    ax2.set_xlabel("Time")
    ax2.set_title("Drawdown")
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.xticks(rotation=45)
    fig.tight_layout()

    if save_path is not None:
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def save_equity_csv(recorder: Recorder, path: Union[str, Path]) -> None:
    """Write equity curve to CSV: timestamp, equity."""
    try:
        import csv
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "equity"])
            for s in recorder.states:
                w.writerow([s.timestamp, float(s.equity)])
    except Exception:
        raise
