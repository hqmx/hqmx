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
    *   **SSH Key**: `hqmx-ec2.pem` (프로젝트 루트에 위치, 절대 경로 사용 금지, 하위 프로젝트 복사 금지)
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

### 통합 배포 (EC2)
모든 HQMX 서비스는 프로젝트 루트의 통합 배포 스크립트를 통해 단일 EC2 인스턴스에 배포됩니다.

```bash
# Frontend Deployment
./deploy.sh converter
./deploy.sh downloader

# Backend Deployment (Separate Directories)
./deploy.sh converter-backend
./deploy.sh downloader-backend
```

이 스크립트는 각 서비스의 `frontend` 또는 `backend` 디렉터리를 서버의 해당 위치(`/var/www/hqmx/service-name` 또는 `/var/www/hqmx/service-name-backend`)로 동기화합니다.
**주의**: 프론트엔드와 백엔드는 서로 다른 디렉토리에 배포되므로 각각 별도로 배포해야 합니다.

### C. 배포 프로세스 변경 (Standardized)

- **표준화된 배포**: 모든 프론트엔드 서비스(`converter`, `downloader` 등)는 **`frontend` 디렉토리만** EC2의 `/var/www/hqmx/{service_name}/` (정확히는 `releases/timestamp`)로 배포됩니다.
- **Nginx 설정**: 따라서 Nginx의 `alias`는 `.../current/frontend/`가 아닌 **`.../current/`** 를 가리켜야 합니다.
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
*   **통합 배포 (권장)**: 새로운 모듈식 배포 스크립트를 사용하여 필요한 서비스만 빠르고 안전하게 배포합니다.
    ```bash
    # 사용법: ./deploy.sh <service_name>
    ./deploy.sh main        # 메인 페이지 배포
    ./deploy.sh converter   # Converter 서비스 배포
    ./deploy.sh downloader  # Downloader 서비스 배포
    ./deploy.sh generator   # Generator 서비스 배포
    ./deploy.sh calculator  # Calculator 서비스 배포
    ```
*   **백엔드 재시작**: 백엔드 서비스(pm2, systemd)를 재시작하여 새로운 환경에서 정상 작동하는지 확인합니다.
*   **종합 테스트**: `hqmx.net`에 접속하여 모든 서비스 페이지, 내부 링크, API 기능이 정상적으로 동작하는지 E2E 테스트를 수행합니다.

### 4단계: DNS 전환 및 최종화
*   **DNS 업데이트**: Cloudflare에서 `hqmx.net`의 A 레코드를 EC2 IP로 지정하고, 불필요해진 서브도메인 CNAME 레코드를 모두 삭제합니다.
*   **Cloudflare Pages 비활성화**: 전환이 안정화되면 기존의 Cloudflare Pages 프로젝트들을 비활성화 또는 삭제합니다.

이로써 모든 서비스는 단일 EC2 인스턴스 위에서 통합 관리되며, 이는 아키텍처의 복잡성을 크게 낮추고 유지보수 효율성을 높일 것입니다.

---

## 5. 트러블슈팅 (Troubleshooting)

### 🚨 [CRITICAL] 배포 실패 - 타임존 불일치 문제

**발생 날짜**: 2025-11-29  
**심각도**: CRITICAL (배포 완전 실패)

#### 증상
```
ls: cannot access '/home/ubuntu/hqmx/services/main/current/': No such file or directory
```
- 배포는 성공했다고 나오지만 실제 서비스는 500 에러
- `current` 심볼릭 링크가 존재하지 않는 디렉토리를 가리킴

#### 근본 원인
**타임존 불일치**로 인한 타임스탬프 불일치:
- **로컬 환경**: Bangkok +07:00
- **EC2 서버**: UTC (표준시)
- **배포 스크립트**: 로컬 타임으로 `TIMESTAMP=$(date +%Y%m%d_%H%M%S)` 생성

**결과**:
```bash
# 로컬에서 생성한 디렉토리명
releases/20251129_005940  # 로컬 01:04 기준

# 서버에 실제 존재하는 디렉토리
releases/20251128_180000  # UTC 기준 (7시간 차이)

# current 링크는 존재하지 않는 경로를 가리킴
current -> releases/20251129_005940  ❌
```

#### 해결 방법
**`scripts/deploy-modular.sh` 수정**:
```bash
# ❌ Before (로컬 타임 사용)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ✅ After (서버 타임 사용)
# Generate timestamp on SERVER to avoid timezone issues
TIMESTAMP=$(ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "date +%Y%m%d_%H%M%S")
```

**서버 측 긴급 복구**:
```bash
ssh -i hqmx-ec2.pem ubuntu@23.21.183.81
cd /home/ubuntu/hqmx/services/main
LATEST=$(ls -t releases/ | head -1)
ln -sfn /home/ubuntu/hqmx/services/main/releases/$LATEST current
```

**커밋**: `8818102` - "배포 스크립트 타임존 문제 수정"

---

### 🚨 [CRITICAL] 500 에러 - Nginx 무한 리다이렉션 루프

**발생 날짜**: 2025-11-29  
**심각도**: CRITICAL (메인 페이지, Downloader 접근 불가)

#### 증상
```
[error] 48217#48217: *942 rewrite or internal redirection cycle while internally redirecting to "/index.html"
```
- **정상**: `/converter/`, `/generator/` (200 OK)
- **500 에러**: `/`, `/downloader/`

#### 근본 원인
**Nginx location 블록 순서 및 try_files 설정 오류**:

```nginx
# ❌ 문제가 있던 설정
location / {
    try_files $uri $uri/ /index.html;  # 모든 경로에 적용됨!
}

# /api/converter/ 요청도 location /에 매칭
# -> /index.html로 리다이렉션
# -> 다시 location /에 매칭
# -> 무한 루프 → 500 에러
```

#### 해결 방법
**Nginx 설정 재구성** (`/etc/nginx/sites-available/hqmx.net`):

1. **API 프록시를 먼저 배치** (우선순위 확보)
2. **서브 경로 명시적 정의**
3. **메인 페이지는 마지막에** 배치

```nginx
server {
    listen 443 ssl;
    server_name hqmx.net www.hqmx.net;
    
    root /home/ubuntu/hqmx/services/main/current;
    index index.html;

    # ✅ 1. API 프록시 먼저 (^~ 사용으로 우선순위 확보)
    location ^~ /api/converter/ {
        proxy_pass http://localhost:3001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location ^~ /api/downloader/ {
        proxy_pass http://localhost:5000/api/;
        # ... (동일한 proxy headers)
    }

    # ✅ 2. 서브 경로 명시적 정의
    location ^~ /converter/ {
        alias /home/ubuntu/hqmx/services/converter/current/;
        try_files $uri $uri/ /converter/index.html;
    }

    location ^~ /downloader/ {
        alias /home/ubuntu/hqmx/services/downloader/current/;
        try_files $uri $uri/ /downloader/index.html;
    }

    # ✅ 3. 메인 페이지는 마지막에 (fallback 없이)
    location / {
        try_files $uri $uri/ =404;  # /index.html 리다이렉션 제거
    }
}
```

**적용 명령**:
```bash
sudo mv /tmp/hqmx.net.nginx /etc/nginx/sites-available/hqmx.net
sudo nginx -t
sudo systemctl reload nginx
```

#### 검증 결과
```bash
$ curl -s -o /dev/null -w "%{http_code}\n" https://hqmx.net/
200 ✅

$ curl -s -o /dev/null -w "%{http_code}\n" https://hqmx.net/downloader/
200 ✅
```

---

### 📚 교훈 및 예방 조치

1. **타임존**: 
   - ✅ 서버 측에서 타임스탬프 생성 (완전 해결)
   - 🔒 향후 모든 배포 스크립트에 동일 원칙 적용

2. **Nginx 설정**:
   - ✅ location 블록 순서 중요 (`^~` prefix로 우선순위 명확화)
   - ✅ `try_files` 마지막 fallback은 신중하게 사용
   - 🔒 설정 변경 시 항상 `nginx -t` 테스트

### 🚨 [CRITICAL] 배포 후 500 에러 - Cleanup 스크립트 오작동

**발생 날짜**: 2025-11-29
**심각도**: HIGH (배포 직후 파일 사라짐)

#### 증상
- 배포 스크립트는 성공했다고 나오지만, Nginx 로그에 `directory index of "..." is forbidden` 또는 `rewrite or internal redirection cycle` 에러 발생.
- 서버에서 확인해보면 `current` 심볼릭 링크가 가리키는 디렉토리가 **삭제되어 없음**.

#### 근본 원인
- `rsync -a`는 원본 파일/디렉토리의 **수정 시간(mtime)**을 보존함.
- 로컬의 `generator/frontend` 디렉토리가 오래전에 생성된 경우, 서버에 업로드된 후에도 오래된 날짜를 유지함.
- 배포 스크립트의 **Cleanup 로직** (`ls -t | tail -n +6 | xargs rm -rf`)은 수정 시간 순으로 정렬하여 상위 5개만 남기고 삭제함.
- 방금 업로드한 디렉토리가 날짜가 오래되어 "오래된 릴리스"로 인식되어 **즉시 삭제됨**.

#### 해결 방법
- `deploy-modular.sh`에서 `scp` 또는 `rsync` 업로드 직후, **`touch` 명령어로 타임스탬프를 갱신**하도록 수정.

```bash
# Ensure the release directory has the latest timestamp to prevent accidental cleanup
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "touch $RELEASE_DIR"
```

**커밋**: `deploy-modular.sh` 수정됨.

18. **배포 효율성**: `deploy-to-ec2.sh`는 모든 파일을 배포하므로, **변경된 (수정한) 파일만** 배포해야 할 경우 수동 배포를 활용하거나 꼭 필요한 경우에만 전체 배포 스크립트를 사용합니다 (캐시 버스팅은 필요에 따라 수동 적용).
9. **캐시 버스팅 필수**: CSS, JS 등 수정이 잦은 정적 파일은 브라우저 캐시로 인해 변경사항이 즉시 반영되지 않을 수 있습니다. 배포 전 `index.html`에서 해당 파일의 쿼리 파라미터(예: `style.css?v=20251129_1830`)를 반드시 업데이트해야 합니다.
10. **Backend .env 동기화**: 백엔드 `wrangler.toml` 또는 `package.json`의 `vars` 섹션이 변경되면, EC2 서버의 `/home/ubuntu/hqmx/backend/.env` 파일을 수동으로 업데이트해야 합니다. `pm2 restart hqmx-backend` 명령으로 변경 사항을 적용합니다. 이는 자동화된 배포 스크립트가 `.env` 파일을 직접 관리하지 않기 때문입니다.
**배포 검증**:
   - 🔒 배포 후 반드시 HTTP 상태 코드 확인
   - 🔒 Nginx 에러 로그 모니터링 필수: `tail -f /var/log/nginx/error.log`

**참고 파일**:
- Nginx 설정 백업: `nginx/hqmx.net.conf`
- 배포 스크립트: `scripts/deploy-modular.sh`

---

### ✅ [RESOLVED] Converter 서비스 경로 문제 (배경, SW, API)

**발생 날짜**: 2025-11-29  
**해결 날짜**: 2025-11-29  
**심각도**: HIGH (UI 깨짐 및 기능 오류)

#### 증상
1.  **UI**: 배경 이미지가 로드되지 않고 흰색으로 표시됨.
2.  **Console**: 
    - `Service Worker registration failed: 404`
    - `Tier mapping 로드 실패: SyntaxError` (JSON 대신 HTML 반환)
    - `GET /api/queue-status 404`

#### 원인 분석
**서브디렉토리 구조(/converter/) 미반영**:
- **CSS**: `url('assets/bg.webp')`는 상대 경로로 해석되어 `/converter/assets/`가 아닌 `/assets/`를 찾음 (또는 그 반대).
- **SW**: `/sw.js`로 등록되어 루트 경로에서 찾음.
- **API**: `/api/queue-status`로 호출하여 Nginx 라우팅 규칙(`/api/converter/`)과 불일치.
- **JSON**: `converter/docs/` 폴더가 배포 대상인 `frontend` 폴더 밖에 있어 배포되지 않음.

#### 해결 방법
1.  **CSS 경로 수정**: `style.css`, `sitemap.css` 등에서 `url('/converter/assets/...')` 절대 경로로 수정.
2.  **SW 등록 수정**: 모든 HTML 파일(13,000+개)에서 `navigator.serviceWorker.register('/converter/sw.js')`로 일괄 수정.
3.  **API 경로 수정**: `batch-conversion-network-recovery.js`에서 `/api/converter/queue-status`로 수정.
4.  **파일 이동**: `converter/docs/conversion-tier-mapping.json`을 `converter/frontend/docs/`로 복사하여 배포에 포함되도록 함.

**커밋**: (자동 배포됨)

---

### 📚 교훈 및 예방 조치

1.  **서브디렉토리 배포 시 경로 주의**:
    - CSS `url()`은 항상 절대 경로(`/service-name/assets/...`) 사용 권장.
    - JS `fetch()` 및 `Worker` 등록도 서비스 접두사 포함 필수.
    
2.  **배포 범위 확인**:
    - `frontend` 폴더만 배포되므로, 필요한 리소스(JSON, 문서 등)는 반드시 그 안에 위치해야 함.

---

### ✅ [RESOLVED] 네비게이션 링크 하드코딩 문제 (Converter, Calculator)

**발생 날짜**: 2025-11-29  
**해결 날짜**: 2025-11-29  
**심각도**: MEDIUM (기능은 작동하지만 아키텍처 불일치)

#### 원인 분석

**Converter SEO 페이지들 (13,503개 파일)**:
- 하드코딩된 서브도메인 링크 사용: `https://converter.hqmx.net/api.html`
- SEO 다국어 페이지들의 상대 경로 오류: `/api.html`, `/how-to-use.html`

**Calculator 서브 페이지들 (40개 파일)**:
- 서브디렉토리 접두사 누락: `/how-to-use.html` (올바른: `/calculator/how-to-use.html`)
- 루트 링크 오류: `/` (올바른: `/calculator/`)

#### 해결 방법

**Converter 수정** (`fix_converter_navigation.py`, `fix_converter_seo_links.py`):
```python
# 1단계: 하드코딩된 서브도메인 제거
'https://converter.hqmx.net/api.html' → '/converter/api.html'  # 16개 파일

# 2단계: SEO 다국어 페이지 경로 수정
'/api.html' → '/converter/api.html'
'/how-to-use.html' → '/converter/how-to-use.html'
'/faq.html' → '/converter/faq.html'
'/sitemap.html' → '/converter/sitemap.html'
# 총 13,503개 파일 수정
```

**Calculator 수정** (`fix_calculator_navigation.py`):
```python
# 모든 상대 링크에 서브디렉토리 접두사 추가
'href="/"' → 'href="/calculator/"'
'href="/how-to-use.html"' → 'href="/calculator/how-to-use.html"'
'href="/faq"' → 'href="/calculator/faq.html"'
'href="/api.html"' → 'href="/calculator/api.html"'
'href="/sitemap"' → 'href="/calculator/sitemap.html"'
# 총 40개 파일 수정
```

#### 배포 내역

**Converter**:
```bash
커밋: 216c529
배포: ./scripts/deploy-modular.sh --service=converter --env=prod
상태: ✅ 완료 (2025-11-29 18:33 UTC)
```

**Calculator**:
```bash
커밋: 34a9863
배포: ./scripts/deploy-modular.sh --service=calculator --env=prod
상태: ✅ 완료 (2025-11-29 18:34 UTC)
```

#### 검증 결과

모든 네비게이션 링크가 단일 EC2 서브디렉토리 구조(`/converter/`, `/calculator/`)에 맞게 수정됨:

**수정된 파일 수**:
- Converter: 13,519개 (메인 파일 16개 + SEO 페이지 13,503개)
- Calculator: 40개

**참고 스크립트**:
- `fix_converter_navigation.py`
- `fix_converter_seo_links.py`
- `fix_calculator_navigation.py`

---
### ✅ [RESOLVED] Deployment Path Fixes & Cache Busting

**발생 날짜**: 2025-11-29
**해결 날짜**: 2025-11-29
**심각도**: HIGH (배포 직후 404/500 에러 및 캐시 문제)

#### 증상
1.  **배포 후 404/500 에러**: 배포 스크립트 실행 후 `current` 심볼릭 링크가 가리키는 디렉토리가 삭제되어 Nginx가 파일을 찾지 못함.
2.  **캐시 문제**: CSS/JS 수정 사항이 브라우저 캐시로 인해 즉시 반영되지 않음.

#### 원인 분석
1.  **Cleanup 로직 오류**: `deploy-modular.sh`의 `ls -t` (시간순 정렬)가 `rsync`로 보존된 과거 타임스탬프 때문에 최신 릴리스를 "오래된 것"으로 오판하여 삭제함.
2.  **캐시 버스팅 부재**: 정적 파일에 대한 버전 관리가 자동화되어 있지 않음.

#### 해결 방법
1.  **Cleanup 로직 수정**: `ls -t` 대신 **`ls -r` (역순 정렬)**을 사용하여 디렉토리 이름(타임스탬프) 기준으로 정렬하도록 수정. 이로써 파일시스템 타임스탬프와 무관하게 항상 최신 릴리스를 보존함.
2.  **Cache Busting 구현**: `deploy-modular.sh`에 배포 단계 추가. `sed -E`를 사용하여 `index.html` 내의 `.css` 및 `.js` 참조에 `?v=TIMESTAMP` 쿼리 파라미터를 자동으로 추가/갱신함.

```bash
# scripts/deploy-modular.sh
# Use -E for extended regex to simplify syntax
# Use # as delimiter to avoid conflict with | (alternation) in regex
sed -E -i 's#\.(css|js)(\?v=[^"]*)?"#.\1?v='""'"#g' index.html
```

#### 배포 및 검증
- **Main**: `./deploy.sh main` -> 성공. `index.html`에서 `style.css?v=20251129_...` 확인.
- **Downloader**: `./deploy.sh downloader` -> 성공.
- **Nginx**: 404/500 에러 해결됨.

**참고**: `deploy-modular.sh`

---
