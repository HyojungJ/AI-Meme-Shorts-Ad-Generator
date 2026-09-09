# UV 팀 프로젝트 환경 설정 매뉴얼

> 이 문서는 팀원 모두가 동일한 Python 환경에서 작업할 수 있도록 uv 사용법을 안내합니다.

---

## 목차

1. [uv 설치](#1-uv-설치)
2. [프로젝트 초기 설정 (팀장)](#2-프로젝트-초기-설정-팀장)
3. [팀원 환경 설정](#3-팀원-환경-설정)
4. [패키지 관리](#4-패키지-관리)
5. [가상환경 사용법](#5-가상환경-사용법)
6. [Git 워크플로우](#6-git-워크플로우)
7. [트러블슈팅](#7-트러블슈팅)
8. [명령어 요약](#8-명령어-요약)

---

## 1. uv 설치

### macOS / Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 설치 확인
```bash
uv --version
```

> 설치 후 터미널을 재시작하거나 `source ~/.bashrc` (또는 `~/.zshrc`) 실행

---

## 2. 프로젝트 초기 설정 (팀장)

> 프로젝트를 처음 생성하는 팀장만 수행합니다.

### 2.1 프로젝트 초기화
```bash
cd ~/Desktop/skn-final-proj
uv init
```

생성되는 파일:
| 파일 | 설명 |
|------|------|
| `pyproject.toml` | 프로젝트 설정 및 의존성 정의 |
| `.python-version` | Python 버전 지정 |
| `hello.py` | 샘플 파일 (삭제 가능) |

### 2.2 Python 버전 고정

**팀 전체가 사용할 Python 버전을 지정합니다.**

```bash
# Python 버전 확인
uv python list

# 특정 버전으로 고정 (예: 3.11)
uv python pin 3.11
```

이 명령어는 `.python-version` 파일을 생성/수정합니다.

```
# .python-version 파일 내용
3.11
```

### 2.3 가상환경 생성 및 필수 패키지 설치

```bash
# 가상환경 생성 (.venv 폴더)
uv venv

# 필요한 패키지 추가
uv add pandas numpy matplotlib
```

### 2.4 Git 저장소 초기화 및 첫 커밋

```bash
git init
git add pyproject.toml uv.lock .python-version
git commit -m "Initialize project with uv"
```

### 2.5 .gitignore 설정

```bash
# .gitignore에 추가할 내용
echo ".venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
```

---

## 3. 팀원 환경 설정

> 프로젝트를 clone 받은 팀원이 수행합니다.

### 3.1 저장소 클론
```bash
git clone <repository-url>
cd data-pipeline
```

### 3.2 환경 동기화 (단 한 줄!)
```bash
uv sync
```


이 명령어가 자동으로 수행하는 작업:
1. `.python-version`에 지정된 Python 버전 설치 (없으면)
2. `.venv` 가상환경 생성
3. `uv.lock`에 명시된 정확한 버전의 패키지 설치

> **중요**: `uv sync`만 실행하면 팀장과 100% 동일한 환경이 구성됩니다.

---

## 4. 패키지 관리

### 4.1 패키지 추가

```bash
# 기본 패키지 추가
uv add requests

# 여러 패키지 동시 추가
uv add pandas numpy scikit-learn

# 특정 버전 지정
uv add "pandas>=2.0.0"
uv add "numpy==1.26.0"
```

**패키지 추가 후 반드시 해야 할 일:**
```bash
git add pyproject.toml uv.lock
git commit -m "Add <패키지명> dependency"
git push
```

### 4.2 개발용 패키지 추가

테스트, 린터 등 개발에만 필요한 패키지:

```bash
uv add --dev pytest
uv add --dev black flake8
```

`pyproject.toml`에 `[tool.uv.dev-dependencies]`로 분리 저장됩니다.

### 4.3 패키지 삭제

```bash
uv remove pandas
```

삭제 후에도 `pyproject.toml`과 `uv.lock` 커밋 필요!

### 4.4 패키지 업데이트

```bash
# 특정 패키지 업데이트
uv lock --upgrade-package pandas

# 모든 패키지 업데이트
uv lock --upgrade
```

업데이트 후:
```bash
uv sync  # 로컬 환경에 적용
git add uv.lock
git commit -m "Upgrade dependencies"
```

### 4.5 현재 설치된 패키지 확인

```bash
uv pip list
```

---

## 5. 가상환경 사용법

### 5.1 방법 1: uv run 사용 (권장)

가상환경 활성화 없이 바로 실행:

```bash
# Python 스크립트 실행
uv run python main.py

# Python 인터프리터 실행
uv run python

# pytest 실행
uv run pytest
```

### 5.2 방법 2: 가상환경 직접 활성화

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (cmd)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

활성화 후에는 일반적인 Python 명령어 사용:
```bash
python main.py
pytest
```

비활성화:
```bash
deactivate
```

---

## 6. Git 워크플로우

### 6.1 커밋해야 하는 파일

| 파일 | 필수 | 설명 |
|------|:----:|------|
| `pyproject.toml` | ✅ | 프로젝트 설정 및 의존성 |
| `uv.lock` | ✅ | 정확한 패키지 버전 고정 |
| `.python-version` | ✅ | Python 버전 지정 |
| `.gitignore` | ✅ | Git 제외 파일 목록 |

### 6.2 커밋하지 않는 파일

| 파일/폴더 | 이유 |
|-----------|------|
| `.venv/` | 각자 로컬에서 생성 |
| `__pycache__/` | Python 캐시 |
| `*.pyc` | 컴파일된 Python 파일 |

### 6.3 팀원이 패키지를 추가했을 때

다른 팀원이 새 패키지를 추가하고 push 했다면:

```bash
git pull
uv sync  # 변경된 의존성 자동 설치
```

### 6.4 충돌 방지 규칙

1. **패키지 추가/삭제 시** 바로 커밋 & 푸시
2. **작업 시작 전** 항상 `git pull` → `uv sync`
3. `uv.lock` 충돌 시 → `uv lock` 재실행 후 커밋

---

## 7. 트러블슈팅

### Q1. `uv sync` 시 Python 버전 오류

```
error: No interpreter found for Python 3.11
```

**해결:**
```bash
uv python install 3.11
uv sync
```

### Q2. 패키지 설치 충돌

```
error: Could not find a version that satisfies the requirement
```

**해결:**
```bash
# 캐시 삭제 후 재시도
uv cache clean
uv sync
```

### Q3. `.venv` 폴더가 손상된 경우

```bash
rm -rf .venv
uv sync
```

### Q4. `uv.lock` 충돌 발생

```bash
# 충돌 파일 삭제 후 재생성
git checkout --theirs uv.lock  # 또는 --ours
uv lock
uv sync
git add uv.lock
git commit -m "Resolve lock file conflict"
```

### Q5. uv 명령어를 찾을 수 없음

```bash
# PATH 추가 (macOS/Linux)
export PATH="$HOME/.cargo/bin:$PATH"

# 영구 적용
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## 8. 명령어 요약

### 초기 설정
| 명령어 | 설명 |
|--------|------|
| `uv init` | 프로젝트 초기화 |
| `uv python pin 3.11` | Python 버전 고정 |
| `uv venv` | 가상환경 생성 |

### 패키지 관리
| 명령어 | 설명 |
|--------|------|
| `uv add <패키지>` | 패키지 추가 |
| `uv add --dev <패키지>` | 개발용 패키지 추가 |
| `uv remove <패키지>` | 패키지 삭제 |
| `uv sync` | 의존성 동기화 (팀원 필수!) |
| `uv lock` | lock 파일 갱신 |
| `uv pip list` | 설치된 패키지 목록 |

### 실행
| 명령어 | 설명 |
|--------|------|
| `uv run python <파일>` | 스크립트 실행 |
| `uv run pytest` | 테스트 실행 |
| `source .venv/bin/activate` | 가상환경 활성화 |

---

## 빠른 시작 체크리스트

### 팀장 (최초 1회)
- [ ] `uv init` 실행
- [ ] `uv python pin <버전>` 으로 Python 버전 고정
- [ ] `uv add <패키지>` 로 필요한 패키지 설치
- [ ] `pyproject.toml`, `uv.lock`, `.python-version` 커밋
- [ ] `.gitignore`에 `.venv/` 추가

### 팀원 (clone 후)
- [ ] `git clone` 으로 저장소 복제
- [ ] `uv sync` 실행 (끝!)

### 패키지 추가 시 (누구나)
- [ ] `uv add <패키지>` 실행
- [ ] `pyproject.toml`, `uv.lock` 커밋 & 푸시
- [ ] 팀원들에게 `git pull` → `uv sync` 안내

---

> 문서 작성일: 2026-01-01
> uv 공식 문서: https://docs.astral.sh/uv/
