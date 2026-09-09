# Meme Influencer

데이터 기반 밈 인플루언서 생성 프로젝트입니다.

## 프로젝트 구조


```
project_plan/
│
├── data/                    
│   ├── raw/                # 원천데이터
│   └── processed/          # 전처리된 데이터
│
├── scripts/                 
│   ├── crawling/           # 데이터 수집
│   ├── preprocessing/      # 데이터 가공
│   └── analysis/           # 데이터 분석
│
├── backend/
│   ├── rag/
│   │   ├── retriever/
│   │   ├── embedder/
│   │   └── llm/
│   └── vectorDB/
│
├── frontend/
│
├── docs/                    # 기획 문서
│      ├── YYYY-MM-DD_[feature_name].md
│      └── weekly-report/
│               └── YYYY-MM-DD~DD.md     
│
├── tests/                   # 단위 테스트
│
├── README.md
├── .gitignore
└── .env
```

레파지토리 3개 분리 
1. 크롤링 + DB + 밈 선정 로직          => 레포 : data-pipeline 
2. 각본 생성 + 이미지 생성 + 영상 생성  => 레포 : content-generator 
3. 영상 업로드 + 프론트엔드             => 레포 : 생성 예정


```
data-pipeline/
│
├── data/                    
│   ├── raw/                 # 원천데이터
│   └── processed/           # 전처리된 데이터
│
├── scripts/                 
│   ├── crawling/            # 데이터 수집
│   ├── preprocessing/       # 데이터 가공
│   └── analysis/            # 데이터 분석
│
├── docs/                    # 진행 상황
│      ├── YYYY-MM-DD_[feature_name].md
│      └── weekly-report/
│               └── YYYY-MM-DD~DD.md  
│
├── .python-version          # 프로젝트에 고정된 Python 버전을 명시 (uv가 이를 감지해 가상환경 생성)
├── UV_MANUAL.md             # uv 명령어 사용법 및 워크플로우를 정리한 팀/개인 가이드 문서
├── pyproject.toml           # 프로젝트 설정 및 설치할 라이브러리 목록을 정의하는 메인 파일 (requirements.txt 대체)
├── uv.lock                  # 설치된 라이브러리의 정확한 버전을 잠금(Lock)하여 모든 환경에서 동일한 실행 보장
├── README.md
├── .gitignore
└── .env
```


```
content-generator/
│
├── data/                    
│   ├── raw/                 # 원천데이터
│   └── processed/           # 전처리된 데이터
│
├── backend/
│   ├── rag/
│   │   ├── retriever/
│   │   ├── embedder/
│   │   └── llm/
│   └── vectorDB/
│
├── docs/                    # 진행 상황
│      ├── YYYY-MM-DD_[feature_name].md
│      └── weekly-report/
│               └── YYYY-MM-DD~DD.md  
│
├── README.md
├── .gitignore
└── .env
```