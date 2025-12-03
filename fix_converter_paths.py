import os
import glob

def fix_html_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    original_content = content

    replacements = {
        # Service Worker
        "navigator.serviceWorker.register('/sw.js')": "navigator.serviceWorker.register('/converter/sw.js')",

        # Assets, manifest, components
        'href="/assets/': 'href="/converter/assets/',
        'src="/assets/': 'src="/converter/assets/',
        'content="/assets/': 'content="/converter/assets/',
        'href="/manifest.json"': 'href="/converter/manifest.json"',
        'href="/sitemap.css': 'href="/converter/sitemap.css',
        'href="/style.css': 'href="/converter/style.css',
        
        # JS files
        'src="/feature-flags.js': 'src="/converter/feature-flags.js',
        'src="/url-router.js': 'src="/converter/url-router.js',
        'src="/converter-engine.js': 'src="/converter/converter-engine.js',
        'src="/script.js': 'src="/converter/script.js',
        'src="/i18n.js': 'src="/converter/i18n.js',
        'src="/locales.js': 'src="/converter/locales.js',
        'src="/nav-common.js': 'src="/converter/nav-common.js',
        
        # Batch conversion JS
        'src="/batch-conversion-': 'src="/converter/batch-conversion-',
        'href="/batch-conversion-': 'href="/converter/batch-conversion-',

        # Nav links
        'href="/how-to-use.html"': 'href="/converter/how-to-use.html"',
        'href="/faq.html"': 'href="/converter/faq.html"',
        'href="/api.html"': 'href="/converter/api.html"',
        'href="/sitemap.html"': 'href="/converter/sitemap.html"',
        'href="/" class="converter-logo-link"': 'href="/converter/" class="converter-logo-link"',
    }

    for old, new in replacements.items():
        content = content.replace(old, new)

    # Special handling for root links that are not the logo
    content = content.replace('href="/" class="nav-link"', 'href="/converter/" class="nav-link"')
    content = content.replace('href="/" class="mobile-menu-link"', 'href="/converter/" class="mobile-menu-link"')

    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed paths in {file_path}")
        except Exception as e:
            print(f"Error writing to {file_path}: {e}")


def main():
    # Use a relative path to make the script more portable
    frontend_dir = os.path.join('converter', 'frontend')
    if not os.path.isdir(frontend_dir):
        print(f"Directory not found: {frontend_dir}")
        return

    # Using glob to find all HTML files recursively
    html_files = glob.glob(os.path.join(frontend_dir, '**', '*.html'), recursive=True)
    
    print(f"Found {len(html_files)} HTML files to process.")

    for file_path in html_files:
        fix_html_file(file_path)
    
    print("Done fixing HTML files.")

if __name__ == "__main__":
    main()