"""Run a backtest with momentum strategy on downloaded data.

Run from project root:  python scripts/run_backtest.py
Or:  PYTHONPATH=. python scripts/run_backtest.py

Same data + same parameters = same result every time (deterministic). To see
different results: use --download to refresh data, or change --lookback, --size,
--fee-pct, --slippage-pct.

  python scripts/run_backtest.py --download --years 4
  python scripts/run_backtest.py --lookback 50 --size 0.02
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root so `src` resolves
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from decimal import Decimal

from src.data.download import load_bars, download_bars
from src.backtest.engine import run
from src.backtest.recorder import Recorder
from src.portfolio.portfolio import Portfolio
from src.execution.simulated import SimulatedExecution
from src.strategies.momentum import MomentumStrategy
from src.strategies.dual_ma import DualMAStrategy
from src.reporting.metrics import compute_metrics
from src.reporting.plots import plot_equity_and_drawdown, save_equity_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Run backtest on BTC 1h data.")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download data before backtesting (uses --limit).",
    )
    parser.add_argument(
        "--years",
        type=float,
        default=None,
        help="When using --download, number of years of 1h data (overrides --limit).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=26280,
        help="Number of 1h bars to download when using --download (default: 26280). Ignored if --years is set.",
    )
    parser.add_argument(
        "--data-path",
        default="data/BTCUSDT_1h.parquet",
        help="Path to Parquet data file (default: data/BTCUSDT_1h.parquet).",
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=20,
        help="Momentum lookback bars for SMA (default: 20).",
    )
    parser.add_argument(
        "--size",
        type=float,
        default=0.01,
        help="Target BTC position size when long (default: 0.01).",
    )
    parser.add_argument(
        "--fee-pct",
        type=float,
        default=0.001,
        help="Fee as decimal of notional, e.g. 0.001 = 0.1%% (default: 0.001).",
    )
    parser.add_argument(
        "--slippage-pct",
        type=float,
        default=0.0005,
        help="Slippage as decimal, e.g. 0.0005 = 5 bps (default: 0.0005).",
    )
    parser.add_argument(
        "--strategy",
        choices=["momentum", "dual_ma"],
        default="momentum",
        help="Strategy: momentum (price vs SMA) or dual_ma (fast MA vs slow MA) (default: momentum).",
    )
    parser.add_argument(
        "--fast",
        type=int,
        default=10,
        help="Dual MA: fast lookback in bars (default: 10).",
    )
    parser.add_argument(
        "--slow",
        type=int,
        default=30,
        help="Dual MA: slow lookback in bars (default: 30).",
    )
    args = parser.parse_args()

    data_path = args.data_path
    symbol = "BTCUSDT"
    initial_cash = Decimal("100000")
    size = Decimal(str(args.size))
    fee_pct = Decimal(str(args.fee_pct))
    slippage_pct = Decimal(str(args.slippage_pct))

    if args.download:
        path = _project_root / data_path
        limit = int(args.years * 8760) if args.years is not None else args.limit
        print(f"Downloading up to {limit} bars ({limit / 8760:.1f} years) to {path}...")
        download_bars(symbol="BTCUSDT", interval="1h", path=path, limit=limit)
        print("Download done.")

    bars = load_bars(_project_root / data_path)
    print(f"Loaded {len(bars)} bars from {data_path}")

    if args.strategy == "momentum":
        strategy = MomentumStrategy(lookback=args.lookback, size=size)
        print(f"Strategy: momentum (lookback={args.lookback})")
    else:
        strategy = DualMAStrategy(fast_lookback=args.fast, slow_lookback=args.slow, size=size)
        print(f"Strategy: dual_ma (fast={args.fast}, slow={args.slow})")
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
    config = {
        "data_path": data_path,
        "num_bars": len(bars),
        "strategy": args.strategy,
        "size": str(size),
        "fee_pct": str(fee_pct),
        "slippage_pct": str(slippage_pct),
    }
    if args.strategy == "momentum":
        config["lookback"] = args.lookback
    else:
        config["fast"] = args.fast
        config["slow"] = args.slow
    (run_dir / "config.json").write_text(json.dumps(config, indent=2))
    save_equity_csv(recorder, run_dir / "equity.csv")
    plot_equity_and_drawdown(recorder, save_path=run_dir / "equity_drawdown.png", show=False)
    print(f"\nRun saved to: {run_dir}")


if __name__ == "__main__":
    main()
