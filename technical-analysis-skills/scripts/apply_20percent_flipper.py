#!/usr/bin/env python3
"""20% trailing-stop flipper strategy — trend-following with capital protection."""

import sys
import click
import pandas as pd
import numpy as np

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calculate_indicators import add_donchian_channels


def signal_20pct_flipper(df, stop_pct=20.0, entry_period=100):
    """Generate BUY / SELL / HOLD signals using a trailing-stop flipper.

    Entry: Momentum trigger when close hits a new *entry_period*-day high.
    Exit:  A trailing stop at *stop_pct*% below the peak close since entry.

    The strategy "flips" between IN and OUT states:
      - OUT → BUY when a new 100-day high is made
      - IN  → SELL when the close drops stop_pct% from the peak since entry
      - IN  → HOLD otherwise (ride the trend)

    Args:
        df: DataFrame with 'Close' and 'High' columns (sorted by date ascending).
        stop_pct: Trailing stop percentage (default 20).
        entry_period: Lookback for the Donchian high entry trigger.

    Returns:
        DataFrame with 'Signal', 'Peak', and 'Trail_Stop' columns added.
    """
    if "DC_High" not in df.columns:
        df = add_donchian_channels(df, period=entry_period)

    stop_frac = stop_pct / 100.0
    signals = []
    peaks = []
    trail_stops = []

    in_position = False
    peak_price = 0.0

    for i in range(len(df)):
        close = df["Close"].iloc[i]
        dc_high = df["DC_High"].iloc[i]

        if pd.isna(dc_high):
            signals.append("HOLD")
            peaks.append(np.nan)
            trail_stops.append(np.nan)
            continue

        if not in_position:
            # Check for entry: close hits a new Donchian high
            if close >= dc_high:
                in_position = True
                peak_price = close
                signals.append("BUY")
                peaks.append(peak_price)
                trail_stops.append(peak_price * (1 - stop_frac))
            else:
                signals.append("HOLD")
                peaks.append(np.nan)
                trail_stops.append(np.nan)
        else:
            # Update peak
            if close > peak_price:
                peak_price = close
            trail_stop = peak_price * (1 - stop_frac)

            if close <= trail_stop:
                # Trailing stop hit — exit
                in_position = False
                signals.append("SELL")
                peaks.append(peak_price)
                trail_stops.append(trail_stop)
                peak_price = 0.0
            else:
                signals.append("HOLD")
                peaks.append(peak_price)
                trail_stops.append(trail_stop)

    df["Signal"] = signals
    df["Peak"] = peaks
    df["Trail_Stop"] = trail_stops

    return df


@click.command()
@click.argument("input_csv", type=click.Path(exists=True))
@click.option("--stop-pct", default=20.0, type=float,
              help="Trailing stop percentage (default 20).")
@click.option("--entry-period", default=100, type=int,
              help="Donchian lookback for entry trigger (default 100).")
@click.option("--output", default=None, help="Save signals to this CSV path.")
def main(input_csv, stop_pct, entry_period, output):
    """Run the 20% trailing-stop flipper strategy on INPUT_CSV.

    Entry: close hits a new ENTRY_PERIOD-day high (Donchian breakout).
    Exit:  close drops STOP_PCT% from the peak since entry.
    """
    df = pd.read_csv(input_csv, parse_dates=["Date"])
    if "Date" in df.columns:
        df = df.set_index("Date")

    if "Ticker" in df.columns:
        df = df.groupby("Ticker", group_keys=False).apply(
            lambda g: signal_20pct_flipper(g.copy(), stop_pct=stop_pct, entry_period=entry_period)
        )
    else:
        df = signal_20pct_flipper(df, stop_pct=stop_pct, entry_period=entry_period)

    buy_count = (df["Signal"] == "BUY").sum()
    sell_count = (df["Signal"] == "SELL").sum()

    if output:
        df.to_csv(output)
        click.secho(f"Saved signals ({buy_count} BUY, {sell_count} SELL) to {output}", fg="green")
    else:
        active = df[df["Signal"].isin(["BUY", "SELL"])]
        if active.empty:
            click.secho("No BUY or SELL signals found.", fg="yellow")
        else:
            click.echo(active[["Close", "Peak", "Trail_Stop", "Signal"]].to_string())

    click.secho(
        f"\n--- 20% Flipper: {buy_count} BUY, {sell_count} SELL signal(s) ---",
        fg="cyan", bold=True,
    )


if __name__ == "__main__":
    main()
