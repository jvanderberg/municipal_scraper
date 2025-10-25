#!/usr/bin/env python3
"""
Catalog analyzer tool - parses the output directory and generates structured data
for creating reference documents about the municipal website.
"""
import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import re


class CatalogAnalyzer:
    def __init__(self, output_dir: str = 'output'):
        self.output_dir = Path(output_dir)
        self.pages_dir = self.output_dir / 'pages'
        self.pdfs_dir = self.output_dir / 'pdfs'

        self.metadata = None
        self.pages = []
        self.pdfs = []

    def load_data(self):
        """Load all data from the catalog."""
        print("Loading catalog data...")

        # Load metadata
        with open(self.output_dir / 'site_metadata.json', 'r') as f:
            self.metadata = json.load(f)

        # Load all pages
        page_files = list(self.pages_dir.glob('*.json'))
        print(f"Loading {len(page_files)} pages...")
        for page_file in page_files:
            with open(page_file, 'r') as f:
                self.pages.append(json.load(f))

        # Load PDFs
        with open(self.pdfs_dir / 'catalog.json', 'r') as f:
            pdf_data = json.load(f)
            self.pdfs = pdf_data.get('pdfs', [])

        print(f"Loaded {len(self.pages)} pages and {len(self.pdfs)} PDFs")

    def extract_sections(self) -> Dict[str, List[Dict]]:
        """Extract main sections/departments from URLs and page titles."""
        sections = defaultdict(list)

        for page in self.pages:
            url = page['url']
            title = page['title']

            # Parse URL path to extract section
            parsed_url = url.replace(self.metadata['base_url'], '').replace('https://www.oak-park.us', '')
            path_parts = [p for p in parsed_url.split('/') if p]

            if path_parts:
                section = path_parts[0].title().replace('-', ' ')
            else:
                section = 'Home'

            sections[section].append({
                'url': url,
                'title': title,
                'word_count': page.get('word_count', 0),
                'headings': page.get('headings', []),
                'links': page.get('links', []),
                'path': parsed_url
            })

        return dict(sections)

    def identify_key_pages(self, sections: Dict) -> List[Dict]:
        """Identify key/important pages based on various factors."""
        key_pages = []

        for section, pages_list in sections.items():
            # Sort pages by word count (indicator of content richness)
            sorted_pages = sorted(pages_list, key=lambda p: p['word_count'], reverse=True)

            # Take top pages from each section
            for page in sorted_pages[:5]:  # Top 5 per section
                if page['word_count'] > 100:  # Only pages with substantial content
                    key_pages.append({
                        'section': section,
                        'title': page['title'],
                        'url': page['url'],
                        'word_count': page['word_count'],
                        'has_pdfs': any(link['type'] == 'pdf' for link in page['links'])
                    })

        # Sort by word count globally
        key_pages.sort(key=lambda p: p['word_count'], reverse=True)
        return key_pages

    def categorize_pdfs(self) -> Dict[str, List[Dict]]:
        """Categorize PDFs based on title and parent page."""
        categories = defaultdict(list)

        keywords = {
            'meeting_minutes': ['minutes', 'agenda', 'meeting'],
            'ordinances': ['ordinance', 'resolution'],
            'financial': ['budget', 'financial', 'audit', 'fiscal', 'finance'],
            'planning': ['planning', 'zoning', 'development', 'comprehensive plan'],
            'reports': ['report', 'annual', 'quarterly', 'study'],
            'notices': ['notice', 'notification', 'announcement'],
            'policies': ['policy', 'protocol', 'procedure', 'guideline'],
            'memos': ['memo', 'memorandum']
        }

        for pdf in self.pdfs:
            title_lower = pdf['title'].lower()
            parent_lower = pdf.get('parent_page', '').lower()
            combined_text = title_lower + ' ' + parent_lower

            categorized = False
            for category, keyword_list in keywords.items():
                if any(keyword in combined_text for keyword in keyword_list):
                    categories[category].append(pdf)
                    categorized = True
                    break

            if not categorized:
                categories['other'].append(pdf)

        return dict(categories)

    def find_common_topics(self) -> Dict[str, List[str]]:
        """Find common topics and what pages contain them."""
        topic_keywords = {
            'parking': ['parking', 'permit', 'garage'],
            'taxes': ['tax', 'property tax', 'assessment'],
            'permits': ['permit', 'license', 'application'],
            'utilities': ['water', 'sewer', 'utility', 'billing'],
            'public_safety': ['police', 'fire', 'emergency', 'safety'],
            'development': ['development', 'building', 'construction', 'zoning'],
            'recreation': ['park', 'recreation', 'library', 'event'],
            'public_works': ['street', 'road', 'infrastructure', 'public works'],
            'elections': ['election', 'voting', 'voter', 'ballot'],
            'business': ['business', 'commercial', 'economic development']
        }

        topic_pages = defaultdict(list)

        for page in self.pages:
            content = page.get('content_text', '').lower()
            title = page['title'].lower()
            combined = content + ' ' + title

            for topic, keywords in topic_keywords.items():
                if any(keyword in combined for keyword in keywords):
                    topic_pages[topic].append({
                        'title': page['title'],
                        'url': page['url']
                    })

        # Deduplicate and limit
        for topic in topic_pages:
            seen = set()
            unique = []
            for page in topic_pages[topic]:
                if page['url'] not in seen:
                    seen.add(page['url'])
                    unique.append(page)
            topic_pages[topic] = unique[:10]  # Top 10 per topic

        return dict(topic_pages)

    def get_statistics(self) -> Dict:
        """Get overall statistics about the site."""
        total_words = sum(p.get('word_count', 0) for p in self.pages)
        pages_with_pdfs = sum(1 for p in self.pages if any(link['type'] == 'pdf' for link in p.get('links', [])))

        return {
            'total_pages': len(self.pages),
            'total_pdfs': len(self.pdfs),
            'total_words': total_words,
            'avg_words_per_page': total_words // len(self.pages) if self.pages else 0,
            'pages_with_pdfs': pages_with_pdfs,
            'base_url': self.metadata.get('base_url', ''),
            'crawl_date': self.metadata.get('crawl_completed', '')
        }

    def generate_analysis(self) -> Dict:
        """Generate comprehensive analysis of the catalog."""
        self.load_data()

        print("\nAnalyzing catalog structure...")
        sections = self.extract_sections()

        print("Identifying key pages...")
        key_pages = self.identify_key_pages(sections)

        print("Categorizing PDFs...")
        pdf_categories = self.categorize_pdfs()

        print("Finding common topics...")
        topic_pages = self.find_common_topics()

        print("Calculating statistics...")
        stats = self.get_statistics()

        analysis = {
            'statistics': stats,
            'sections': sections,
            'key_pages': key_pages,
            'pdf_categories': pdf_categories,
            'topic_pages': topic_pages
        }

        # Save analysis to file
        with open(self.output_dir / 'analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2, default=str)

        print(f"\n✓ Analysis complete! Saved to {self.output_dir / 'analysis.json'}")
        return analysis


def main():
    analyzer = CatalogAnalyzer()
    analysis = analyzer.generate_analysis()

    print("\n" + "=" * 60)
    print("CATALOG ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Base URL: {analysis['statistics']['base_url']}")
    print(f"Total Pages: {analysis['statistics']['total_pages']}")
    print(f"Total PDFs: {analysis['statistics']['total_pdfs']}")
    print(f"Total Words: {analysis['statistics']['total_words']:,}")
    print(f"Avg Words/Page: {analysis['statistics']['avg_words_per_page']}")
    print(f"\nMain Sections: {len(analysis['sections'])}")
    for section in list(analysis['sections'].keys())[:10]:
        print(f"  - {section} ({len(analysis['sections'][section])} pages)")
    print(f"\nPDF Categories:")
    for category, pdfs in analysis['pdf_categories'].items():
        print(f"  - {category.replace('_', ' ').title()}: {len(pdfs)} PDFs")


if __name__ == '__main__':
    main()
