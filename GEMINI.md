# HQMX 프로젝트 통합 및 URL 구조 변경 심층 분석 보고서

**최종 업데이트**: 2025-11-23
**작성자**: HQMX Development Team

## 1. 결론 요약 (Executive Summary)

*   **실현 가능성**: **가능함 (Feasible)**. 기술적으로 충분히 구현 가능합니다.
*   **난이도**: **상 (High)**. 단순 병합이 아니라, 각 프로젝트의 **프론트엔드 경로(Path)**와 **백엔드 API 라우팅**을 전면적으로 수정해야 합니다.
*   **서버 리소스**: 현재 분산된 부하(Downloader의 `yt-dlp`, Converter의 `FFmpeg`)가 한 곳으로 몰리게 됩니다. 기존 `t3.medium` (2 vCPU, 4GB RAM)으로는 부족할 수 있으며, **최소 `t3.large` 이상** 또는 **`c5.large`** 로의 업그레이드가 권장됩니다.
*   **추천 전략**: **단계적 통합**. 먼저 Nginx 리버스 프록시로 URL 라우팅을 통합하고, 안정화된 후 물리적 서버를 하나로 합치는 방식을 추천합니다.

---

## 2. 현황 분석 (Current Status)

각 프로젝트의 `GEMINI.md` 및 `CLAUDE.md`를 분석한 결과입니다.

| 프로젝트 | 현재 URL (서브도메인) | 백엔드 기술 | 프론트엔드 특징 | 리소스 특성 | 현재 서버 IP |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Downloader** | `downloader.hqmx.net` | Python Flask + `yt-dlp` | Vanilla JS | **CPU/Network Heavy** (영상 다운로드/병합) | 52.55.219.204 |
| **Converter** | `converter.hqmx.net` | Node.js Express + `FFmpeg` | Vanilla JS + `FFmpeg.wasm` | **CPU/RAM Heavy** (이미지/영상 변환) | 23.21.183.81 |
| **Calculator** | `calculator.hqmx.net` | 없음 (Static) 또는 경량 | Vanilla JS | **Low** (클라이언트 연산 위주) | 3.213.100.223 |
| **Generator** | `generator.hqmx.net` | (Phase 1) Static | Next.js (예정) | **Low** (초기), 추후 DB 필요 | (미정) |

**현재 문제점**:
1.  **리소스 파편화**: 3개의 EC2 인스턴스가 각각 돌아가고 있어 관리 포인트가 3배입니다.
2.  **SEO 분산**: 서브도메인(`downloader.`, `converter.`)으로 나뉘어 있어 도메인 권위(Domain Authority)가 분산됩니다. 서브디렉토리(`hqmx.net/download`) 통합 시 SEO 이점이 큽니다.

---

## 3. 통합 시나리오 및 기술적 과제

### A. URL 구조 변경 (`/en/download/...` 등)

가장 큰 작업은 **경로(Path) 문제 해결**입니다.

1.  **프론트엔드 자산 경로 (Asset Paths)**
    *   **현재**: `<script src="/script.js">` (루트 기준 절대 경로 사용 중)
    *   **통합 후**: `/en/download/script.js`로 접근해야 함.
    *   **수정 필요**: 모든 HTML/JS/CSS에서 경로를 상대 경로(`script.js`)로 바꾸거나, `<base href="/en/download/">` 태그를 적용해야 합니다. 특히 `script.js` 내부에서 API를 호출할 때 `/api/analyze` 같은 경로를 `/api/downloader/analyze` 등으로 변경해야 합니다.

2.  **백엔드 API 충돌 방지 (Namespace)**
    *   Downloader와 Converter 모두 `/api` 엔드포인트를 사용할 가능성이 높습니다.
    *   Nginx에서 이를 구분해줘야 합니다.
        *   `hqmx.net/api/downloader/*` → Python Flask (Port 5000)
        *   `hqmx.net/api/converter/*` → Node.js Express (Port 3001)
    *   이에 맞춰 **백엔드 코드(Flask/Express)의 라우트 설정**과 **프론트엔드 API 호출 코드**를 모두 수정해야 합니다.

### B. 단일 EC2 통합 (Server Consolidation)

1.  **포트 관리 (Port Management)**
    *   한 서버에서 여러 서비스를 띄워야 하므로 포트 충돌을 피해야 합니다.
    *   Downloader (Flask): `5000`
    *   Converter (Express): `3001`
    *   Calculator/Generator: 정적 파일이므로 Nginx가 직접 서빙.

2.  **리소스 경합 (Resource Contention)**
    *   **위험**: 누군가 대용량 영상을 다운로드(`yt-dlp`)하면서 동시에 대용량 변환(`ffmpeg`)을 요청하면 CPU가 100%를 칠 수 있습니다.
    *   **해결**:
        *   `systemd` (Python)와 `pm2` (Node)로 프로세스 관리.
        *   스왑 메모리(Swap Memory) 충분히 확보 (최소 4GB 이상).
        *   **Queue 시스템**: Converter는 이미 큐가 있지만, 통합 서버 전체의 부하를 조절하는 글로벌 큐 관리가 필요할 수 있습니다.

3.  **용량 문제 (Storage)**
    *   프로젝트 용량이 수십 GB라고 하셨는데, 이는 대부분 `node_modules`, `venv`, 그리고 **캐시된 미디어 파일**일 것입니다.
    *   통합 서버의 EBS 볼륨을 넉넉하게 (50GB~100GB) 잡아야 합니다.

---

## 4. 단계별 실행 계획 (Action Plan)

이 작업은 서비스 중단을 최소화하기 위해 단계적으로 진행해야 합니다.

### 1단계: 통합 서버 준비 (Infrastructure)
*   가장 사양이 좋은 기존 서버(아마도 Converter 서버 `t3.medium`)를 베이스로 하거나, 신규 `t3.large` 인스턴스를 생성합니다.
*   **필수 설치**: Nginx, Python 3.8+, Node.js 18+, FFmpeg, yt-dlp, PM2.

### 2단계: 코드 리팩토링 (Local Environment)
*   **Downloader**:
    *   Flask 앱의 `base_url` 처리를 유연하게 변경.
    *   Frontend의 API 호출 경로를 `/api/downloader`로 변경.
*   **Converter**:
    *   Express 앱의 라우팅을 `/api/converter` prefix를 지원하도록 수정.
    *   Frontend 자산 경로 수정.
*   **Calculator**:
    *   자산 경로를 상대 경로로 수정.

### 3단계: Nginx 라우팅 설정 (Core)
가장 중요한 Nginx 설정 예시입니다.

```nginx
server {
    listen 80;
    server_name hqmx.net;

    # 1. Landing Page (Main)
    location / {
        root /var/www/html/main;
        index index.html;
    }

    # 2. Downloader
    location /en/download/ {
        alias /var/www/html/downloader/frontend/;
        try_files $uri $uri/ /index.html;
    }
    location /api/downloader/ {
        proxy_pass http://localhost:5000/; # Python Flask
        proxy_set_header Host $host;
    }

    # 3. Converter
    location /en/convert/ {
        alias /var/www/html/converter/frontend/;
        try_files $uri $uri/ /index.html;
    }
    location /api/converter/ {
        proxy_pass http://localhost:3001/; # Node Express
        proxy_set_header Host $host;
    }

    # 4. Calculator
    location /en/calculate/ {
        alias /var/www/html/calculator/frontend/;
    }
}
```

### 4단계: 배포 및 테스트
*   `scp`로 프로젝트 파일 전송 (이때 `node_modules`, `venv`, `.git` 등 불필요한 대용량 파일은 제외하고 전송 후 서버에서 다시 설치하여 전송 시간 단축).
*   서비스 구동 및 Nginx Reload.
*   각 경로 접속 및 기능 테스트.