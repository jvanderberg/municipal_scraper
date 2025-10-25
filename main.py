#!/usr/bin/env python3
"""
Municipal Website Scraper
Creates an on-disk catalog of municipal website content for LLM indexing.

Usage:
    python main.py <base_url> [options]

Example:
    python main.py https://www.cityofexample.gov --max-depth 3 --delay 1.5
"""
import argparse
import sys
from scraper import MunicipalScraper
from cleaner import ContentCleaner
from output_writer import OutputWriter


def main():
    parser = argparse.ArgumentParser(
        description='Scrape and catalog a municipal website for LLM indexing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://www.cityofexample.gov
  python main.py https://www.cityofexample.gov --max-depth 4 --delay 2.0
  python main.py https://www.cityofexample.gov --output my_catalog
        """
    )

    parser.add_argument(
        'base_url',
        help='The base URL of the municipal website to scrape'
    )

    parser.add_argument(
        '--max-depth',
        type=int,
        default=3,
        help='Maximum crawl depth from base URL (default: 3)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay in seconds between requests (default: 1.0)'
    )

    parser.add_argument(
        '--output',
        default='output',
        help='Output directory for the catalog (default: output)'
    )

    parser.add_argument(
        '--user-agent',
        help='Custom user agent string'
    )

    parser.add_argument(
        '--no-skip-languages',
        action='store_true',
        help='Include non-English language versions (default: skip them)'
    )

    args = parser.parse_args()

    # Validate URL
    if not args.base_url.startswith(('http://', 'https://')):
        print("Error: base_url must start with http:// or https://")
        sys.exit(1)

    print("=" * 60)
    print("Municipal Website Scraper")
    print("=" * 60)
    print(f"Target: {args.base_url}")
    print(f"Max Depth: {args.max_depth}")
    print(f"Delay: {args.delay}s")
    print(f"Output: {args.output}/")
    print("=" * 60)
    print()

    # Phase 1: Scrape
    print("PHASE 1: SCRAPING")
    print("-" * 60)
    scraper = MunicipalScraper(
        base_url=args.base_url,
        max_depth=args.max_depth,
        delay=args.delay,
        user_agent=args.user_agent,
        skip_languages=not args.no_skip_languages,
        output_dir=args.output  # Enable incremental writing
    )
    scraper.start()

    results = scraper.get_results()
    print()

    # Phase 2: Clean
    print("PHASE 2: CLEANING CONTENT")
    print("-" * 60)
    cleaner = ContentCleaner()
    cleaned_pages = cleaner.clean_all_pages(results['pages'])
    print()

    # Phase 3: Write to disk
    print("PHASE 3: WRITING CATALOG")
    print("-" * 60)
    writer = OutputWriter(output_dir=args.output)
    writer.write_catalog(
        pages=cleaned_pages,
        pdfs=results['pdfs'],
        site_graph=results['site_graph'],
        metadata=results['metadata']
    )
    print()

    # Summary
    print("=" * 60)
    print(writer.get_catalog_summary())
    print("=" * 60)
    print()
    print("✓ Scraping complete!")
    print()
    print("Next steps:")
    print("  1. Review the catalog in the output directory")
    print("  2. Use an LLM to index and summarize the catalog")
    print("  3. Create a document suitable for prompting another LLM")
    print()


if __name__ == '__main__':
    main()
