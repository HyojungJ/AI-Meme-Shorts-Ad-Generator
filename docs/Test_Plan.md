# 테스트 계획서 (Test Plan)

## 프로젝트 정보
- **프로젝트명**: Meme Influencer - 밈 기반 광고 영상 자동 생성 플랫폼
- **버전**: 4.0.0
- **작성일**: 2026-02-09
- **작성자**: Development Team

---

## 1. 테스트 개요

### 1.1 테스트 목적
- 밈 기반 광고 영상 자동 생성 시스템의 기능적 정확성 검증
- 사용자 인증 및 권한 관리 시스템의 보안성 확인
- AI 파이프라인(캐릭터, 음성, 시나리오, 영상 생성)의 안정성 검증
- 프론트엔드-백엔드 통합 및 배포 환경(EC2, CloudFront, Vercel)의 안정성 확인

### 1.2 테스트 범위

#### 포함 범위
- 사용자 인증 및 권한 관리 (회원가입, 로그인, JWT 토큰)
- 광고 영상 생성 워크플로우 (캐릭터 → 음성 → 시나리오 → 영상)
- 검수 및 승인 프로세스 (Client/Admin)
- 실시간 상태 업데이트 (Polling 방식)
- 파일 업로드 및 S3 스토리지 연동
- YouTube 자동 게시 기능
- 성과 분석 및 대시보드
- CORS 및 배포 환경 설정

#### 제외 범위
- 외부 AI API (OpenAI, ElevenLabs, ComfyUI) 내부 로직
- 데이터베이스 성능 튜닝
- 부하 테스트 (향후 별도 진행)

### 1.3 테스트 환경

#### 개발 환경
- **Backend**: Python 3.11, FastAPI, PostgreSQL
- **Frontend**: Next.js 14, TypeScript, TailwindCSS
- **AI Pipeline**: OpenAI GPT-4, ElevenLabs TTS, ComfyUI (LTX Video)

#### 배포 환경
- **Backend**: AWS EC2 (Ubuntu 22.04), Docker, Nginx
- **Frontend**: Vercel
- **CDN**: AWS CloudFront
- **Database**: AWS Lightsail PostgreSQL
- **Storage**: AWS S3

---

## 2. 테스트 전략

### 2.1 테스트 레벨

#### Unit Test (단위 테스트)
- CRUD 함수 검증
- 유틸리티 함수 검증
- 데이터 검증 로직

#### Integration Test (통합 테스트)
- API 엔드포인트 테스트
- 데이터베이스 연동 테스트
- 외부 서비스 연동 테스트 (S3, YouTube API)

#### System Test (시스템 테스트)
- 전체 워크플로우 End-to-End 테스트
- 사용자 시나리오 기반 테스트

#### Acceptance Test (인수 테스트)
- 실제 사용자 환경에서의 기능 검증
- 성능 및 사용성 검증

### 2.2 테스트 방법

#### Manual Testing (수동 테스트)
- UI/UX 검증
- 사용자 시나리오 테스트
- 배포 환경 검증

#### Automated Testing (자동화 테스트)
- API 엔드포인트 자동화 테스트 (Postman/pytest)
- 회귀 테스트 자동화

---

## 3. 테스트 케이스

### 3.1 인증 및 권한 관리

#### TC-AUTH-001: 회원가입
- **목적**: 새로운 사용자 계정 생성
- **전제조건**: 유효한 이메일 주소
- **테스트 데이터**:
  - 이메일: `test@example.com`
  - 비밀번호: `Test1234!`
  - 회사명: `테스트 회사`
- **예상 결과**: 
  - HTTP 200 OK
  - JWT Access Token 및 Refresh Token 반환
  - 데이터베이스에 계정 및 회사 정보 저장

#### TC-AUTH-002: 로그인 (Client)
- **목적**: 기존 사용자 로그인
- **전제조건**: 회원가입 완료된 계정
- **테스트 데이터**:
  - 이메일: `test@example.com`
  - 비밀번호: `Test1234!`
- **예상 결과**:
  - HTTP 200 OK
  - JWT Access Token 및 Refresh Token 반환
  - 사용자 정보 (account_id, company_id, role) 포함

#### TC-AUTH-003: 로그인 (Admin)
- **목적**: 관리자 계정 로그인
- **전제조건**: Admin 계정 생성 완료
- **테스트 데이터**:
  - 이메일: `admin@example.com`
  - 비밀번호: `Admin1234!`
- **예상 결과**:
  - HTTP 200 OK
  - account_type: `admin`
  - Admin 권한 부여

#### TC-AUTH-004: 토큰 갱신
- **목적**: Access Token 만료 시 Refresh Token으로 갱신
- **전제조건**: 유효한 Refresh Token
- **예상 결과**:
  - HTTP 200 OK
  - 새로운 Access Token 발급

#### TC-AUTH-005: 잘못된 비밀번호
- **목적**: 잘못된 비밀번호 입력 시 에러 처리
- **테스트 데이터**:
  - 이메일: `test@example.com`
  - 비밀번호: `WrongPassword`
- **예상 결과**:
  - HTTP 401 Unauthorized
  - 에러 메시지: "이메일 또는 비밀번호가 올바르지 않습니다"

#### TC-AUTH-006: 중복 이메일 회원가입
- **목적**: 이미 존재하는 이메일로 회원가입 시도
- **예상 결과**:
  - HTTP 400 Bad Request
  - 에러 메시지: "이미 사용 중인 이메일입니다"

---

### 3.2 광고 영상 생성 워크플로우

#### TC-VIDEO-001: 광고 요청 생성
- **목적**: 새로운 광고 영상 생성 요청
- **전제조건**: 로그인된 Client 계정
- **테스트 데이터**:
  ```json
  {
    "item_name": "테스트 상품",
    "item_category": "뷰티",
    "item_description": "피부에 좋은 천연 화장품",
    "item_url": "https://example.com/product",
    "item_images": ["https://example.com/image.jpg"],
    "character_image_prompt": "20대 여성, 밝은 미소",
    "meme_id": 1
  }
  ```
- **예상 결과**:
  - HTTP 200 OK
  - ad_id 반환
  - 워크플로우 실행 시작

#### TC-VIDEO-002: 캐릭터 이미지 생성
- **목적**: AI 기반 캐릭터 이미지 생성
- **전제조건**: 광고 요청 생성 완료
- **API**: `POST /api/v1/video/{ad_id}/character/generate`
- **예상 결과**:
  - HTTP 200 OK
  - character_id 반환
  - S3에 이미지 업로드
  - image_url 반환

#### TC-VIDEO-003: 음성 생성
- **목적**: ElevenLabs를 통한 음성 생성
- **전제조건**: 캐릭터 생성 완료
- **API**: `POST /api/v1/video/{ad_id}/voice/generate`
- **테스트 데이터**:
  ```json
  {
    "sample_text": "안녕하세요, 테스트 음성입니다.",
    "voice_description": "밝고 친근한 목소리"
  }
  ```
- **예상 결과**:
  - HTTP 200 OK
  - voice_url 반환
  - S3에 음성 파일 업로드

#### TC-VIDEO-004: 시나리오 생성
- **목적**: GPT-4 기반 시나리오 생성
- **전제조건**: 캐릭터 및 음성 승인 완료
- **API**: `POST /api/v1/video/{ad_id}/scenario/generate`
- **예상 결과**:
  - HTTP 200 OK
  - script_id 반환
  - 3개 씬으로 구성된 시나리오
  - 각 씬에 content 포함

#### TC-VIDEO-005: 영상 생성
- **목적**: ComfyUI를 통한 영상 생성
- **전제조건**: 시나리오 승인 완료
- **API**: `POST /api/v1/video/{ad_id}/video/generate`
- **예상 결과**:
  - HTTP 200 OK
  - video_id 반환
  - S3에 영상 파일 업로드
  - 생성 완료 시 status: `completed`

#### TC-VIDEO-006: 캐릭터 승인
- **목적**: 생성된 캐릭터 이미지 승인
- **API**: `POST /api/v1/video/{ad_id}/character/approve`
- **테스트 데이터**:
  ```json
  {
    "approved": true,
    "feedback": "좋습니다"
  }
  ```
- **예상 결과**:
  - HTTP 200 OK
  - 워크플로우 다음 단계로 진행

#### TC-VIDEO-007: 캐릭터 거부 및 재생성
- **목적**: 캐릭터 거부 후 수정 요청
- **API**: `POST /api/v1/video/{ad_id}/character/revise`
- **테스트 데이터**:
  ```json
  {
    "revision_notes": "더 밝은 표정으로 수정해주세요",
    "character_prompt": "20대 여성, 환한 미소, 자연스러운 메이크업"
  }
  ```
- **예상 결과**:
  - HTTP 200 OK
  - 새로운 캐릭터 이미지 생성
  - 재검수 대기 상태

#### TC-VIDEO-008: 시나리오 수정
- **목적**: 시나리오 씬별 수정 요청
- **API**: `POST /api/v1/video/{ad_id}/scenario/revise`
- **테스트 데이터**:
  ```json
  {
    "scene_revisions": [
      {
        "scene_number": 1,
        "scenario_notes": "더 재미있는 표현으로 수정"
      }
    ],
    "general_notes": "전체적으로 밝은 톤으로"
  }
  ```
- **예상 결과**:
  - HTTP 200 OK
  - 수정된 시나리오 생성

---

### 3.3 실시간 상태 업데이트

#### TC-POLL-001: 생성 상태 Polling
- **목적**: 광고 생성 진행 상태 실시간 조회
- **API**: `GET /api/v1/sse/generation-poll?token={jwt_token}`
- **예상 결과**:
  - HTTP 200 OK
  - 회사의 모든 광고 요청 상태 반환
  - 각 항목에 ad_id, status, current_stage, progress 포함

#### TC-POLL-002: Polling 주기
- **목적**: 프론트엔드에서 3초 간격으로 polling
- **예상 결과**:
  - 3초마다 자동 요청
  - 상태 변경 시 UI 업데이트
  - 토스트 알림 표시

---

### 3.4 파일 업로드 및 스토리지

#### TC-STORAGE-001: 이미지 S3 업로드
- **목적**: 생성된 이미지 S3 업로드
- **예상 결과**:
  - S3 버킷에 파일 저장
  - Public URL 반환
  - CloudFront를 통한 접근 가능

#### TC-STORAGE-002: 음성 파일 S3 업로드
- **목적**: 생성된 음성 파일 S3 업로드
- **예상 결과**:
  - S3 버킷에 파일 저장
  - Public URL 반환

#### TC-STORAGE-003: 영상 파일 S3 업로드
- **목적**: 생성된 영상 파일 S3 업로드
- **예상 결과**:
  - S3 버킷에 파일 저장
  - 파일 크기 및 duration 메타데이터 저장

---

### 3.5 Admin 기능

#### TC-ADMIN-001: 전체 영상 목록 조회
- **목적**: Admin이 모든 회사의 영상 조회
- **API**: `GET /api/v1/admin/videos/all`
- **전제조건**: Admin 계정 로그인
- **예상 결과**:
  - HTTP 200 OK
  - 모든 광고 요청 목록 반환
  - 페이지네이션 지원

#### TC-ADMIN-002: YouTube 게시
- **목적**: 완성된 영상을 YouTube에 자동 게시
- **API**: `POST /api/v1/admin/videos/{video_id}/publish`
- **테스트 데이터**:
  ```json
  {
    "channel_id": "UC...",
    "yt_title": "테스트 영상",
    "yt_description": "테스트 설명"
  }
  ```
- **예상 결과**:
  - HTTP 200 OK
  - YouTube 업로드 완료
  - youtube_url 반환

#### TC-ADMIN-003: 워크플로우 재시도
- **목적**: 실패한 워크플로우 재시도
- **API**: `POST /api/v1/admin/workflows/{execution_id}/retry`
- **예상 결과**:
  - HTTP 200 OK
  - 워크플로우 재실행
  - retry_count 증가

---

### 3.6 CORS 및 배포 환경

#### TC-DEPLOY-001: CORS Preflight 요청
- **목적**: CloudFront를 통한 CORS 검증
- **테스트 방법**:
  ```bash
  curl -X OPTIONS https://d3akm36fp2lv3d.cloudfront.net/api/v1/auth/login \
    -H "Origin: https://admeme-frontend.vercel.app" \
    -H "Access-Control-Request-Method: POST" \
    -v
  ```
- **예상 결과**:
  - HTTP 200 OK
  - `Access-Control-Allow-Origin` 헤더 포함
  - `Access-Control-Allow-Methods` 헤더 포함

#### TC-DEPLOY-002: Vercel 프리뷰 도메인 CORS
- **목적**: Vercel 프리뷰 배포 시 동적 CORS 허용
- **예상 결과**:
  - `.vercel.app`로 끝나는 모든 도메인 자동 허용
  - CORS 에러 없이 API 호출 성공

#### TC-DEPLOY-003: EC2 Security Group
- **목적**: EC2 포트 8000 외부 접근 가능 여부
- **테스트 방법**:
  ```bash
  curl http://3.36.129.41:8000/health
  ```
- **예상 결과**:
  - HTTP 200 OK
  - `{"status":"healthy","version":"4.0.0"}`

#### TC-DEPLOY-004: Docker 컨테이너 상태
- **목적**: Docker 컨테이너 정상 실행 확인
- **테스트 방법**:
  ```bash
  docker-compose ps
  ```
- **예상 결과**:
  - meme-api 컨테이너 `Up (healthy)` 상태

---

### 3.7 성과 분석

#### TC-ANALYTICS-001: 대시보드 조회
- **목적**: Client 대시보드 데이터 조회
- **API**: `GET /api/v1/analytics/dashboard`
- **예상 결과**:
  - HTTP 200 OK
  - 총 조회수, 평균 시청 시간, 참여율 등 반환

#### TC-ANALYTICS-002: 밈 성과 분석
- **목적**: 밈별 성과 데이터 조회
- **API**: `GET /api/v1/analytics/memes`
- **예상 결과**:
  - HTTP 200 OK
  - 밈별 조회수, 참여율, 전환율 반환

---

## 4. 테스트 일정

| 단계 | 기간 | 담당자 | 비고 |
|------|------|--------|------|
| 테스트 계획 수립 | 2026-02-09 | 전체 팀 | 완료 |
| Unit Test | 2026-02-10 ~ 02-11 | Backend 개발자 | |
| Integration Test | 2026-02-12 ~ 02-14 | Backend/Frontend 개발자 | |
| System Test | 2026-02-15 ~ 02-17 | QA 팀 | |
| Acceptance Test | 2026-02-18 ~ 02-19 | Product Owner | |
| 버그 수정 | 2026-02-20 ~ 02-21 | 전체 팀 | |
| 최종 검증 | 2026-02-22 | 전체 팀 | |

---

## 5. 테스트 도구

### 5.1 Backend Testing
- **pytest**: Python 단위 테스트
- **Postman**: API 엔드포인트 테스트
- **curl**: CLI 기반 API 테스트

### 5.2 Frontend Testing
- **Jest**: JavaScript 단위 테스트
- **React Testing Library**: 컴포넌트 테스트
- **Cypress**: E2E 테스트 (선택사항)

### 5.3 Deployment Testing
- **Docker**: 컨테이너 환경 테스트
- **AWS CLI**: 배포 환경 검증

---

## 6. 리스크 관리

### 6.1 주요 리스크

| 리스크 | 영향도 | 발생 가능성 | 대응 방안 |
|--------|--------|-------------|-----------|
| 외부 AI API 장애 | 높음 | 중간 | Retry 로직, Fallback 메커니즘 |
| CloudFront SSE 호환 문제 | 높음 | 높음 | Polling 방식으로 대체 (완료) |
| S3 업로드 실패 | 중간 | 낮음 | Retry 로직, 에러 핸들링 |
| Database 연결 끊김 | 높음 | 낮음 | Connection Pool, Auto-reconnect |
| CORS 에러 | 중간 | 중간 | 동적 CORS 미들웨어 (완료) |

---

## 7. 테스트 완료 기준

### 7.1 Pass Criteria
- 모든 Critical 테스트 케이스 통과
- 주요 사용자 시나리오 End-to-End 테스트 통과
- CORS 및 배포 환경 검증 완료
- 성능 기준 충족 (API 응답 시간 < 3초)

### 7.2 Exit Criteria
- Critical/High 우선순위 버그 0건
- Medium 우선순위 버그 < 5건
- 테스트 커버리지 > 70%

---

## 8. 참고 문서
- [EC2 Docker 배포 가이드](./EC2_Docker_Deploy_Guide.md)
- [API 문서](http://localhost:8000/docs)
- [프로젝트 README](../README.md)
