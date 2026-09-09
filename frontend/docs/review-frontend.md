# Frontend 코드 품질 및 UX 리뷰

> 리뷰 일자: 2026-02-08
> 리뷰 대상: `/Users/kimjm/Desktop/meme-fluencer/frontend/src`
> 기술 스택: Next.js 14 (App Router), React 18, TypeScript 5.9, Tailwind CSS 3

---

## 목차
1. [프로젝트 구조](#1-프로젝트-구조)
2. [컴포넌트 설계](#2-컴포넌트-설계)
3. [상태 관리](#3-상태-관리)
4. [API 통신](#4-api-통신)
5. [타입 안전성](#5-타입-안전성)
6. [UI/UX](#6-uiux)
7. [테스트](#7-테스트)
8. [성능](#8-성능)

---

## 1. 프로젝트 구조

### 현재 상태

Next.js 14 App Router를 사용하며, Route Group으로 `(auth)`, `(dashboard)`, `admin`을 분리한 구조. 공용 컴포넌트는 `components/`, 훅은 `hooks/`, API 레이어는 `lib/api/`에 위치.

```
src/
├── app/
│   ├── (auth)/login/         # 로그인
│   ├── (dashboard)/          # 사용자 대시보드
│   │   ├── main/             # 메인 대시보드
│   │   ├── user/             # 영상 목록, 상세, 요청
│   │   └── profile/          # 프로필
│   └── admin/                # 관리자
├── components/
│   ├── auth/
│   ├── forms/
│   ├── layout/
│   └── ui/
├── contexts/
├── hooks/
├── lib/
│   ├── api/
│   └── constants.ts
└── types/
```

### 발견된 문제점

**[Warning] index.ts re-export 패턴 사용**
`lib/api/index.ts:1-104` -- CLAUDE.md에서 `index.ts`로 re-export하는 것을 금지하고 있으나, 104줄에 걸쳐 모든 API 모듈을 re-export하고 있다. 프로젝트 컨벤션 위반.

**[Warning] @types 패키지가 dependencies에 위치**
`package.json:28-29` -- `@types/node`, `@types/react`가 `devDependencies`가 아닌 `dependencies`에 있다. 빌드 시 불필요하게 프로덕션 번들에 영향을 줄 수 있고, 패키지 역할 분류가 부정확하다.

**[Info] contexts 디렉토리 분리**
`contexts/GenerationContext.tsx`만 별도 디렉토리에 있다. 나머지 Context(Auth, Theme, Toast)는 `hooks/`와 `components/ui/`에 분산되어 있어 일관성이 부족하다. AuthProvider는 `hooks/useAuth.tsx`에, ThemeProvider는 `hooks/useTheme.tsx`에, ToastProvider는 `components/ui/Toast.tsx`에 각각 위치.

### 개선 제안
- `lib/api/index.ts`를 제거하고, 각 파일에서 직접 import하도록 변경 (CLAUDE.md 규칙 준수)
- `@types/node`, `@types/react`를 `devDependencies`로 이동
- Context/Provider 위치를 `contexts/` 디렉토리로 통일하거나, 현재처럼 분산할 경우 명확한 규칙 문서화

---

## 2. 컴포넌트 설계

### 현재 상태

대부분의 컴포넌트가 `'use client'` 디렉티브를 사용하는 CSR 방식. 33개 파일에서 `'use client'`를 선언. UI 컴포넌트(Toast, Skeleton, FileDropzone)는 잘 분리되어 있으나, 몇몇 페이지 컴포넌트가 과도하게 크다.

### 발견된 문제점

**[Critical] CLAUDE.md 200줄 제한 초과 -- 대형 컴포넌트 다수 존재**

| 파일 | 줄 수 | 초과 배율 |
|------|-------|----------|
| `app/(dashboard)/user/video/[id]/page.tsx` | 1,547줄 | **7.7x** |
| `components/forms/VideoRequestForm.tsx` | 1,098줄 | **5.5x** |
| `lib/api/analytics.ts` | 1,013줄 | 5.1x (API 파일) |
| `lib/api/video.ts` | 782줄 | 3.9x (API 파일) |
| `app/page.tsx` (랜딩) | 531줄 | 2.7x |
| `app/(dashboard)/main/page.tsx` | 353줄 | 1.8x |
| `app/(dashboard)/user/page.tsx` | 380줄 | 1.9x |

CLAUDE.md 규칙: "컴포넌트는 한 파일에 200줄 이하"를 대부분의 주요 페이지가 위반.

**[Warning] GradientMesh 컴포넌트 4회 중복 정의**

동일한 `GradientMesh` 함수가 4개 파일에 각각 별도로 정의되어 있다:
- `components/auth/LoginForm.tsx:8`
- `app/page.tsx:6`
- `app/(dashboard)/DashboardContent.tsx:9`
- `app/admin/AdminLayoutContent.tsx:62`

**[Warning] Sidebar에서 네비게이션 렌더링 중복**
`components/layout/Sidebar.tsx` -- 데스크톱과 모바일 사이드바에서 동일한 네비게이션 항목을 별도 JSX로 두 번 렌더링.

**[Info] 랜딩 페이지 단일 파일 구조**
`app/page.tsx:531줄` -- Navbar, HeroSection, FeaturesSection, ProcessSection 등 모든 섹션이 한 파일에 포함. CLAUDE.md에서 "과도한 컴포넌트 분리 금지"를 언급하므로 현재 구조가 의도적일 수 있으나, 531줄은 200줄 기준의 2.7배.

### 개선 제안
- `video/[id]/page.tsx` (1,547줄): ProgressStepper, AssetReview, ScenarioReview, VideoPlayer, PerformanceCharts 등 논리적 섹션 단위로 분리 (가장 시급)
- `VideoRequestForm.tsx` (1,098줄): 폼 스텝별 분리 또는 밈 선택/캐릭터 선택 섹션을 별도 컴포넌트로 추출
- `GradientMesh`를 `components/ui/GradientMesh.tsx`로 추출하여 공유
- Sidebar 네비게이션 렌더링을 함수로 추출하여 중복 제거

---

## 3. 상태 관리

### 현재 상태

React Context API를 사용한 전역 상태 관리:
- `AuthProvider` (`hooks/useAuth.tsx`) -- 인증 상태
- `ThemeProvider` (`hooks/useTheme.tsx`) -- 다크/라이트 테마
- `ToastProvider` (`components/ui/Toast.tsx`) -- 알림
- `GenerationProvider` (`contexts/GenerationContext.tsx`) -- SSE 실시간 생성 상태

Provider 중첩 순서: `ThemeProvider > AuthProvider > ToastProvider > GenerationProvider`

### 발견된 문제점

**[Warning] video/[id]/page.tsx에서 과도한 useState 사용**
`app/(dashboard)/user/video/[id]/page.tsx` -- 단일 컴포넌트에서 15개 이상의 `useState` 훅 사용. 관련 상태를 그룹화하지 않아 가독성과 유지보수성이 떨어진다.

**[Warning] 상태 매핑 로직 4곳 중복**

동일한 "백엔드 상태 -> 프론트엔드 상태" 변환 로직이 여러 곳에 분산:

1. `lib/constants.ts:15-54` -- `STATUS_CONFIG`, `STATUS_CONFIG_WITH_BORDER`, `ADMIN_STATUS_CONFIG` (3개 객체)
2. `contexts/GenerationContext.tsx:56-93` -- `mapBackendStatus()` 함수
3. `lib/api/video.ts:31-57` -- `transformWorkflowToVideo()` 내 `statusMap`
4. `app/(dashboard)/user/video/[id]/page.tsx:19-28` -- `progressSteps`, `STATUS_PROGRESS`

각각 매핑 키와 값이 미묘하게 다르며, 새로운 상태 추가 시 4곳 모두 수정이 필요해 버그 유발 가능성이 높다.

**[Info] useApi 훅의 stale closure 가능성**
`hooks/useApi.ts:36` -- `fetcher` 함수가 `useEffect` 의존성 배열에 포함되지 않고, `trigger` 카운터로만 re-fetch를 트리거한다. 호출 측에서 `fetcher`를 인라인 함수로 전달할 경우, 외부 변수(예: 필터, ID)가 변경되어도 이전 클로저의 값을 참조할 수 있다. 다만, 대부분의 사용처에서 `refetch()`로 명시적 재호출하므로 실제 버그 가능성은 제한적.

### 개선 제안
- 상태 매핑을 `lib/status.ts` 등 단일 파일로 통합하고, 모든 곳에서 해당 유틸리티를 참조
- `video/[id]/page.tsx`의 관련 useState들을 `useReducer`나 객체 상태로 그룹화
- `useApi`에 `deps` 파라미터를 추가하거나, fetcher를 의존성에 포함 (useCallback 적용)

---

## 4. API 통신

### 현재 상태

`lib/api/client.ts`에서 인증 토큰 관리, 자동 갱신, API 요청 래퍼를 제공. `MOCK_MODE`를 통해 백엔드 없이도 로컬 개발 가능. SSE(Server-Sent Events)로 실시간 생성 상태를 수신.

### 발견된 문제점

**[Critical] SSE 연결 시 토큰이 URL 쿼리 파라미터로 노출**
`contexts/GenerationContext.tsx:115`
```ts
const es = new EventSource(`${API_URL}/api/v1/sse/generation-status?token=${token}`)
```
JWT 토큰이 URL에 포함되어 브라우저 히스토리, 서버 액세스 로그, 네트워크 프록시에 기록될 수 있다. EventSource API가 커스텀 헤더를 지원하지 않는 제약이 있으나, 보안상 단기 토큰(SSE 전용) 발급이나 `EventSourcePolyfill` 라이브러리를 통한 헤더 전송 방식을 고려해야 한다.

**[Warning] apiRequest에서 unsafe null cast**
`lib/api/client.ts:158`
```ts
if (!text) return null as T
```
응답 본문이 비어있을 때 `null`을 `T`로 강제 캐스팅. 호출 측에서 `T` 타입의 속성에 바로 접근할 경우 런타임 에러 발생 가능. `T | null` 반환 타입으로 변경하거나, `void` 처리가 필요.

**[Warning] 프로덕션 코드에 console.log 8건 잔존**

총 3개 파일에서 8건의 `console.log`가 발견됨:
- `lib/api/video.ts:59` -- 상태 변환 디버그 로그
- `components/forms/VideoRequestForm.tsx:101,114,220,222,231,233` -- 밈 정렬 및 프로필 로딩 로그
- `app/(dashboard)/user/video/[id]/page.tsx:168` -- 비디오 데이터 로드 로그

프로덕션 빌드에 포함되면 사용자 브라우저 콘솔에 내부 정보가 노출된다.

**[Warning] Mock 모드 분기가 각 API 함수에 산재**
`lib/api/video.ts`, `lib/api/auth.ts` 등 -- 각 API 함수 내에서 `if (MOCK_MODE)` 분기가 반복. Mock 레이어를 API 클라이언트 수준에서 통합 처리하면 코드 중복을 줄일 수 있다.

**[Info] Token refresh 경쟁 조건 처리**
`lib/api/client.ts:41-51` -- subscriber 패턴으로 동시 요청 시 토큰 갱신 경쟁 조건을 적절히 처리하고 있다. 좋은 패턴.

### 개선 제안
- SSE 토큰을 URL에서 제거하고, 단기 SSE 전용 토큰으로 전환하거나 `EventSourcePolyfill` 사용
- `apiRequest` 반환 타입을 `T | null`로 변경
- `console.log` 전수 제거 또는 환경 변수 기반 logger 유틸리티로 교체
- Mock 모드를 API 클라이언트 레벨에서 Proxy/Interceptor 패턴으로 처리

---

## 5. 타입 안전성

### 현재 상태

`tsconfig.json`에서 `strict: true` 활성화. `types/index.ts` (486줄)에서 프론트엔드 타입과 백엔드 API 응답 타입을 함께 정의. VideoStatus는 25개 이상의 상태를 포함하는 union type.

### 발견된 문제점

**[Warning] User 타입 중복 정의**

`types/index.ts:95-106`와 `hooks/useAuth.tsx:6-16`에서 `User` 타입이 각각 독립적으로 정의되어 있다. 두 타입은 필드가 미묘하게 다르다:

| 필드 | types/index.ts | hooks/useAuth.tsx |
|------|---------------|-------------------|
| `role` | `'manager' \| 'member'` | 없음 |
| `profile_img` | `string \| null` | `string \| null \| undefined` (optional) |
| `is_admin` | `boolean` | `boolean \| undefined` (optional) |
| `access_token` | `string` | `string \| undefined` (optional) |

동일한 엔티티에 대해 두 개의 타입이 존재하면 타입 불일치 버그가 발생하기 쉽다.

**[Warning] 과도한 as 캐스팅**
`lib/api/video.ts:13` -- `project.status as Video['status']`
`lib/api/video.ts:21` -- `project.meme_type as Video['memeType']`
백엔드 응답값을 검증 없이 캐스팅. 백엔드가 예상치 못한 값을 반환하면 런타임에서 잡지 못한다.

**[Info] types/index.ts가 프론트엔드와 백엔드 타입을 혼합**
`types/index.ts` (486줄)에 `Video`, `User` 등 프론트엔드 도메인 타입과 `ProjectResponse`, `WorkflowStatusResponse` 등 API 응답 타입이 함께 존재. 분리하면 관심사 구분이 명확해진다.

### 개선 제안
- `hooks/useAuth.tsx`의 `User` 타입을 `types/index.ts`의 정의를 import하여 사용하도록 통합
- 백엔드 응답에 대한 런타임 검증 유틸리티 도입 (간단한 타입 가드 함수)
- `types/index.ts`를 `types/domain.ts`와 `types/api.ts`로 분리 검토

---

## 6. UI/UX

### 현재 상태

Tailwind CSS 기반의 다크/라이트 테마 지원. CSS 변수를 활용한 테마 시스템. 반응형 디자인 적용. 접근성 관련 패턴이 일부 구현됨.

### 발견된 문제점

**[Info] 접근성 패턴 부분 적용**

좋은 패턴:
- `components/ui/Toast.tsx` -- `role="alert"`, `aria-live="assertive"` 적용
- `app/(dashboard)/user/page.tsx` -- `role="link"`, `tabIndex={0}`, `onKeyDown` 키보드 네비게이션
- `app/globals.css` -- `prefers-reduced-motion` 미디어 쿼리로 애니메이션 감소 지원

미흡한 부분:
- 폼 입력 필드에 `aria-label` 또는 연관된 `<label>` 요소가 일관되지 않음
- 모달/드롭다운에 포커스 트래핑(focus trap) 미구현
- Skip navigation 링크 없음

**[Info] Error Boundary 적절히 구현**
`app/(dashboard)/error.tsx`, `app/(dashboard)/main/error.tsx`, `app/(dashboard)/user/error.tsx`, `app/(dashboard)/user/video/[id]/error.tsx` -- 각 주요 경로에 Next.js error boundary가 적용되어 있어, 에러 발생 시 사용자에게 적절한 폴백 UI를 제공.

**[Info] 로딩 상태 처리**
대부분의 페이지에서 Skeleton 컴포넌트나 로딩 스피너를 사용하여 로딩 상태를 표시. `app/(dashboard)/main/page.tsx`에서 Skeleton loading이 잘 구현되어 있다.

**[Info] Not Found 페이지**
`app/not-found.tsx` -- 커스텀 404 페이지 구현으로 사용자 경험 향상.

### 개선 제안
- 폼 필드에 일관된 `<label>` 연결 또는 `aria-label` 적용
- 모달/드롭다운에 포커스 트래핑 추가
- 랜딩 페이지에 Skip to content 링크 추가
- 색상 대비(contrast ratio) WCAG AA 기준 충족 여부 점검 (특히 다크 모드에서 `text-[#b0b0b0]` on `bg-[#1a1a1a]` 등)

---

## 7. 테스트

### 현재 상태

Jest 30 + Testing Library 구성. 테스트 파일 **3개**만 존재:

| 파일 | 테스트 대상 | 테스트 수 |
|------|-----------|----------|
| `lib/api.test.ts` | Mock CRUD 함수, 토큰 관리 | ~8 |
| `components/ui/Toast.test.tsx` | Toast 렌더링, 자동 닫기, Provider | ~5 |
| `hooks/useAuth.test.tsx` | Auth 로딩, 토큰 로드, 로그아웃 | ~4 |

### 발견된 문제점

**[Critical] 테스트 커버리지 극히 부족**

전체 소스 파일 대비 테스트 파일 비율: **3/40+ (약 7%)**

테스트가 없는 핵심 영역:
- `GenerationContext` (SSE 연결 로직)
- `VideoRequestForm` (1,098줄의 복잡한 폼)
- `video/[id]/page.tsx` (1,547줄의 영상 상세 페이지)
- API 클라이언트 (`client.ts` -- 토큰 갱신, 에러 핸들링)
- 상태 매핑 로직 (`mapBackendStatus`, `transformWorkflowToVideo`)
- 모든 관리자 페이지

**[Warning] E2E 테스트 미구현**
`package.json:58`에 `puppeteer`가 devDependencies에 있으나, E2E 테스트 파일이 확인되지 않음. 스크린샷 캡처 스크립트(`scripts/capture-screenshots.js`)만 존재.

### 개선 제안
- 우선순위 1: 상태 매핑 함수(`mapBackendStatus`, `transformWorkflowToVideo`) 단위 테스트 (버그 발생 가능성 최고)
- 우선순위 2: API 클라이언트 토큰 갱신 로직 테스트
- 우선순위 3: `VideoRequestForm` 주요 인터랙션 통합 테스트
- 우선순위 4: 주요 사용자 플로우 E2E 테스트 (영상 요청 -> 검수 -> 완료)

---

## 8. 성능

### 현재 상태

Next.js 14 App Router를 사용하지만 SSR/SSG를 거의 활용하지 않음. 모든 페이지가 `'use client'`로 CSR 처리.

### 발견된 문제점

**[Warning] SSR/SSG 미활용**
33개 파일이 `'use client'`를 선언하여 서버 사이드 렌더링을 사용하지 않음. Next.js App Router의 핵심 이점인 서버 컴포넌트, ISR, SSG를 활용하지 못하고 있다.

SSR/SSG 적용 가능한 후보:
- 랜딩 페이지 (`app/page.tsx`) -- 정적 콘텐츠, SSG 적합
- 대시보드 레이아웃 -- 서버 컴포넌트로 처리 가능
- 관리자 목록 페이지 -- 초기 데이터를 서버에서 fetch 가능

**[Warning] 대형 컴포넌트의 번들 영향**
`video/[id]/page.tsx` (1,547줄)에서 `recharts` 전체를 import하여 차트를 렌더링. 영상 상세 페이지를 방문할 때마다 차트 라이브러리 전체가 로드됨. 성과 차트 섹션을 `React.lazy`로 분리하면 초기 로드를 줄일 수 있다.

**[Info] next/image 사용**
이미지 렌더링에 `next/image` 컴포넌트를 사용하고 있어 자동 최적화(WebP 변환, 지연 로딩) 혜택을 받고 있다.

**[Info] SSE 재연결 최적화**
`GenerationContext.tsx:104-106,152` -- 지수 백오프(exponential backoff) 전략으로 SSE 재연결을 처리. 최대 10회 재시도, 30초 상한. 적절한 구현.

### 개선 제안
- 랜딩 페이지를 서버 컴포넌트로 전환 (가장 큰 SEO/성능 향상)
- 대시보드 차트 섹션에 `dynamic(() => import(...), { ssr: false })` 적용
- `video/[id]/page.tsx`의 성과 차트 섹션을 lazy loading으로 분리

---

## 종합 요약

### 심각도별 분류

| 심각도 | 건수 | 항목 |
|--------|------|------|
| Critical | 3 | 컴포넌트 200줄 초과 (다수), 테스트 커버리지 부족, SSE 토큰 URL 노출 |
| Warning | 11 | index.ts re-export, @types 위치, GradientMesh 중복, Sidebar 렌더링 중복, 과도한 useState, 상태 매핑 4곳 중복, null as T, console.log 잔존, Mock 분기 산재, User 타입 중복, SSR 미활용 |
| Info | 8 | contexts 분산, stale closure 가능성, 랜딩 단일파일, types 혼합, 접근성 부분 적용, error boundary 양호, next/image 사용, SSE 재연결 양호 |

### 즉시 조치 권장 사항 (Top 5)

1. **console.log 제거** -- 3개 파일 8건 (10분 이내 완료 가능)
2. **SSE 토큰 URL 노출 개선** -- 보안 이슈 (`GenerationContext.tsx:115`)
3. **상태 매핑 로직 통합** -- 4곳 분산된 매핑을 단일 유틸리티로 (`lib/status.ts`)
4. **User 타입 통합** -- `hooks/useAuth.tsx:6-16`에서 `types/index.ts`의 타입 사용
5. **video/[id]/page.tsx 분리** -- 1,547줄을 논리적 섹션 단위로 분리

### 아키텍처적 강점

- Token refresh 경쟁 조건 처리가 잘 되어 있음 (`client.ts:41-51`)
- SSE 기반 실시간 상태 업데이트 구조가 적절함
- Error Boundary가 각 라우트에 일관되게 적용됨
- 다크/라이트 테마가 CSS 변수 기반으로 깔끔하게 구현됨
- `prefers-reduced-motion` 접근성 고려
- Mock 모드로 백엔드 독립적 개발 환경 제공
