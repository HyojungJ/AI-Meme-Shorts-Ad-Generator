# 데이터베이스 초기 데이터 세팅 (Database Seeding)

## 개요

데이터베이스 스키마 생성 후 시스템 운영에 필요한 기본 데이터와 개발/테스트용 샘플 데이터를 자동으로 생성하는 가이드입니다.

---

## 사전 요구사항

1. **Alembic 마이그레이션 완료**
   ```bash
   alembic upgrade head
   ```

2. **데이터베이스 연결 설정**
   - `.env` 파일에 `DATABASE_URL` 설정 완료

3. **Python 가상환경 활성화**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Mac/Linux
   source .venv/bin/activate
   ```

---

## Seeding 스크립트 실행

### 1. 전체 데이터 생성 (시스템 + 테스트)

```bash
python scripts/seed_data.py --all
```

### 2. 시스템 기본 데이터만 생성

```bash
python scripts/seed_data.py --system
```

### 3. 테스트 데이터만 생성

```bash
python scripts/seed_data.py --test
```

---

## 생성되는 데이터

### 1. 시스템 기본 데이터 (`--system`)

#### 관리자 계정
- **이메일**: `admin@meme-fluencer.com`
- **비밀번호**: `admin123!@#` (기본값, 환경변수로 변경 가능)
- **계정 타입**: admin
- **권한**: 전체 관리자

**환경변수 설정 (선택):**
```env
# .env
ADMIN_PASSWORD=your_secure_password
```

#### 프롬프트 버전
| 프롬프트 이름 | 버전 | 설명 |
|--------------|------|------|
| scenario_generation | v1.0 | 시나리오 생성용 프롬프트 |
| video_generation | v1.0 | 영상 생성용 프롬프트 |
| character_generation | v1.0 | 캐릭터 생성용 프롬프트 |

---

### 2. 테스트 데이터 (`--test`)

#### 테스트 회사
| 회사명 | company_id |
|--------|-----------|
| 테스트기업 | 자동 생성 |
| 스타트업코리아 | 자동 생성 |

#### 테스트 계정
| 이메일 | 비밀번호 | 회사 | 이름 | 부서 | 역할 | Primary |
|--------|---------|------|------|------|------|---------|
| manager@test.com | test1234 | 테스트기업 | 김매니저 | 마케팅팀 | manager | ✅ |
| member1@test.com | test1234 | 테스트기업 | 이멤버 | 마케팅팀 | member | ❌ |
| startup@test.com | test1234 | 스타트업코리아 | 박대표 | 경영지원 | manager | ✅ |

---

## 중복 실행 방지

Seeding 스크립트는 **중복 실행 방지 로직**이 포함되어 있습니다:

- 이미 존재하는 데이터는 자동으로 스킵
- 에러 없이 안전하게 재실행 가능

**실행 결과 예시:**
```
=== 시스템 기본 데이터 Seeding ===
⏭️  관리자 계정 이미 존재: admin@meme-fluencer.com
✅ 프롬프트 버전 생성: scenario_generation v1.0
```

---

## 환경별 실행 가이드

### 개발 환경 (Development)
```bash
# 전체 데이터 생성 (시스템 + 테스트)
python scripts/seed_data.py --all
```

### 스테이징 환경 (Staging)
```bash
# 시스템 데이터만 생성
python scripts/seed_data.py --system
```

### 프로덕션 환경 (Production)
```bash
# 시스템 데이터만 생성 (테스트 데이터 제외)
python scripts/seed_data.py --system

# 관리자 비밀번호 반드시 환경변수로 설정
export ADMIN_PASSWORD=secure_production_password
```

---

## 주의사항

### 1. 밈 데이터는 제외됨
- `memes`, `meme_examples` 테이블은 이미 실제 데이터가 존재
- Seeding 스크립트에서 밈 데이터는 생성하지 않음

### 2. 시나리오 데이터는 제외됨
- `scenario_scripts` 테이블도 실제 데이터 존재
- Seeding 스크립트에서 건드리지 않음

### 3. Primary Member 제약
- 각 회사당 `is_primary=True`인 멤버는 1명만 가능
- 추가 멤버는 `is_primary=False`로 설정

### 4. 프로덕션 환경 보안
- 관리자 비밀번호는 반드시 환경변수로 설정
- 기본 비밀번호(`admin123!@#`) 사용 금지
- 테스트 계정은 프로덕션에 생성하지 말 것

---

## 데이터 초기화 (Reset)

테스트 데이터를 삭제하고 다시 생성하려면:

### 1. 테스트 계정 삭제
```sql
-- 특정 이메일 계정 삭제 (CASCADE로 연관 데이터 자동 삭제)
DELETE FROM accounts WHERE email IN (
  'manager@test.com',
  'member1@test.com',
  'startup@test.com'
);
```

### 2. 테스트 회사 삭제
```sql
-- 특정 회사 삭제 (CASCADE로 연관 데이터 자동 삭제)
DELETE FROM companies WHERE company_name IN (
  '테스트기업',
  '스타트업코리아'
);
```

### 3. 전체 클라이언트 데이터 초기화 (주의!)
```sql
-- 모든 클라이언트 계정 삭제 (관리자는 남김)
DELETE FROM accounts WHERE account_type = 'client';
DELETE FROM companies;
```

### 4. 재실행
```bash
python scripts/seed_data.py --test
```

---

## 트러블슈팅

### 에러: "duplicate key value violates unique constraint"

**원인:** 이미 동일한 데이터가 존재

**해결:**
1. 기존 데이터 확인:
   ```sql
   SELECT * FROM accounts WHERE email = 'admin@meme-fluencer.com';
   ```

2. 기존 데이터 삭제 후 재실행:
   ```sql
   DELETE FROM accounts WHERE email = 'admin@meme-fluencer.com';
   ```

### 에러: "invalid keyword argument"

**원인:** 모델 컬럼명과 데이터 키가 불일치

**해결:** 
- 모델 파일(`app/models/*.py`) 확인
- Seeding 스크립트의 데이터 구조 수정

### 에러: "connection refused"

**원인:** 데이터베이스 연결 실패

**해결:**
1. 데이터베이스 서버 실행 확인
2. `.env` 파일의 `DATABASE_URL` 확인
3. 네트워크 연결 확인

---

## 스크립트 구조

```
scripts/
└── seed_data.py          # 메인 Seeding 스크립트
    ├── get_db()          # DB 세션 생성
    ├── seed_system_data() # 시스템 기본 데이터
    ├── seed_test_data()   # 테스트 데이터
    └── main()            # 메인 실행 함수
```

---

## 추가 데이터 생성

### 커스텀 데이터 추가

`scripts/seed_data.py` 파일을 수정하여 추가 데이터 생성 가능:

```python
def seed_custom_data(db: Session):
    """커스텀 데이터 생성"""
    # 여기에 추가 데이터 생성 로직 작성
    pass

# main() 함수에 추가
if args.custom:
    seed_custom_data(db)
```

### 대량 데이터 생성

성능 테스트를 위한 대량 데이터 생성:

```python
# 100개 회사 생성
for i in range(100):
    company = Company(company_name=f"테스트회사{i}")
    db.add(company)
db.commit()
```

---

## 백업 권장사항

Seeding 실행 전 데이터베이스 백업 권장:

```bash
# PostgreSQL 백업
pg_dump -U postgres -d meme-fluencer > backup_before_seeding.sql

# 복구 (필요시)
psql -U postgres -d meme-fluencer < backup_before_seeding.sql
```

---

## 참고 문서

- [API 변경 사항](./API_CHANGES_20260126.md)
- [데이터베이스 스키마](./COMPLETE_SCHEMA.sql)
- [Alembic 마이그레이션](../alembic/versions/)

---

## 문의

Seeding 관련 문제 발생 시:
1. 에러 메시지 전체 복사
2. 실행한 명령어 기록
3. 데이터베이스 상태 확인 (어떤 데이터가 이미 존재하는지)
