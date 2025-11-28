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
*   **EC2**: `t3.medium` (2 vCPU, 4GB RAM) - **IP: 23.21.183.81** [SSH Key](hqmx-ec2.pem)
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
        alias /home/ubuntu/hqmx/services/converter/current/frontend/;
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

3. **배포 검증**:
   - 🔒 배포 후 반드시 HTTP 상태 코드 확인
   - 🔒 Nginx 에러 로그 모니터링 필수: `tail -f /var/log/nginx/error.log`

**참고 파일**:
- Nginx 설정 백업: `nginx/hqmx.net.conf`
- 배포 스크립트: `scripts/deploy-modular.sh`

---

### 🔄 [ONGOING] 네비게이션 표시 문제 (Converter, Calculator)

**발생 날짜**: 2025-11-29  
**심각도**: MEDIUM (기능은 작동하지만 UX 문제)  
**상태**: 조사 중

#### 사용자 보고 증상
- Converter와 Calculator의 네비게이션이 "비정상"으로 표시됨
- 정확한 증상 미확인 (브라우저 서브에이전트 오류로 직접 확인 불가)

#### 서버 측 확인 결과 (2025-11-29 01:25 UTC+7)

**✅ Calculator** (`/calculator/`):
```html
<!-- 데스크톱 네비게이션 -->
<a href="/calculator/" class="nav-link active">Home</a>
<a href="/calculator/how-to-use.html" class="nav-link">How to Use</a>
<a href="/calculator/faq.html" class="nav-link">FAQ</a>
<a href="/calculator/api.html" class="nav-link">API</a>
<a href="/calculator/sitemap.html" class="nav-link">Site Map</a>

<!-- 모바일 네비게이션 -->
<a href="/calculator/" class="mobile-menu-link active">Home</a>
<!-- ... 동일한 패턴 -->
```
- ✅ 모든 링크가 `/calculator/` 접두사 사용
- ✅ 서브디렉토리 구조에 맞게 정상

**✅ Converter** (`/converter/`):
```html
<!-- 로고 링크 (메인 페이지로 이동) -->
<a href="/" class="converter-logo-link">

<!-- 데스크톱 네비게이션 -->
<a href="/converter/" class="nav-link active">Convert</a>  <!-- ⚠️ href="#"이 아님 -->
<a href="/converter/how-to-use.html" class="nav-link">How to Use</a>
<!-- ... -->
```
- ✅ 모든 링크가 `/converter/` 접두사 사용
- ✅ 로고는 `/` (메인 페이지로 이동, 정상)

#### 가능한 원인 분석

1. **브라우저 캐시 문제**
   - 사용자 브라우저가 이전 버전의 HTML을 캐시하고 있을 가능성
   - 서버 응답은 정상이지만 브라우저가 표시하는 내용이 다를 수 있음

2. **JavaScript 동작 문제**
   - 페이지 로드 후 JavaScript가 네비게이션을 동적으로 수정할 가능성
   - `script.js`, `nav-common.js` 등의 스크립트 확인 필요

3. **CSS 표시 문제**
   - 링크는 올바르게 설정되었지만 스타일링 문제로 "비정상"으로 보일 가능성
   - `active` 클래스가 올바르게 적용되지 않을 수 있음

4. **특정 서브 페이지 문제**
   - 메인 `index.html`은 정상이지만 서브 페이지들이 문제일 가능성
   - 예: `/calculator/sitemap.html`, `/converter/faq.html` 등

#### 진단 절차 (Diagnostic Workflow)

**Phase 1: 브라우저 캐시 확인**
```bash
# 사용자측 조치
1. Hard Refresh (Cmd+Shift+R 또는 Ctrl+Shift+R)
2. 시크릿 모드/프라이빗 브라우징으로 테스트
3. 브라우저 캐시 완전 삭제
```

**Phase 2: 서버 헤더 확인**
```bash
# 캐시 헤더 확인
curl -I https://hqmx.net/calculator/
curl -I https://hqmx.net/converter/

# 예상 헤더
Cache-Control: public, immutable
Expires: [1년 후]
```

**Phase 3: JavaScript 동작 확인**
```bash
# 서버에서 JavaScript 파일 확인
ssh ubuntu@23.21.183.81
cd /home/ubuntu/hqmx/services/calculator/current/
grep -n "nav-link" frontend/*.js
grep -n "active" frontend/*.js
```

**Phase 4: 서브 페이지 확인**
```bash
# 각 서브 페이지의 네비게이션 확인
curl -s https://hqmx.net/calculator/sitemap.html | grep 'nav-link'
curl -s https://hqmx.net/converter/faq.html | grep 'nav-link'
```

#### 임시 해결 방안

1. **캐시 버스팅 강화**
   ```nginx
   # Nginx 설정에 추가
   location ~* \.html$ {
       add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
   }
   ```

2. **버전 쿼리 파라미터 추가**
   ```html
   <link rel="stylesheet" href="/calculator/style.css?v=20251129">
   <script src="/calculator/script.js?v=20251129"></script>
   ```

#### 다음 단계 (Next Actions)

1. ✅ **사용자에게 구체적 증상 확인 요청**
   - 어떤 페이지에서 문제 발생?
   - 어떤 부분이 "비정상"으로 보이는지?
   - 스크린샷 또는 브라우저 개발자 도구 콘솔 로그 공유

2. ⏳ **브라우저 캐시 삭제 후 재확인**

3. ⏳ **JavaScript 코드 분석**
   - `nav-common.js` 검토
   - 동적 클래스 추가/제거 로직 확인

4. ⏳ **모든 서브 페이지 네비게이션 일괄 확인**

**관련 파일**:
- Calculator: `calculator/frontend/index.html`
- Converter: `converter/frontend/index.html`
- 공통 스타일: `*/frontend/style.css`
- 공통 스크립트: `*/frontend/nav-common.js`