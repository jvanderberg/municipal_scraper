#!/usr/bin/env python3
"""Generate document_catalog.md from analysis data"""
import json
import argparse
from pathlib import Path
from collections import defaultdict

# Parse arguments
parser = argparse.ArgumentParser(description='Generate document catalog from analysis')
parser.add_argument('--site-id', type=str, default='', help='Site identifier for multi-site catalogs (e.g., "village", "district97")')
args = parser.parse_args()

# Determine filename prefix
prefix = f"{args.site_id}_" if args.site_id else ""

# Load analysis
with open('output/analysis.json', 'r') as f:
    analysis = json.load(f)

pdf_categories = analysis['pdf_categories']

# Start building the markdown
output = ["# Oak Park Website - Document Catalog\n\n"]
output.append("A comprehensive catalog of PDF documents available on the Village of Oak Park website.\n\n")
output.append(f"**Total Documents**: {sum(len(pdfs) for pdfs in pdf_categories.values())}\n")
output.append(f"**Total Size**: {analysis['statistics']['total_pdfs']} documents cataloged\n\n")
output.append("---\n\n")

# Summary by category
output.append("## Document Categories Summary\n\n")
output.append("| Category | Count |\n")
output.append("|----------|-------|\n")
for category, pdfs in sorted(pdf_categories.items(), key=lambda x: len(x[1]), reverse=True):
    cat_name = category.replace('_', ' ').title()
    output.append(f"| {cat_name} | {len(pdfs)} |\n")
output.append("\n---\n\n")

# Detailed sections
category_descriptions = {
    'financial': "Budget documents, financial reports, audits, and fiscal transparency documents.",
    'meeting_minutes': "Meeting minutes, agendas, and proceedings from Village Board and commissions.",
    'policies': "Official village policies, protocols, procedures, and guidelines.",
    'memos': "Memos from the Village Manager to the Village President on various operational matters.",
    'planning': "Planning documents, zoning information, and development plans.",
    'reports': "Various official reports including studies, assessments, and analyses.",
    'ordinances': "Village ordinances, resolutions, and legislation.",
    'notices': "Official public notices and announcements.",
    'other': "Miscellaneous documents that don't fit into specific categories."
}

for category, pdfs in sorted(pdf_categories.items(), key=lambda x: len(x[1]), reverse=True):
    cat_name = category.replace('_', ' ').title()
    output.append(f"## {cat_name}\n\n")

    if category in category_descriptions:
        output.append(f"*{category_descriptions[category]}*\n\n")

    output.append(f"**Total Documents**: {len(pdfs)}\n\n")

    # Group by parent page for better organization
    by_parent = defaultdict(list)
    for pdf in pdfs:
        parent = pdf.get('parent_page', 'Unknown')
        by_parent[parent].append(pdf)

    # Show documents grouped by parent page (top 10 parent pages)
    sorted_parents = sorted(by_parent.items(), key=lambda x: len(x[1]), reverse=True)

    for parent_url, parent_pdfs in sorted_parents[:10]:
        # Clean up parent page name
        parent_name = parent_url.replace('https://www.oak-park.us/', '').replace('https://oak-park.us/', '')
        parent_name = parent_name.replace('/', ' › ').replace('-', ' ').title()

        output.append(f"### {parent_name}\n")
        output.append(f"*Source: {parent_url}*\n\n")

        # List PDFs from this parent (limit to 10)
        for pdf in parent_pdfs[:10]:
            title = pdf['title'].strip()
            if title == "Untitled PDF" or not title:
                title = pdf['url'].split('/')[-1]

            size_str = f"{pdf['file_size_mb']} MB" if pdf['file_size_mb'] > 0 else "Unknown size"

            output.append(f"- **{title}**\n")
            output.append(f"  - URL: {pdf['url']}\n")
            output.append(f"  - Size: {size_str}\n")

            if pdf.get('last_modified'):
                output.append(f"  - Last Modified: {pdf['last_modified']}\n")
            output.append("\n")

        if len(parent_pdfs) > 10:
            output.append(f"  *...and {len(parent_pdfs) - 10} more documents*\n\n")

    if len(sorted_parents) > 10:
        remaining_docs = sum(len(pdfs) for _, pdfs in sorted_parents[10:])
        output.append(f"\n*...and {remaining_docs} more documents from other pages*\n\n")

    output.append("---\n\n")

# Key document finder section
output.append("## Finding Specific Documents\n\n")
output.append("### Most Common Document Locations\n\n")

# Identify pages with most documents
all_pdfs = [pdf for pdfs in pdf_categories.values() for pdf in pdfs]
by_parent_all = defaultdict(list)
for pdf in all_pdfs:
    by_parent_all[pdf.get('parent_page', 'Unknown')].append(pdf)

sorted_all_parents = sorted(by_parent_all.items(), key=lambda x: len(x[1]), reverse=True)

output.append("These pages contain the most documents:\n\n")
for parent_url, parent_pdfs in sorted_all_parents[:10]:
    parent_name = parent_url.replace('https://www.oak-park.us/', '').replace('https://oak-park.us/', '')
    parent_name = parent_name.replace('/', ' › ').replace('-', ' ').title()
    output.append(f"- **{parent_name}**: {len(parent_pdfs)} documents\n")
    output.append(f"  - {parent_url}\n\n")

# Write the output
# Ensure analysis directory exists
Path('output/analysis').mkdir(parents=True, exist_ok=True)
output_path = Path(f'output/analysis/{prefix}document_catalog.md')
with open(output_path, 'w') as f:
    f.writelines(output)

print(f"✓ Generated {output_path}")
