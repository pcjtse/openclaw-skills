#!/usr/bin/env python3
import yfinance as yf
import click
import json

@click.command()
@click.argument('ticker')
@click.option('--info/--no-info', default=True, help='Display general company information')
@click.option('--news/--no-news', default=True, help='Display recent news')
@click.option('--analysts/--no-analysts', default=True, help='Display analyst recommendations')
def main(ticker, info, news, analysts):
    """
    Fetch financial data, news, and analyst recommendations for a given TICKER using yfinance.
    Example: python stock_data.py AAPL
    """
    try:
        stock = yf.Ticker(ticker)
        
        if info:
            click.secho(f"--- Information for {ticker.upper()} ---", fg="cyan", bold=True)
            stock_info = stock.info
            # Filter for some key metrics to avoid overwhelming output
            keys_to_print = ['longName', 'sector', 'industry', 'marketCap', 'trailingPE', 'forwardPE', 'dividendYield']
            filtered_info = {k: stock_info.get(k, 'N/A') for k in keys_to_print}
            for k, v in filtered_info.items():
                click.echo(f"{k}: {v}")
            click.echo("\n")

        if news:
            click.secho(f"--- Recent News for {ticker.upper()} ---", fg="cyan", bold=True)
            recent_news = stock.news
            if recent_news:
                for item in recent_news[:5]: # Show top 5
                    content = item.get('content', {})
                    if not content:
                        continue
                    
                    title = content.get('title', 'No Title')
                    provider = content.get('provider', {}).get('displayName', 'Unknown Publisher')
                    
                    canonical_url = content.get('canonicalUrl', {}).get('url', '')
                    click_through = content.get('clickThroughUrl', {})
                    if isinstance(click_through, dict):
                        link = canonical_url if canonical_url else click_through.get('url', 'No Link')
                    else:
                        link = canonical_url if canonical_url else 'No Link'
                    
                    click.echo(f"Title: {title}")
                    click.echo(f"Publisher: {provider}")
                    click.echo(f"Link: {link}")
                    click.echo("-" * 40)
            else:
                click.echo("No recent news found.")
            click.echo("\n")

        if analysts:
            click.secho(f"--- Analyst Recommendations for {ticker.upper()} ---", fg="cyan", bold=True)
            recs = stock.recommendations
            if recs is not None and not recs.empty:
                # Print the most recent recommendations
                click.echo(recs.tail(5).to_string())
            else:
                click.echo("No analyst recommendations found.")
                
            click.echo("\nUpgrades/Downgrades:")
            upgrades = stock.upgrades_downgrades
            if upgrades is not None and not upgrades.empty:
                 click.echo(upgrades.head(5).to_string())
            else:
                 click.echo("No upgrades/downgrades found.")
            click.echo("\n")

    except Exception as e:
        click.secho(f"Error fetching data for {ticker}: {e}", fg="red")

if __name__ == '__main__':
    main()
