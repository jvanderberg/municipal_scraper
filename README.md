# Municipal Website Scraper

Catalog any municipal website and create LLM-ready reference documents that enable a GPT to help residents navigate government services.

## Quick Start

```bash
# 1. Setup once
./setup.sh

# 2. Scrape your municipal website
./run.sh https://your-city.gov

# 3. Prompt Claude to analyze (see below)
```

## Complete Workflow

### Step 1: Scrape the Website

```bash
./run.sh https://your-city.gov
```

This creates an `output/` directory with:
- 200-300 pages of cleaned content (JSON files)
- Catalog of all PDFs (metadata only, not downloaded)
- Site structure and relationships

**What gets captured:**
- Page content (cleaned of nav, headers, footers)
- All internal links
- PDF documents (URL, size, title, location)
- Site structure and navigation

### Step 2: Analyze with Claude

Point Claude at your `output/` directory and use this prompt:

```
I've scraped a municipal website using the municipal_scraper tool.
Please read claude_prompt.md and analyze the output directory to create
the reference documents for a GPT.
```

Claude will create 5 markdown files in `output/`:
- **site_overview.md** - Overall structure and organization
- **page_index.md** - Organized index of all important pages
- **document_catalog.md** - Complete PDF catalog by category
- **navigation_guide.md** - "How to find..." guide for common queries
- **gpt_instructions.md** - System prompt for your GPT

### Step 3: Create Your GPT

1. Create a new GPT (ChatGPT Plus required)
2. Upload these 4 files as "Knowledge":
   - site_overview.md
   - page_index.md
   - document_catalog.md
   - navigation_guide.md
3. Use `gpt_instructions.md` as your GPT's system prompt
4. Done! Your GPT can now help residents navigate your city's website

## What It Does

### Phase 1: Scrape (Python)
- **Crawls** the website following internal links (configurable depth)
- **Cleans** content algorithmically (removes nav, headers, footers, boilerplate)
- **Catalogs PDFs** without downloading (metadata only: size, title, location)
- **Filters** non-English pages to avoid duplicates
- **Writes incrementally** with crash recovery
- **Respects** robots.txt and implements rate limiting

### Phase 2: Analyze (Claude)
Claude reads your catalog and creates:
- Site structure overview
- Organized page index
- Document catalog by category
- Navigation guide for finding information
- GPT system prompt

### Phase 3: Use (Your GPT)
Your GPT can now:
- Answer "Where do I find...?" questions
- Direct residents to specific pages and documents
- Explain site structure and available services
- Help navigate complex municipal websites

## Features

- **Incremental writing**: Pages saved as scraped (survives crashes)
- **Resume capability**: Picks up where it left off if interrupted
- **Language filtering**: Skips translated versions automatically
- **Smart content cleaning**: Identifies and removes common boilerplate
- **Progress tracking**: Shows pages crawled, links found, PDFs discovered
- **PDF cataloging**: HEAD requests only (fast, no downloads)
- **De-duplication**: Won't fetch the same URL twice

## Usage

### Basic
```bash
./run.sh https://your-city.gov
```

### With Options
```bash
./run.sh https://your-city.gov \
  --max-depth 4 \
  --delay 2.0 \
  --output my_catalog \
  --no-skip-languages  # Include all language versions
```

### Options
- `--max-depth N` - Crawl depth from base URL (default: 3)
- `--delay N` - Seconds between requests (default: 1.0)
- `--output DIR` - Output directory (default: output)
- `--no-skip-languages` - Include non-English pages
- `--user-agent STR` - Custom user agent

## Output Structure

After scraping:
```
output/
├── site_metadata.json       # Crawl statistics
├── pages/
│   └── {hash}.json          # Individual pages (cleaned content)
├── pdfs/
│   └── catalog.json         # PDF metadata
├── site_graph.json          # Page relationships
└── .crawl_state.json        # Resume state
```

After Claude analysis:
```
output/
├── [Above files...]
└── [Reference documents]    # Ready for GPT
    ├── site_overview.md
    ├── page_index.md
    ├── document_catalog.md
    ├── navigation_guide.md
    └── gpt_instructions.md
```

## Example: Oak Park, Illinois

Real example from this repo:
- **Scraped**: 228 pages, 1,236 PDFs in ~10 minutes
- **Generated**: 5 reference documents totaling 130KB
- **Result**: GPT that helps residents find parking info, meeting minutes, permits, etc.

Sample questions the GPT can answer:
- "Where can I get a parking permit?"
- "Where are the city council meeting minutes?"
- "How do I apply for a building permit?"
- "When is leaf collection in my area?"

## What Gets Cataloged

**Web Pages:**
- URL, title, cleaned content
- Heading hierarchy
- Links (internal/external/PDF)
- Metadata hints (department, date)
- Word count

**PDF Documents:**
- URL, title, file size
- Parent page that links to it
- Last modified date
- Auto-categorized by Claude (meeting minutes, ordinances, financial, etc.)

## Content Cleaning

Automatically removes:
- Navigation, headers, footers, sidebars
- Social media widgets, language selectors
- Advertisement blocks, cookie notices
- Boilerplate text repeated across pages
- JavaScript/CSS content

Preserves:
- Main content paragraphs
- Headings and structure
- Links to documents and pages
- Department/topic metadata

## Use Cases

- **Resident assistance GPT**: Help citizens find services and information
- **Document search**: Quickly locate ordinances, minutes, reports
- **Website audit**: Understand site structure and identify content gaps
- **Migration planning**: Catalog existing site before redesign
- **Accessibility analysis**: Find pages with minimal content
- **Archive creation**: Snapshot of municipal website at a point in time

## Crash Recovery

If scraping stops (crash, Ctrl-C, network issue):
```bash
# Just run again - it resumes automatically
./run.sh https://your-city.gov
```

The scraper:
- Loads `.crawl_state.json` to see what's been crawled
- Skips already-visited URLs
- Continues from where it left off
- State saved every 10 pages

## Requirements

- Python 3.7+
- Dependencies: `requests`, `beautifulsoup4`, `lxml` (installed by setup.sh)
- ~100MB disk space per 200 pages + PDFs
- Claude API access for analysis phase
- ChatGPT Plus (for creating GPTs)

## Tips

- **Start with depth 3**: Good balance of coverage and speed
- **Increase delay for large sites**: `--delay 2.0` is gentler on servers
- **Check robots.txt first**: Ensure scraping is allowed
- **Review output/site_metadata.json**: Quick summary of what was captured
- **Language filtering saves time**: Default behavior, disable with `--no-skip-languages` if needed
- **Let Claude analyze**: Don't try to manually create the reference docs
- **Progress tracking**: Watch for page counts and link totals during scraping

## Developer Notes

If you want to run the analysis tools directly (without Claude):
```bash
python3 analyze_catalog.py
python3 generate_page_index.py
python3 generate_document_catalog.py
```

You'll still need to manually create `site_overview.md` and `navigation_guide.md`, which is why prompting Claude is recommended.

## License

MIT
