# Cloudflare Pages 배포 가이드

**작성일**: 2025-11-23  
**작성자**: HQMX Development Team  
**목적**: 프론트엔드를 Cloudflare Pages에 배포하여 EC2 부하 감소 및 글로벌 성능 향상

---

## 🎯 Cloudflare Pages란?

Cloudflare Pages는 **정적 사이트를 무료로 호스팅**하는 서비스입니다.
- **무료 플랜**: 무제한 대역폭, 무제한 트래픽
- **자동 배포**: GitHub/GitLab 연동 시 push만 하면 자동 배포
- **글로벌 CDN**: 전 세계 300+ 도시에 자동 캐싱
- **커스텀 도메인**: 무료 SSL 인증서 자동 발급

---

## 📊 HQMX 서비스별 배포 전략

| 서비스 | 프론트엔드 | 백엔드 | 배포 방법 |
|--------|-----------|--------|----------|
| **Main** (랜딩페이지) | Cloudflare Pages | 없음 | GitHub → Cloudflare Pages |
| **Calculator** | Cloudflare Pages | 없음 (클라이언트 계산) | GitHub → Cloudflare Pages |
| **Generator** | Cloudflare Pages | 없음 (클라이언트 생성) | GitHub → Cloudflare Pages |
| **Downloader** | Cloudflare Pages | EC2 (Flask + yt-dlp) | Pages (FE) + EC2 (API) |
| **Converter** | Cloudflare Pages | EC2 (Express + FFmpeg) | Pages (FE) + EC2 (API) |

---

## 🚀 단계별 배포 가이드

### 1단계: Cloudflare Pages 프로젝트 생성

#### A. Cloudflare 대시보드 접속
1. https://dash.cloudflare.com/ 로그인
2. 좌측 메뉴에서 **"Workers & Pages"** 클릭
3. **"Create application"** → **"Pages"** → **"Connect to Git"** 선택

#### B. GitHub Repository 연결
1. **"Connect GitHub"** 클릭하여 GitHub 계정 인증
2. HQMX Repository 선택
3. **Production branch**: `main` 선택

#### C. 빌드 설정 (서비스별)

##### Main Landing Page (정적 HTML)
```yaml
Project name: hqmx-main
Production branch: main
Build command: (없음 - Static HTML)
Build output directory: main/frontend
Root directory: /
```

##### Calculator (정적 HTML + JS)
```yaml
Project name: hqmx-calculator
Production branch: main
Build command: (없음 - Static HTML)
Build output directory: calculator/frontend
Root directory: /
```

##### Generator (정적 HTML + JS)
```yaml
Project name: hqmx-generator
Production branch: main
Build command: (없음 - Static HTML)
Build output directory: generator/frontend
Root directory: /
```

##### Downloader (프론트엔드만)
```yaml
Project name: hqmx-downloader
Production branch: main
Build command: (없음 - Static HTML)
Build output directory: downloader/frontend
Root directory: /
Environment variables:
  - API_BASE_URL: https://api.hqmx.net (EC2 백엔드 주소)
```

##### Converter (프론트엔드만)
```yaml
Project name: hqmx-converter
Production branch: main
Build command: (없음 - Static HTML)
Build output directory: converter/frontend
Root directory: /
Environment variables:
  - API_BASE_URL: https://api.hqmx.net (EC2 백엔드 주소)
```

---

### 2단계: 커스텀 도메인 연결

#### A. DNS 레코드 설정 (Cloudflare DNS)
Cloudflare Pages 프로젝트마다 자동 도메인(`*.pages.dev`)이 제공되지만, 커스텀 도메인을 사용해야 합니다.

**DNS 설정 (Cloudflare DNS 패널)**:

| 서비스 | 레코드 타입 | 이름 | 대상 | Proxy 상태 |
|--------|------------|------|------|-----------|
| Main | CNAME | `@` (루트) | `hqmx-main.pages.dev` | ✅ Proxied |
| Main | CNAME | `www` | `hqmx-main.pages.dev` | ✅ Proxied |
| Calculator | CNAME | `calculator` | `hqmx-calculator.pages.dev` | ✅ Proxied |
| Generator | CNAME | `generator` | `hqmx-generator.pages.dev` | ✅ Proxied |
| Downloader | CNAME | `downloader` | `hqmx-downloader.pages.dev` | ✅ Proxied |
| Converter | CNAME | `converter` | `hqmx-converter.pages.dev` | ✅ Proxied |

#### B. Cloudflare Pages 도메인 추가
각 Pages 프로젝트 대시보드에서:
1. **"Custom domains"** 탭 클릭
2. **"Set up a custom domain"** 클릭
3. 도메인 입력:
   - Main: `hqmx.net`, `www.hqmx.net`
   - Calculator: `calculator.hqmx.net`
   - Generator: `generator.hqmx.net`
   - Downloader: `downloader.hqmx.net`
   - Converter: `converter.hqmx.net`
4. **SSL 인증서 자동 발급** (1~5분 소요)

---

### 3단계: 백엔드 API 연결 (Downloader, Converter만)

Downloader와 Converter는 프론트엔드(Cloudflare Pages)와 백엔드(EC2)가 분리되므로 **CORS 설정**이 필요합니다.

#### A. EC2 백엔드 CORS 설정

##### Flask (Downloader)
**파일**: `downloader/backend/app.py`

```python
from flask_cors import CORS

app = Flask(__name__)

# CORS 설정: Cloudflare Pages 도메인 허용
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://downloader.hqmx.net",
            "https://hqmx-downloader.pages.dev"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

**설치**:
```bash
pip install flask-cors
```

##### Express (Converter)
**파일**: `converter/backend/server.js`

```javascript
const cors = require('cors');

const allowedOrigins = [
    'https://converter.hqmx.net',
    'https://hqmx-converter.pages.dev'
];

app.use(cors({
    origin: function(origin, callback) {
        if (!origin || allowedOrigins.includes(origin)) {
            callback(null, true);
        } else {
            callback(new Error('Not allowed by CORS'));
        }
    },
    methods: ['GET', 'POST', 'OPTIONS'],
    credentials: true
}));
```

**설치**:
```bash
npm install cors
```

#### B. 프론트엔드 API 호출 수정

기존 상대 경로(`/api/analyze`)를 절대 경로로 변경:

**JavaScript 수정 예시**:
```javascript
// Before (EC2에서만 작동)
fetch('/api/analyze', { ... })

// After (Cloudflare Pages에서 EC2 API 호출)
const API_BASE_URL = 'https://api.hqmx.net'; // 또는 환경 변수
fetch(`${API_BASE_URL}/api/analyze`, { ... })
```

---

## 🔧 배포 자동화

### GitHub Actions 워크플로우

Cloudflare Pages는 Git push 시 자동 배포되지만, 더 세밀한 제어를 원한다면 GitHub Actions를 사용할 수 있습니다.

**파일**: `.github/workflows/deploy-pages.yml`

```yaml
name: Deploy to Cloudflare Pages

on:
  push:
    branches: [main]
    paths:
      - 'main/frontend/**'
      - 'calculator/frontend/**'
      - 'generator/frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy Main to Cloudflare Pages
        if: contains(github.event.head_commit.modified, 'main/frontend')
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: hqmx-main
          directory: main/frontend
          
      - name: Deploy Calculator to Cloudflare Pages
        if: contains(github.event.head_commit.modified, 'calculator/frontend')
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: hqmx-calculator
          directory: calculator/frontend
```

---

## 📝 환경 변수 관리

### Cloudflare Pages 환경 변수 설정

Pages 프로젝트 대시보드 → **"Settings"** → **"Environment variables"**

**Downloader 예시**:
```
API_BASE_URL=https://api.hqmx.net
ENVIRONMENT=production
```

**프론트엔드에서 사용**:
```javascript
// Cloudflare Pages는 환경 변수를 빌드 시 주입
const apiUrl = process.env.API_BASE_URL || 'https://api.hqmx.net';
```

---

## ✅ 검증 체크리스트

### 배포 후 확인 사항

#### Main Landing Page
- [ ] https://hqmx.net 접속 확인
- [ ] https://www.hqmx.net 리다이렉트 확인
- [ ] 네비게이션 링크 작동 확인
- [ ] 다국어 토글 작동 확인

#### Calculator
- [ ] https://calculator.hqmx.net 접속 확인
- [ ] BMI 계산기 작동 확인
- [ ] 다국어 전환 확인

#### Downloader
- [ ] https://downloader.hqmx.net 접속 확인
- [ ] **API 연결 확인** (YouTube URL 분석 테스트)
- [ ] 다운로드 기능 작동 확인
- [ ] CORS 에러 없는지 확인 (브라우저 콘솔)

#### Converter
- [ ] https://converter.hqmx.net 접속 확인
- [ ] **API 연결 확인** (파일 변환 테스트)
- [ ] 변환 기능 작동 확인
- [ ] CORS 에러 없는지 확인

---

## 🐛 트러블슈팅

### 1. "404 Not Found" 에러
**원인**: `Build output directory` 경로가 잘못됨  
**해결**: Pages 프로젝트 설정에서 올바른 경로 지정

### 2. CORS 에러
**증상**: 브라우저 콘솔에 `Access-Control-Allow-Origin` 에러  
**해결**: EC2 백엔드에 CORS 설정 추가 (위 3단계 참조)

### 3. API 호출 실패 (Mixed Content)
**증상**: `https` 페이지에서 `http` API 호출 시 차단  
**해결**: EC2 백엔드에 SSL 인증서 설치 (Let's Encrypt)

### 4. 빌드 실패
**증상**: Pages 배포 시 빌드 에러  
**해결**: 정적 HTML이므로 빌드 명령어를 비워두세요

---

## 💰 비용 비교

| 항목 | EC2 호스팅 | Cloudflare Pages |
|------|-----------|-----------------|
| **호스팅 비용** | $30~40/월 (인스턴스) | **$0 (무료)** |
| **대역폭 비용** | $0.09/GB (AWS) | **$0 (무제한)** |
| **SSL 인증서** | $0 (Let's Encrypt) | **$0 (자동 발급)** |
| **CDN 비용** | 별도 구매 필요 | **$0 (내장)** |
| **총 월 비용** | $50~100 (트래픽 증가 시) | **$0** |

**절약 효과**: 월 $50~100 절약 + EC2 인스턴스 사양 다운그레이드 가능

---

## 🚀 마이그레이션 로드맵

### Phase 1: 정적 사이트 먼저 (1주)
1. ✅ Main Landing Page → Cloudflare Pages
2. ✅ Calculator → Cloudflare Pages
3. ✅ Generator → Cloudflare Pages

**효과**: EC2 부하 50% 감소, 응답 속도 3~5배 향상

### Phase 2: 동적 사이트 프론트엔드 분리 (2주)
1. ⏳ Downloader Frontend → Cloudflare Pages
2. ⏳ Downloader Backend → EC2 (CORS 설정)
3. ⏳ Converter Frontend → Cloudflare Pages
4. ⏳ Converter Backend → EC2 (CORS 설정)

**효과**: EC2 부하 80% 감소, 글로벌 응답 속도 10배 향상

### Phase 3: 최적화 (진행 중)
1. ⏳ 이미지 최적화 (Cloudflare Images)
2. ⏳ 캐시 전략 최적화
3. ⏳ Analytics 연동

---

## 📚 참고 자료

- [Cloudflare Pages 공식 문서](https://developers.cloudflare.com/pages/)
- [Custom Domain 설정](https://developers.cloudflare.com/pages/platform/custom-domains/)
- [Functions (Serverless)](https://developers.cloudflare.com/pages/platform/functions/)
- [환경 변수 관리](https://developers.cloudflare.com/pages/platform/build-configuration/#environment-variables)

---

**최종 업데이트**: 2025-11-23  
**다음 업데이트 예정**: Phase 1 배포 완료 후
