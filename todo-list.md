# HQMX 통합 EC2 아키텍처 마이그레이션 To-Do List

이 문서는 모든 HQMX 서비스를 단일 EC2 인스턴스로 통합하고 서브디렉토리 URL 구조로 전환하는 전체 과정을 추적합니다.

## Phase 1: 기반 설정 및 계획 (Setting the Foundation)

- [x] **아키텍처 변경 결정**: Cloudflare Pages 의존성 제거 및 단일 EC2 통합 결정 (2025-11-28)
- [x] **todo-list.md 생성**: 마이그레이션 계획 수립 및 추적 시작 (2025-11-28)
- [x] **GEMINI.md 업데이트**: 최상위 설계 문서를 새로운 단일 EC2 아키텍처로 업데이트 (2025-11-28)
- [ ] **DNS 계획 수립**: `hqmx.net` A 레코드를 EC2 IP로 지정하고, 기존 서브도메인(`converter`, `downloader` 등) CNAME 레코드를 제거 또는 리디렉션으로 전환할 계획 수립

## Phase 2: 서버 환경 구성 (Server Configuration)

- [x] **Nginx 통합 설정**: `hqmx.net/` 의 루트, `/converter/`, `/downloader/`, `/generator/`, `/calculator/` 등의 요청을 올바르게 라우팅하는 Nginx 리버스 프록시 설정 파일 재설계 (2025-11-28)
- [ ] **통합 웹 루트 디렉토리 생성**: 모든 프론트엔드 파일을 배포할 단일 디렉토리 구조 설계 (예: `/var/www/hqmx/`)
- [x] **백엔드 API 라우팅**: `/api/converter/` 및 `/api/downloader/` 요청을 내부 포트(`3001`, `5000`)로 전달하는 Nginx location 블록 설정 (2025-11-28, Nginx 통합 설정에 포함)
- [ ] **SSL 인증서 재설정**: `hqmx.net` 단일 도메인에 대한 Let's Encrypt SSL 인증서 설정 확인 및 갱신

## Phase 3: 코드베이스 수정 (Codebase Refactoring)

**전략**: 수동 URL 수정 대신, 각 프로젝트의 SEO 페이지 **생성 스크립트**를 수정하여 모든 URL을 루트 상대 경로(`/`) 기준으로 자동 생성하도록 변경합니다.

### 3.1. `converter` 프로젝트
- [x] **SEO 페이지 생성 로직 수정**: `frontend/_scripts/generate-all-seo-pages.js` 스크립트를 수정하여, 생성되는 모든 HTML 파일의 Canonical URL, `og:url`, 내부 링크 등이 `https://converter.hqmx.net` 대신 `/converter/`로 시작하도록 변경합니다.
- [x] **메인 템플릿 수정**: SEO 페이지의 기반이 되는 `frontend/index.html` 파일의 헤더, 푸터, 네비게이션 등에 포함된 모든 절대 경로 URL을 루트 상대 경로로 수정합니다.
- [x] **API 호출 로직 수정**: `frontend/js/converter-engine.js`, `batch-conversion-manager.js` 등 API를 호출하는 모든 JS 파일에서 엔드포인트를 `https://api.hqmx.net/converter/`에서 `/api/converter/`로 변경합니다.
- [ ] **기타 파일 검토**: `GEMINI.md`, `README.md` 등 문서 파일에 포함된 이전 URL들을 업데이트합니다.

### 3.2. `downloader` 프로젝트
- [x] **SEO 페이지 생성 로직 수정**: `downloader` 프로젝트의 SEO 및 플랫폼별 페이지 생성 스크립트를 찾아, `converter`와 동일한 원칙으로 모든 URL을 `/downloader/` 기준으로 생성하도록 수정합니다.
- [x] **메인 템플릿 수정**: `frontend/index.html`의 모든 절대 경로를 루트 상대 경로로 변경합니다.
- [x] **API 호출 로직 수정**: `frontend/js/main.js` 등에서 API 엔드포인트를 `/api/downloader/`로 변경합니다.
- [ ] **기타 파일 검토**: 관련 문서 파일의 URL을 업데이트합니다.

### 3.3. `calculator` & `generator` 프로젝트
- [x] **SEO 페이지 생성 구조 분석 및 수정**: 각 프로젝트의 페이지 생성 스크립트를 분석하고, 모든 URL이 각각 `/calculator/`, `/generator/`를 기준으로 생성되도록 수정합니다.
- [x] **메인 템플릿 수정**: `frontend/index.html`의 모든 절대 경로를 루트 상대 경로로 변경합니다.

### 3.4. `main` 프로젝트 (랜딩 페이지)
- [x] **서비스 링크 수정**: `frontend/index.html`에서 각 서비스로 연결되는 링크(`<a>` 태그)를 `https://converter.hqmx.net` 과 같은 절대 경로에서 `/converter/`, `/downloader/` 등의 루트 상대 경로로 수정합니다.

### 3.5. 전역 SEO 설정
- [x] **통합 Sitemap 생성 스크립트 개발**: 최종적으로 EC2에 배포된 파일 구조 (`/var/www/hqmx/`)를 기반으로 `hqmx.net/sitemap.xml` 하나를 생성하는 새로운 스크립트를 작성합니다. 이 사이트맵은 `/converter/*`, `/downloader/*` 등 모든 페이지를 포함해야 합니다.
- [x] **통합 `robots.txt` 생성**: `hqmx.net/robots.txt` 파일을 생성하고, 새로운 통합 사이트맵 주소를 명시합니다.

## Phase 4: 배포 및 테스트 (Deployment & Testing)

- [x] **통합 배po 스크립트 작성**: 모든 프로젝트의 `frontend` 빌드 결과물을 EC2의 통합 웹 루트 디렉토리로 배포하는 단일 쉘 스크립트 작성
- [ ] **단계적 배포**: `main` 프로젝트부터 시작하여 하나씩 서비스를 새 구조로 배포
- [ ] **E2E 테스트**: 모든 서비스가 새로운 URL 구조에서 정상적으로 작동하는지 종합적인 테스트 수행 (링크 클릭, API 호출, 리소스 로딩 등)
- [ ] **Nginx 설정 적용 및 재시작**
- [ ] **DNS 변경 실행**: 계획에 따라 DNS 레코드를 업데이트하여 트래픽을 EC2로 전환

## Phase 5: 최종 정리 (Finalization)

- [ ] **Cloudflare Pages 프로젝트 비활성화**: 모든 전환이 완료된 후 기존 Cloudflare Pages 프로젝트들을 아카이빙 또는 삭제
- [x] **관련 문서 업데이트**: 모든 `GEMINI.md` 및 `README.md` 파일에서 Cloudflare Pages 관련 내용을 제거하고 새로운 배포 절차 안내
