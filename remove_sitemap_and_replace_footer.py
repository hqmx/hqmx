
import re

def remove_sitemap_and_replace_footer(converter_file_path, downloader_file_path):
    # 1. Read converter/frontend/index.html content
    with open(converter_file_path, 'r', encoding='utf-8') as f:
        converter_content = f.read()

    # 2. Remove HTML sitemap section
    sitemap_html_start_marker = '<section class="sitemap">'
    sitemap_html_end_marker = '</section><!-- /sitemap -->'
    sitemap_html_pattern = re.compile(f'{re.escape(sitemap_html_start_marker)}.*?{re.escape(sitemap_html_end_marker)}', re.DOTALL)
    converter_content = sitemap_html_pattern.sub('', converter_content)

    # 3. Remove JavaScript sitemap section
    # The script block to be removed starts with 'document.addEventListener('DOMContentLoaded', () => {' and contains sitemap related logic.
    # It seems there are two such blocks in the provided file, so I need to target the one specifically for the sitemap.
    # Based on the content, the sitemap JS is the one that contains 'converterExpandBtn', 'downloaderExpandBtn', etc.
    sitemap_js_start_marker = "        document.addEventListener('DOMContentLoaded', () => {"
    sitemap_js_end_marker = "        });" # This is too generic, need more specific end marker

    # Let's try to capture the specific script block related to sitemap functionality
    # by looking for unique identifiers like converterExpandBtn, downloaderExpandBtn
    sitemap_js_pattern = re.compile(r"(\s*<script>\s*document\.addEventListener\('DOMContentLoaded', \(\) => \{\s*//\s*---\s*CONVERTER EXPAND FUNCTIONALITY\s*---\s*const converterExpandBtn[\s\S]*?\}\);?\s*</script>\s*)", re.DOTALL)
    converter_content = sitemap_js_pattern.sub('', converter_content)

    # After removing the sitemap HTML and JS, there's another DOMContentLoaded listener at the very end
    # that also contains sitemap logic. This needs to be removed too.
    # Looking at the full content again, it seems the sitemap-related JS is inside a single <script> block
    # that starts with 'document.addEventListener('DOMContentLoaded', () => {' and ends with '});'
    # and has comments like '--- CONVERTER EXPAND FUNCTIONALITY ---'
    # There are two such blocks because the user has provided the content twice (truncated read_file and then cat)

    # Re-evaluating the JS removal based on the provided content.
    # There are two identical script blocks with DOMContentLoaded listeners, both contain sitemap logic.
    # I should remove both of them if they contain sitemap specific logic.
    # The first one is embedded directly after the sitemap HTML.
    # The second one is at the very end before </body>.

    # Let's target the exact script blocks
    # First script block (after the sitemap section)
    # The first script tag has the sitemap content inside it.
    # It starts with `<script>` and ends with `</script>`
    # And contains `document.addEventListener('DOMContentLoaded', () => {`
    # and has `converterExpandBtn` and `downloaderExpandBtn`

    # From the file content, the problematic script block is:
    # <script>
    #         document.addEventListener('DOMContentLoaded', () => {
    #             // --- CONVERTER EXPAND FUNCTIONALITY ---
    #             const converterExpandBtn = document.getElementById('converterExpandBtn');
    #             ...
    #         });
    #     </script>
    # I need to capture the entire script block that matches this pattern.

    script_block_pattern = re.compile(r"(\s*<script>\s*document\.addEventListener\('DOMContentLoaded', \(\) => \{\s*//\s*---\s*CONVERTER EXPAND FUNCTIONALITY\s*---\s*const converterExpandBtn[\s\S]*?\}\);?\s*</script>\s*)", re.DOTALL)
    converter_content = script_block_pattern.sub('', converter_content)

    # 4. Read downloader/frontend/index.html to get footer content
    with open(downloader_file_path, 'r', encoding='utf-8') as f:
        downloader_content = f.read()

    # Extract footer from downloader_content
    footer_pattern = re.compile(r'(<footer[\s\S]*?</footer>)', re.DOTALL)
    downloader_footer_match = footer_pattern.search(downloader_content)
    
    if downloader_footer_match:
        downloader_footer = downloader_footer_match.group(1)
    else:
        print("Downloader footer not found. Using default empty footer.")
        downloader_footer = "<footer><!-- Default empty footer --></footer>"

    # 5. Replace existing footer in converter_content
    converter_content = re.sub(r'<footer[\s\S]*?</footer>', downloader_footer, converter_content, flags=re.DOTALL)

    # 6. Write modified content back to converter/frontend/index.html
    with open(converter_file_path, 'w', encoding='utf-8') as f:
        f.write(converter_content)

    print(f"Removed sitemap sections and replaced footer in {converter_file_path}")

# Paths to the files
converter_file = 'converter/frontend/index.html'
downloader_file = 'downloader/frontend/index.html'

remove_sitemap_and_replace_footer(converter_file, downloader_file)
