#!/usr/bin/env python3
"""Fetch OHLCV market data for one or more tickers using yfinance."""

import sys
import click
import yfinance as yf
import pandas as pd


def fetch_ohlcv(tickers, start=None, end=None, period="1y"):
    """Download OHLCV data for a list of tickers.

    Args:
        tickers: List of ticker symbols.
        start: Start date string (YYYY-MM-DD). Overrides period if set.
        end: End date string (YYYY-MM-DD).
        period: yfinance period string (e.g. '1y', '5y'). Used when start is None.

    Returns:
        dict[str, pd.DataFrame]: Mapping of ticker -> OHLCV DataFrame.
    """
    results = {}
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            if start:
                df = t.history(start=start, end=end, auto_adjust=True)
            else:
                df = t.history(period=period, auto_adjust=True)

            if df.empty:
                click.secho(f"Warning: No data returned for {ticker}", fg="yellow", err=True)
                continue

            # Keep only OHLCV columns and add a Ticker column
            df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
            df["Ticker"] = ticker.upper()
            df.index.name = "Date"
            results[ticker.upper()] = df
        except Exception as e:
            click.secho(f"Error fetching {ticker}: {e}", fg="red", err=True)

    return results


@click.command()
@click.argument("tickers")
@click.option("--start", default=None, help="Start date (YYYY-MM-DD). Overrides --period.")
@click.option("--end", default=None, help="End date (YYYY-MM-DD).")
@click.option("--period", default="1y", help="Lookback period if --start is not set (e.g. 1y, 5y).")
@click.option("--output", default=None, help="Save combined data to this CSV path.")
def main(tickers, start, end, period, output):
    """Fetch OHLCV data for TICKERS (comma-separated, e.g. SPY,AAPL,MSFT).

    Note on survivorship bias: yfinance only serves currently-listed symbols.
    For delisted stocks, supply pre-downloaded CSV data to downstream scripts.
    """
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        click.secho("Error: No tickers provided.", fg="red")
        sys.exit(1)

    click.secho(f"Fetching data for {len(ticker_list)} ticker(s)...", fg="cyan")
    data = fetch_ohlcv(ticker_list, start=start, end=end, period=period)

    if not data:
        click.secho("No data retrieved for any ticker.", fg="red")
        sys.exit(1)

    combined = pd.concat(data.values())

    if output:
        combined.to_csv(output)
        click.secho(f"Saved {len(combined)} rows to {output}", fg="green")
    else:
        click.echo(combined.to_string())

    # Summary
    click.secho(f"\n--- Summary ---", fg="cyan", bold=True)
    for ticker, df in data.items():
        click.echo(f"  {ticker}: {len(df)} rows, "
                    f"{df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    main()
