# UX 폴리시: 생성 경험 개선

## 배경

생성 대기 → 검수 → 완료까지의 핵심 플로우를 개선하여 사용자 체감 품질을 높인다.
SSE + React Context 인프라가 구축된 상태에서 그 위에 UX를 쌓는다.

## 개선 항목

### 1. 단계별 실시간 진행 카드

**현재**: 스피너 + 고정 텍스트
**개선**: 단계별 체크리스트 + 프로그레스바

- SSE `current_stage` + `progress` 값 활용
- 각 단계: 대기(회색) → 진행 중(펄스) → 완료(체크)
- 하단 프로그레스바로 전체 진행률 표시
- "다른 페이지에서도 알림을 받습니다" 안내 문구

**수정**: `user/video/[id]/page.tsx` generating UI 섹션

### 2. 글로벌 알림 센터

**현재**: 토스트 3초 후 소멸
**개선**: 헤더에 벨 아이콘 + 알림 드롭다운

- `GenerationContext`에 `notifications` 배열 추가
- 상태 전환 시 자동 기록 (generating → review/completed)
- 읽지 않은 알림 개수 뱃지
- 클릭 시 해당 영상 상세 페이지로 이동
- 메모리에만 저장 (새로고침 시 초기화)

**신규**: `components/ui/NotificationDropdown.tsx`
**수정**: `GenerationContext.tsx`, 헤더 컴포넌트

### 3. 에셋 검수 비교 뷰

**현재**: 결과만 표시, 요청 스타일은 하단 작은 텍스트
**개선**: 요청 vs 결과를 나란히 비교

- 좌: 요청 스타일 텍스트 (카드)
- 우: 생성된 이미지 / 음성 샘플
- 비교가 직관적이어서 승인 판단이 쉬워짐

**수정**: `user/video/[id]/page.tsx` 에셋 검수 섹션

### 4. 마이크로 인터랙션

- 프로그레스 스텝 전환: 슬라이드/페이드 트랜지션
- 대시보드 카드: SSE 상태 변경 시 하이라이트 펄스 (1회)
- 스켈레톤 → 컨텐츠: 페이드인
- CSS `@keyframes` + Tailwind `animate-` 클래스로 경량 구현

**수정**: `user/page.tsx`, 글로벌 CSS

## 수정 파일

| 파일 | 작업 |
|------|------|
| `frontend/src/contexts/GenerationContext.tsx` | notifications 추가 |
| `frontend/src/components/ui/NotificationDropdown.tsx` | NEW |
| `frontend/src/app/(dashboard)/DashboardContent.tsx` | 벨 아이콘 추가 |
| `frontend/src/app/(dashboard)/user/video/[id]/page.tsx` | 진행 카드 + 비교 뷰 |
| `frontend/src/app/(dashboard)/user/page.tsx` | 카드 하이라이트 |
| `frontend/src/app/globals.css` | 트랜지션 키프레임 |

## 제외

- 컨페티 애니메이션 (과하다)
- 씬 동기화 영상 플레이어 (과하다)
- 알림 DB 저장 (불필요)
