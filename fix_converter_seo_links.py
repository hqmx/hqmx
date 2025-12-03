#!/usr/bin/env python3
"""
Converter SEO 다국어 페이지의 상대 경로를 절대 서브디렉토리 경로로 수정

수정 대상:
- /api.html → /converter/api.html
- /how-to-use.html → /converter/how-to-use.html
- /faq.html → /converter/faq.html
"""

import os
import re
from pathlib import Path

def fix_converter_seo_multilingual_pages():
    """Converter SEO 다국어 페이지의 모든 내부 링크를 서브디렉토리 경로로 수정"""
    seo_pages_dir = Path("/Users/wonjunjang/hqmx/converter/frontend/seo-pages")
    
    if not seo_pages_dir.exists():
        print("❌ SEO 페이지 디렉토리가 존재하지 않습니다.")
        return
    
    total_files = 0
    modified_files = 0
    
    replacements = [
        ('href="/api.html"', 'href="/converter/api.html"'),
        ('href="/how-to-use.html"', 'href="/converter/how-to-use.html"'),
        ('href="/faq.html"', 'href="/converter/faq.html"'),
        ('href="/sitemap.html"', 'href="/converter/sitemap.html"'),
    ]
    
    print(f"🔍 SEO 다국어 페이지 검사 및 수정 시작... ({seo_pages_dir})")
    
    for html_file in seo_pages_dir.rglob("*.html"):
        total_files += 1
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 모든 교체 규칙 적용
            for old, new in replacements:
                content = content.replace(old, new)
            
            # 변경사항이 있으면 파일 저장
            if content != original_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                modified_files += 1
                
                if modified_files <= 10:
                    print(f"  ✅ {html_file.relative_to(seo_pages_dir)}")
                    
        except Exception as e:
            print(f"  ❌ 오류: {html_file.name} - {e}")
    
    print(f"\n📊 결과:")
    print(f"  - 검사한 파일: {total_files:,}개")
    print(f"  - 수정한 파일: {modified_files:,}개")

if __name__ == "__main__":
    fix_converter_seo_multilingual_pages()
    print("\n✨ 완료!")
