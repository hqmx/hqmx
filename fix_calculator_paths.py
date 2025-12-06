import os
import re

def fix_html_paths(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Function to replace paths
    def replace_path(match):
        full_attr = match.group(0)
        attr_name = match.group(1)
        path = match.group(2)
        
        # Exclude external links and mailto and javascript
        if path.startswith(('http://', 'https://', 'mailto:', '//', '#', 'javascript:')):
            return full_attr

        # Already correctly prefixed
        if path.startswith('/calculator/'):
            return full_attr

        # Absolute path without /calculator/ (e.g., /css/style.css -> /calculator/css/style.css)
        if path.startswith('/'):
            # Only prefix if the path is not already correct
            if not path.startswith('/calculator/'):
                return full_attr.replace(path, f'/calculator{path}')
        
        # Relative path (e.g., "style.css", "../assets/img.png")
        # For relative paths, we need to be careful. The current Nginx setup expects absolute paths from the root.
        # So, if a relative path is found and it's a resource (css, js, image), we assume it should be prefixed with /calculator/
        # This might require manual verification if relative paths are complex.
        # For now, we'll prefix simple relative paths to make them absolute under /calculator/
        # This will mainly affect paths that are just "style.css" or "assets/..."
        # If it's a file, it's likely a resource that needs the prefix.
        if not path.startswith('/') and (path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.json', '.html')) or re.match(r'[^/]+\.js\?v=', path)):
            return full_attr.replace(path, f'/calculator/{path}')

        return full_attr

    # Regex to find href and src attributes, excluding data-attributes and other protocols
    # It captures the attribute name and the path within the attribute
    # Updated regex to handle query parameters (e.g., ?v=...) and more file extensions
    content = re.sub(r'(href|src)=["\'](?!data:|#|javascript:)(?!https?://)(?!//)((?:/[^"\\]*)?|[^"\\]*\.(?:css|js|png|jpg|jpeg|gif|svg|webp|ico|json|html)(?:\?v=[^"\\]*)?)["\\]', replace_path, content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Modified: {file_path}")
        return True
    return False

html_files = [
    "calculator/frontend/index.html",
    "calculator/frontend/construction/concrete-calculator.html",
    "calculator/frontend/construction/paint-calculator.html",
    "calculator/frontend/construction/tile-calculator.html",
    "calculator/frontend/construction/wallpaper-calculator.html",
    "calculator/frontend/conversion/area-converter.html",
    "calculator/frontend/conversion/length-converter.html",
    "calculator/frontend/conversion/temperature-converter-fixed.html",
    "calculator/frontend/conversion/temperature-converter-v2.html",
    "calculator/frontend/conversion/temperature-converter.html",
    "calculator/frontend/conversion/volume-converter.html",
    "calculator/frontend/conversion/weight-converter.html",
    "calculator/frontend/date-time/age-calculator.html",
    "calculator/frontend/date-time/date-calculator.html",
    "calculator/frontend/date-time/time-calculator.html",
    "calculator/frontend/date-time/work-hours-calculator.html",
    "calculator/frontend/finance/currency-converter.html",
    "calculator/frontend/finance/interest-calculator.html",
    "calculator/frontend/finance/loan-calculator.html",
    "calculator/frontend/finance/mortgage-calculator.html",
    "calculator/frontend/finance/roi-calculator.html",
    "calculator/frontend/finance/salary-calculator.html",
    "calculator/frontend/finance/tax-calculator.html",
    "calculator/frontend/finance/tip-calculator.html",
    "calculator/frontend/general/basic-calculator.html",
    "calculator/frontend/general/fraction-calculator.html",
    "calculator/frontend/general/percentage-calculator.html",
    "calculator/frontend/general/scientific-calculator.html",
    "calculator/frontend/health/bmi-calculator-old.html",
    "calculator/frontend/health/bmi-calculator-old2.html",
    "calculator/frontend/health/bmi-calculator-v3.html",
    "calculator/frontend/health/bmi-calculator.html",
    "calculator/frontend/health/calorie-calculator.html",
    "calculator/frontend/health/pregnancy-calculator.html",
    "calculator/frontend/health/protein-calculator.html",
    "calculator/frontend/health/weight-loss-calculator.html",
    "calculator/frontend/math/equation-solver.html",
    "calculator/frontend/math/probability-calculator.html",
    "calculator/frontend/math/statistics-calculator.html",
    "calculator/frontend/media/aspect-ratio-calculator.html",
    "calculator/frontend/media/pixel-calculator.html",
    "calculator/frontend/media/video-bitrate-calculator.html",
    "calculator/frontend/sitemap.html"
]

total_modified = 0
for html_file in html_files:
    if fix_html_paths(html_file):
        total_modified += 1

print(f"\nTotal HTML files modified: {total_modified}")
