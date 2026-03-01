#!/usr/bin/env python3
"""Generate performance metrics: CAGR, Max Drawdown, MAR Ratio, and Underwater Equity Curve."""

import sys
import json
import click
import pandas as pd
import numpy as np


def compute_metrics(equity_series):
    """Compute key performance metrics from a time-indexed equity series.

    Args:
        equity_series: pd.Series with a DatetimeIndex and equity values.

    Returns:
        dict with CAGR, max_drawdown, mar_ratio, and drawdown Series.
    """
    if equity_series.empty or len(equity_series) < 2:
        raise ValueError("Equity series must have at least 2 data points.")

    start_val = equity_series.iloc[0]
    end_val = equity_series.iloc[-1]
    start_date = equity_series.index[0]
    end_date = equity_series.index[-1]

    # Years between first and last date
    years = (end_date - start_date).days / 365.25
    if years <= 0:
        raise ValueError("Equity series must span more than 0 days.")

    # CAGR
    cagr = (end_val / start_val) ** (1 / years) - 1

    # Max Drawdown & Underwater Curve
    cumulative_max = equity_series.cummax()
    drawdown = (equity_series - cumulative_max) / cumulative_max
    max_drawdown = drawdown.min()  # most negative value

    # MAR Ratio (CAGR / |Max Drawdown|)
    mar_ratio = cagr / abs(max_drawdown) if max_drawdown != 0 else float("inf")

    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "years": round(years, 2),
        "start_equity": round(start_val, 2),
        "end_equity": round(end_val, 2),
        "cagr": round(cagr * 100, 4),  # percentage
        "max_drawdown": round(max_drawdown * 100, 4),  # percentage (negative)
        "mar_ratio": round(mar_ratio, 4),
        "drawdown_series": drawdown,
    }


@click.command()
@click.option("--equity-csv", required=True, type=click.Path(exists=True),
              help="CSV with Date and Equity columns.")
@click.option("--output", default=None, help="Save underwater curve to this CSV path.")
@click.option("--json-output", "json_out", is_flag=True, help="Output metrics as JSON.")
def main(equity_csv, output, json_out):
    """Compute performance metrics and generate the Underwater Equity Curve.

    The equity CSV must have a 'Date' column and an 'Equity' column representing
    the portfolio's total value over time.
    """
    df = pd.read_csv(equity_csv, parse_dates=["Date"])
    if "Equity" not in df.columns:
        click.secho("Error: CSV must have an 'Equity' column.", fg="red")
        sys.exit(1)

    df = df.set_index("Date").sort_index()
    equity = df["Equity"]

    try:
        metrics = compute_metrics(equity)
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        sys.exit(1)

    drawdown = metrics.pop("drawdown_series")

    if json_out:
        click.echo(json.dumps(metrics, indent=2))
    else:
        click.secho("--- Performance Metrics ---", fg="cyan", bold=True)
        click.echo(f"  Period:        {metrics['start_date']} to {metrics['end_date']} ({metrics['years']} yrs)")
        click.echo(f"  Start Equity:  ${metrics['start_equity']:,.2f}")
        click.echo(f"  End Equity:    ${metrics['end_equity']:,.2f}")
        click.echo(f"  CAGR:          {metrics['cagr']:.2f}%")
        click.echo(f"  Max Drawdown:  {metrics['max_drawdown']:.2f}%")
        click.secho(f"  MAR Ratio:     {metrics['mar_ratio']:.2f}", fg="green" if metrics["mar_ratio"] > 0.5 else "red", bold=True)

    if output:
        underwater = pd.DataFrame({"Date": drawdown.index, "Drawdown_Pct": drawdown.values})
        underwater.to_csv(output, index=False)
        click.secho(f"Saved underwater equity curve to {output}", fg="green")


if __name__ == "__main__":
    main()
