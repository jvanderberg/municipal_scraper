"""
Web scraper for municipal websites with robots.txt compliance and rate limiting.
"""
import re
import time
import urllib.parse
import urllib.robotparser
from typing import Set, Dict, Optional, List
from datetime import datetime
import requests
from bs4 import BeautifulSoup


class MunicipalScraper:
    # Common language codes to skip (excluding English)
    DEFAULT_SKIP_LANGUAGES = [
        'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 'ar',
        'hi', 'nl', 'pl', 'tr', 'vi', 'th', 'id', 'uk', 'ro', 'cs',
        'sv', 'da', 'fi', 'no', 'hu', 'el', 'he', 'bn', 'fa', 'ur'
    ]

    def __init__(self, base_url: str, max_depth: int = 3, delay: float = 1.0,
                 user_agent: str = None, skip_languages: bool = True, output_dir: str = None):
        """
        Initialize the scraper.

        Args:
            base_url: The starting URL for the municipal website
            max_depth: Maximum depth to crawl from the base URL
            delay: Delay in seconds between requests (rate limiting)
            user_agent: Custom user agent string
            skip_languages: Whether to skip non-English language versions (default: True)
            output_dir: Directory for incremental output (enables crash recovery)
        """
        self.base_url = base_url.rstrip('/')
        self.domain = urllib.parse.urlparse(base_url).netloc
        self.max_depth = max_depth
        self.delay = delay
        self.user_agent = user_agent or "MunicipalScraper/1.0 (Educational/Archival)"
        self.skip_languages = skip_languages
        self.output_dir = output_dir

        self.visited_urls: Set[str] = set()
        self.pages: List[Dict] = []
        self.pdfs: List[Dict] = []
        self.site_graph: Dict[str, List[str]] = {}
        self.skipped_language_count: int = 0
        self.total_links_found: int = 0

        # Setup incremental writing if output_dir provided
        if self.output_dir:
            from pathlib import Path
            import json
            self.output_path = Path(self.output_dir)
            self.pages_dir = self.output_path / 'pages'
            self.pdfs_dir = self.output_path / 'pdfs'
            self.state_file = self.output_path / '.crawl_state.json'

            # Create directories
            self.pages_dir.mkdir(parents=True, exist_ok=True)
            self.pdfs_dir.mkdir(parents=True, exist_ok=True)

            # Load previous state if resuming
            self._load_state()

        # Setup robots.txt parser
        self.robot_parser = urllib.robotparser.RobotFileParser()
        robots_url = urllib.parse.urljoin(self.base_url, '/robots.txt')
        self.robot_parser.set_url(robots_url)
        try:
            self.robot_parser.read()
        except Exception as e:
            print(f"Warning: Could not read robots.txt: {e}")

    def _load_state(self):
        """Load previous crawl state for resuming."""
        import json
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.visited_urls = set(state.get('visited_urls', []))
                    self.skipped_language_count = state.get('skipped_language_count', 0)
                    self.total_links_found = state.get('total_links_found', 0)
                    print(f"Resuming: Found {len(self.visited_urls)} previously crawled URLs")
            except Exception as e:
                print(f"Warning: Could not load previous state: {e}")

    def _save_state(self):
        """Save current crawl state."""
        import json
        if self.output_dir:
            try:
                state = {
                    'visited_urls': list(self.visited_urls),
                    'skipped_language_count': self.skipped_language_count,
                    'total_links_found': self.total_links_found,
                    'base_url': self.base_url,
                    'last_updated': datetime.utcnow().isoformat()
                }
                with open(self.state_file, 'w') as f:
                    json.dump(state, f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save state: {e}")

    def _url_to_hash(self, url: str) -> str:
        """Convert URL to a consistent filename hash."""
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()

    def _write_page_incremental(self, page_data: Dict):
        """Write a single page immediately to disk."""
        import json
        if self.output_dir:
            try:
                url_hash = self._url_to_hash(page_data['url'])
                file_path = self.pages_dir / f"{url_hash}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(page_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Warning: Could not write page {page_data['url']}: {e}")

    def _write_pdfs_incremental(self):
        """Write the current PDF catalog to disk."""
        import json
        if self.output_dir:
            try:
                catalog_path = self.pdfs_dir / 'catalog.json'
                catalog = {
                    'total_pdfs': len(self.pdfs),
                    'total_size_mb': sum(pdf['file_size_mb'] for pdf in self.pdfs),
                    'pdfs': self.pdfs
                }
                with open(catalog_path, 'w', encoding='utf-8') as f:
                    json.dump(catalog, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Warning: Could not write PDF catalog: {e}")

    def can_fetch(self, url: str) -> bool:
        """Check if we're allowed to fetch this URL according to robots.txt."""
        try:
            return self.robot_parser.can_fetch(self.user_agent, url)
        except Exception:
            return True  # If check fails, proceed cautiously

    def normalize_domain(self, domain: str) -> str:
        """Normalize domain by removing www prefix for comparison."""
        if domain.startswith('www.'):
            return domain[4:]
        return domain

    def is_internal_url(self, url: str) -> bool:
        """Check if URL is internal to the base domain."""
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc == '':
            return True  # Relative URL

        # Normalize both domains for comparison (handles www subdomain)
        url_domain = self.normalize_domain(parsed.netloc)
        base_domain = self.normalize_domain(self.domain)

        return url_domain == base_domain

    def is_valid_http_url(self, url: str) -> bool:
        """Check if URL uses HTTP or HTTPS scheme."""
        parsed = urllib.parse.urlparse(url)
        # If no scheme, it's a relative URL (valid)
        # If scheme exists, it must be http or https
        return parsed.scheme in ('', 'http', 'https')

    def is_language_url(self, url: str) -> bool:
        """Check if URL appears to be a non-English language version."""
        if not self.skip_languages:
            return False

        parsed = urllib.parse.urlparse(url)
        path = parsed.path.lower()
        query = parsed.query.lower()

        # Check for language codes in path (e.g., /es/, /fr/, /es-es/)
        for lang in self.DEFAULT_SKIP_LANGUAGES:
            # Match /es/ or /es-XX/ patterns
            if f'/{lang}/' in path or f'/{lang}-' in path:
                return True
            # Match paths starting with language code
            if path.startswith(f'/{lang}/') or path.startswith(f'/{lang}-'):
                return True

        # Check for language in query parameters
        # Matches: ?lang=es, &lang=es, ?oc_lang=es, ?language=es, etc.
        for lang in self.DEFAULT_SKIP_LANGUAGES:
            # Match any parameter containing 'lang' followed by =<langcode>
            if f'lang={lang}' in query:
                return True
            # Also check for language code at start of query param value
            if f'={lang}' in query:
                # More specific check to avoid false positives
                # Match patterns like lang=es, oc_lang=es, language=es
                if re.search(rf'[_-]?lang(?:uage)?={lang}\b', query):
                    return True

        return False

    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and making absolute."""
        parsed = urllib.parse.urlparse(url)
        # Remove fragment
        normalized = urllib.parse.urlunparse(parsed._replace(fragment=''))
        # Make absolute
        if not normalized.startswith('http'):
            normalized = urllib.parse.urljoin(self.base_url, normalized)
        return normalized

    def is_pdf(self, url: str) -> bool:
        """Check if URL points to a PDF."""
        return url.lower().endswith('.pdf')

    def fetch_page(self, url: str) -> Optional[requests.Response]:
        """Fetch a page with proper headers and error handling."""
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_links(self, soup: BeautifulSoup, current_url: str) -> List[Dict[str, str]]:
        """Extract all links from a page with context."""
        links = []
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']

            # Skip non-HTTP(S) URLs (mailto:, tel:, javascript:, etc.)
            if not self.is_valid_http_url(href):
                continue

            normalized = self.normalize_url(href)

            if not self.is_internal_url(normalized):
                link_type = 'external'
            elif self.is_pdf(normalized):
                link_type = 'pdf'
            else:
                link_type = 'internal'

            links.append({
                'url': normalized,
                'text': anchor.get_text(strip=True),
                'type': link_type
            })

        return links

    def crawl_page(self, url: str, depth: int = 0):
        """Crawl a single page and follow internal links."""
        if depth > self.max_depth:
            return

        if url in self.visited_urls:
            return

        # Skip non-English language versions
        if self.is_language_url(url):
            self.skipped_language_count += 1
            if self.skipped_language_count % 20 == 1:  # Report periodically
                print(f"  Skipping language URL: {url}")
            return

        if not self.can_fetch(url):
            print(f"Skipping {url} (robots.txt disallows)")
            return

        # Better progress reporting
        pages_so_far = len(self.pages)
        print(f"[{pages_so_far + 1}] Crawling (depth {depth}): {url}")
        self.visited_urls.add(url)

        # Rate limiting
        time.sleep(self.delay)

        response = self.fetch_page(url)
        if not response:
            return

        # Check if it's actually HTML
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            print(f"Skipping non-HTML content: {url}")
            return

        soup = BeautifulSoup(response.content, 'lxml')

        # Extract title
        title = soup.title.string if soup.title else url

        # Extract links
        links = self.extract_links(soup, url)

        # Update total links counter
        self.total_links_found += len(links)

        # Show link counts for this page
        internal_count = sum(1 for link in links if link['type'] == 'internal')
        pdf_count = sum(1 for link in links if link['type'] == 'pdf')
        external_count = sum(1 for link in links if link['type'] == 'external')
        print(f"  Found {len(links)} links: {internal_count} internal, {pdf_count} PDFs, {external_count} external")
        print(f"  [Total so far: {len(self.pages) + 1} pages crawled, {self.total_links_found} links found]")

        # Store page data (will be cleaned later)
        page_data = {
            'url': url,
            'title': title,
            'scraped_at': datetime.utcnow().isoformat(),
            'depth': depth,
            'html': str(soup),  # Store full HTML for cleaning phase
            'links': links
        }
        self.pages.append(page_data)

        # Write incrementally if enabled
        self._write_page_incremental(page_data)

        # Save state periodically (every 10 pages)
        if self.output_dir and len(self.pages) % 10 == 0:
            self._save_state()

        # Build site graph
        self.site_graph[url] = [link['url'] for link in links if link['type'] == 'internal']

        # Handle PDFs
        for link in links:
            if link['type'] == 'pdf':
                self.catalog_pdf(link['url'], link['text'], url)

        # Follow internal links
        for link in links:
            if link['type'] == 'internal' and link['url'] not in self.visited_urls:
                self.crawl_page(link['url'], depth + 1)

    def catalog_pdf(self, pdf_url: str, link_text: str, parent_page: str):
        """Catalog a PDF without downloading the full content."""
        if any(pdf['url'] == pdf_url for pdf in self.pdfs):
            return  # Already cataloged

        try:
            # HEAD request to get metadata without downloading
            response = requests.head(pdf_url, timeout=10)
            file_size = int(response.headers.get('Content-Length', 0))
            last_modified = response.headers.get('Last-Modified', '')

            pdf_data = {
                'url': pdf_url,
                'title': link_text or 'Untitled PDF',
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'last_modified': last_modified,
                'parent_page': parent_page,
                'discovered_at': datetime.utcnow().isoformat()
            }
            self.pdfs.append(pdf_data)
            print(f"  [PDF #{len(self.pdfs)}] {link_text} ({pdf_data['file_size_mb']} MB)")

            # Write PDF catalog incrementally
            self._write_pdfs_incremental()

        except Exception as e:
            print(f"  Error cataloging PDF {pdf_url}: {e}")

    def start(self):
        """Start the crawl from the base URL."""
        print(f"Starting crawl of {self.base_url}")
        print(f"Domain: {self.domain} (normalized: {self.normalize_domain(self.domain)})")
        print(f"Max depth: {self.max_depth}, Delay: {self.delay}s")
        if self.skip_languages:
            print(f"Language filtering: Enabled (skipping non-English versions)")
        if self.output_dir:
            print(f"Incremental writing: Enabled (writing to {self.output_dir})")
        print()

        self.crawl_page(self.base_url, depth=0)

        # Save final state
        if self.output_dir:
            self._save_state()
            print(f"\n✓ Data saved incrementally to {self.output_dir}")

        print(f"\nCrawl complete!")
        print(f"Pages crawled: {len(self.pages)}")
        print(f"Total links found: {self.total_links_found}")
        print(f"PDFs found: {len(self.pdfs)}")
        if self.skip_languages and self.skipped_language_count > 0:
            print(f"Language pages skipped: {self.skipped_language_count}")

    def get_results(self) -> Dict:
        """Return the crawl results."""
        return {
            'pages': self.pages,
            'pdfs': self.pdfs,
            'site_graph': self.site_graph,
            'metadata': {
                'base_url': self.base_url,
                'total_pages': len(self.pages),
                'total_pdfs': len(self.pdfs),
                'max_depth': self.max_depth,
                'crawl_completed': datetime.utcnow().isoformat()
            }
        }
