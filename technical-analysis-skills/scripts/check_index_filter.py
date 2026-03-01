#!/usr/bin/env python3
"""Check market regime using index SMA filter (Unholy Grails 75-day SMA rule)."""

import json
import sys
import click
import yfinance as yf
import pandas as pd


def get_index_regime(index_ticker="^GSPC", period=75):
    """Determine bull/bear regime for a market index.

    Args:
        index_ticker: Yahoo Finance ticker for the index (e.g. ^GSPC, ^AXJO).
        period: SMA lookback period in trading days.

    Returns:
        dict with keys: index, close, sma, regime ('BULLISH' or 'BEARISH').
    """
    t = yf.Ticker(index_ticker)
    # Fetch enough history to compute the SMA reliably
    df = t.history(period="1y", auto_adjust=True)

    if df.empty or len(df) < period:
        raise ValueError(
            f"Insufficient data for {index_ticker}: got {len(df)} rows, need >= {period}"
        )

    sma = df["Close"].rolling(window=period, min_periods=period).mean()
    latest_close = float(df["Close"].iloc[-1])
    latest_sma = float(sma.iloc[-1])

    regime = "BULLISH" if latest_close > latest_sma else "BEARISH"

    return {
        "index": index_ticker,
        "date": df.index[-1].strftime("%Y-%m-%d"),
        "close": round(latest_close, 2),
        f"sma_{period}": round(latest_sma, 2),
        "regime": regime,
    }


@click.command()
@click.option("--index", "index_ticker", default="^GSPC",
              help="Index ticker symbol (default: ^GSPC for S&P 500).")
@click.option("--period", default=75, type=int,
              help="SMA lookback period in trading days (default: 75).")
@click.option("--json-output", "json_out", is_flag=True,
              help="Output as raw JSON instead of formatted text.")
def main(index_ticker, period, json_out):
    """Check the market regime filter for INDEX using a PERIOD-day SMA.

    Bullish: Index close > SMA  — allow new long positions.
    Bearish: Index close < SMA  — stop new entries, consider defensive exits.
    """
    try:
        result = get_index_regime(index_ticker, period)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")
        sys.exit(1)

    if json_out:
        click.echo(json.dumps(result, indent=2))
    else:
        color = "green" if result["regime"] == "BULLISH" else "red"
        click.secho(f"--- Market Regime Filter ---", fg="cyan", bold=True)
        click.echo(f"  Index:   {result['index']}")
        click.echo(f"  Date:    {result['date']}")
        click.echo(f"  Close:   {result['close']}")
        click.echo(f"  SMA({period}): {result[f'sma_{period}']}")
        click.secho(f"  Regime:  {result['regime']}", fg=color, bold=True)

        if result["regime"] == "BEARISH":
            click.secho("\n  ⚠  Bearish regime — halt new entries, consider defensive exits.",
                        fg="yellow")
        else:
            click.secho("\n  ✓  Bullish regime — new long entries allowed.",
                        fg="green")


if __name__ == "__main__":
    main()
