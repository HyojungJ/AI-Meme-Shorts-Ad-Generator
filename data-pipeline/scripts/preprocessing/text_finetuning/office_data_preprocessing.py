import json

def extract_system_utterances(input_file_path, output_file_path, min_length=15):
    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        system_utterances = []
        filtered_nim_count = 0
        filtered_length_count = 0
        
        for item in data:
            if 'system_utterance' in item:
                utterance = item['system_utterance']
                
                # "님" 포함 발화 제외
                if "님" in utterance:
                    filtered_nim_count += 1
                    continue
                
                # 최소 길이 조건 확인
                if len(utterance) >= min_length:
                    system_utterances.append(utterance)
                else:
                    filtered_length_count += 1
        
        # 중복 제거
        unique_utterances = list(set(system_utterances))
        duplicate_count = len(system_utterances) - len(unique_utterances)
        
        # 결과 저장
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(unique_utterances, json_file, ensure_ascii=False, indent=2)
        
        return unique_utterances
        
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return []

def main():
    # 파일 경로 설정
    input_file = "data/raw/text_finetuning/output_daily_1st.json"
    output_file = "data/processed/system_utterances_daily_1st.json"
    
    # 추출 실행
    utterances = extract_system_utterances(input_file, output_file)
    
    # 통계 정보
    if utterances:
        print(f"\n=== 통계 정보 ===")
        print(f"최종 발화 수: {len(utterances)}")

if __name__ == "__main__":
    main()