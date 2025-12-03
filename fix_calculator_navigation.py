#!/usr/bin/env python3
"""
Calculator 페이지의 상대 경로를 서브디렉토리 절대 경로로 수정

수정 대상:
- /how-to-use.html → /calculator/how-to-use.html
- /faq.html → /calculator/faq.html
- /api.html → /calculator/api.html
- /sitemap.html → /calculator/sitemap.html
- / (홈) → /calculator/ (단, 이미 /calculator/로 된 것은 그대로)
"""

import os
import re
from pathlib import Path

def fix_calculator_navigation():
    """Calculator frontend의 모든 네비게이션 링크 수정"""
    frontend_dir = Path("/Users/wonjunjang/hqmx/calculator/frontend")
    
    # 제외할 파일 목록 (이미 올바른 경로를 가진 메인 파일들)
    excluded_files = {
        "index.html"
    }
    
    total_files = 0
    modified_files = 0
    
    replacements = [
        ('href="/"', 'href="/calculator/"'),  # 루트 링크
        ('href="/how-to-use.html"', 'href="/calculator/how-to-use.html"'),
        ('href="/how-to-use"', 'href="/calculator/how-to-use.html"'),  # .html 없는 버전
        ('href="/faq.html"', 'href="/calculator/faq.html"'),
        ('href="/faq"', 'href="/calculator/faq.html"'),
        ('href="/api.html"', 'href="/calculator/api.html"'),  
        ('href="/sitemap.html"', 'href="/calculator/sitemap.html"'),
        ('href="/sitemap"', 'href="/calculator/sitemap.html"'),
    ]
    
    print(f"🔍 Calculator 페이지 네비게이션 링크 검사 및 수정 시작...")
    
    for html_file in frontend_dir.rglob("*.html"):
        # 제외 조건 확인
        if html_file.name in excluded_files:
            continue
            
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
                
                if modified_files <= 15:  # 처음 15개만 출력
                    print(f"  ✅ {html_file.relative_to(frontend_dir)}")
                    
        except Exception as e:
            print(f"  ❌ 오류: {html_file.name} - {e}")
    
    print(f"\n📊 결과:")
    print(f"  - 검사한 파일: {total_files:,}개")
    print(f"  - 수정한 파일: {modified_files:,}개")

if __name__ == "__main__":
    fix_calculator_navigation()
    print("\n✨ 완료!")
