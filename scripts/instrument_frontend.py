
import os
import re

# Base paths
BASE_DIR = '/Users/wonjunjang/hqmx'
CALCULATOR_DIR = os.path.join(BASE_DIR, 'calculator/frontend/js/calculators')
GENERATOR_DIR = os.path.join(BASE_DIR, 'generator/frontend/js/generators')

def instrument_file(filepath, service_type):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    filename = os.path.basename(filepath)
    print(f"Processing {filename} ({service_type})...")

    # Regex patterns to find the main method
    # We look for:
    # 1. calculate() {
    # 2. generate...() {
    
    method_pattern = r''
    if service_type == 'calculator':
        # Find 'calculate() {'
        # We need to capture the opening brace and insert code after it
        # And find the closing brace (simplistically assuming balanced braces for the method body is hard with regex, 
        # so we'll try to find the return statement or end of method if it's simple, 
        # OR better: we assume these are well-formatted methods and try to wrap the body content)
        
        # Actually, a safer bet for these specific files (usually simple classes):
        # Inject start time at beginning of method
        # Inject trackUsage calls before 'return' statements and at the end of the method
        # Wrap the whole body in try-catch? No, that might be too invasive if they already have try-catch.
        
        # Strategy:
        # 1. Start tracking at start of method.
        # 2. Hook into existing try/catch if present? 
        #    Check if the method has a top-level try/catch.
        
        # Let's try a regex for the method signature
        pattern = r'(calculate\s*\(\)\s*\{)'
    else:
        # For generators: generatePassword(), generateQRCode(), etc.
        pattern = r'(generate[a-zA-Z0-9]*\s*\([^)]*\)\s*\{)'

    match = re.search(pattern, content)
    if not match:
        print(f"  [SKIP] No main method found in {filename}")
        return False

    method_sig = match.group(1)
    
    # Check if already instrumented fully (both start time and usage)
    if "_trackStartTime" in content and "window.trackUsage" in content:
        print(f"  [SKIP] {filename} is already fully instrumented.")
        return False
        
    print(f"  Found method: {method_sig}")

    # Injection 1: Start time
    injection_start = f"\n        const _trackStartTime = Date.now();\n"
    if "_trackStartTime" not in content:
        current_method_sig = match.group(1)
        # Find the actual sig used in this file to replace
        content = content.replace(current_method_sig, current_method_sig + injection_start, 1)

    # Injection 2: Success tracking
    # Calculators
    if service_type == 'calculator':
        # Hook into displayResult or displayResults
        display_pattern = r'(this\.display[a-zA-Z]*\s*\()'
        if re.search(display_pattern, content) and "calculate_success" not in content:
             # Use a generic name or try to use filename
             track_code = f"if(window.trackUsage) window.trackUsage('calculate_success', true, {{ duration: Date.now() - _trackStartTime, calculator: '{filename}' }});\\n            "
             # Replace the first occurrence of display call
             content = re.sub(display_pattern, track_code + r'\1', content, count=1)
        else:
             print(f"  [WARN] No display* method found or already tracked in {filename}")

        # Hook into displayError or showError
        error_pattern = r'(this\.(displayError|showError)\s*\()'
        if re.search(error_pattern, content) and "calculate_error" not in content:
            track_error_code = f"if(window.trackUsage) window.trackUsage('calculate_error', false, {{ calculator: '{filename}' }});\\n            "
            content = re.sub(error_pattern, track_error_code + r'\1', content, count=1)

    else:
        # Generators
        # Hook into display* methods (e.g. displayPasswords)
        display_pattern = r'(this\.display[a-zA-Z]*\s*\()'
        if re.search(display_pattern, content) and "generate_success" not in content:
             track_code = f"if(window.trackUsage) window.trackUsage('generate_success', true, {{ duration: Date.now() - _trackStartTime, generator: '{filename}' }});\\n            "
             content = re.sub(display_pattern, track_code + r'\1', content, count=1)
        
        # Error tracking via catch
        if 'catch' in content and "generate_error" not in content:
            # Inject error tracking in catch
            # catch (error) { or catch (e) {
            content = re.sub(r'(catch\s*\([a-zA-Z0-9_]+\)\s*\{)', 
                             r"\\1\\n            if(window.trackUsage) window.trackUsage('generate_error', false, { generator: '" + filename + r"', error: arguments[0]?.message });", 
                             content, count=1)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [DONE] Instrumented {filename}")
        return True
    else:
        print(f"  [NO CHANGE] Could not apply instrumentation to {filename}")
        return False

# Main execution
count = 0
# Process Calculators
if os.path.exists(CALCULATOR_DIR):
    for f in os.listdir(CALCULATOR_DIR):
        if f.endswith('.js'):
            if instrument_file(os.path.join(CALCULATOR_DIR, f), 'calculator'):
                count += 1

# Process Generators (Basic instrumentation)
if os.path.exists(GENERATOR_DIR):
    for f in os.listdir(GENERATOR_DIR):
        if f.endswith('.js'):
             if instrument_file(os.path.join(GENERATOR_DIR, f), 'generator'):
                count += 1

print(f"Instrumentation complete. Modified {count} files.")
