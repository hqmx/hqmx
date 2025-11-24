# HQMX 아키텍처 비교: All-in-EC2 vs Cloudflare + EC2

**작성일**: 2025-11-23
**작성자**: HQMX Lead Engineer

## 1. 결론 요약 (Executive Summary)

**"Cloudflare (Frontend) + EC2 (Backend)" 조합이 압도적으로 유리합니다.**

현재 HQMX 프로젝트가 커지고 있고(Downloader, Converter, Calculator, Generator), 글로벌 서비스(21개 언어)를 지향하므로, **프론트엔드와 정적 자산(Image, JS, CSS)을 Cloudflare로 분리하는 것은 선택이 아닌 필수**에 가깝습니다.

| 비교 항목 | All-in-EC2 (기존) | Cloudflare + EC2 (추천) | 승자 |
| :--- | :--- | :--- | :--- |
| **비용 (Cost)** | 트래픽 증가 시 AWS 데이터 전송 비용 폭탄 위험 | 정적 트래픽 100% 무료 (Cloudflare) | 🏆 **Cloudflare** |
| **속도 (Speed)** | 서버 위치(예: 미국)와 먼 국가(한국, 유럽)는 느림 | 전 세계 Edge 서버에서 즉시 로딩 (CDN) | 🏆 **Cloudflare** |
| **서버 부하** | 정적 파일 요청까지 EC2가 처리 (CPU/RAM 낭비) | EC2는 오직 API/다운로드/변환만 집중 | 🏆 **Cloudflare** |
| **보안 (Security)** | EC2 IP 노출 위험, DDoS 취약 | EC2 IP 은폐, Cloudflare WAF 보호 | 🏆 **Cloudflare** |
| **관리 난이도** | 배포 파이프라인 1개 (단순) | 배포 파이프라인 2개 (Frontend/Backend 분리) | 🔺 **All-in-EC2** |

---

## 2. 상세 분석

### A. 비용 (Cost Efficiency)
*   **AWS EC2**: 서버 비용뿐만 아니라 **Data Transfer Out(데이터 전송료)** 비용이 비쌉니다 ($0.09/GB). 이미지나 JS 파일이 많아질수록 비용이 기하급수적으로 늘어납니다.
*   **Cloudflare**: 정적 콘텐츠 캐싱 및 전송이 **무료**입니다. EC2에서 나가는 트래픽을 획기적으로 줄여주므로 AWS 청구서를 방어하는 가장 좋은 방패입니다.

### B. 성능 (Global Performance)
*   **HQMX의 특성**: 21개 언어를 지원하는 글로벌 서비스입니다.
*   **All-in-EC2**: 한국 사용자가 미국 서버에 접속하면 왕복 지연시간(Latency)이 발생하여 초기 로딩이 느립니다.
*   **Cloudflare**: 한국 사용자는 서울 노드에서, 유럽 사용자는 런던 노드에서 HTML/JS/CSS를 받아옵니다. **"즉시 로딩"** 경험을 제공합니다.

### C. 서버 리소스 최적화
*   **현재 문제**: `yt-dlp`와 `ffmpeg`는 CPU를 많이 씁니다. 여기에 웹페이지 서빙까지 시키면 서버가 버거워합니다.
*   **해결책**:
    *   **Frontend (Cloudflare)**: HTML, CSS, JS, 로고, 아이콘 등 가벼운 파일 처리.
    *   **Backend (EC2)**: 오직 `yt-dlp`, `ffmpeg` 같은 무거운 작업과 API 응답에만 집중.
    *   결과적으로 더 낮은 사양의 EC2로도 더 많은 사용자를 감당할 수 있습니다.

---

## 3. 추천 마이그레이션 전략 (Phased Approach)

갑작스러운 변경은 위험하므로 3단계로 진행하는 것을 추천합니다.

### 1단계: Cloudflare Proxy 도입 (즉시 가능)
*   **방법**: DNS 설정에서 구름 아이콘을 켜서(Orange Cloud) 프록시 모드로 전환.
*   **효과**: 코드 수정 없이 CDN 캐싱, 보안, SSL 적용 효과를 즉시 얻음.
*   **난이도**: 하 (설정만 변경)

### 2단계: 정적 사이트 완전 분리 (Calculator, Generator)
*   **대상**: 백엔드가 없거나 가벼운 `calculator`, `generator`, `main`.
*   **방법**: GitHub Repo를 Cloudflare Pages에 연결하여 자동 배포.
*   **효과**: EC2 부하 50% 감소, 배포 속도 10초 이내.
*   **난이도**: 중 (DNS 및 배포 설정)

### 3단계: 동적 서비스 프론트엔드 분리 (Downloader, Converter)
*   **대상**: `downloader`, `converter`.
*   **방법**: 프론트엔드 코드(HTML/JS)는 Cloudflare Pages로, 백엔드 API는 EC2로 분리.
*   **주의**: CORS(Cross-Origin) 설정 필요.
*   **난이도**: 상 (코드 및 아키텍처 수정)

## 4. 결론
**"몸덩이가 커지면 옷을 나눠 입어야 합니다."**
지금이 바로 그 타이밍입니다. 1단계(Proxy)부터 시작해서 점진적으로 2단계(정적 사이트 분리)로 넘어가는 것이 엔지니어링 관점에서 가장 현명한 선택입니다.
