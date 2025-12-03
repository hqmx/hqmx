import os
import glob

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix index.html specifically
    if filepath.endswith('index.html'):
        # Password Tab
        content = content.replace('href="#" class="nav-link" data-generator-tab="password"', 'href="/generator/" class="nav-link" data-generator-tab="password"')
        content = content.replace('href="#" class="mobile-menu-link" data-generator-tab="password"', 'href="/generator/" class="mobile-menu-link" data-generator-tab="password"')
        
        # QR Code Tab
        content = content.replace('href="#" class="nav-link" data-generator-tab="qr-code"', 'href="/generator/" class="nav-link" data-generator-tab="qr-code"')
        content = content.replace('href="#" class="mobile-menu-link" data-generator-tab="qr-code"', 'href="/generator/" class="mobile-menu-link" data-generator-tab="qr-code"')

    if content != original_content:
        print(f"Updating {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

# Get all HTML files in generator/frontend
files = glob.glob('/Users/wonjunjang/hqmx/generator/frontend/*.html')
for file in files:
    replace_in_file(file)
