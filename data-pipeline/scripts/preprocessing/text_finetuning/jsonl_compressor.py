import json
import os

def compress_jsonl(input_file, output_file):
    """
    JSONL 파일의 각 JSON 객체를 한 줄로 압축합니다.
    """
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        current_json = ""
        brace_count = 0
        
        for line in infile:
            line = line.strip()
            if not line:
                continue
                
            current_json += line
            
            # 중괄호 개수를 세어서 완전한 JSON 객체인지 확인
            for char in line:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
            
            # 완전한 JSON 객체가 완성되면 한 줄로 압축해서 저장
            if brace_count == 0 and current_json:
                try:
                    # JSON 파싱해서 다시 한 줄로 압축
                    json_obj = json.loads(current_json)
                    compressed_line = json.dumps(json_obj, ensure_ascii=False, separators=(',', ':'))
                    outfile.write(compressed_line + '\n')
                    print(f"✅ 압축 완료: {len(current_json)} → {len(compressed_line)} 문자")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 오류: {e}")
                    print(f"문제가 된 내용: {current_json}")
                
                # 다음 JSON 객체를 위해 초기화
                current_json = ""
                brace_count = 0

def main():
    input_file = "../../../data/processed/newbie/office_output_v1.jsonl"
    output_file = "../../../data/processed/newbie/office_output_v1_compressed.jsonl"
    
    print(f"입력 파일: {input_file}")
    print(f"출력 파일: {output_file}")
    print("=" * 50)
    
    # 입력 파일 존재 확인
    if not os.path.exists(input_file):
        print(f"❌ 입력 파일을 찾을 수 없습니다: {input_file}")
        return
    
    # 출력 디렉토리 생성 (필요한 경우)
    output_dir = os.path.dirname(output_file)
    os.makedirs(output_dir, exist_ok=True)
    
    # 압축 실행
    compress_jsonl(input_file, output_file)
    
    # 결과 확인
    if os.path.exists(output_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            original_size = len(f.read())
        with open(output_file, 'r', encoding='utf-8') as f:
            compressed_size = len(f.read())
        
        print("=" * 50)
        print(f"✅ 압축 완료!")
        print(f"원본 크기: {original_size:,} 문자")
        print(f"압축 크기: {compressed_size:,} 문자")
        print(f"압축률: {((original_size - compressed_size) / original_size * 100):.1f}% 감소")
    else:
        print("❌ 출력 파일 생성에 실패했습니다.")

if __name__ == "__main__":
    main()