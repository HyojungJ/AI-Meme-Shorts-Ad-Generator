"""가상 기업/제품 템플릿 - 학습 데이터 다양성 확보용"""

import random


# 업종별 분포: 식음료 25%, IT 20%, 뷰티 15%, 금융 15%, 기타 25%
# voice_design_prompt: ElevenLabs Voice Design API용 음성 설명
# 포함 요소: 나이, 성별, 톤/음색, 말하기 속도, 감정/태도
# item_keymessage: 제품 설명 (사용자가 입력하는 형태와 동일하게 구체적으로 작성)
COMPANY_TEMPLATES = [
    # 식음료 (25%)
    {"company_name": "프레시주스", "item_name": "매일착즙 오렌지", "item_category": "음료", "item_keymessage": "매일 아침 산지에서 직송한 오렌지를 착즙해 병입한 100% 과즙 주스. 무첨가, 무방부제로 냉장 유통하며 한 병에 오렌지 5개 분량의 비타민C가 들어있음",
     "voice_design_prompt": "20대 초반 여성, 밝고 청량한 목소리, 빠르고 경쾌한 말투, 에너지 넘치고 상쾌한 느낌"},
    {"company_name": "버블티하우스", "item_name": "흑당버블티", "item_category": "음료", "item_keymessage": "대만산 흑설탕으로 직접 끓인 흑당 시럽에 쫄깃한 타피오카 펄을 넣은 밀크티. 당도 조절 가능하고 매장에서 주문 즉시 만들어 제공",
     "voice_design_prompt": "10대 후반 여성, 달콤하고 귀여운 목소리, 약간 느린 말투, 애교 섞인 톤"},
    {"company_name": "치킨마스터", "item_name": "바삭순살치킨", "item_category": "치킨", "item_keymessage": "국내산 닭가슴살 100%로 만든 순살 치킨. 두 번 튀겨서 겉은 바삭하고 속은 촉촉함. 특제 시즈닝 3종(오리지널, 갈릭, 매운맛) 선택 가능",
     "voice_design_prompt": "30대 남성, 굵고 호탕한 목소리, 빠르고 시원시원한 말투, 자신감 넘치고 호쾌한 느낌"},
    {"company_name": "피자헛", "item_name": "치즈폭발피자", "item_category": "피자", "item_keymessage": "모짜렐라, 고다, 체다, 크림치즈 4종을 블렌딩한 피자. 도우 가장자리에도 치즈가 들어있고 먹을 때 치즈가 늘어나는 비주얼이 특징",
     "voice_design_prompt": "20대 중반 남성, 열정적이고 따뜻한 목소리, 중간 속도, 흥분과 기대감이 느껴지는 톤"},
    {"company_name": "배민", "item_name": "배달의민족", "item_category": "배달앱", "item_keymessage": "전국 맛집 배달 앱. 최소주문금액 없는 '배민1' 서비스와 30분 내 도착하는 빠른배달 제공. 매달 다양한 할인 쿠폰과 멤버십 혜택 운영 중",
     "voice_design_prompt": "30대 남성, 약간 코믹하고 친근한 목소리, 여유로운 말투, B급 감성의 유머러스한 톤"},
    {"company_name": "스낵월드", "item_name": "꼬북칩 초코츄러스맛", "item_category": "과자", "item_keymessage": "옥수수 반죽을 4겹으로 겹겹이 쌓아 구운 스낵. 초코 츄러스맛 코팅으로 달콤하면서도 바삭한 식감. 한 봉지 80g에 간식이나 안주로 인기",
     "voice_design_prompt": "20대 초반 여성, 장난기 가득한 목소리, 빠르고 리드미컬한 말투, 중독성 있는 톤"},
    {"company_name": "아이스팩토리", "item_name": "쿨미니멜론바", "item_category": "아이스크림", "item_keymessage": "진짜 멜론과즙을 넣어 만든 미니 사이즈 아이스바. 한 입에 쏙 들어가는 크기로 한 박스에 10개입. 칼로리 45kcal로 부담 없이 즐기는 여름 간식",
     "voice_design_prompt": "20대 여성, 시원하고 청량한 목소리, 느긋한 말투, 상쾌하고 쿨한 느낌"},
    {"company_name": "에너지플러스", "item_name": "파워업 에너지드링크", "item_category": "에너지드링크", "item_keymessage": "카페인 200mg과 타우린, 비타민B군을 함유한 에너지 음료. 탄산이 강하고 250ml 캔 하나로 집중력 유지에 도움. 시험기간, 야근할 때 많이 찾는 제품",
     "voice_design_prompt": "20대 후반 남성, 힘차고 파워풀한 목소리, 매우 빠른 말투, 폭발적인 에너지"},
    {"company_name": "커피브루", "item_name": "콜드브루 아메리카노", "item_category": "커피", "item_keymessage": "에티오피아 예가체프 원두를 24시간 저온 추출한 콜드브루. 산미가 적고 부드러운 맛이 특징. 500ml 페트병으로 출시하여 편의점에서 바로 구매 가능",
     "voice_design_prompt": "30대 중반 남성, 낮고 깊은 목소리, 천천히 말하는 차분한 톤, 여유롭고 성숙한 느낌"},
    {"company_name": "라면킹", "item_name": "왕뚜껑", "item_category": "라면", "item_keymessage": "기존 컵라면보다 1.5배 큰 대용량 사발면. 두꺼운 면발에 얼큰한 소고기 육수 베이스. 별첨 건더기 스프에 파, 당근, 계란후레이크 포함",
     "voice_design_prompt": "40대 남성, 굵고 힘 있는 목소리, 당당하고 자신감 넘치는 말투, 카리스마 있는 톤"},

    # IT/앱 (20%)
    {"company_name": "토스", "item_name": "토스뱅크", "item_category": "핀테크", "item_keymessage": "앱 하나로 계좌개설부터 송금, 대출, 투자까지 가능한 인터넷은행. 수수료 무료 송금과 연 2% 이자의 통장을 제공하며 간편인증으로 3분 만에 가입 완료",
     "voice_design_prompt": "20대 후반 여성, 또렷하고 깔끔한 목소리, 적당히 빠른 말투, 똑똑하고 친절한 느낌"},
    {"company_name": "카카오게임즈", "item_name": "오딘", "item_category": "모바일게임", "item_keymessage": "북유럽 신화를 배경으로 한 MMORPG 모바일게임. 오픈월드 탐험과 대규모 전투가 특징이며 PC에서도 플레이 가능한 크로스플랫폼 지원",
     "voice_design_prompt": "40대 남성, 웅장하고 깊은 목소리, 느리고 무게감 있는 말투, 서사적이고 장엄한 톤"},
    {"company_name": "당근마켓", "item_name": "당근", "item_category": "중고거래앱", "item_keymessage": "GPS 기반 동네 주민끼리 중고거래하는 앱. 직거래가 기본이라 택배비 없고 매너온도 시스템으로 신뢰도 확인 가능. 중고거래 외에 동네 소식, 알바 정보도 제공",
     "voice_design_prompt": "30대 여성, 따뜻하고 부드러운 목소리, 편안한 말투, 이웃집 언니 같은 친근한 느낌"},
    {"company_name": "네이버", "item_name": "네이버페이", "item_category": "간편결제", "item_keymessage": "네이버 아이디로 온·오프라인 결제가 가능한 간편결제 서비스. 포인트 적립률이 높고 네이버쇼핑과 연동되어 자동 최저가 비교 및 결제 할인 제공",
     "voice_design_prompt": "20대 후반 남성, 깔끔하고 세련된 목소리, 중간 속도, 스마트하고 신뢰감 있는 톤"},
    {"company_name": "쿠팡", "item_name": "로켓배송", "item_category": "이커머스", "item_keymessage": "밤 12시 전 주문하면 다음날 새벽에 도착하는 쿠팡의 배송 서비스. 로켓와우 회원은 무료배송에 무료반품까지 가능. 식료품부터 가전까지 취급 품목 수백만 개",
     "voice_design_prompt": "20대 남성, 활기차고 빠른 목소리, 매우 빠른 말투, 급하고 역동적인 느낌"},
    {"company_name": "직방", "item_name": "직방", "item_category": "부동산앱", "item_keymessage": "원룸, 투룸, 오피스텔, 아파트까지 매물을 검색하고 비교할 수 있는 부동산 앱. 허위매물 필터링 시스템을 운영하고 3D 방 보기와 VR투어 기능 제공",
     "voice_design_prompt": "30대 중반 남성, 진지하고 믿음직한 목소리, 차분한 말투, 정직하고 신뢰감 있는 톤"},
    {"company_name": "클래스101", "item_name": "클래스101", "item_category": "온라인교육", "item_keymessage": "드로잉, 공예, 요리, 음악 등 취미부터 부업, 재테크까지 다양한 분야의 온라인 클래스를 제공하는 플랫폼. 현직 전문가가 강사이며 준비물 키트도 함께 배송",
     "voice_design_prompt": "20대 후반 여성, 열정적이고 밝은 목소리, 중간 속도, 영감을 주는 격려하는 톤"},
    {"company_name": "밀리의서재", "item_name": "밀리의서재", "item_category": "전자책", "item_keymessage": "월 9,900원으로 전자책과 오디오북을 무제한 이용할 수 있는 독서 앱. 베스트셀러 포함 12만 권 이상 보유하고 AI가 취향에 맞는 책을 추천해줌",
     "voice_design_prompt": "30대 여성, 차분하고 지적인 목소리, 느긋한 말투, 편안하고 사색적인 느낌"},

    # 뷰티/패션 (15%)
    {"company_name": "이니스프리", "item_name": "그린티 씨드 세럼", "item_category": "스킨케어", "item_keymessage": "제주산 유기농 녹차에서 추출한 씨드 오일이 주성분인 수분 세럼. 세안 후 첫 단계에 바르면 수분 장벽을 형성해 하루 종일 촉촉함 유지. 용량 80ml",
     "voice_design_prompt": "20대 중반 여성, 맑고 자연스러운 목소리, 부드럽고 느린 말투, 순수하고 청순한 느낌"},
    {"company_name": "마녀공장", "item_name": "퓨어 클렌징 오일", "item_category": "클렌징", "item_keymessage": "호호바 오일 기반의 저자극 클렌징 오일. 워터프루프 메이크업도 한 번에 녹여내고 물로 헹구면 깔끔하게 씻겨나감. 200ml 대용량에 가성비 좋음",
     "voice_design_prompt": "20대 후반 여성, 깨끗하고 산뜻한 목소리, 또박또박한 말투, 깔끔하고 청결한 느낌"},
    {"company_name": "에뛰드", "item_name": "플레이컬러아이즈", "item_category": "메이크업", "item_keymessage": "10색 아이섀도 팔레트. 매트, 글리터, 쉬머 다양한 질감이 한 팔레트에 구성되어 데일리부터 파티 메이크업까지 가능. 발색력이 좋고 가격은 만원대",
     "voice_design_prompt": "10대 후반 여성, 발랄하고 높은 목소리, 빠르고 경쾌한 말투, 트렌디하고 귀여운 느낌"},
    {"company_name": "젠틀몬스터", "item_name": "2025 컬렉션", "item_category": "아이웨어", "item_keymessage": "실험적인 디자인으로 유명한 프리미엄 아이웨어 브랜드의 최신 컬렉션. 독특한 프레임 형태와 고급 소재를 사용하며 연예인 착용으로 화제. 가격대 20~40만원",
     "voice_design_prompt": "20대 후반 여성, 낮고 쿨한 목소리, 느리고 무심한 말투, 도도하고 아방가르드한 느낌"},
    {"company_name": "무신사", "item_name": "무신사 스탠다드", "item_category": "패션", "item_keymessage": "무신사가 자체 제작하는 베이직 의류 라인. 티셔츠, 맨투맨, 슬랙스 등 기본 아이템을 합리적인 가격(1~3만원대)에 제공. 핏과 원단 품질 대비 가성비 좋다는 평가",
     "voice_design_prompt": "20대 남성, 담백하고 깔끔한 목소리, 중간 속도, 심플하고 세련된 느낌"},
    {"company_name": "올리브영", "item_name": "올영세일", "item_category": "뷰티편집샵", "item_keymessage": "올리브영에서 연 4회 진행하는 대규모 할인 행사. 스킨케어, 메이크업, 헤어, 건강식품까지 인기 제품을 최대 50% 할인. 온·오프라인 동시 진행되며 올영 멤버십 적립도 가능",
     "voice_design_prompt": "20대 초반 여성, 신나고 들뜬 목소리, 빠르고 흥분된 말투, 쇼핑 욕구를 자극하는 톤"},

    # 금융 (15%)
    {"company_name": "삼성카드", "item_name": "taptap카드", "item_category": "신용카드", "item_keymessage": "삼성페이 탭 결제에 특화된 신용카드. 탭 결제 시 모든 가맹점에서 1.5% 적립되고 편의점, 카페, 대중교통에서는 추가 적립. 연회비 1만원이지만 전월 실적 30만원 이상이면 면제",
     "voice_design_prompt": "30대 여성, 세련되고 또렷한 목소리, 적당히 빠른 말투, 스마트하고 실속있는 느낌"},
    {"company_name": "현대해상", "item_name": "하이카다이렉트", "item_category": "자동차보험", "item_keymessage": "온라인으로 직접 가입하는 다이렉트 자동차보험. 설계사 수수료가 없어서 보험료가 저렴하고 앱에서 사고접수부터 보상처리까지 가능. 무사고 할인, 마일리지 특약 등 다양한 할인 제공",
     "voice_design_prompt": "40대 남성, 안정감 있고 따뜻한 목소리, 차분한 말투, 믿음직하고 합리적인 느낌"},
    {"company_name": "카카오뱅크", "item_name": "카카오뱅크 모임통장", "item_category": "은행", "item_keymessage": "카카오톡 친구를 초대해서 만드는 공동 통장. 회비 자동이체 설정이 가능하고 입출금 내역이 카톡으로 알림이 와서 정산이 투명함. 여행, 동아리, 모임 경비 관리에 편리",
     "voice_design_prompt": "20대 후반 남성, 친근하고 편안한 목소리, 자연스러운 말투, 친구 같은 느낌"},
    {"company_name": "케이뱅크", "item_name": "플러스박스", "item_category": "은행", "item_keymessage": "매일 이자가 붙는 케이뱅크 파킹통장. 연 3.5% 금리(세전)로 5천만원까지 적용되고 입출금이 자유로움. 앱에서 간편하게 개설 가능하며 별도 조건 없이 누구나 가입",
     "voice_design_prompt": "30대 여성, 알뜰하고 현명한 느낌의 목소리, 명확한 말투, 실속파 느낌"},
    {"company_name": "미래에셋", "item_name": "투자는 미래에셋", "item_category": "증권", "item_keymessage": "국내외 주식, ETF, 펀드를 거래할 수 있는 종합 투자 플랫폼. 해외주식 거래 수수료가 업계 최저 수준이고 투자 리포트와 AI 종목 추천 서비스를 무료 제공",
     "voice_design_prompt": "40대 남성, 낮고 신뢰감 있는 목소리, 천천히 또박또박, 전문적이고 권위있는 톤"},
    {"company_name": "DB손해보험", "item_name": "다이렉트 운전자보험", "item_category": "보험", "item_keymessage": "교통사고, 일상생활 사고, 벌금, 변호사 비용까지 보장하는 운전자보험. 온라인 가입으로 보험료가 저렴하고 월 1만원대부터 가입 가능. 자전거, 킥보드 사고도 보장",
     "voice_design_prompt": "30대 후반 남성, 든든하고 안정적인 목소리, 차분한 말투, 보호자 같은 느낌"},

    # 기타 (25%)
    {"company_name": "삼성전자", "item_name": "갤럭시Z폴드6", "item_category": "스마트폰", "item_keymessage": "접이식 7.6인치 대화면 스마트폰. 펼치면 태블릿처럼 멀티태스킹이 가능하고 접으면 주머니에 들어가는 크기. Galaxy AI로 실시간 통역, 문서 요약 기능 탑재. IPX8 방수 지원",
     "voice_design_prompt": "30대 남성, 세련되고 미래지향적인 목소리, 중간 속도, 혁신적이고 프리미엄한 느낌"},
    {"company_name": "LG전자", "item_name": "LG 스탠바이미", "item_category": "모니터", "item_keymessage": "27인치 이동식 터치스크린 모니터. 바퀴가 달려 있어서 거실, 침실, 주방 어디든 옮겨 사용 가능. 내장 배터리로 3시간 무선 사용 가능하고 넷플릭스, 유튜브 등 OTT 앱 내장",
     "voice_design_prompt": "20대 후반 여성, 자유롭고 편안한 목소리, 느긋한 말투, 라이프스타일 지향적인 느낌"},
    {"company_name": "현대자동차", "item_name": "아이오닉 6", "item_category": "전기차", "item_keymessage": "1회 충전으로 최대 524km 주행 가능한 전기 세단. 18분 급속충전으로 80%까지 충전되고 차량 내부에서 220V 가전 사용 가능. 공기저항을 줄인 유선형 디자인이 특징",
     "voice_design_prompt": "30대 중반 남성, 세련되고 깔끔한 목소리, 차분한 말투, 미래지향적이고 고급스러운 느낌"},
    {"company_name": "스터디맥스", "item_name": "AI 영어회화", "item_category": "교육", "item_keymessage": "AI 캐릭터와 1:1로 영어 대화 연습을 하는 앱. 발음 교정과 문법 피드백을 실시간으로 받을 수 있고 여행, 비즈니스 등 상황별 시나리오 제공. 월 9,900원 구독제",
     "voice_design_prompt": "20대 후반 여성, 밝고 격려하는 목소리, 또렷한 말투, 선생님처럼 친절하고 응원하는 느낌"},
    {"company_name": "야놀자", "item_name": "야놀자", "item_category": "숙박앱", "item_keymessage": "호텔, 펜션, 모텔, 게스트하우스까지 국내 숙소를 비교하고 예약하는 앱. 실시간 특가 할인이 자주 올라오고 앱 전용 쿠폰 제공. 레저·티켓 예약과 항공권 검색도 가능",
     "voice_design_prompt": "20대 남성, 신나고 들뜬 목소리, 빠르고 경쾌한 말투, 여행 설레는 느낌"},
    {"company_name": "여기어때", "item_name": "여기어때", "item_category": "숙박앱", "item_keymessage": "국내 숙박 예약 앱으로 호텔, 펜션, 글램핑 등 다양한 숙소를 한눈에 비교 가능. 실제 이용자 리뷰와 사진을 확인할 수 있고 가격 비교 기능으로 최저가 숙소를 찾아줌",
     "voice_design_prompt": "20대 후반 여성, 친근하고 추천하는 느낌의 목소리, 자연스러운 말투, 친구에게 추천하는 톤"},
    {"company_name": "마이리얼트립", "item_name": "마이리얼트립", "item_category": "여행플랫폼", "item_keymessage": "해외여행 투어, 액티비티, 숙소, 항공권을 한 곳에서 예약하는 플랫폼. 현지 가이드가 진행하는 소그룹 투어가 인기이고 자유여행자를 위한 입장권, 교통패스 등도 판매",
     "voice_design_prompt": "20대 중반 남성, 모험적이고 설레는 목소리, 중간 속도, 여행자 감성의 낭만적인 느낌"},
    {"company_name": "왓챠", "item_name": "왓챠", "item_category": "OTT", "item_keymessage": "독립영화, 다큐멘터리, 해외 명작 등 다른 OTT에 없는 작품을 주로 보유한 스트리밍 서비스. AI 취향 분석으로 맞춤 추천을 해주고 월 7,900원에 광고 없이 시청 가능",
     "voice_design_prompt": "20대 남성, 덕후 감성의 열정적인 목소리, 빠른 말투, 취향 존중하는 느낌"},
    {"company_name": "컬리", "item_name": "샛별배송", "item_category": "신선식품", "item_keymessage": "밤 11시까지 주문하면 다음날 새벽 7시 전에 문 앞에 도착하는 신선식품 배송. 산지직송 과일, 채소부터 밀키트, 간편식까지 취급. 스티로폼 대신 종이 포장재 사용",
     "voice_design_prompt": "30대 여성, 고급스럽고 신뢰감 있는 목소리, 차분한 말투, 프리미엄하고 세심한 느낌"},
    {"company_name": "오늘의집", "item_name": "오늘의집", "item_category": "인테리어", "item_keymessage": "인테리어 사진 공유 커뮤니티와 가구·소품 쇼핑몰이 합쳐진 앱. 다른 사람의 집꾸미기를 구경하고 마음에 드는 제품을 바로 구매 가능. 3D 방 꾸미기 시뮬레이션 기능도 제공",
     "voice_design_prompt": "30대 여성, 따뜻하고 영감을 주는 목소리, 부드러운 말투, 인테리어 전문가 느낌"},

    # 추가 업종: 헬스/피트니스
    {"company_name": "나이키코리아", "item_name": "에어맥스 DN", "item_category": "스포츠화", "item_keymessage": "다이나믹 에어 유닛이 탑재된 러닝화. 달릴 때 착지 충격을 흡수해서 무릎에 부담이 적고 메쉬 소재 갑피로 통기성이 좋음. 290g의 가벼운 무게로 장거리 러닝에 적합",
     "voice_design_prompt": "20대 후반 남성, 힘차고 역동적인 목소리, 빠른 말투, 운동선수 같은 에너지"},
    {"company_name": "룰루레몬", "item_name": "어라인 레깅스", "item_category": "애슬레저", "item_keymessage": "나일론+라이크라 소재의 프리미엄 레깅스. 두께감이 있어 비침 걱정 없고 하이웨이스트 디자인으로 몸매 보정 효과. 요가, 필라테스는 물론 일상복으로도 입기 좋은 편안한 핏",
     "voice_design_prompt": "20대 후반 여성, 차분하고 세련된 목소리, 중간 속도, 건강한 라이프스타일 느낌"},
    {"company_name": "마이프로틴", "item_name": "임팩트웨이 프로틴", "item_category": "건강보조식품", "item_keymessage": "1스쿱당 단백질 21g 함유된 유청 단백질 보충제. 초코, 바닐라, 딸기 등 40가지 이상 맛이 있고 2.5kg 대용량 기준 타 브랜드 대비 절반 가격. 운동 후 물이나 우유에 타서 섭취",
     "voice_design_prompt": "20대 중반 남성, 에너지 넘치고 씩씩한 목소리, 빠른 말투, 헬스 유튜버 느낌"},

    # 추가 업종: 반려동물
    {"company_name": "로얄캐닌", "item_name": "미니 인도어", "item_category": "반려동물사료", "item_keymessage": "실내에서 생활하는 소형견 전용 사료. 활동량이 적은 반려견의 체중 관리를 위해 칼로리를 조절했고 변 냄새를 줄이는 성분 함유. 수의사 추천 브랜드로 1.5kg, 3kg 패키지 판매",
     "voice_design_prompt": "30대 여성, 다정하고 부드러운 목소리, 느린 말투, 반려인 특유의 사랑스러운 톤"},
    {"company_name": "펫프렌즈", "item_name": "펫프렌즈", "item_category": "반려동물쇼핑", "item_keymessage": "반려동물 사료, 간식, 장난감, 위생용품을 판매하는 온라인 쇼핑몰. 오후 5시까지 주문하면 다음날 새벽에 도착하고 정기배송 설정 시 10% 추가 할인 적용",
     "voice_design_prompt": "20대 여성, 밝고 친근한 목소리, 경쾌한 말투, 동물 좋아하는 활기찬 느낌"},

    # 추가 업종: 가전
    {"company_name": "다이슨", "item_name": "에어랩 멀티스타일러", "item_category": "헤어가전", "item_keymessage": "코안다 효과를 이용해 고열 없이 컬, 웨이브, 스트레이트 등 다양한 스타일링이 가능한 헤어 기기. 6종 어태치먼트가 포함되고 젖은 머리부터 드라이와 스타일링을 동시에 처리",
     "voice_design_prompt": "30대 여성, 고급스럽고 자신감 있는 목소리, 차분한 말투, 프리미엄 브랜드 느낌"},
    {"company_name": "샤오미", "item_name": "로봇청소기 X10+", "item_category": "생활가전", "item_keymessage": "LDS 레이저 센서로 집안 구조를 파악해 자동으로 청소하는 로봇청소기. 물걸레와 흡입 동시 가능하고 도킹스테이션에서 먼지 자동 비움. 앱으로 구역별 청소 스케줄 설정 가능",
     "voice_design_prompt": "20대 후반 남성, 가벼운 톤의 친근한 목소리, 중간 속도, 테크 리뷰어 느낌"},

    # 추가 업종: 엔터테인먼트
    {"company_name": "CGV", "item_name": "IMAX 관람", "item_category": "영화관", "item_keymessage": "일반 상영관보다 화면이 3배 크고 12채널 사운드로 몰입감이 극대화되는 IMAX 상영관. 레이저 프로젝터로 선명한 화질을 제공하며 액션, SF 영화에 특히 추천. 일반 관람 대비 약 5천원 추가",
     "voice_design_prompt": "30대 남성, 웅장하고 울림 있는 목소리, 느린 말투, 영화 예고편 나레이션 느낌"},
    {"company_name": "멜론", "item_name": "멜론 VIP", "item_category": "음악스트리밍", "item_keymessage": "음원 스트리밍·다운로드 무제한에 오프라인 재생까지 가능한 프리미엄 요금제. 무손실 FLAC 음질을 지원하고 AI가 취향에 맞는 플레이리스트를 자동 생성해줌. 월 10,900원",
     "voice_design_prompt": "20대 여성, 감성적이고 부드러운 목소리, 느긋한 말투, 음악 DJ 느낌"},

    # 추가 업종: 식음료 확장
    {"company_name": "CJ제일제당", "item_name": "비비고 왕교자", "item_category": "냉동식품", "item_keymessage": "돼지고기와 두부, 채소를 넣어 만든 대형 만두. 전자레인지 3분이면 바로 먹을 수 있고 에어프라이어로 구우면 군만두도 가능. 한 봉지에 350g, 냉동실에 보관하면 6개월",
     "voice_design_prompt": "40대 여성, 따뜻하고 정겨운 목소리, 편안한 말투, 엄마의 밥상 느낌"},
    {"company_name": "스타벅스코리아", "item_name": "콜드브루", "item_category": "카페", "item_keymessage": "14시간 이상 저온 추출한 콜드브루 커피. 아이스로만 제공되며 산미가 적고 깔끔한 맛이 특징. 톨 사이즈 기준 4,500원이며 사이렌오더로 미리 주문하면 매장에서 바로 수령 가능",
     "voice_design_prompt": "20대 후반 여성, 세련되고 힙한 목소리, 중간 속도, 카페 감성의 트렌디한 느낌"},
    {"company_name": "BBQ", "item_name": "황금올리브치킨", "item_category": "치킨", "item_keymessage": "올리브유로 튀겨서 기름기가 적고 담백한 맛이 특징인 치킨. 겉은 황금색으로 바삭하고 속은 촉촉한 육즙이 살아있음. 한 마리 기준 18,000원이며 반반 선택 가능",
     "voice_design_prompt": "30대 남성, 쾌활하고 맛있는 느낌의 목소리, 빠른 말투, 먹방 유튜버 같은 톤"},

    # 추가 업종: 교육/자기계발
    {"company_name": "해커스", "item_name": "토익 인강", "item_category": "어학교육", "item_keymessage": "토익 점수 보장 온라인 강의. 목표 점수 미달성 시 수강 연장이 무료이고 파트별 집중 공략 커리큘럼 제공. 매일 모의고사 풀이와 1:1 첨삭 서비스 포함",
     "voice_design_prompt": "30대 남성, 또렷하고 자신감 있는 목소리, 적당히 빠른 말투, 학원 강사 느낌"},
    {"company_name": "리디", "item_name": "리디 셀렉트", "item_category": "전자책", "item_keymessage": "월 9,900원으로 전자책, 웹소설, 만화를 무제한 구독하는 서비스. 15만 권 이상의 라이브러리를 보유하고 오프라인 다운로드도 가능. 베스트셀러 신간은 출간 후 2주 내 업데이트",
     "voice_design_prompt": "20대 후반 남성, 차분하고 지적인 목소리, 느긋한 말투, 책 좋아하는 문학청년 느낌"},

    # 추가 업종: 금융 확장
    {"company_name": "신한카드", "item_name": "Deep Dream", "item_category": "신용카드", "item_keymessage": "쇼핑, 외식, 교통, 통신 등 4대 영역에서 선택형 할인을 제공하는 신용카드. 전월 실적에 따라 최대 월 3만원 할인 가능하고 해외 결제 시 수수료 면제. 연회비 15,000원",
     "voice_design_prompt": "30대 여성, 세련되고 따뜻한 목소리, 중간 속도, 혜택을 잘 설명하는 친절한 느낌"},
    {"company_name": "한화투자증권", "item_name": "STEPS", "item_category": "투자앱", "item_keymessage": "주식 초보자를 위한 투자 앱. 1,000원부터 소수점 단위로 주식을 살 수 있고 투자 성향 테스트 후 맞춤 포트폴리오를 추천해줌. UI가 심플하고 용어 설명 기능이 내장되어 있음",
     "voice_design_prompt": "20대 후반 남성, 친근하고 쉬운 설명의 목소리, 자연스러운 말투, 재테크 초보 친구 느낌"},

    # 추가 업종: 뷰티 확장
    {"company_name": "아모레퍼시픽", "item_name": "설화수 자음생크림", "item_category": "스킨케어", "item_keymessage": "인삼 추출물을 주성분으로 한 안티에이징 크림. 피부 탄력과 주름 개선에 도움을 주며 밤 사용 시 다음날 아침 피부결이 정돈되는 효과. 60ml 기준 10만원대의 프리미엄 라인",
     "voice_design_prompt": "40대 여성, 우아하고 품위 있는 목소리, 느린 말투, 전통미와 고급스러움이 느껴지는 톤"},
    {"company_name": "닥터지", "item_name": "레드 블레미쉬 시카 수딩 크림", "item_category": "시카크림", "item_keymessage": "센텔라 아시아티카(병풀) 추출물이 주성분인 진정 크림. 피부 자극을 완화하고 붉은기를 잡아줌. 민감성·여드름 피부에 적합하며 70ml 기준 만원대로 가성비 좋은 시카크림",
     "voice_design_prompt": "20대 중반 여성, 부드럽고 안심되는 목소리, 또박또박한 말투, 피부과 전문의 느낌"},

    # 추가 업종: IT 확장
    {"company_name": "넥슨", "item_name": "메이플스토리", "item_category": "온라인게임", "item_keymessage": "2003년 출시된 대한민국 대표 2D 횡스크롤 MMORPG. 귀여운 캐릭터와 다양한 직업군이 특징이며 친구와 파티를 맺어 보스를 잡는 협동 플레이가 핵심. PC와 모바일 버전 모두 서비스 중",
     "voice_design_prompt": "20대 초반 남성, 발랄하고 흥분된 목소리, 빠른 말투, 게임 스트리머 느낌"},
    {"company_name": "삼성SDS", "item_name": "Brity Works", "item_category": "업무자동화", "item_keymessage": "AI가 문서작성, 회의록 정리, 이메일 초안, 데이터 분석 등 반복 업무를 자동화해주는 기업용 SaaS. 사내 시스템과 연동 가능하고 보안이 강화된 온프레미스 설치도 지원",
     "voice_design_prompt": "30대 남성, 깔끔하고 전문적인 목소리, 명확한 말투, IT 컨설턴트 느낌"},
]

def get_random_company():
    """랜덤 기업 템플릿 반환"""
    return random.choice(COMPANY_TEMPLATES)


def get_company_by_category(category: str) -> list[dict]:
    """특정 카테고리의 기업들 반환"""
    return [c for c in COMPANY_TEMPLATES if c["item_category"] == category]


def get_all_categories() -> list[str]:
    """모든 카테고리 목록"""
    return list(set(c["item_category"] for c in COMPANY_TEMPLATES))
