"""Compute performance metrics from backtest recorder."""

from typing import Any, Dict, List, Optional, Tuple

from src.backtest.recorder import Recorder


def _equity_series(recorder: Recorder) -> List[float]:
    return [float(s.equity) for s in recorder.states]


def total_return(recorder: Recorder) -> float:
    """Total return (fraction). (final_equity - initial_equity) / initial_equity."""
    states = recorder.states
    if not states or len(states) < 2:
        return 0.0
    initial = float(states[0].equity)
    final = float(states[-1].equity)
    if initial <= 0:
        return 0.0
    return (final - initial) / initial


def max_drawdown(recorder: Recorder) -> Tuple[float, float]:
    """
    Max drawdown in absolute terms and as fraction of peak.
    Returns (max_drawdown_pct, max_drawdown_abs).
    """
    eq = _equity_series(recorder)
    if not eq or len(eq) < 2:
        return 0.0, 0.0
    peak = eq[0]
    max_dd_pct = 0.0
    max_dd_abs = 0.0
    for e in eq:
        if e > peak:
            peak = e
        dd_abs = peak - e
        dd_pct = dd_abs / peak if peak > 0 else 0.0
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct
            max_dd_abs = dd_abs
    return max_dd_pct, max_dd_abs


def sharpe_ratio(
    recorder: Recorder,
    periods_per_year: float = 8760.0,
    risk_free_rate: float = 0.0,
) -> Optional[float]:
    """
    Annualized Sharpe from bar-to-bar returns. Assumes 1h bars -> 8760 periods/year.
    Returns None if not enough data or zero volatility.
    """
    eq = _equity_series(recorder)
    if not eq or len(eq) < 3:
        return None
    returns = []
    for i in range(1, len(eq)):
        if eq[i - 1] > 0:
            r = (eq[i] - eq[i - 1]) / eq[i - 1] - risk_free_rate / periods_per_year
            returns.append(r)
    if not returns:
        return None
    mean_r = sum(returns) / len(returns)
    variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
    std = variance ** 0.5
    if std <= 0:
        return None
    return mean_r / std * (periods_per_year ** 0.5)


def compute_metrics(recorder: Recorder) -> Dict[str, Any]:
    """All metrics as a dict for display or JSON."""
    states = recorder.states
    trades = recorder.trades
    if not states:
        return {
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "max_drawdown_abs": 0.0,
            "num_trades": 0,
            "sharpe_ratio": None,
            "initial_equity": 0.0,
            "final_equity": 0.0,
            "num_bars": 0,
        }
    initial = float(states[0].equity)
    final = float(states[-1].equity)
    dd_pct, dd_abs = max_drawdown(recorder)
    return {
        "total_return_pct": total_return(recorder) * 100,
        "max_drawdown_pct": dd_pct * 100,
        "max_drawdown_abs": dd_abs,
        "num_trades": len(trades),
        "sharpe_ratio": sharpe_ratio(recorder),
        "initial_equity": initial,
        "final_equity": final,
        "num_bars": len(states),
    }
