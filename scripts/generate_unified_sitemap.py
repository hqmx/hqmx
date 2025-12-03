import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime

# --- Configuration ---
BASE_URL = "https://hqmx.net"
# Adjust PROJECT_ROOT to the absolute path of /Users/wonjunjang/hqmx
# For local execution, this should be the root of the hqmx repository.
PROJECT_ROOT = "/Users/wonjunjang/hqmx"
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'scripts', 'output') # Output sitemaps into scripts/output

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Languages from main/frontend/api.html (updated)
LANGUAGES = [
    'en', 'ko', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'zh-CN', 'zh-TW',
    'ar', 'hi', 'nl', 'sv', 'pl', 'tr', 'vi', 'th', 'id', 'he', 'cs', 'bn', 'my', 'ms', 'fil'
]
NAVER_LANG = 'ko'

# --- Helper Functions ---
def generate_sitemap_xml(urls, filename):
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url_data in urls:
        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = url_data["loc"]
        ET.SubElement(url_elem, "lastmod").text = url_data["lastmod"]
        ET.SubElement(url_elem, "changefreq").text = url_data["changefreq"]
        ET.SubElement(url_elem, "priority").text = url_data["priority"]

    tree = ET.ElementTree(urlset)
    # Pretty print XML
    ET.indent(tree, space="  ", level=0)
    tree.write(os.path.join(OUTPUT_DIR, filename), encoding="utf-8", xml_declaration=True)
    print(f"Generated {filename} with {len(urls)} URLs.")

def get_today_date():
    return datetime.now().isoformat().split('T')[0]

def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: JSON file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {file_path}")
        return None

def read_markdown_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Markdown file not found at {file_path}")
        return None

# --- URL Collection Functions ---

def get_main_urls():
    """Collects URLs for the main project."""
    urls = []
    today = get_today_date()
    # Base pages (some have .html suffix, some don't based on architecture doc)
    # For main, the sitemap needs to reflect how they are actually accessed.
    # main/index.html is accessed as hqmx.net/
    # main/terms.html is accessed as hqmx.net/terms.html
    # main/privacy.html is accessed as hqmx.net/privacy.html
    # main/api.html is accessed as hqmx.net/api.html (confirmed from main/frontend/api.html links)

    # hqmx.net/
    urls.append({
        "loc": BASE_URL + "/",
        "lastmod": today,
        "changefreq": "daily",
        "priority": "1.0"
    })
    # hqmx.net/terms.html
    urls.append({
        "loc": f"{BASE_URL}/terms.html",
        "lastmod": today,
        "changefreq": "monthly",
        "priority": "0.8"
    })
    # hqmx.net/privacy.html
    urls.append({
        "loc": f"{BASE_URL}/privacy.html",
        "lastmod": today,
        "changefreq": "monthly",
        "priority": "0.8"
    })
    # hqmx.net/api.html
    urls.append({
        "loc": f"{BASE_URL}/api.html",
        "lastmod": today,
        "changefreq": "weekly",
        "priority": "0.9"
    })
    return urls

def get_converter_urls():
    """Collects URLs for the converter project."""
    urls = []
    today = get_today_date()
    # Corrected path for conversions.json
    conversions_path = os.path.join(PROJECT_ROOT, 'converter', 'frontend', '_scripts', 'conversions.json')
    conversions = read_json_file(conversions_path)

    if not conversions:
        return []

    conversion_pages = [c for c in conversions if not c.get('category') or (
        'compression' not in c['category'] and
        c['category'] != 'optimization' and
        c['category'] != 'resize' and
        c['category'] != 'compress-convert'
    )]
    compression_pages = [c for c in conversions if c.get('category') and (
        'compression' in c['category'] or
        c['category'] == 'optimization' or
        c['category'] == 'resize' or
        c['category'] == 'compress-convert'
    )]

    # Add base converter page
    urls.append({
        "loc": f"{BASE_URL}/converter/",
        "lastmod": today,
        "changefreq": "daily",
        "priority": "1.0"
    })
    # Add converter API page
    urls.append({
        "loc": f"{BASE_URL}/converter/api.html",
        "lastmod": today,
        "changefreq": "weekly",
        "priority": "0.9"
    })

    for lang in LANGUAGES:
        for conv in conversion_pages:
            from_fmt = conv['from']
            to_fmt = conv['to']
            # Corrected URL construction to include /converter/ prefix
            loc = f"{BASE_URL}/converter/{from_fmt}-to-{to_fmt}.html" if lang == 'en' else f"{BASE_URL}/converter/{from_fmt}-to-{to_fmt}-{lang}.html"
            urls.append({
                "loc": loc,
                "lastmod": today,
                "changefreq": "monthly",
                "priority": "0.7"
            })
        for comp in compression_pages:
            from_fmt = comp['from']
            to_fmt = comp['to']
            type_fmt = comp['type']
            loc = ""
            if type_fmt == 'compress':
                if from_fmt == to_fmt:
                    loc = f"{BASE_URL}/converter/compress-{from_fmt}.html" if lang == 'en' else f"{BASE_URL}/converter/compress-{from_fmt}-{lang}.html"
                else:
                    loc = f"{BASE_URL}/converter/{from_fmt}-to-{to_fmt}-compress.html" if lang == 'en' else f"{BASE_URL}/converter/{from_fmt}-to-{to_fmt}-compress-{lang}.html"
            elif type_fmt == 'optimize':
                loc = f"{BASE_URL}/converter/optimize-{from_fmt}.html" if lang == 'en' else f"{BASE_URL}/converter/optimize-{from_fmt}-{lang}.html"
            elif type_fmt == 'resize':
                loc = f"{BASE_URL}/converter/resize-{from_fmt}.html" if lang == 'en' else f"{BASE_URL}/converter/resize-{from_fmt}-{lang}.html"
            if loc:
                urls.append({
                    "loc": loc,
                    "lastmod": today,
                    "changefreq": "weekly",
                    "priority": "0.9"
                })
    return urls

def get_downloader_urls():
    """Collects URLs for the downloader project."""
    urls = []
    today = get_today_date()
    downloader_frontend_path = os.path.join(PROJECT_ROOT, 'downloader', 'frontend')

    # Add base downloader page
    urls.append({
        "loc": f"{BASE_URL}/downloader/",
        "lastmod": today,
        "changefreq": "daily",
        "priority": "1.0"
    })

    # Verify and add other static pages if they exist
    potential_pages = ["privacy.html", "terms.html", "api.html"]
    for page in potential_pages:
        if os.path.exists(os.path.join(downloader_frontend_path, page)):
            urls.append({
                "loc": f"{BASE_URL}/downloader/{page}",
                "lastmod": today,
                "changefreq": "monthly",
                "priority": "0.8"
            })
    return urls

def get_generator_urls():
    """Collects URLs for the generator project."""
    urls = []
    today = get_today_date()
    generator_frontend_path = os.path.join(PROJECT_ROOT, 'generator', 'frontend')

    # Add base generator page
    urls.append({
        "loc": f"{BASE_URL}/generator/",
        "lastmod": today,
        "changefreq": "daily",
        "priority": "1.0"
    })

    # Scan generator/frontend for .html files (excluding index.html)
    for root, _, files in os.walk(generator_frontend_path):
        for file in files:
            if file.endswith('.html') and file != 'index.html':
                # Construct path relative to generator/frontend/
                relative_path = os.path.relpath(os.path.join(root, file), generator_frontend_path)
                urls.append({
                    "loc": f"{BASE_URL}/generator/{relative_path}",
                    "lastmod": today,
                    "changefreq": "monthly",
                    "priority": "0.0" # Default low priority, to be adjusted
                })
    return urls


def get_calculator_urls():
    """Collects URLs for the calculator project."""
    urls = []
    today = get_today_date()
    calculator_root = os.path.join(PROJECT_ROOT, 'calculator', 'frontend')

    # Add base calculator page
    urls.append({
        "loc": f"{BASE_URL}/calculator/",
        "lastmod": today,
        "changefreq": "daily",
        "priority": "1.0"
    })

    # Parse GEMINI.md files for calculator URLs (categories and url_slugs)
    categories = ['conversion', 'date-time', 'finance', 'general', 'health']
    for category in categories:
        gemini_path = os.path.join(calculator_root, category, 'GEMINI.md')
        content = read_markdown_file(gemini_path)

        if not content:
            continue

        import re
        # Find url_slugs from Metadata sections
        url_slugs = re.findall(r'url_slug:\s*"([^"]+)"', content)

        for slug in url_slugs:
            # According to calculator/GEMINI.md, the URL structure for language is /calculator/{lang}/{slug}
            for lang in LANGUAGES:
                # English URLs do not have /en/ prefix
                loc = f"{BASE_URL}/calculator/{slug}"
                if lang != 'en':
                    loc = f"{BASE_URL}/calculator/{lang}/{slug}"

                urls.append({
                    "loc": loc,
                    "lastmod": today,
                    "changefreq": "weekly",
                    "priority": "0.7"
                })
    return urls

# --- Main Script ---
def main():
    all_urls = []

    print("Collecting URLs from main project...")
    all_urls.extend(get_main_urls())

    print("Collecting URLs from converter project...")
    all_urls.extend(get_converter_urls())

    print("Collecting URLs from downloader project...")
    all_urls.extend(get_downloader_urls())

    print("Collecting URLs from generator project...")
    all_urls.extend(get_generator_urls())

    print("Collecting URLs from calculator project...")
    all_urls.extend(get_calculator_urls())

    # Generate full sitemap.xml
    generate_sitemap_xml(all_urls, "sitemap.xml")

    # Generate sitemap-naver.xml (main pages + Korean versions)
    naver_urls = []
    for url_data in all_urls:
        loc = url_data['loc']
        # 1. Main project base URLs (always included)
        if loc in [f"{BASE_URL}/", f"{BASE_URL}/terms.html", f"{BASE_URL}/privacy.html", f"{BASE_URL}/api.html"]:
            naver_urls.append(url_data)
        # 2. Other project URLs (converter, downloader, generator, calculator)
        #    Include if:
        #    a) it's a Korean version (ends with -ko.html or contains /ko/ for calculator)
        #    b) it's the base URL for the project itself (e.g., /converter/, /downloader/, /generator/, /calculator/)
        #    c) it's a specific static page (privacy.html, terms.html, api.html) within downloader and NAVER_LANG is 'ko'
        elif "/converter/" in loc:
            if loc.endswith(f"-{NAVER_LANG}.html") or loc == f"{BASE_URL}/converter/":
                naver_urls.append(url_data)
        elif "/downloader/" in loc:
            if loc.endswith(f"-{NAVER_LANG}.html") or loc == f"{BASE_URL}/downloader/" or \
               (NAVER_LANG == 'ko' and loc == f"{BASE_URL}/downloader/privacy.html") or \
               (NAVER_LANG == 'ko' and loc == f"{BASE_URL}/downloader/terms.html") or \
               (NAVER_LANG == 'ko' and loc == f"{BASE_URL}/downloader/api.html"):
                 naver_urls.append(url_data)
        elif "/generator/" in loc:
            # For generator, we assume generated pages follow the pattern /generator/{pagename}-{lang}.html
            # or it's the base /generator/
            if loc.endswith(f"-{NAVER_LANG}.html") or loc == f"{BASE_URL}/generator/":
                naver_urls.append(url_data)
            # Also include base static generator pages if they exist, and they are not language specific (or if they are in ko)
            elif NAVER_LANG == 'ko' and loc.startswith(f"{BASE_URL}/generator/") and not any(f"-{lang}.html" in loc for lang in LANGUAGES if lang != 'en' and lang != 'ko'):
                # This is a bit tricky, needs careful consideration for non-language specific pages.
                # For now, let's keep it simple and only include explicitly Korean or base pages for generator.
                pass
        elif "/calculator/" in loc:
            # Calculator URLs are like hqmx.net/calculator/ko/slug or hqmx.net/calculator/slug
            # So, we check for /calculator/ko/ in the path or if it's the base /calculator/
            if f"/calculator/{NAVER_LANG}/" in loc or loc == f"{BASE_URL}/calculator/":
                naver_urls.append(url_data)

    generate_sitemap_xml(naver_urls, "sitemap-naver.xml")

if __name__ == "__main__":
    main()
