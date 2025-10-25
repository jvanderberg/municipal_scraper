#!/usr/bin/env python3
"""Generate complete_index.md - lightweight index of ALL pages and PDFs"""
import json
from pathlib import Path

# Load analysis
with open('output/analysis.json', 'r') as f:
    analysis = json.load(f)

sections = analysis['sections']
pdf_categories = analysis['pdf_categories']

# Start building the markdown
output = ["# Complete Site Index\n\n"]
output.append("A comprehensive, lightweight index of every page and document on the Village of Oak Park website.\n\n")
output.append(f"**Total Pages**: {sum(len(pages) for pages in sections.values())}\n")
output.append(f"**Total Documents**: {sum(len(pdfs) for pdfs in pdf_categories.values())}\n\n")
output.append("---\n\n")

# All Pages Section
output.append("## All Pages\n\n")
output.append("Complete list of all pages, alphabetically sorted.\n\n")

# Collect all pages
all_pages = []
for section_name, pages in sections.items():
    # Skip language variants
    if section_name in ['Home?Oc_Lang=Tl', 'Home?Oc_Lang=En Us']:
        continue
    for page in pages:
        # Clean up title
        title = page['title'].replace(' | Village of Oak Park', '').strip()
        all_pages.append({
            'title': title,
            'url': page['url'],
            'word_count': page['word_count'],
            'section': section_name
        })

# Sort alphabetically by title
all_pages.sort(key=lambda p: p['title'].lower())

# Write pages
for page in all_pages:
    wc = page['word_count']
    if wc > 800:
        size_indicator = "📖 Comprehensive"
    elif wc > 400:
        size_indicator = "📄 Detailed"
    elif wc > 100:
        size_indicator = "📝 Brief"
    else:
        size_indicator = "⚠️ Minimal"

    output.append(f"- **[{page['title']}]({page['url']})** - {size_indicator} ({wc} words) - *{page['section']}*\n")

output.append("\n---\n\n")

# All Documents Section
output.append("## All Documents\n\n")
output.append("Complete list of all PDF documents, sorted by category then alphabetically.\n\n")

# Process each category
for category in sorted(pdf_categories.keys(), key=lambda c: len(pdf_categories[c]), reverse=True):
    pdfs = pdf_categories[category]
    if not pdfs:
        continue

    cat_name = category.replace('_', ' ').title()
    output.append(f"### {cat_name} ({len(pdfs)} documents)\n\n")

    # Sort PDFs by title
    sorted_pdfs = sorted(pdfs, key=lambda p: p['title'].lower())

    for pdf in sorted_pdfs:
        title = pdf['title'].strip()
        if title == "Untitled PDF" or not title:
            title = pdf['url'].split('/')[-1]

        size_str = f"{pdf['file_size_mb']} MB" if pdf['file_size_mb'] > 0 else "Size unknown"

        output.append(f"- **[{title}]({pdf['url']})** - {size_str}\n")

    output.append("\n")

output.append("---\n\n")

# Statistics
output.append("## Index Statistics\n\n")
output.append(f"- Total Pages: {len(all_pages)}\n")
output.append(f"- Total Documents: {sum(len(pdfs) for pdfs in pdf_categories.values())}\n")
output.append(f"- Sections: {len([s for s in sections.keys() if s not in ['Home?Oc_Lang=Tl', 'Home?Oc_Lang=En Us']])}\n")
output.append(f"- Document Categories: {len([c for c in pdf_categories.keys() if pdf_categories[c]])}\n")
output.append(f"\n**Total Index Size**: ~{len(''.join(output)) / 1024:.0f} KB\n")

# Write the output
output_path = Path('output/complete_index.md')
with open(output_path, 'w') as f:
    f.writelines(output)

print(f"✓ Generated {output_path}")
print(f"  Pages indexed: {len(all_pages)}")
print(f"  Documents indexed: {sum(len(pdfs) for pdfs in pdf_categories.values())}")
print(f"  File size: {output_path.stat().st_size / 1024:.0f} KB")
