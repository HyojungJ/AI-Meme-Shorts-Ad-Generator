# AI 파이프라인 아키텍처 및 역할 분담

> 작성일: 2026-01-16
> 최종 수정: 2026-01-19

---

## 1. 프로젝트 개요

밈 데이터를 수집하고, 사용자가 선택한 캐릭터와 밈으로 숏폼 영상을 자동 생성하는 SaaS 플랫폼.

### 핵심 흐름

```
[밈 수집] → [DB 저장] → [사용자 요청] → [시나리오 생성] → [영상 생성] → [완료]
   ↑                          ↑
 자동화                    사용자 트리거
(스케줄러)                  (버튼 클릭)
```

---

## 2. 시스템 아키텍처

### 2.1 전체 구조

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              시스템 아키텍처                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────┐                                │
│  │  자동화 (스케줄러)                        │                                │
│  │                                         │                                │
│  │  MemeCollector (밈 수집)                  │                                │
│  │  ├── Collector Worker (정보 수집)        │                                │
│  │  ├── Analyzer Worker (영상 분석)         │                                │
│  │  ├── Verifier Worker (품질 검증)         │                                │
│  │  └── DB에 meme 테이블 저장               │                                │
│  └─────────────────────────────────────────┘                                │
│                          │                                                   │
│                          ▼                                                   │
│                    ┌──────────┐                                             │
│                    │    DB    │                                             │
│                    │ (meme)   │                                             │
│                    └──────────┘                                             │
│                          │                                                   │
│                          ▼                                                   │
│  ┌─────────────────────────────────────────┐                                │
│  │  사용자 트리거 (온디맨드)                 │                                │
│  │                                         │                                │
│  │  1. 밈 선택 (DB에서 조회)                │                                │
│  │  2. 캐릭터 선택/생성                     │                                │
│  │  3. "생성" 버튼 클릭                     │                                │
│  │           ↓                             │                                │
│  │  ContentPipeline (Celery Worker)        │                                │
│  │  ├── ScenarioAgent (시나리오 생성)       │                                │
│  │  ├── QG1 검증                           │                                │
│  │  ├── TTS 생성                           │                                │
│  │  ├── QG2 검증                           │                                │
│  │  ├── Sora 영상 생성                     │                                │
│  │  ├── QG3 검증                           │                                │
│  │  ├── FFmpeg 합성                        │                                │
│  │  └── S3 업로드                          │                                │
│  └─────────────────────────────────────────┘                                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 파이프라인 분리

| 구분 | Agent | 실행 방식 | 트리거 |
|------|-------|----------|--------|
| 자동화 | MemeCollector | 스케줄러 (Cron/Celery Beat) | 매일 자동 |
| 사용자 트리거 | ContentPipeline | Celery Worker | 버튼 클릭 |

---

## 3. 역할 분담

### 3.1 팀 구성

| 역할 | 담당 업무 |
|------|----------|
| **파이프라인 담당** | 전체 아키텍처, 에이전트 통합, 밈 수집, 스케줄러 |
| **시나리오 담당** | ScenarioAgent 노드 구현 (skeleton, dialogue, finalizer) |
| **영상 담당** | VideoGenerator 노드 구현 (TTS, Sora, Compose) |
| **검증 담당** | Quality Gate 노드 구현 (QG1, QG2, QG3, QG4) |
| **API 담당** | FastAPI 백엔드, 인증, DB 연동 |
| **프론트엔드 담당** | Next.js UI, 사용자 인터페이스 |
| **DevOps 담당** | AWS 배포, CI/CD, 모니터링 |

### 3.2 협업 구조

```
                    ┌─────────────────┐
                    │ 파이프라인 담당  │
                    │ (뼈대 + 인터페이스)│
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │ 시나리오 담당 │   │  영상 담당   │   │  검증 담당   │
    │ (노드 구현)  │   │ (노드 구현)  │   │ (노드 구현)  │
    └─────────────┘   └─────────────┘   └─────────────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   API 담당      │
                    │ (Celery 연동)   │
                    └─────────────────┘
```

---

## 4. 담당별 작업 목록

### 4.1 파이프라인 담당

#### 에이전트 통합
| 작업 | 설명 |
|------|------|
| PipelineState 스키마 정의 | 전체 파이프라인 공유 State 타입 |
| 노드 입출력 인터페이스 정의 | 각 노드가 받을/반환할 데이터 명세 |
| ContentPipeline Graph 구조 | 노드 연결 순서, 조건부 라우팅 |
| Stub 노드 작성 | 팀원 구현 전 테스트용 더미 노드 |
| Finalize 노드 | S3 업로드, DB 저장 |
| 진행률 관리 | Redis에 진행률 저장/조회 |
| Celery 태스크 정의 | 메인 태스크, 에러 핸들링 |

#### 밈 수집 에이전트 (MemeCollector)

**Multi-Agent 구조**
```
┌─────────────────────────────────────────────────────────┐
│               MemeCollector Graph                        │
├─────────────────────────────────────────────────────────┤
│  Collector → Analyzer → Verifier → Finalize             │
│     │           │          │                            │
│     ▼           ▼          ▼                            │
│  [Tools]    [Grounding] [Reflexion]                     │
└─────────────────────────────────────────────────────────┘
```

| Worker | 역할 | 패턴 | 도구 |
|--------|------|------|------|
| Collector | 밈 정보 수집 | ReAct | namuwiki, naver, youtube, video_analyzer, usage_extractor |
| Analyzer | 영상 제작용 분석 | Grounding | LLM (GPT-4o) |
| Verifier | 품질 검증 + 피드백 | Reflexion | LLM self-critique |

**수집 도구 (Tools)**
| 도구 | 용도 |
|------|------|
| search_namuwiki | 밈 정의, 유래, 핵심 대사 |
| search_naver_blog/news | 맥락, 사용례 |
| search_youtube_shorts/videos | 참고 영상 검색 |
| analyze_meme_video | Gemini Vision 프레임 분석 |
| extract_usage_examples | 활용 예시 추출 (상황/맥락 + 사용법) |

**수집 데이터 (MemeOutput)**
| 필드 | 용도 |
|------|------|
| definition | 시나리오 맥락 이해 |
| key_phrase | 대사 작성 (예: "무야호~!") |
| motion_prompt | Sora 프롬프트 (영어) |
| emotion | TTS 톤 힌트 (excited, sarcastic, playful 등) |
| usage_examples | 활용 예시 (context, usage, tone) |
| reference_videos | 참고 YouTube 영상 |
| origin | 출처 (source, creator, date) |

| 작업 | 설명 |
|------|------|
| Verifier 검증 | 필수 필드, 정보 일관성, motion_prompt 품질 |
| DB 저장 노드 | meme, video, audio 테이블 저장 |
| 스케줄러 구축 | Celery Beat 주기적 실행 |
| 트렌드 밈 탐지 | Google Trends 등 연동 |

---

### 4.2 시나리오 담당

| 작업 | 설명 |
|------|------|
| skeleton 노드 | 시나리오 골격 생성 |
| dialogue 노드 | 캐릭터별 대사 생성 |
| finalizer 노드 | 최종 시나리오 완성 |
| 캐릭터 동적화 | 하드코딩 제거, 동적 프롬프트 |

**입력**: meme_data (definition, key_phrase, usage_examples 포함), characters, style
**출력**: scenario (scenes, beats, dialogues)

**meme_data 활용**
- `definition`: 밈 맥락 이해
- `key_phrase`: 대사에 반영
- `usage_examples`: 상황별 활용법 참고 (context, usage, tone)

---

### 4.3 영상 담당

| 작업 | 설명 |
|------|------|
| TTS 노드 | OpenAI TTS로 음성 생성 |
| Sora 노드 | Sora API로 영상 생성 |
| Compose 노드 | FFmpeg로 음성+영상 합성 |

**입력**: scenario, meme_data
**출력**: final_video_path

**meme_data 활용**
- `motion_prompt`: Sora 영상 생성 프롬프트 (영어, Gemini Vision 분석 기반)
- `emotion`: TTS 톤 힌트 (ElevenLabs stability/style 파라미터용)

---

### 4.4 검증 담당

| 작업 | 설명 |
|------|------|
| QG1 시나리오 검증 | 구조, 캐릭터 일관성, 밈 반영도 (60점 기준) |
| QG2 TTS 검증 | 음성 길이, 무음 비율 |
| QG3 Sora 검증 | 영상 생성 성공, 길이 |
| QG4 합성 검증 | FFmpeg 성공, 싱크 |
| 재시도 로직 | 실패 시 재생성 (최대 2-3회) |

---

### 4.5 API 담당

| 작업 | 설명 |
|------|------|
| FastAPI 프로젝트 구조 | 라우터, 서비스 레이어 |
| Firebase 인증 | 토큰 검증, 미들웨어 |
| 사용자/캐릭터 API | CRUD 엔드포인트 |
| 밈 API | 목록, 상세 조회 |
| 영상 생성 API | POST /generate, 상태 조회 |
| Celery 태스크 발행 | API → Worker 연동 |
| Redis 연결 | 상태 캐싱 |

---

## 5. E2E 시나리오

### 5.1 사용자 여정

```
1. 랜딩 페이지 접속
   └── "AI로 밈 영상 만들기" 소개

2. 로그인 (Google)
   └── Firebase Auth → 무료 크레딧 3개 지급

3. 대시보드
   ├── 내 영상 목록
   ├── 남은 크레딧 확인
   └── [새 영상 만들기] 버튼

4. 영상 생성 위자드
   ├── Step 1: 캐릭터 선택 (프리셋 또는 커스텀)
   ├── Step 2: 밈 선택 (검색, 카테고리)
   ├── Step 3: 스타일 선택 (톤, 길이)
   └── Step 4: 확인 & [생성하기] 클릭

5. 생성 진행 화면
   ├── "시나리오 생성 중..." (10초)
   ├── "음성 생성 중..." (30초)
   ├── "영상 생성 중..." (2-3분)
   └── "최종 합성 중..." (30초)

6. 완료
   ├── 영상 미리보기
   ├── [다운로드] 버튼
   └── [공유하기] 버튼
```

### 5.2 시스템 내부 흐름

```
[사용자]          [Frontend]        [FastAPI]         [Celery Worker]
   │                  │                 │                    │
   │ 생성 버튼 클릭    │                 │                    │
   │ ───────────────▶│                 │                    │
   │                  │ POST /generate  │                    │
   │                  │ ──────────────▶│                    │
   │                  │                 │ ── 태스크 발행 ───▶│
   │                  │ ◀────────────── │                    │
   │ ◀─────────────── │ (request_id)    │                    │
   │                  │                 │                    │
   │                  │                 │         ┌──────────┴──────────┐
   │                  │                 │         │   ContentPipeline   │
   │ 상태 폴링        │                 │         ├─────────────────────┤
   │ ───────────────▶│ GET /status     │         │ 1. Scenario         │
   │                  │ ──────────────▶│ Redis   │ 2. QG1              │
   │                  │ ◀────────────── │ ◀───────│ 3. TTS              │
   │ ◀─────────────── │ "영상 생성 중"   │         │ 4. QG2              │
   │                  │                 │         │ 5. Sora             │
   │                  │                 │         │ 6. QG3              │
   │ ───────────────▶│                 │         │ 7. Compose          │
   │                  │ ──────────────▶│         │ 8. S3 Upload        │
   │                  │ ◀────────────── │ ◀───────│                     │
   │ ◀─────────────── │ (video_url)     │         └─────────────────────┘
   │                  │                 │
```

### 5.3 백그라운드: 밈 수집

```
[스케줄러] ──(매일 새벽)──▶ [MemeCollector Graph]
                                    │
                          ┌─────────┴─────────┐
                          │    Collector      │
                          │  (ReAct 패턴)     │
                          ├───────────────────┤
                          │ • 나무위키 크롤링  │
                          │ • 네이버 검색      │
                          │ • YouTube 검색    │
                          │ • 활용 예시 추출   │
                          └─────────┬─────────┘
                                    ▼
                          ┌───────────────────┐
                          │     Analyzer      │
                          │  (Grounding)      │
                          ├───────────────────┤
                          │ • 수집 정보 종합   │
                          │ • motion_prompt   │
                          │ • emotion 추출    │
                          └─────────┬─────────┘
                                    ▼
                          ┌───────────────────┐
                          │     Verifier      │
                          │  (Reflexion)      │
                          ├───────────────────┤
                          │ • 품질 검증       │
                          │ • 부족시 재수집    │
                          └─────────┬─────────┘
                                    ▼
                          ┌───────────────────┐
                          │    Finalize       │
                          ├───────────────────┤
                          │ • MemeOutput 생성 │
                          │ • usage_examples  │
                          │ • DB 저장         │
                          └─────────┬─────────┘
                                    ▼
                          [DB: meme 테이블]
                                    │
                                    ▼
                        사용자가 /memes에서 조회
```

---

## 6. 협업 인터페이스

### 6.1 공유 State (PipelineState)

```
PipelineState
├── Input (파이프라인 담당이 채움)
│   ├── request_id
│   ├── meme_id
│   ├── meme_data
│   ├── characters
│   └── style, video_length
│
├── Scenario (시나리오 담당이 채움)
│   └── scenario
│
├── Video (영상 담당이 채움)
│   ├── tts_files
│   ├── video_files
│   └── final_video_path
│
├── QG (검증 담당이 채움)
│   └── qg_results
│
└── Control (파이프라인 담당이 관리)
    ├── current_stage
    ├── progress
    ├── retry_counts
    └── errors
```

### 6.2 노드 인터페이스 규칙

각 노드는 다음 규칙을 따름:
1. `PipelineState`를 입력으로 받음
2. 자신의 결과를 State에 저장
3. `PipelineState`를 반환
4. 에러 발생 시 `errors` 리스트에 추가

---

## 7. 기술 스택

| 영역 | 기술 |
|------|------|
| 파이프라인 | LangGraph, Celery |
| 밈 수집 | LangChain (ReAct Agent), OpenAI GPT-4o |
| 영상 분석 | Gemini 2.0 Flash Vision |
| 시나리오 | LangChain, OpenAI GPT-4 |
| 영상 | OpenAI TTS / ElevenLabs, Sora API, FFmpeg |
| API | FastAPI |
| 인증 | Firebase Auth |
| DB | PostgreSQL |
| 캐시/큐 | Redis |
| 스토리지 | AWS S3 |
| 배포 | AWS ECS |

---

*문서 버전: v1.1*
