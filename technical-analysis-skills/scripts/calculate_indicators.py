#!/usr/bin/env python3
"""Calculate technical indicators: SMA, Bollinger Bands, and Donchian Channels."""

import sys
import click
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Indicator computation functions (importable by other scripts)
# ---------------------------------------------------------------------------

def add_sma(df, periods=None):
    """Add Simple Moving Average columns to a DataFrame.

    Args:
        df: DataFrame with a 'Close' column.
        periods: List of SMA periods. Defaults to [50, 75, 200].

    Returns:
        DataFrame with SMA_<n> columns added.
    """
    if periods is None:
        periods = [50, 75, 200]
    for p in periods:
        df[f"SMA_{p}"] = df["Close"].rolling(window=p, min_periods=p).mean()
    return df


def add_bollinger_bands(df, period=100, num_std=2):
    """Add Bollinger Band columns to a DataFrame.

    Args:
        df: DataFrame with a 'Close' column.
        period: Lookback window for the central moving average.
        num_std: Number of standard deviations for the bands.

    Returns:
        DataFrame with BB_Mid, BB_Upper, BB_Lower columns added.
    """
    df["BB_Mid"] = df["Close"].rolling(window=period, min_periods=period).mean()
    rolling_std = df["Close"].rolling(window=period, min_periods=period).std()
    df["BB_Upper"] = df["BB_Mid"] + (num_std * rolling_std)
    df["BB_Lower"] = df["BB_Mid"] - (num_std * rolling_std)
    return df


def add_donchian_channels(df, period=100):
    """Add Donchian Channel columns to a DataFrame.

    Args:
        df: DataFrame with 'High' and 'Low' columns.
        period: Lookback window.

    Returns:
        DataFrame with DC_High and DC_Low columns added.
    """
    df["DC_High"] = df["High"].rolling(window=period, min_periods=period).max()
    df["DC_Low"] = df["Low"].rolling(window=period, min_periods=period).min()
    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

INDICATOR_MAP = {
    "sma": add_sma,
    "bollinger": add_bollinger_bands,
    "donchian": add_donchian_channels,
}


@click.command()
@click.argument("input_csv", type=click.Path(exists=True))
@click.option(
    "--indicators",
    default="sma,bollinger,donchian",
    help="Comma-separated list of indicators to compute (sma, bollinger, donchian).",
)
@click.option("--output", default=None, help="Save enriched data to this CSV path.")
def main(input_csv, indicators, output):
    """Read OHLCV data from INPUT_CSV and compute technical indicators.

    The input CSV must have columns: Date (or index), Open, High, Low, Close, Volume.
    If multiple tickers are present, include a 'Ticker' column and each will be
    processed independently.
    """
    df = pd.read_csv(input_csv, parse_dates=["Date"])
    if "Date" in df.columns:
        df = df.set_index("Date")

    chosen = [i.strip().lower() for i in indicators.split(",") if i.strip()]
    invalid = [i for i in chosen if i not in INDICATOR_MAP]
    if invalid:
        click.secho(f"Unknown indicators: {', '.join(invalid)}", fg="red")
        click.echo(f"Available: {', '.join(INDICATOR_MAP.keys())}")
        sys.exit(1)

    def _apply(group):
        for ind in chosen:
            group = INDICATOR_MAP[ind](group)
        return group

    if "Ticker" in df.columns:
        df = df.groupby("Ticker", group_keys=False).apply(_apply)
    else:
        for ind in chosen:
            df = INDICATOR_MAP[ind](df)

    if output:
        df.to_csv(output)
        click.secho(f"Saved enriched data ({len(df)} rows) to {output}", fg="green")
    else:
        click.echo(df.to_string())

    # Summary
    new_cols = [c for c in df.columns if c.startswith(("SMA_", "BB_", "DC_"))]
    click.secho(f"\n--- Indicators added: {', '.join(new_cols)} ---", fg="cyan", bold=True)


if __name__ == "__main__":
    main()
