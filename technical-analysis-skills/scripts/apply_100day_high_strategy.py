#!/usr/bin/env python3
"""100-day high breakout strategy (Donchian Channel entry)."""

import sys
import click
import pandas as pd

# Allow imports from sibling modules
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calculate_indicators import add_donchian_channels


def signal_100day_high(df, dc_period=100):
    """Generate BUY signals when close hits a new 100-day high.

    Args:
        df: DataFrame with 'Close' and 'High' columns.
        dc_period: Donchian Channel lookback period.

    Returns:
        DataFrame with 'DC_High', 'DC_Low', and 'Signal' columns added.
    """
    if "DC_High" not in df.columns:
        df = add_donchian_channels(df, period=dc_period)

    # BUY when today's close reaches or exceeds the Donchian high
    # The DC_High is the rolling max of *High* over the lookback window,
    # so a close >= DC_High means a decisive breakout.
    df["Signal"] = "HOLD"
    mask = df["Close"] >= df["DC_High"]
    df.loc[mask, "Signal"] = "BUY"

    return df


@click.command()
@click.argument("input_csv", type=click.Path(exists=True))
@click.option("--period", default=100, type=int, help="Donchian Channel lookback (default 100).")
@click.option("--output", default=None, help="Save signals to this CSV path.")
def main(input_csv, period, output):
    """Scan INPUT_CSV for 100-day high breakout entries.

    Generates a BUY signal on any day the closing price reaches or exceeds
    the 100-day Donchian Channel high.
    """
    df = pd.read_csv(input_csv, parse_dates=["Date"])
    if "Date" in df.columns:
        df = df.set_index("Date")

    if "Ticker" in df.columns:
        df = df.groupby("Ticker", group_keys=False).apply(
            lambda g: signal_100day_high(g, dc_period=period)
        )
    else:
        df = signal_100day_high(df, dc_period=period)

    buy_count = (df["Signal"] == "BUY").sum()

    if output:
        df.to_csv(output)
        click.secho(f"Saved signals ({buy_count} BUY) to {output}", fg="green")
    else:
        # Show only rows with BUY signals for readability
        buys = df[df["Signal"] == "BUY"]
        if buys.empty:
            click.secho("No BUY signals found.", fg="yellow")
        else:
            click.echo(buys[["Close", "DC_High", "Signal"]].to_string())

    click.secho(f"\n--- 100-Day High Strategy: {buy_count} BUY signal(s) ---", fg="cyan", bold=True)


if __name__ == "__main__":
    main()
