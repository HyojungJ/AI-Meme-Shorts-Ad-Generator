# Meme Influencer

데이터 기반 밈 인플루언서 분석 및 생성 프로젝트입니다.

## 프로젝트 구조

```
meme-influencer/
├── data/
│   ├── raw/                  # 원본 JSON 데이터
│   └── processed/            # 가공된 CSV 데이터
│
├── diary/                    # 진행 일지
│   ├── sw/
│   ├── kj/
│   ├── jm/
│   ├── jh/
│   ├── hj/
│   └── weekly/               # 주간 진행사항 정리
│
├── notebooks/                # 주피터 노트북 (탐색/실험용)
│   ├── 01_collection.ipynb   # 데이터 수집
│   ├── 02_processing.ipynb   # 데이터 가공
│   ├── 03_db_load.ipynb      # DB 적재
│   └── 04_eda.ipynb          # 탐색적 분석
│
├── src/                      # 소스 코드 패키지
│   ├── collection/           # 데이터 수집 모듈
│   ├── processing/           # 전처리 로직
│   ├── db/                   # 데이터베이스 연결 및 쿼리
│   ├── generation/           # 콘텐츠 생성 모델
│   └── selection/            # 밈 선별 로직
│
├── scripts/                  # 실행 스크립트
│   └── run_pipeline.py       # 파이프라인 실행 진입점
│
├── tests/                    # 테스트용, (버젼별 프롬프트, 모델, 파인튜닝 데이터셋, 테스트 정보) 프레임워크 사용 예정
├── .env                      
├── .gitignore                
└── README.md                
```

진님 프로젝트 구조
```
ProjectName/
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
|
├── README.md
├── .gitignore
├── .env
└── requirements.txt
```