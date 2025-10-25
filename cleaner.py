"""
HTML content cleaner for extracting main content and removing boilerplate.
Uses heuristics and common patterns without LLM assistance.
"""
from bs4 import BeautifulSoup, NavigableString
from typing import List, Dict, Set
import re


class ContentCleaner:
    # Common boilerplate CSS selectors to remove
    BOILERPLATE_SELECTORS = [
        'nav', 'header', 'footer', 'aside',
        '.navigation', '.nav', '.navbar', '.menu',
        '.sidebar', '.side-bar', '.widget',
        '.footer', '.header', '.banner',
        '.advertisement', '.ad', '.ads',
        '.social-media', '.social', '.share-buttons',
        '.breadcrumb', '.breadcrumbs',
        '#navigation', '#nav', '#sidebar', '#footer', '#header',
        '.cookie-notice', '.cookie-banner',
        '[role="navigation"]', '[role="banner"]', '[role="complementary"]'
    ]

    # Common boilerplate text patterns
    BOILERPLATE_PATTERNS = [
        r'©\s*\d{4}',  # Copyright notices
        r'All rights reserved',
        r'Skip to (?:main )?content',
        r'JavaScript (?:must be|is) (?:enabled|disabled)',
        r'This site uses cookies',
    ]

    # Content-rich selectors (preferred main content areas)
    CONTENT_SELECTORS = [
        'main', 'article', '[role="main"]',
        '.content', '.main-content', '.page-content',
        '#content', '#main-content', '#main'
    ]

    def __init__(self):
        self.boilerplate_fragments: Set[str] = set()

    def clean_page(self, html: str, url: str) -> Dict:
        """
        Clean a single page's HTML and extract structured content.

        Returns a dict with cleaned text, headings, and metadata.
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove boilerplate elements
        self._remove_boilerplate(soup)

        # Extract main content area
        main_content = self._extract_main_content(soup)

        # Extract headings hierarchy
        headings = self._extract_headings(main_content)

        # Extract clean text
        text = self._extract_clean_text(main_content)

        # Extract metadata hints
        metadata = self._extract_metadata(soup)

        return {
            'content_text': text,
            'headings': headings,
            'metadata': metadata,
            'word_count': len(text.split())
        }

    def _remove_boilerplate(self, soup: BeautifulSoup):
        """Remove common boilerplate elements from soup."""
        # Remove by CSS selectors
        for selector in self.BOILERPLATE_SELECTORS:
            for element in soup.select(selector):
                element.decompose()

        # Remove script and style tags
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg']):
            tag.decompose()

        # Remove hidden elements
        for element in soup.find_all(style=re.compile(r'display:\s*none')):
            element.decompose()

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, NavigableString) and text.strip().startswith('<!--')):
            comment.extract()

    def _extract_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Extract the main content area using heuristics.
        Returns the most likely content container.
        """
        # Try explicit content selectors first
        for selector in self.CONTENT_SELECTORS:
            content = soup.select_one(selector)
            if content:
                return content

        # Fallback: find the element with the most text
        return self._find_largest_text_block(soup)

    def _find_largest_text_block(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Find the element with the most text content."""
        candidates = soup.find_all(['div', 'section', 'article'])

        if not candidates:
            return soup.body if soup.body else soup

        # Score each candidate by text length
        best_candidate = soup.body if soup.body else soup
        max_text_length = 0

        for candidate in candidates:
            # Get text but ignore nested candidates we've already counted
            text_length = len(candidate.get_text(strip=True))
            if text_length > max_text_length:
                max_text_length = text_length
                best_candidate = candidate

        return best_candidate

    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract heading hierarchy from the content."""
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.get_text(strip=True)
            if text and not self._is_boilerplate_text(text):
                headings.append({
                    'level': tag.name,
                    'text': text
                })
        return headings

    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """
        Extract clean, readable text from content.
        Preserves paragraph structure with double newlines.
        """
        # Get text from paragraphs and list items
        text_blocks = []

        for tag in soup.find_all(['p', 'li', 'td', 'th', 'blockquote']):
            text = tag.get_text(strip=True)
            if text and not self._is_boilerplate_text(text):
                text_blocks.append(text)

        # If no structured text found, fall back to all text
        if not text_blocks:
            text = soup.get_text(separator=' ', strip=True)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            return text

        # Join with double newlines to preserve structure
        return '\n\n'.join(text_blocks)

    def _is_boilerplate_text(self, text: str) -> bool:
        """Check if text matches boilerplate patterns."""
        text_lower = text.lower()

        # Check length
        if len(text) < 3 or len(text) > 500:  # Very short or suspiciously long single strings
            return False

        # Check patterns
        for pattern in self.BOILERPLATE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        # Check against known boilerplate fragments
        if text in self.boilerplate_fragments:
            return True

        return False

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata hints from the page."""
        metadata = {}

        # Try to find department/category
        for tag in soup.find_all(class_=re.compile(r'(department|category|section)')):
            text = tag.get_text(strip=True)
            if text:
                metadata['department'] = text
                break

        # Try to find dates
        for tag in soup.find_all(['time', 'span', 'div'], class_=re.compile(r'(date|published|updated)')):
            datetime_attr = tag.get('datetime')
            if datetime_attr:
                metadata['date'] = datetime_attr
                break
            text = tag.get_text(strip=True)
            # Simple date pattern matching
            date_match = re.search(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b', text)
            if date_match:
                metadata['date'] = date_match.group(1)
                break

        # Try to find document type
        for tag in soup.find_all(class_=re.compile(r'(document-type|doc-type|type)')):
            text = tag.get_text(strip=True)
            if text:
                metadata['document_type'] = text
                break

        return metadata

    def identify_common_boilerplate(self, pages: List[Dict]):
        """
        Identify text that appears on many pages (likely boilerplate).
        Call this after scraping all pages to identify repeated content.
        """
        # Count text fragments across pages
        fragment_counts = {}

        for page in pages:
            soup = BeautifulSoup(page.get('html', ''), 'lxml')
            # Get all text nodes
            for text in soup.find_all(string=True):
                cleaned = text.strip()
                if 10 < len(cleaned) < 200:  # Reasonable fragment size
                    fragment_counts[cleaned] = fragment_counts.get(cleaned, 0) + 1

        # Mark fragments that appear on >50% of pages as boilerplate
        threshold = len(pages) * 0.5
        for fragment, count in fragment_counts.items():
            if count > threshold:
                self.boilerplate_fragments.add(fragment)

        print(f"Identified {len(self.boilerplate_fragments)} common boilerplate fragments")

    def clean_all_pages(self, pages: List[Dict]) -> List[Dict]:
        """
        Clean all pages in the crawl results.
        First identifies common boilerplate, then cleans each page.
        """
        print("Analyzing pages for common boilerplate...")
        self.identify_common_boilerplate(pages)

        print("Cleaning page content...")
        cleaned_pages = []

        for i, page in enumerate(pages):
            print(f"  Cleaning {i+1}/{len(pages)}: {page['url']}")
            cleaned_data = self.clean_page(page.get('html', ''), page['url'])

            # Merge with original page data (excluding HTML)
            cleaned_page = {
                'url': page['url'],
                'title': page['title'],
                'scraped_at': page['scraped_at'],
                'depth': page['depth'],
                'links': page['links'],
                **cleaned_data
            }
            cleaned_pages.append(cleaned_page)

        return cleaned_pages
