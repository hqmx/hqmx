# HQMX 통합 배포 및 관리 전략 (Modular Deployment Strategy)

**작성일**: 2025-11-23
**작성자**: HQMX Development Team
**상태**: **표준 (Standard)**

## 1. 핵심 철학

1.  **모듈화 (Modularity)**: 각 서비스(Downloader, Calculator 등)는 독립적으로 배포되고 관리됩니다.
2.  **안전성 (Safety)**: 심볼릭 링크를 사용하여 배포 중단 시간을 최소화하고, 즉시 롤백(Rollback)이 가능합니다.
3.  **개발/운영 분리 (Dev/Prod Separation)**: 동일한 서버 내에서도 **개발(Dev)** 환경과 **운영(Prod)** 환경을 철저히 분리하여, 라이브 서비스에 영향을 주지 않고 테스트합니다.

## 2. 서버 디렉토리 구조 (Server Directory Structure)

메인 서버(`/home/ubuntu/hqmx/`)의 표준 구조입니다. 이 구조는 스크립트를 통해 자동으로 관리됩니다.

```bash
/home/ubuntu/hqmx/
├── services/                  # 각 서비스별 격리된 공간
│   ├── downloader/
│   │   ├── releases/          # 배포된 버전들이 저장되는 곳 (Timestamp)
│   │   │   ├── 20251123_1200/
│   │   │   └── 20251123_1400/
│   │   ├── current -> releases/20251123_1200/  # [PROD] 실제 라이브 서비스 (안정 버전)
│   │   └── dev -> releases/20251123_1400/      # [DEV]  테스트용 서비스 (개발 버전)
│   │
│   ├── converter/
│   │   ├── releases/ ...
│   │   ├── current -> ...
│   │   └── dev -> ...
│   │
│   ├── calculator/ ...
│   └── generator/ ...
│
└── shared/                    # 모든 버전이 공유하는 정적 자원 (설정, 로그, 업로드)
    ├── downloader/
    │   ├── .env               # 환경 변수 (API 키 등)
    │   └── logs/              # 로그 파일
    └── ...
```

### 환경별 접속 경로 (Nginx 설정 예시)

*   **Production (일반 사용자)**
    *   URL: `https://calculator.hqmx.net`
    *   Path: `/home/ubuntu/hqmx/services/calculator/current`
*   **Development (개발자 테스트)**
    *   URL: `https://calculator.hqmx.net/dev` (또는 별도 포트/서브도메인)
    *   Path: `/home/ubuntu/hqmx/services/calculator/dev`

## 3. 배포 프로세스 (Deployment Process)

모든 배포는 `scripts/deploy-modular.sh` 스크립트를 통해 이루어집니다.

### 3.1. 개발용 배포 (Dev Deployment)
개발 중인 기능을 서버에서 테스트할 때 사용합니다. `current` 링크는 건드리지 않습니다.

```bash
# 계산기 개발 버전을 서버의 'dev' 경로로 배포
./scripts/deploy-modular.sh --service=calculator --env=dev
```
*   **결과**: `/home/ubuntu/hqmx/services/calculator/dev` 링크가 방금 올린 버전을 가리킴.
*   **확인**: 브라우저에서 Dev 경로로 접속하여 테스트.

### 3.2. 운영용 배포 (Prod Deployment)
테스트가 완료된 버전을 라이브 서비스에 적용합니다.

```bash
# 계산기 운영 버전을 서버의 'current' 경로로 배포
./scripts/deploy-modular.sh --service=calculator --env=prod
```
*   **결과**: `/home/ubuntu/hqmx/services/calculator/current` 링크가 방금 올린 버전을 가리킴.
*   **효과**: 일반 사용자들에게 즉시 변경 사항 적용.

## 4. 초기 셋업 (Initial Setup)

서버에 이 구조가 없다면, `scripts/setup-server-structure.sh`를 실행하여 기본 뼈대를 생성합니다.

```bash
./scripts/setup-server-structure.sh
```

## 5. 롤백 (Rollback)

문제가 발생했을 때 이전 버전으로 되돌리는 방법입니다.

```bash
# SSH 접속 후
cd /home/ubuntu/hqmx/services/calculator
ln -sfn releases/20251123_1200 current  # 이전 버전 폴더로 링크 변경
```
