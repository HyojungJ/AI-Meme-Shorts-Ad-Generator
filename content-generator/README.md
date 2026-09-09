# content-generator

각본 생성 + 이미지 생성 + 영상 생성

## 레포지토리 구조
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