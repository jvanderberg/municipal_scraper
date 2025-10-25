"""
Output writer for creating the on-disk catalog structure.
"""
import json
import os
import hashlib
from pathlib import Path
from typing import Dict, List


class OutputWriter:
    def __init__(self, output_dir: str = 'output'):
        """
        Initialize the output writer.

        Args:
            output_dir: Directory to write the catalog to
        """
        self.output_dir = Path(output_dir)
        self.pages_dir = self.output_dir / 'pages'
        self.pdfs_dir = self.output_dir / 'pdfs'

    def _create_directories(self):
        """Create the output directory structure."""
        self.output_dir.mkdir(exist_ok=True)
        self.pages_dir.mkdir(exist_ok=True)
        self.pdfs_dir.mkdir(exist_ok=True)

    def _url_to_hash(self, url: str) -> str:
        """Convert URL to a consistent filename hash."""
        return hashlib.md5(url.encode()).hexdigest()

    def write_catalog(self, pages: List[Dict], pdfs: List[Dict], site_graph: Dict, metadata: Dict):
        """
        Write the complete catalog to disk.

        Args:
            pages: List of cleaned page data
            pdfs: List of PDF catalog entries
            site_graph: Graph of page relationships
            metadata: Overall site metadata
        """
        print(f"\nWriting catalog to {self.output_dir}")
        self._create_directories()

        # Write individual page files
        print(f"Writing {len(pages)} page files...")
        for page in pages:
            self._write_page(page)

        # Write PDF catalog
        print(f"Writing PDF catalog ({len(pdfs)} PDFs)...")
        self._write_pdf_catalog(pdfs)

        # Write site graph
        print("Writing site graph...")
        self._write_site_graph(site_graph)

        # Write overall metadata
        print("Writing site metadata...")
        self._write_site_metadata(metadata, len(pages), len(pdfs))

        print(f"\nCatalog written successfully to {self.output_dir.absolute()}")

    def _write_page(self, page: Dict):
        """Write a single page to disk."""
        url_hash = self._url_to_hash(page['url'])
        file_path = self.pages_dir / f"{url_hash}.json"

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(page, f, indent=2, ensure_ascii=False)

    def _write_pdf_catalog(self, pdfs: List[Dict]):
        """Write the PDF catalog."""
        catalog_path = self.pdfs_dir / 'catalog.json'

        # Group PDFs by type/category if possible
        categorized_pdfs = self._categorize_pdfs(pdfs)

        catalog = {
            'total_pdfs': len(pdfs),
            'total_size_mb': sum(pdf['file_size_mb'] for pdf in pdfs),
            'pdfs': pdfs,
            'by_category': categorized_pdfs
        }

        with open(catalog_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)

    def _categorize_pdfs(self, pdfs: List[Dict]) -> Dict[str, List[Dict]]:
        """Attempt to categorize PDFs based on title and context."""
        categories = {
            'meeting_minutes': [],
            'ordinances': [],
            'resolutions': [],
            'financial': [],
            'planning': [],
            'reports': [],
            'notices': [],
            'other': []
        }

        # Keywords for categorization
        category_keywords = {
            'meeting_minutes': ['minutes', 'meeting', 'agenda', 'session'],
            'ordinances': ['ordinance'],
            'resolutions': ['resolution'],
            'financial': ['budget', 'financial', 'audit', 'fiscal', 'finance'],
            'planning': ['planning', 'zoning', 'development', 'comprehensive plan'],
            'reports': ['report', 'annual', 'quarterly'],
            'notices': ['notice', 'notification', 'announcement'],
        }

        for pdf in pdfs:
            title_lower = pdf['title'].lower()
            categorized = False

            for category, keywords in category_keywords.items():
                if any(keyword in title_lower for keyword in keywords):
                    categories[category].append(pdf)
                    categorized = True
                    break

            if not categorized:
                categories['other'].append(pdf)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def _write_site_graph(self, site_graph: Dict):
        """Write the site graph (page relationships)."""
        graph_path = self.output_dir / 'site_graph.json'

        # Convert to more readable format with hashes and URLs
        graph_with_metadata = {}
        for source_url, target_urls in site_graph.items():
            source_hash = self._url_to_hash(source_url)
            graph_with_metadata[source_hash] = {
                'url': source_url,
                'links_to': [
                    {
                        'hash': self._url_to_hash(target_url),
                        'url': target_url
                    }
                    for target_url in target_urls
                ]
            }

        with open(graph_path, 'w', encoding='utf-8') as f:
            json.dump(graph_with_metadata, f, indent=2, ensure_ascii=False)

    def _write_site_metadata(self, metadata: Dict, page_count: int, pdf_count: int):
        """Write overall site metadata."""
        metadata_path = self.output_dir / 'site_metadata.json'

        # Add statistics
        enhanced_metadata = {
            **metadata,
            'catalog_statistics': {
                'total_pages_cataloged': page_count,
                'total_pdfs_cataloged': pdf_count,
                'output_directory': str(self.output_dir.absolute())
            },
            'structure': {
                'pages': 'pages/{url-hash}.json - Individual page content',
                'pdfs': 'pdfs/catalog.json - PDF catalog with metadata',
                'site_graph': 'site_graph.json - Page relationship graph',
                'site_metadata': 'site_metadata.json - This file'
            }
        }

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_metadata, f, indent=2, ensure_ascii=False)

    def get_catalog_summary(self) -> str:
        """
        Generate a human-readable summary of the catalog.
        Useful for verifying the output.
        """
        if not self.output_dir.exists():
            return "No catalog found."

        metadata_path = self.output_dir / 'site_metadata.json'
        if not metadata_path.exists():
            return "Catalog incomplete."

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        summary = [
            "=== Municipal Website Catalog Summary ===",
            f"Base URL: {metadata.get('base_url', 'N/A')}",
            f"Crawled: {metadata.get('crawl_completed', 'N/A')}",
            f"Pages: {metadata['catalog_statistics']['total_pages_cataloged']}",
            f"PDFs: {metadata['catalog_statistics']['total_pdfs_cataloged']}",
            f"Max Depth: {metadata.get('max_depth', 'N/A')}",
            f"\nOutput Directory: {metadata['catalog_statistics']['output_directory']}"
        ]

        return '\n'.join(summary)
