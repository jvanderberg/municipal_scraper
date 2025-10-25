# Claude Prompt: Multi-Site Community Catalog and Analysis

## Overview

You will catalog multiple websites for a community (government, schools, parks, library, news, etc.) and create a unified GPT assistant that helps residents navigate all community information.

## Workflow

### Phase 1: Understand the Community (Read community.md)
### Phase 2: Discover Sites (Create sites_config.yaml)
### Phase 3: Scrape All Sites (Run municipal scraper)
### Phase 4: Analyze Each Site (Create site-specific indexes)
### Phase 5: Cross-Site Synthesis (Create unified navigation)
### Phase 6: Create GPT Instructions (Unified assistant)

---

## Phase 1: Understand the Community

**Read `community.md`** - A plain text file describing the community and its organizations.

The file will include:
- Community name and overview
- Key organizations (government, schools, parks, library, news, etc.)
- URLs (if known)
- Description of what to catalog from each site
- Any special instructions

**Example format**:
```
# Oak Park, Illinois

## Village Government
Website: https://oak-park.us
What to catalog: All departments, services, meetings, permits

## School District 97
Serves K-8 students
Website: https://www.op97.org
What to catalog: Enrollment, calendar, board meetings, policies
```

**Your task**:
1. Read and understand the community structure
2. Identify all organizations that need cataloging
3. Note which URLs are provided and which are missing

---

## Phase 2: Discover Sites

**Create `sites_config.yaml`** with structured information about each site.

### For sites WITH URLs provided:
- Use the URL from community.md

### For sites WITHOUT URLs:
- Search the web to find the official website
- Verify it's the correct organization
- Document what you found

### sites_config.yaml Format:

```yaml
community:
  name: "Oak Park, Illinois"
  description: "Comprehensive community information assistant"

sites:
  - id: village              # Short identifier (used for output directory)
    name: Village of Oak Park
    url: https://oak-park.us
    type: government         # government, school, recreation, library, news
    description: Official village government - permits, services, meetings, ordinances
    scrape_config:
      max_depth: 3           # Crawl depth (default: 3)
      delay: 1.0             # Rate limiting (default: 1.0)

  - id: district97
    name: Oak Park Elementary School District 97
    url: https://www.op97.org
    type: school
    description: Public elementary schools (K-8) - enrollment, calendar, policies

  - id: park_district
    name: Oak Park Park District
    url: https://www.pdop.org
    type: recreation
    description: Parks, recreation programs, facilities, sports leagues
```

**Write this file** before proceeding.

---

## Phase 3: Scrape All Sites

For each site in `sites_config.yaml`, run the municipal scraper:

```bash
# For each site:
./run.sh <url> --output output/<site-id> --max-depth <depth> --delay <delay>
```

**Example**:
```bash
./run.sh https://oak-park.us --output output/village --max-depth 3
./run.sh https://www.op97.org --output output/district97 --max-depth 3
./run.sh https://www.pdop.org --output output/park_district --max-depth 3
```

This creates:
```
output/
├── village/
│   ├── site_metadata.json
│   ├── pages/
│   └── pdfs/
├── district97/
│   ├── site_metadata.json
│   ├── pages/
│   └── pdfs/
└── park_district/
    ├── site_metadata.json
    ├── pages/
    └── pdfs/
```

**Run these in sequence**, reporting progress for each site.

---

## Phase 4: Analyze Each Site

For each site catalog in `output/`, create site-specific reference documents.

### Run analysis tools:

```bash
# For each site directory, run from the repo root:
# (Replace <site-id> with: village, district97, park_district, etc.)

cd output/<site-id>
python3 ../../analyze_catalog.py
cd ../..

python3 generate_page_index.py --site-id <site-id>
python3 generate_complete_index.py --site-id <site-id>
python3 generate_document_catalog.py --site-id <site-id>
```

**Example for village site:**
```bash
cd output/village
python3 ../../analyze_catalog.py
cd ../..

python3 generate_page_index.py --site-id village
python3 generate_complete_index.py --site-id village
python3 generate_document_catalog.py --site-id village
```

This creates files like: `output/analysis/village_page_index.md`, `output/analysis/village_complete_index.md`, etc.

### Create site-specific documents:

For each site, create in `output/analysis/` with prefixed filenames:

1. **`{site-id}_site_overview.md`**
   - Organization name and purpose
   - Main sections/departments
   - Content types available
   - Key areas of interest
   - **How this organization fits in the community**

2. **`{site-id}_page_index.md`**
   - Organized index of important pages
   - Grouped by topic/department
   - Top ~15 pages per section

3. **`{site-id}_complete_index.md`**
   - ALL pages alphabetically
   - ALL documents by category
   - For comprehensive search

4. **`{site-id}_document_catalog.md`**
   - PDFs organized by category
   - Grouped by parent page

5. **`{site-id}_navigation_guide.md`**
   - "How to find..." for this organization
   - Common user scenarios
   - Topic-specific guidance

**Example**: `output/analysis/village_site_overview.md`, `output/analysis/district97_site_overview.md`, etc.

**Note**: All analysis files go in a single `output/analysis/` directory with site-prefixed names because GPT file uploads don't preserve directory structure.

---

## Phase 5: Cross-Site Synthesis

Create community-wide documents in `output/analysis/`:

### 1. `community_overview.md`

High-level view of the entire community information ecosystem:

```markdown
# Oak Park Community Information Overview

## Community Structure
- Population, location, character
- How organizations are organized
- Key community values/priorities

## Organizations Cataloged

### Village Government
Purpose: Municipal services, permits, public safety
Pages: 228 | Documents: 1,236
Key services: Parking, utilities, building permits, public meetings
→ See village_site_overview.md and village_complete_index.md for details

### School District 97
Purpose: K-8 public education
Pages: XX | Documents: XX
Key information: Enrollment, calendar, curriculum, board meetings
→ See district97_site_overview.md and district97_complete_index.md for details

[... for each organization ...]

## How to Navigate This Information

- **For village services**: Start with village_site_overview.md and village_complete_index.md
- **For school information**: Check district97_*.md or district200_*.md files
- **For recreation programs**: See park_district_*.md files
- **For recent community news**: Check news_*.md files

## Cross-Organization Topics

Some topics span multiple organizations:

- **Youth Programs**: Park District (sports/rec), Schools (academics), Library (programs)
- **Community Events**: All organizations host events - check each calendar
- **Facilities**: Village (permits), Schools (buildings), Park District (facilities)
- **Meetings**: Each organization has its own board - different schedules
```

### 2. `cross_site_navigation.md`

Guide for finding information across organizations:

```markdown
# Finding Information Across Oak Park

## Common Scenarios

### "I want to enroll my child in school"
→ **District 97** (K-8): district97_complete_index.md - search for "enrollment"
→ **District 200** (HS): district200_complete_index.md - search for "enrollment"

### "I need a building permit"
→ **Village**: village_complete_index.md - search Building & Business section

### "I want to sign up for youth sports"
→ **Park District**: park_district_complete_index.md - search for "recreation programs"

### "When is my garbage picked up?"
→ **Village**: village_complete_index.md - search Services-Parking section

### "What's the school calendar?"
→ **District 97** or **District 200**: respective complete_index.md files

## Topic Guide

**Public Safety**
- Village: Police, Fire, Emergency Management
- Schools: School safety policies, resource officers

**Recreation & Youth**
- Park District: Sports leagues, camps, programs
- Schools: After-school programs, athletics
- Library: Youth programs, homework help

**Meetings & Government**
- Village: Village Board, commissions
- Schools: School board meetings (separate for D97 and D200)
- Park District: Park Board meetings

**Facilities**
- Village: Building permits, inspections
- Park District: Park facilities, rental spaces
- Library: Meeting rooms, facilities

**Events**
- Village: Community events, public meetings
- Schools: School events, performances
- Park District: Recreation events
- Library: Programs and events
- News: Community calendar and coverage
```

### 3. `community_index.md`

Master index spanning all sites - organized by topic:

```markdown
# Oak Park Community Master Index

## By Topic

### Education
- [School District 97 Enrollment](url) - District 97
- [High School Programs](url) - District 200
- [School Calendar D97](url) - District 97
- [High School Athletics](url) - District 200

### Recreation
- [Park District Programs](url) - Park District
- [Youth Sports](url) - Park District
- [Library Programs](url) - Library

### Village Services
- [Parking Permits](url) - Village
- [Building Permits](url) - Village
- [Waste & Recycling](url) - Village

[... comprehensive topic-organized index ...]
```

---

## Phase 6: Create GPT Instructions

Create `output/analysis/gpt_instructions.md` - The system prompt for the unified GPT.

### Key Principles

The GPT has access to (all files in the analysis/ directory):
- **community_overview.md** - High-level structure
- **cross_site_navigation.md** - How to route questions
- **community_index.md** - Master topic index
- **{site-id}_complete_index.md** - Comprehensive search per site
- **{site-id}_site_overview.md** - Each organization's structure
- **{site-id}_page_index.md** - Curated important pages per site
- **{site-id}_document_catalog.md** - PDFs per site
- **{site-id}_navigation_guide.md** - How-to guide per site

### Instructions Structure

```markdown
# GPT Instructions: Oak Park Community Assistant

## Your Role

You are a comprehensive community information assistant for Oak Park, Illinois. You help residents navigate information across multiple community organizations:

- Village Government (municipal services)
- School Districts (education)
- Park District (recreation)
- Library (library services)
- Local News (community context)

## Your Knowledge Base

You have complete catalogs of multiple community websites:

### Community-Wide Documents:
1. **community_overview.md** - Understand which organization handles what
2. **cross_site_navigation.md** - Route questions to the right organization
3. **community_index.md** - Master index organized by topic

### Site-Specific Documents (for each organization):
1. **{site-id}_site_overview.md** - Organization structure and purpose
2. **{site-id}_complete_index.md** - Complete searchable index
3. **{site-id}_page_index.md** - Important pages (curated)
4. **{site-id}_document_catalog.md** - PDFs and documents
5. **{site-id}_navigation_guide.md** - How to find information

(Where {site-id} is: village, district97, park_district, library, news, etc.)

## How to Assist Users

### 1. Determine Which Organization(s) to Use

**Use cross_site_navigation.md** to route questions:
- Village services (permits, utilities, parking) → Village catalog
- School information (enrollment, calendar) → District 97 or District 200
- Recreation programs → Park District
- Library services → Library
- Recent news/context → News

### 2. Search the Appropriate Catalog(s)

Once you know which organization:
- Use that site's **{site-id}_complete_index.md** for comprehensive search
- Use **{site-id}_page_index.md** for curated important pages
- Use **{site-id}_navigation_guide.md** for common scenarios

### 3. Provide Helpful, Synthesized Answers

**Don't just provide links** - Explain and guide:

✅ GOOD:
> "To enroll your child in elementary school, you'll work with Oak Park School District 97. They handle K-8 education. The enrollment process requires proof of residency, birth certificate, and immunization records. You can find the enrollment page at [URL], which includes downloadable forms and detailed requirements. The district also offers an online enrollment option. If you have a high-schooler, that's a separate district (District 200) with its own enrollment process."

❌ NOT THIS:
> "For school enrollment, visit [URL]"

### 4. Cross-Reference When Appropriate

Many topics span organizations:
- Youth programs → Park District AND Schools AND Library
- Community events → Check all organizations
- Facilities/buildings → Village (permits) AND Park District (facilities)

### 5. Provide Context from News

When relevant, reference recent news coverage:
> "According to recent Wednesday Journal coverage, the village is currently working on [project]. For official details and how to provide input, see [village URL]..."

## Response Style

- **Helpful and conversational**, like a knowledgeable community member
- **Guide users to the right organization** - don't make them guess
- **Synthesize across multiple pages** when needed
- **Compare options** (e.g., different programs, different schools)
- **Provide context** about how things work in this community
- **Anticipate related needs** - suggest related information proactively
- **Include URLs** for details, but explain what they'll find first

## Organization Boundaries

Be clear about which organization handles what:
- "That's handled by the Park District, not the Village..."
- "The schools have their own board meetings separate from Village Board meetings..."
- "Each district has its own calendar and policies..."

## Your Goal

Help residents navigate Oak Park's community resources efficiently. You know the entire information landscape and can guide them to exactly what they need, explaining along the way.

Feel like talking to someone who knows Oak Park inside and out - not a search engine.
```

---

## Output Structure

After completing all phases, you should have:

```
output/
├── sites_config.yaml                 # Site configuration
│
├── village/                          # Village government raw data
│   ├── site_metadata.json
│   ├── pages/
│   ├── pdfs/
│   ├── site_graph.json
│   └── .crawl_state.json
│
├── district97/                       # Elementary school raw data
│   ├── site_metadata.json
│   ├── pages/
│   └── [... same structure ...]
│
├── park_district/                    # Park district raw data
│   └── [... same structure ...]
│
├── [... additional sites ...]
│
└── analysis/                         # All GPT-ready documents (UPLOAD THIS FOLDER)
    ├── community_overview.md
    ├── cross_site_navigation.md
    ├── community_index.md
    ├── gpt_instructions.md
    ├── village_site_overview.md
    ├── village_complete_index.md
    ├── village_page_index.md
    ├── village_document_catalog.md
    ├── village_navigation_guide.md
    ├── district97_site_overview.md
    ├── district97_complete_index.md
    ├── district97_page_index.md
    ├── district97_document_catalog.md
    ├── district97_navigation_guide.md
    ├── park_district_site_overview.md
    └── [... all other site-prefixed files ...]
```

**Note**: The `analysis/` directory contains all files ready for GPT upload. Each site's analysis files use the site-id as a prefix to avoid filename conflicts since GPT uploads don't preserve directory structure.

## Files for GPT Knowledge Base

Upload the entire `output/analysis/` directory to your GPT. All files are in one location with no subdirectories.

**Community-wide files**:
1. community_overview.md
2. cross_site_navigation.md
3. community_index.md
4. gpt_instructions.md (use this as your GPT's system prompt)

**Site-specific files (one set per organization)**:
5. {site-id}_site_overview.md
6. {site-id}_complete_index.md
7. {site-id}_page_index.md
8. {site-id}_document_catalog.md
9. {site-id}_navigation_guide.md

(Repeat for each site: village, district97, park_district, library, news, etc.)

**Total**: ~3-4 MB for a typical community with 5-6 organizations (well within GPT limits)

**To upload**: Simply select all files in the `output/analysis/` directory when creating your GPT's knowledge base.

---

## Success Criteria

The unified GPT should:
- ✅ Know which organization handles what
- ✅ Route questions to the appropriate site catalog
- ✅ Search comprehensively across all relevant sites
- ✅ Synthesize information from multiple organizations
- ✅ Explain processes that span organizations
- ✅ Provide context about how the community works
- ✅ Guide users through multi-step processes
- ✅ Feel like a knowledgeable community member, not a search engine

**The user should never have to know which organization's website to check** - the GPT figures that out and provides the answer.

---

## Getting Started

1. User creates `community.md` describing their community
2. User runs: "Please read community.md and create a complete community information catalog"
3. You execute all 6 phases above
4. User uploads the reference documents to create their GPT
