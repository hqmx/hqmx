#!/usr/bin/env python3
"""
Converter SEO 페이지의 하드코딩된 서브도메인 링크를 서브디렉토리 경로로 일괄 수정

수정 대상:
- https://converter.hqmx.net/api.html → /converter/api.html
"""

import os
import re
from pathlib import Path

def fix_converter_seo_pages():
    """Converter frontend의 모든 SEO 페이지 수정"""
    frontend_dir = Path("/Users/wonjunjang/hqmx/converter/frontend")
    
    # 제외할 파일 목록
    excluded_files = {
        "index.html",
        "how-to-use.html", 
        "faq.html",
        "api.html",
        "sitemap.html"
    }
    
    # 제외할 디렉토리
    excluded_dirs = {"_templates", "_scripts"}
    
    total_files = 0
    modified_files = 0
    
    print("🔍 Converter SEO 페이지 검사 및 수정 시작...")
    
    for html_file in frontend_dir.rglob("*.html"):
        # 제외 조건 확인
        if html_file.name in excluded_files:
            continue
        if any(part in excluded_dirs for part in html_file.parts):
            continue
        if html_file.name.startswith("naver") or html_file.name.startswith("test-"):
            continue
            
        total_files += 1
        
        try:
            # UTF-8로 파일 읽기
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 하드코딩된 API 링크 수정
            content = content.replace(
                'https://converter.hqmx.net/api.html',
                '/converter/api.html'
            )
            
            # 변경사항이 있으면 파일 저장
            if content != original_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                modified_files += 1
                
                if modified_files <= 10:  # 처음 10개만 출력
                    print(f"  ✅ {html_file.relative_to(frontend_dir)}")
                    
        except Exception as e:
            print(f"  ❌ 오류: {html_file.name} - {e}")
    
    print(f"\n📊 결과:")
    print(f"  - 검사한 파일: {total_files:,}개")
    print(f"  - 수정한 파일: {modified_files:,}개")

if __name__ == "__main__":
    fix_converter_seo_pages()
    print("\n✨ 완료!")
