#!/usr/bin/env python3
from duckduckgo_search import DDGS
import click

@click.command()
@click.argument('query', nargs=-1, required=True)
@click.option('--limit', default=5, type=int, help='Maximum number of results to return (default: 5)')
@click.option('--region', default='wt-wt', help='Search region (default: wt-wt for worldwide)')
def main(query, limit, region):
    """
    Perform a general web search using DuckDuckGo.
    Provide the search terms as arguments. Note: Multiple words will be combined into a single query.
    Example: python web_search.py latest AI regulations
    """
    search_term = " ".join(query)
    click.secho(f"Searching for: '{search_term}'", fg="cyan", bold=True)
    
    try:
        with DDGS() as ddgs:
            # Using backend="lite" to bypass some of the anti-bot measures that cause 202 errors
            results = ddgs.text(search_term, region=region, max_results=limit, backend="lite")
            
            if not results:
                click.echo("No results found.")
                return

            for i, result in enumerate(results, 1):
                click.secho(f"{i}. {result.get('title')}", fg="yellow", bold=True)
                click.echo(f"   URL: {result.get('href')}")
                click.echo(f"   Snippet: {result.get('body')}")
                click.echo("-" * 50)
                
    except Exception as e:
         click.secho(f"Error performing search: {e}", fg="red")

if __name__ == '__main__':
    main()
