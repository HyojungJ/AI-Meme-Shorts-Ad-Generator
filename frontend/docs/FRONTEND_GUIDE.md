# Meme-fluencer Frontend 개발 문서

## 개요

B2B 밈 광고 영상 자동 제작 플랫폼의 Next.js 프론트엔드 애플리케이션

---

## 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| Next.js | 14.2 | React 프레임워크 (App Router) |
| TypeScript | 5.x | 타입 안정성 |
| Tailwind CSS | 3.x | 스타일링 |
| react-hook-form | 7.x | 폼 상태 관리 |
| react-dropzone | 14.x | 파일 업로드 |
| recharts | 2.x | 차트/그래프 |
| @react-oauth/google | 0.12.x | Google OAuth |

---

## 디렉토리 구조

```
src/
├── app/
│   ├── (auth)/
│   │   └── login/
│   │       └── page.tsx          # 로그인 페이지
│   ├── (dashboard)/
│   │   ├── layout.tsx            # 대시보드 공통 레이아웃
│   │   ├── main/
│   │   │   └── page.tsx          # 메인 대시보드
│   │   ├── user/
│   │   │   ├── page.tsx          # 내 영상 목록
│   │   │   ├── request/
│   │   │   │   └── page.tsx      # 영상 제작 요청
│   │   │   └── video/
│   │   │       └── [id]/
│   │   │           └── page.tsx  # 영상 상세
│   │   ├── profile/
│   │   │   └── page.tsx          # 프로필 설정
│   │   └── admin/
│   │       └── page.tsx          # 관리자 페이지
│   ├── globals.css               # 전역 스타일
│   ├── layout.tsx                # 루트 레이아웃
│   └── page.tsx                  # 랜딩 페이지
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx           # 사이드바 네비게이션
│   │   └── Header.tsx            # 상단 헤더
│   ├── forms/
│   │   └── VideoRequestForm.tsx  # 영상 요청 폼
│   └── ui/
│       └── Toast.tsx             # 토스트 알림
├── hooks/
│   ├── useAuth.tsx               # 인증 상태 관리
│   └── useTheme.tsx              # 다크/라이트 모드
└── lib/
    └── api.ts                    # API 통신 + Mock 데이터
```

---

## 페이지별 기능

### 1. 로그인 (`/login`)

| 기능 | 설명 |
|------|------|
| Google OAuth | Google 계정으로 로그인 |
| 이메일 로그인 | 이메일/비밀번호 로그인 |
| 회원가입 | 이메일/비밀번호/닉네임으로 가입 |
| Mock 모드 | 백엔드 없이 테스트 가능 |

### 2. 메인 대시보드 (`/main`)

| 기능 | 설명 |
|------|------|
| 통계 카드 | 총 영상, 조회수, 반응률, 제작중 영상 |
| 일별 차트 | 조회수/반응률 추이 (recharts) |
| 최근 영상 | 최근 제작된 영상 목록 |
| 빠른 액션 | 새 영상 요청 버튼 |

### 3. 내 영상 목록 (`/user`)

| 기능 | 설명 |
|------|------|
| 상태 필터 | 전체/대기/제작중/검수중/완료 |
| 검색 | 제목, 회사명, 카테고리로 검색 |
| 페이지네이션 | 6개씩 페이지 분할 |
| 영상 카드 | 상태별 다른 액션 버튼 |
| 삭제 | 확인 모달 후 삭제 |

### 4. 영상 제작 요청 (`/user/request`)

| 필드 | 타입 | 필수 |
|------|------|------|
| 회사 이름 | text | ✓ |
| 회사 이미지 | file (image) | - |
| 회사 음성 | file (audio) | - |
| 제품 이름 | text | ✓ |
| 제품 카테고리 | select | ✓ |
| 강조 문구 | textarea | ✓ |
| 캐릭터 분위기 | text | - |
| 제품 이미지 | file (image) | ✓ |
| 제품 URL | text | - |

### 5. 영상 상세 (`/user/video/[id]`)

| 기능 | 설명 |
|------|------|
| 진행 상황 | 5단계 프로그레스 바 |
| 영상 정보 | 요청일, 조회수, 카테고리 |
| 시나리오 | 생성된 시나리오 표시 |
| 검수 액션 | 승인/수정요청 버튼 (review 상태일 때) |
| 완성 영상 | 미리보기/다운로드 (completed 상태일 때) |

### 6. 프로필 (`/profile`)

| 기능 | 설명 |
|------|------|
| 프로필 보기 | 닉네임, 이메일, 가입일 |
| 프로필 수정 | 닉네임 변경 |
| 아바타 변경 | 프로필 이미지 업로드 (UI만) |
| 로그아웃 | 세션 종료 |

### 7. 관리자 (`/admin`)

| 기능 | 설명 |
|------|------|
| 접근 제한 | is_admin: true인 사용자만 접근 |
| 전체 영상 | 모든 사용자의 영상 목록 |
| 상태 관리 | 영상별 진행 상태 모니터링 |

---

## 공통 컴포넌트

### Sidebar

```tsx
// 네비게이션 항목
- Dashboard (/main)
- My Videos (/user)
- Profile (/profile)
- Admin (/admin)  // is_admin일 때만 표시
```

### Header

```tsx
// 기능
- 검색 바 (⌘K 단축키 표시)
- 테마 토글 (다크/라이트)
- 알림 버튼
- 사용자 정보 + 로그아웃
```

### Toast

```tsx
// 사용법
const { showToast } = useToast()
showToast('메시지', 'success')  // success | error | info
```

---

## 커스텀 훅

### useAuth

```tsx
const { user, loading, login, loginWithEmail, register, logout } = useAuth()

// user 타입
{
  user_id: number
  email: string
  nickname: string
  profile_img?: string
  is_admin?: boolean
}
```

### useTheme

```tsx
const { theme, toggleTheme } = useTheme()

// theme: 'dark' | 'light'
```

---

## API 통신 (lib/api.ts)

### Mock 모드

```bash
# .env.local
NEXT_PUBLIC_MOCK_MODE=true
```

Mock 모드 활성화 시 localStorage 기반으로 동작

### API 함수

```tsx
// 인증
loginWithGoogle(googleToken: string)
loginWithEmail(email: string, password: string)
registerWithEmail(email: string, password: string, nickname: string)
getCurrentUser()

// 영상
getVideos(): Video[]
getVideoById(id: string): Video | null
addVideo(data: VideoRequest): Video
updateVideo(id: string, data: Partial<Video>): Video | null
deleteVideo(id: string): boolean

// 시나리오
approveScenario(id: string): Video | null
requestScenarioRevision(id: string): Video | null
```

---

## 영상 상태 흐름

```
pending → processing → review → completed
  │           │          │
  │           │          └─ 수정요청 시 → pending으로 복귀
  │           │
  │           └─ AI가 시나리오 생성 완료
  │
  └─ 영상 제작 요청 시 초기 상태
```

| 상태 | 표시 | 색상 |
|------|------|------|
| pending | 대기 | gray |
| processing | 제작중 | yellow |
| review | 검수중 | blue |
| completed | 완료 | green |

---

## 스타일 가이드

### 색상 팔레트

| 용도 | Dark Mode | Light Mode |
|------|-----------|------------|
| 배경 | #0a0a0a | #f5f5f5 |
| 카드 | #141414 | #ffffff |
| 보조 배경 | #1a1a1a | #f0f0f0 |
| 테두리 | #2a2a2a | #e0e0e0 |
| 액센트 | #c8ff00 | #8bc34a |
| 텍스트 (주) | #ffffff | #1a1a1a |
| 텍스트 (보조) | #888888 | #666666 |

### 폰트

```css
.font-display { font-family: 'Syne', sans-serif; }      /* 제목용 */
.font-body { font-family: 'Space Grotesk', sans-serif; } /* 본문용 */
```

### 컴포넌트 스타일 패턴

```tsx
// 카드
className="bg-[#141414] border border-[#1a1a1a] rounded-2xl p-6"

// 버튼 (Primary)
className="px-5 py-3 bg-[#c8ff00] text-black font-semibold rounded-xl hover:bg-[#d4ff33] transition-colors"

// 버튼 (Secondary)
className="px-4 py-2 bg-[#1a1a1a] text-white rounded-lg hover:bg-[#2a2a2a] transition-colors"

// 입력 필드
className="w-full px-4 py-3 bg-[#0a0a0a] border border-[#2a2a2a] rounded-xl text-white focus:outline-none focus:border-[#c8ff00]/50"
```

---

## 환경 변수

```bash
# .env.local

# Google OAuth
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id

# API 서버
NEXT_PUBLIC_API_URL=http://localhost:8000

# Mock 모드 (백엔드 없이 테스트)
NEXT_PUBLIC_MOCK_MODE=true
```

---

## 실행 방법

```bash
# 의존성 설치
npm install

# 개발 서버
npm run dev

# 프로덕션 빌드
npm run build

# 프로덕션 실행
npm start
```

---

## 백엔드 연동 체크리스트

Mock 모드에서 실제 API로 전환 시:

- [ ] `.env.local`에서 `NEXT_PUBLIC_MOCK_MODE=false` 설정
- [ ] `NEXT_PUBLIC_API_URL`을 실제 백엔드 주소로 변경
- [ ] Google OAuth 설정 (Authorized origins에 프로덕션 도메인 추가)
- [ ] CORS 설정 확인
- [ ] JWT 토큰 만료 처리 확인

---

## 향후 개선 사항

1. **반응형 개선**: 모바일 레이아웃 최적화
2. **알림 기능**: 실시간 알림 (WebSocket)
3. **영상 미리보기**: 실제 비디오 플레이어 연동
4. **다국어 지원**: i18n 적용
5. **테스트**: Jest + React Testing Library
