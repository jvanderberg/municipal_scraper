#!/usr/bin/env python3
"""Generate page_index.md from analysis data"""
import json
from pathlib import Path

# Load analysis
with open('output/analysis.json', 'r') as f:
    analysis = json.load(f)

sections = analysis['sections']
key_pages = analysis['key_pages']

# Start building the markdown
output = ["# Oak Park Website - Page Index\n"]
output.append("An organized index of important pages on the Village of Oak Park website.\n")
output.append(f"**Total Pages**: {len([p for pages in sections.values() for p in pages])}\n")
output.append("---\n\n")

# Table of Contents
output.append("## Table of Contents\n")
for i, section in enumerate(sections.keys(), 1):
    if section not in ['Home?Oc_Lang=Tl', 'Home?Oc_Lang=En Us']:  # Skip language variants
        anchor = section.lower().replace(' ', '-').replace('?', '').replace('=', '')
        output.append(f"{i}. [{section}](#{anchor})\n")
output.append("\n---\n\n")

# Main Sections
for section_name, pages in sections.items():
    # Skip language variant sections
    if section_name in ['Home?Oc_Lang=Tl', 'Home?Oc_Lang=En Us']:
        continue

    output.append(f"## {section_name}\n\n")
    output.append(f"*{len(pages)} pages in this section*\n\n")

    # Sort pages by word count (most substantial first)
    sorted_pages = sorted(pages, key=lambda p: p['word_count'], reverse=True)

    # Take top 15 pages per section or all if fewer
    top_pages = sorted_pages[:15]

    for page in top_pages:
        # Clean up the title
        title = page['title'].replace(' | Village of Oak Park', '').strip()

        # Check if page has PDFs
        has_pdfs = any(link['type'] == 'pdf' for link in page['links'])
        pdf_marker = " 📄" if has_pdfs else ""

        # Word count indicator
        if page['word_count'] > 800:
            length = "Comprehensive"
        elif page['word_count'] > 400:
            length = "Detailed"
        else:
            length = "Brief"

        output.append(f"### {title}{pdf_marker}\n")
        output.append(f"**URL**: {page['url']}\n\n")
        output.append(f"**Content**: {length} ({page['word_count']} words)\n\n")

        # Add key headings if available
        if page['headings']:
            main_headings = [h for h in page['headings'] if h['level'] in ['h1', 'h2']]
            if main_headings:
                output.append("**Topics Covered**:\n")
                for heading in main_headings[:5]:
                    output.append(f"- {heading['text']}\n")
                output.append("\n")

        output.append("---\n\n")

    # If there are more pages, note it
    if len(sorted_pages) > 15:
        output.append(f"*...and {len(sorted_pages) - 15} more pages in this section*\n\n")

# Write the output
output_path = Path('output/page_index.md')
with open(output_path, 'w') as f:
    f.writelines(output)

print(f"✓ Generated {output_path}")
