"""Run a backtest with momentum strategy on downloaded data.

Run from project root:  python scripts/run_backtest.py
Or:  PYTHONPATH=. python scripts/run_backtest.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root so `src` resolves
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from decimal import Decimal

from src.data.download import load_bars
from src.backtest.engine import run
from src.backtest.recorder import Recorder
from src.portfolio.portfolio import Portfolio
from src.execution.simulated import SimulatedExecution
from src.strategies.momentum import MomentumStrategy
from src.reporting.metrics import compute_metrics
from src.reporting.plots import plot_equity_and_drawdown, save_equity_csv


def main() -> None:
    data_path = "data/BTCUSDT_1h.parquet"
    symbol = "BTCUSDT"
    initial_cash = Decimal("100000")
    lookback = 20
    size = Decimal("0.01")  # 0.01 BTC when long
    fee_pct = Decimal("0.001")   # 0.1%
    slippage_pct = Decimal("0.0005")  # 5 bps

    bars = load_bars(data_path)
    print(f"Loaded {len(bars)} bars from {data_path}")

    strategy = MomentumStrategy(lookback=lookback, size=size)
    portfolio = Portfolio(initial_cash=initial_cash)
    execution = SimulatedExecution(fee_pct=fee_pct, slippage_pct=slippage_pct)
    recorder = Recorder()

    run(strategy=strategy, portfolio=portfolio, execution=execution, recorder=recorder, bars=bars, symbol=symbol)

    if not recorder.states:
        print("No state recorded.")
        return

    # Metrics
    metrics = compute_metrics(recorder)
    print("\n--- Backtest result ---")
    print(f"Initial equity:  {metrics['initial_equity']:,.2f}")
    print(f"Final equity:   {metrics['final_equity']:,.2f}")
    print(f"Total return:    {metrics['total_return_pct']:.2f}%")
    print(f"Max drawdown:   {metrics['max_drawdown_pct']:.2f}%")
    print(f"Num trades:     {metrics['num_trades']}")
    sharpe = metrics["sharpe_ratio"]
    print(f"Sharpe (ann.):  {sharpe:.2f}" if sharpe is not None else "Sharpe (ann.):  N/A")

    # Save run to runs/<timestamp>/
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = _project_root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    save_equity_csv(recorder, run_dir / "equity.csv")
    plot_equity_and_drawdown(recorder, save_path=run_dir / "equity_drawdown.png", show=False)
    print(f"\nRun saved to: {run_dir}")


if __name__ == "__main__":
    main()
