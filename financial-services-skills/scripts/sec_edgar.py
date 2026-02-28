#!/usr/bin/env python3
from sec_edgar_downloader import Downloader
import click
import os

@click.command()
@click.argument('ticker')
@click.option('--email', prompt='Your Email (required by SEC)', help='Email address to identify your SEC requests.')
@click.option('--company-name', prompt='Your Company Name (required by SEC)', default='Personal Research', help='Company name to identify your SEC requests.')
@click.option('--limit', default=1, type=int, help='Number of latest filings to download for each type (default: 1)')
@click.option('--output-dir', default='./sec_filings', help='Directory to save downloaded filings (default: ./sec_filings)')
def main(ticker, email, company_name, limit, output_dir):
    """
    Download the latest 10-K and 10-Q filings for a given TICKER from SEC EDGAR.
    Example: python sec_edgar.py MSFT
    """
    click.secho(f"Starting download for {ticker.upper()} filings to {output_dir}...", fg="cyan")
    
    try:
        # Initialize the downloader with identity info
        dl = Downloader(company_name, email, output_dir)
        
        # Download 10-K (Annual Reports)
        click.echo(f"Downloading latest {limit} 10-K filing(s)...")
        num_10k_downloaded = dl.get("10-K", ticker, limit=limit)
        click.secho(f"Successfully downloaded {num_10k_downloaded} 10-K filing(s).", fg="green")
        
        # Download 10-Q (Quarterly Reports)
        click.echo(f"Downloading latest {limit} 10-Q filing(s)...")
        num_10q_downloaded = dl.get("10-Q", ticker, limit=limit)
        click.secho(f"Successfully downloaded {num_10q_downloaded} 10-Q filing(s).", fg="green")
        
        click.echo(f"Finished. Filings are located in: {os.path.abspath(output_dir)}")
        
    except Exception as e:
         click.secho(f"Error downloading filings for {ticker}: {e}", fg="red")

if __name__ == '__main__':
    main()
