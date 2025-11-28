# HQMX 프로젝트 통합 아키텍처 설계 문서 (단일 EC2)

**최종 업데이트**: 2025-11-28
**작성자**: HQMX Development Team, Gemini Agent

## 1. 결론 요약 (Executive Summary)

*   **최종 결정 아키텍처**: **단일 EC2 통합 (Single EC2 Consolidation)**
    *   Cloudflare Pages 사용을 **중단**하고 모든 프론트엔드 및 백엔드 서비스를 단일 `t3.medium` EC2 인스턴스에서 호스팅합니다.
    *   **Frontend**: 각 서비스(`converter`, `downloader` 등)의 정적 파일들은 EC2 내의 통합 웹 루트 (예: `/var/www/hqmx`)에 배포됩니다.
    *   **Backend**: API 서버(`converter-api`, `downloader-api`)는 동일한 EC2 인스턴스에서 내부 포트(예: `3001`, `5000`)로 실행됩니다.
    *   **Routing**: Nginx가 웹 서버 및 리버스 프록시 역할을 수행하며, 모든 요청을 중앙에서 관리합니다.

*   **URL 구조 전략**: **서브디렉토리(Subdirectory)** 구조를 채택하여 관리를 중앙화하고 SEO를 강화합니다.
    *   `hqmx.net/converter/`
    *   `hqmx.net/downloader/`
    *   `hqmx.net/generator/`
    *   `hqmx.net/calculator/`
    *   API 호출 또한 `hqmx.net/api/converter/` 와 같은 방식으로 통합됩니다.

*   **핵심 변경 사항**: 아키텍처 단순화를 통해 Cloudflare Pages 관련 설정 오류 가능성을 원천적으로 제거하고, 모든 리소스를 단일 서버에서 직접 제어하여 관리 효율성을 극대화합니다.

---

## 2. 새로운 목표 아키텍처 (New Target Architecture)

| 구분 | 기술 스택 | 호스팅 | 역할 |
| :--- | :--- | :--- | :--- |
| **Web Server** | Nginx | **AWS EC2 (t3.medium)** | 정적 파일 서빙, 리버스 프록시, SSL 종료 |
| **Frontend** | HTML/CSS/JS (Vanilla) | **AWS EC2 (t3.medium)** | 각 서비스(`main`, `converter` 등)의 UI/UX |
| **Backend** | Python Flask / Node.js Express | **AWS EC2 (t3.medium)** | 내부 API (파일 변환, 다운로드 등) |

### 리소스 계획
*   **EC2**: `t3.medium` (2 vCPU, 4GB RAM) - **IP: 23.21.183.81**
*   **EBS**: 80GB (OS + 모든 서비스 코드 + 라이브러리 + 임시 작업 공간)
*   **DNS**: `hqmx.net` 도메인의 `A` 레코드가 EC2 IP `23.21.183.81`을 직접 가리킵니다. 기존 서브도메인 CNAME 레코드는 모두 제거됩니다.

---

## 3. 통합 시나리오 및 기술적 과제

### A. URL 구조 및 Nginx 라우팅 (Routing Strategy)

Nginx는 `hqmx.net`으로 들어오는 모든 요청을 받아, URL 경로에 따라 적절한 프론트엔드 파일 또는 백엔드 API로 라우팅합니다.

**Nginx 설정 예시 (`/etc/nginx/sites-available/hqmx.net`):**

```nginx
server {
    listen 80;
    listen 443 ssl;
    server_name hqmx.net;

    # SSL 설정 (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/hqmx.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hqmx.net/privkey.pem;

    # 통합 웹 루트
    root /var/www/hqmx;
    index index.html;

    # 메인 페이지 (루트 요청)
    location / {
        try_files $uri $uri/ /main/index.html; # /main/frontend/index.html 을 루트로
    }

    # 각 서비스별 프론트엔드 라우팅
    location /converter/ {
        alias /var/www/hqmx/converter/;
        try_files $uri $uri/ /converter/index.html;
    }
    location /downloader/ {
        alias /var/www/hqmx/downloader/;
        try_files $uri $uri/ /downloader/index.html;
    }
    # ... (generator, calculator 등 추가)

    # 통합 API 게이트웨이 라우팅
    location /api/converter/ {
        proxy_pass http://localhost:3001/;
        # ... (proxy headers)
    }
    location /api/downloader/ {
        proxy_pass http://localhost:5000/;
        # ... (proxy headers)
    }

    # CORS 설정
    add_header 'Access-Control-Allow-Origin' 'https://hqmx.net' always;
    # ... (기타 CORS 헤더)
}
```

### B. 프론트엔드-백엔드 통신 (CORS)

모든 요청이 동일한 `hqmx.net` 도메인 하위에서 발생하므로 CORS 정책이 매우 단순해집니다. Nginx에서 `Access-Control-Allow-Origin 'https://hqmx.net'` 헤더만 설정하면 충분합니다.

### C. 배포 프로세스 변경

- 각 프로젝트(`converter`, `main` 등)의 프론트엔드 결과물(주로 `frontend` 폴더)을 EC2의 `/var/www/hqmx/{service_name}/` 디렉토리로 복사하는 새로운 통합 배포 스크립트가 필요합니다.
- `git push`를 통한 자동 배포는 더 이상 사용되지 않으며, EC2에 직접 배포하는 방식으로 변경됩니다.

---

## 4. 단계별 실행 계획 (Action Plan)

마이그레이션의 전체 과정은 루트 디렉토리의 `todo-list.md` 파일에 의해 관리됩니다.

### 1단계: 서버 환경 재구성
*   **Nginx**: 위에 제시된 예시와 같이 통합 라우팅을 위한 새로운 Nginx 설정을 적용합니다.
*   **디렉토리 구조**: EC2에 `/var/www/hqmx`를 생성하고, 그 아래에 `main`, `converter`, `downloader` 등 각 서비스의 프론트엔드 파일이 위치할 디렉토리를 생성합니다.

### 2단계: 코드베이스 전체 수정
*   **URL 변경**: 모든 프로젝트의 코드에서 하드코딩된 서브도메인(`converter.hqmx.net` 등)을 새로운 서브디렉토리 기반의 상대 경로(`/converter/`)로 수정합니다.
*   **API 엔드포인트 변경**: API 호출 주소를 `api.hqmx.net`에서 `/api/converter/` 와 같은 상대 경로로 수정합니다.

### 3단계: 배포 및 테스트
*   **통합 배포**: 새로운 배포 스크립트를 사용하여 모든 프론트엔드 파일을 EC2에 배포합니다.
*   **백엔드 재시작**: 백엔드 서비스(pm2, systemd)를 재시작하여 새로운 환경에서 정상 작동하는지 확인합니다.
*   **종합 테스트**: `hqmx.net`에 접속하여 모든 서비스 페이지, 내부 링크, API 기능이 정상적으로 동작하는지 E2E 테스트를 수행합니다.

### 4단계: DNS 전환 및 최종화
*   **DNS 업데이트**: Cloudflare에서 `hqmx.net`의 A 레코드를 EC2 IP로 지정하고, 불필요해진 서브도메인 CNAME 레코드를 모두 삭제합니다.
*   **Cloudflare Pages 비활성화**: 전환이 안정화되면 기존의 Cloudflare Pages 프로젝트들을 비활성화 또는 삭제합니다.

이로써 모든 서비스는 단일 EC2 인스턴스 위에서 통합 관리되며, 이는 아키텍처의 복잡성을 크게 낮추고 유지보수 효율성을 높일 것입니다.