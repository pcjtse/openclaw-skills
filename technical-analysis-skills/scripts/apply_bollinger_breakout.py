#!/usr/bin/env python3
"""Bollinger Band breakout strategy — buy when close > upper band."""

import sys
import click
import pandas as pd

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calculate_indicators import add_bollinger_bands


def signal_bollinger_breakout(df, period=100, num_std=2):
    """Generate BUY signals on Bollinger Band upper breakout.

    Args:
        df: DataFrame with a 'Close' column.
        period: Bollinger Band lookback period.
        num_std: Number of standard deviations for the bands.

    Returns:
        DataFrame with Bollinger columns and 'Signal' column added.
    """
    if "BB_Upper" not in df.columns:
        df = add_bollinger_bands(df, period=period, num_std=num_std)

    df["Signal"] = "HOLD"
    mask = df["Close"] > df["BB_Upper"]
    df.loc[mask, "Signal"] = "BUY"

    return df


@click.command()
@click.argument("input_csv", type=click.Path(exists=True))
@click.option("--period", default=100, type=int, help="Bollinger Band lookback (default 100).")
@click.option("--std", "num_std", default=2.0, type=float, help="Std dev multiplier (default 2).")
@click.option("--output", default=None, help="Save signals to this CSV path.")
def main(input_csv, period, num_std, output):
    """Scan INPUT_CSV for Bollinger Band breakout entries.

    Generates a BUY signal when the closing price exceeds the upper
    Bollinger Band (100-day, 2 standard deviations by default).
    """
    df = pd.read_csv(input_csv, parse_dates=["Date"])
    if "Date" in df.columns:
        df = df.set_index("Date")

    if "Ticker" in df.columns:
        df = df.groupby("Ticker", group_keys=False).apply(
            lambda g: signal_bollinger_breakout(g, period=period, num_std=num_std)
        )
    else:
        df = signal_bollinger_breakout(df, period=period, num_std=num_std)

    buy_count = (df["Signal"] == "BUY").sum()

    if output:
        df.to_csv(output)
        click.secho(f"Saved signals ({buy_count} BUY) to {output}", fg="green")
    else:
        buys = df[df["Signal"] == "BUY"]
        if buys.empty:
            click.secho("No BUY signals found.", fg="yellow")
        else:
            click.echo(buys[["Close", "BB_Upper", "Signal"]].to_string())

    click.secho(f"\n--- Bollinger Breakout: {buy_count} BUY signal(s) ---", fg="cyan", bold=True)


if __name__ == "__main__":
    main()
