import asyncio
import os
from playwright.async_api import async_playwright

async def check_urls_for_404(url_file_path):
    not_found_urls = []
    
    with open(url_file_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        print(f"Checking {len(urls)} URLs for 404 errors...")

        for i, url in enumerate(urls):
            try:
                response = await page.goto(url, wait_until="domcontentloaded")
                status = response.status
                if status == 404:
                    not_found_urls.append(url)
                    print(f"[{i+1}/{len(urls)}] 🚨 404 NOT FOUND: {url}")
                else:
                    print(f"[{i+1}/{len(urls)}] ✅ {status}: {url}")
            except Exception as e:
                not_found_urls.append(url)
                print(f"[{i+1}/{len(urls)}] ❌ Error accessing {url}: {e}")
        
        await browser.close()
    
    if not not_found_urls:
        print("\nAll checked URLs returned 200 OK or other non-404 status.")
    else:
        print(f"\nFound {len(not_found_urls)} URLs with 404 errors:")
        for url in not_found_urls:
            print(f"- {url}")

if __name__ == "__main__":
    url_file = "converter_seo_urls.txt"
    asyncio.run(check_urls_for_404(url_file))