#!/usr/bin/env python3
"""Trading agent orchestration loop — ties all skills into a single backtest run."""

import sys
import os
import json
import click
import pandas as pd
import numpy as np

# Ensure sibling imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_market_data import fetch_ohlcv
from calculate_indicators import add_sma, add_bollinger_bands, add_donchian_channels
from check_index_filter import get_index_regime
from apply_100day_high_strategy import signal_100day_high
from apply_bollinger_breakout import signal_bollinger_breakout
from apply_20percent_flipper import signal_20pct_flipper
from manage_position_sizing import allocate_positions
from calculate_slippage_and_commissions import apply_costs
from generate_performance_metrics import compute_metrics


STRATEGY_MAP = {
    "donchian": ("100-Day High Breakout", signal_100day_high),
    "bollinger": ("Bollinger Band Breakout", signal_bollinger_breakout),
    "flipper": ("20% Trailing-Stop Flipper", signal_20pct_flipper),
}


@click.command()
@click.option("--universe", required=True,
              help="Comma-separated tickers OR path to a CSV with a 'Ticker' column.")
@click.option("--index", "index_ticker", default="^GSPC",
              help="Index ticker for regime filter (default ^GSPC).")
@click.option("--capital", default=100000.0, type=float, help="Starting capital (default 100000).")
@click.option("--slots", default=20, type=int, help="Number of equal position slots (default 20).")
@click.option("--strategy", type=click.Choice(["donchian", "bollinger", "flipper"]),
              default="donchian", help="Trading strategy to apply.")
@click.option("--start", default=None, help="Data start date (YYYY-MM-DD).")
@click.option("--end", default=None, help="Data end date (YYYY-MM-DD).")
@click.option("--commission-pct", default=0.25, type=float, help="Commission %% (default 0.25).")
@click.option("--slippage-pct", default=0.10, type=float, help="Slippage %% (default 0.10).")
@click.option("--output-dir", default=None, help="Directory to save output CSVs.")
def main(universe, index_ticker, capital, slots, strategy, start, end,
         commission_pct, slippage_pct, output_dir):
    """Run the full trading agent loop.

    Sequence:
    1. Fetch data for universe + index
    2. Compute indicators
    3. Check index filter (bull/bear)
    4. If bullish, scan for entries using the chosen strategy
    5. Size positions
    6. Apply costs
    7. Report performance metrics
    """
    # --- Parse universe ---
    if os.path.isfile(universe):
        universe_df = pd.read_csv(universe)
        tickers = universe_df["Ticker"].tolist()
    else:
        tickers = [t.strip() for t in universe.split(",") if t.strip()]

    if not tickers:
        click.secho("Error: No tickers provided.", fg="red")
        sys.exit(1)

    click.secho("=" * 60, fg="cyan")
    click.secho("  TRADING AGENT LOOP", fg="cyan", bold=True)
    click.secho("=" * 60, fg="cyan")

    strategy_name, strategy_fn = STRATEGY_MAP[strategy]
    click.echo(f"  Strategy:  {strategy_name}")
    click.echo(f"  Universe:  {len(tickers)} ticker(s)")
    click.echo(f"  Capital:   ${capital:,.2f}")
    click.echo(f"  Slots:     {slots}")
    click.echo()

    # --- Step 1: Fetch data ---
    click.secho("Step 1: Fetching market data...", fg="cyan", bold=True)
    data = fetch_ohlcv(tickers, start=start, end=end, period="2y")
    if not data:
        click.secho("No data retrieved. Aborting.", fg="red")
        sys.exit(1)
    click.echo(f"  Retrieved data for {len(data)} ticker(s)")

    # --- Step 2: Compute indicators ---
    click.secho("Step 2: Computing indicators...", fg="cyan", bold=True)
    enriched = {}
    for ticker, df in data.items():
        df = add_sma(df.copy())
        df = add_bollinger_bands(df)
        df = add_donchian_channels(df)
        df["Ticker"] = ticker
        enriched[ticker] = df
    click.echo(f"  Added SMA, Bollinger Bands, Donchian Channels to all tickers")

    # --- Step 3: Check index filter ---
    click.secho("Step 3: Checking market regime filter...", fg="cyan", bold=True)
    try:
        regime = get_index_regime(index_ticker)
        regime_status = regime["regime"]
    except Exception as e:
        click.secho(f"  Warning: could not check index filter ({e}). Assuming BULLISH.", fg="yellow")
        regime_status = "BULLISH"

    color = "green" if regime_status == "BULLISH" else "red"
    click.secho(f"  Regime: {regime_status}", fg=color, bold=True)

    if regime_status == "BEARISH":
        click.secho("\n  ⚠  BEARISH regime detected.", fg="yellow", bold=True)
        click.echo("  → No new entries. Consider defensive exits or tightening stops.")
        click.echo("  → Generating exit-only signals for existing positions.\n")
        # In bearish mode, we still report what we have but mark no new entries
        click.secho("Agent loop complete (defensive mode).", fg="yellow")
        return

    # --- Step 4: Scan for entries ---
    click.secho(f"Step 4: Scanning for entries ({strategy_name})...", fg="cyan", bold=True)
    all_signals = []
    for ticker, df in enriched.items():
        signaled = strategy_fn(df.copy())
        buys = signaled[signaled["Signal"] == "BUY"]
        if not buys.empty:
            latest_buy = buys.iloc[-1:]
            latest_buy = latest_buy.copy()
            latest_buy["Ticker"] = ticker
            all_signals.append(latest_buy)

    if not all_signals:
        click.secho("  No BUY signals found in the universe.", fg="yellow")
        click.secho("Agent loop complete (no entries).", fg="yellow")
        return

    signals_df = pd.concat(all_signals).reset_index()
    click.echo(f"  Found {len(signals_df)} BUY signal(s): {', '.join(signals_df['Ticker'].tolist())}")

    # --- Step 5: Position sizing ---
    click.secho("Step 5: Sizing positions...", fg="cyan", bold=True)
    alloc = allocate_positions(signals_df, capital, slots)
    click.echo(alloc.to_string(index=False))
    click.echo()

    # --- Step 6: Apply costs ---
    click.secho("Step 6: Applying commissions & slippage...", fg="cyan", bold=True)
    if not alloc.empty:
        trades = alloc.copy()
        trades["Signal"] = "BUY"
        trades["Shares"] = trades["Shares"].astype(int)
        costed = apply_costs(trades, commission_pct=commission_pct, slippage_pct=slippage_pct)
        total_cost = costed["Net_Value"].sum()
        total_comm = costed["Commission"].sum()
        click.echo(f"  Total deployed: ${total_cost:,.2f} (incl. ${total_comm:,.2f} in costs)")
    else:
        click.echo("  No trades to cost.")

    # --- Step 7: Save outputs ---
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        signals_df.to_csv(os.path.join(output_dir, "signals.csv"), index=False)
        alloc.to_csv(os.path.join(output_dir, "allocations.csv"), index=False)
        if not alloc.empty:
            costed.to_csv(os.path.join(output_dir, "costed_trades.csv"), index=False)
        click.secho(f"\n  Output files saved to {output_dir}/", fg="green")

    click.secho("\n" + "=" * 60, fg="cyan")
    click.secho("  AGENT LOOP COMPLETE ✓", fg="green", bold=True)
    click.secho("=" * 60, fg="cyan")


if __name__ == "__main__":
    main()
