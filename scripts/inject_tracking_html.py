
import os
import re

BASE_DIR = '/Users/wonjunjang/hqmx'
SERVICES = ['main', 'converter', 'calculator', 'generator']

SCRIPT_TAG = '<script src="/js/tracking.js"></script>'

def inject_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'tracking.js' in content:
        print(f"  [SKIP] {os.path.basename(filepath)} already has tracking")
        return False
        
    # Inject before </head> if possible, or </body>
    if '</head>' in content:
        new_content = content.replace('</head>', f'    {SCRIPT_TAG}\n</head>')
    elif '</body>' in content:
        new_content = content.replace('</body>', f'    {SCRIPT_TAG}\n</body>')
    else:
        print(f"  [WARN] No head/body tag in {os.path.basename(filepath)}")
        return False
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"  [DONE] Injected into {os.path.basename(filepath)}")
    return True

count = 0
for service in SERVICES:
    dir_path = os.path.join(BASE_DIR, service, 'frontend')
    if not os.path.exists(dir_path):
        continue
        
    print(f"Processing {service}...")
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.html'):
                if inject_html(os.path.join(root, file)):
                    count += 1

print(f"HTML Injection complete. Modified {count} files.")
