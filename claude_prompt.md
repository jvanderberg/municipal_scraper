# Claude Prompt: Municipal Website Catalog Analysis

## Context: What You're Analyzing

The `output/` directory contains a catalog of a municipal website, created by a Python scraper that:

1. **Crawled the website** following internal links up to a specified depth
2. **Extracted clean content** from HTML pages (removed nav, headers, footers, boilerplate)
3. **Cataloged PDFs** without downloading them (metadata only: URL, size, parent page)
4. **Filtered out** non-English language versions to avoid duplicates
5. **Wrote incrementally** to disk as it crawled

## Directory Structure

```
output/
├── site_metadata.json          # Overall site info, crawl date, statistics
├── pages/
│   ├── {url-hash}.json         # Each page: url, title, cleaned content, links, headings
│   └── ...
├── pdfs/
│   └── catalog.json            # PDF metadata (url, size, title, parent page)
└── site_graph.json             # Page relationships (what links to what)
```

### Page File Format
Each `{url-hash}.json` contains:
- `url`: Full URL of the page
- `title`: Page title
- `content_text`: Cleaned text content (paragraphs, main content only)
- `headings`: Array of `{level, text}` heading hierarchy
- `links`: Array of outbound links with type (internal/external/pdf)
- `metadata`: Extracted hints (department, date, document type)
- `word_count`: Number of words in cleaned content

### PDF Catalog Format
`pdfs/catalog.json` contains:
- `total_pdfs`: Count
- `pdfs`: Array of PDF metadata (url, title, file_size_mb, parent_page)
- `by_category`: PDFs grouped by type (meeting_minutes, ordinances, financial, etc.)

## Parsing Tools Available

To help with analysis, the following tools have been created:

### `analyze_catalog.py`
Main analysis tool that:
- Loads all pages and PDFs from the catalog
- Extracts sections/departments from URLs
- Identifies key pages by content quality
- Categorizes PDFs by topic
- Finds common topics across pages
- Generates `output/analysis.json` with structured data

**Run with**: `python3 analyze_catalog.py`

### `generate_page_index.py`
Creates the page index from analysis data:
- Organizes pages by section
- Sorts by content quality (word count)
- Includes headings and PDF markers
- Generates `output/page_index.md`

**Run with**: `python3 generate_page_index.py`

### `generate_document_catalog.py`
Creates the document catalog from analysis data:
- Groups PDFs by category
- Organizes by parent page
- Shows document locations
- Generates `output/document_catalog.md`

**Run with**: `python3 generate_document_catalog.py`

### `generate_complete_index.py`
Creates a lightweight complete index of ALL pages and PDFs:
- Lists every page alphabetically with URL and word count
- Lists every PDF by category with URL and size
- Provides comprehensive search coverage
- Generates `output/complete_index.md`

**Run with**: `python3 generate_complete_index.py`

## Your Task

Create reference documents and instructions for a GPT (pre-prompted LLM) that will help users navigate and understand this municipal website.

### Step 1: Analyze the Catalog

Use the parsing tools to understand:
1. **Site structure**: What are the main sections/departments?
2. **Content types**: What kinds of information are available?
3. **Key pages**: What are the most important pages (by content, links, or topic)?
4. **Document organization**: How are PDFs organized? What types exist?
5. **Navigation patterns**: How is content connected?

**Tool**: Run `analyze_catalog.py` to generate `analysis.json`

### Step 2: Create Reference Documents

Create the following files in `output/`:

#### 1. `site_overview.md`
A high-level summary of the municipal website:
- Name of the municipality
- Main departments/sections
- Types of content available
- Structure and organization
- Key areas of interest

#### 2. `page_index.md`
An organized index of important pages:
- Group by category/department
- Include page title and URL
- Brief description of what each page contains
- Indicate which pages link to PDFs

#### 3. `document_catalog.md`
Summary of available documents (PDFs):
- Organized by category
- Include title, URL, and size
- Note what parent page references each document
- Highlight important/frequently-referenced documents

#### 4. `complete_index.md`
A comprehensive lightweight index of ALL content:
- Every page listed alphabetically with URL and word count
- Every PDF listed by category with URL and size
- Enables complete search coverage for specific queries
- Size indicators for pages (comprehensive, detailed, brief, minimal)

#### 5. `navigation_guide.md`
A guide to finding specific types of information:
- "How to find..." sections for common queries
- Which pages contain specific topics
- Paths through the site structure
- Search strategy recommendations

### Step 3: Create GPT Instructions

Create `gpt_instructions.md` with:

**Short, focused instructions** (1-2 paragraphs) for a GPT that has access to your reference documents. The instructions should:
- Explain the GPT's role (helping users navigate/understand the municipal website)
- Reference the specific documents created (site_overview.md, page_index.md, etc.)
- Explain how to use those documents to answer user questions
- Guide the GPT on when to provide URLs vs. summaries
- Suggest the GPT can ask for PDFs to be fetched if the user needs details

**Example instruction format:**
> "You are a municipal website assistant with access to a comprehensive catalog of [City Name]'s website. Use `site_overview.md` to understand the overall structure, `page_index.md` to find important pages, `complete_index.md` to search all pages and documents, `document_catalog.md` to locate documents by category, and `navigation_guide.md` to help users find information efficiently. When answering questions, provide relevant URLs and explain what users will find there. If detailed information is in a PDF, provide the PDF URL and offer to analyze it if the user provides it."

## Output Files You Should Create

1. `output/site_overview.md`
2. `output/page_index.md`
3. `output/complete_index.md`
4. `output/document_catalog.md`
5. `output/navigation_guide.md`
6. `output/gpt_instructions.md`

## Success Criteria

Your reference documents should enable a GPT (with no other context) to:
- Answer "Where can I find...?" questions accurately
- Explain what sections/departments exist
- Direct users to relevant pages and documents
- Understand the structure and navigation of the site
- Provide helpful context about what information is available

The GPT instructions should be concise enough to fit in a GPT system prompt while effectively leveraging your detailed reference documents.
