#!/usr/bin/env python3
"""
JSONL 파일에서 대화 상대를 "부장님"으로 통일하는 후처리 스크립트
"""

import json
import re

def fix_speaker_references(input_file="../../../data/processed/newbie/office_output_v2.jsonl", output_file="../../../data/processed/newbie/office_output_v3.jsonl"):
    """
    JSONL 파일에서 선배, 팀장 등을 부장님으로 변경
    
    Args:
        input_file (str): 입력 JSONL 파일
        output_file (str): 출력 JSONL 파일
    """
    
    # 변경할 단어들과 대체어 매핑 (실제 데이터에 존재하는 것만)
    replacements = {
        # 중복 호칭 수정 (가장 먼저 처리)
        "부장님님": "부장님",
        
        # 문법 오류 수정
        "부장님가": "부장님이",
        
        # 이름 호칭을 부장님으로 수정
        "데이브님": "부장님",
        
        # 한자를 한글로 변환
        "同行": "동행",
        
        # 직급/호칭 관련 (실제로 사용되는 것만)
        "선배": "부장님",
        "팀장": "부장님", 
        "팀장님": "부장님",
        
        # 상황 설명에서 자주 나오는 표현들
        "선배가": "부장님이",
        "선배께서": "부장님께서",
        "팀장이": "부장님이",
        "팀장님이": "부장님이",
        "팀장께서": "부장님께서",
        "팀장님께서": "부장님께서",
        
        # 존댓말 관련
        "선배님": "부장님",
        "선배분": "부장님",
    }
    
    # 정규표현식: "부장"이 아닌 이름 + "님" 패턴을 찾아서 "부장님"으로 변경
    # 한글 이름 패턴 (2-4글자) + "님"
    name_pattern = re.compile(r'(?<!부장)([가-힣]{2,4})님')
    
    fixed_count = 0
    total_count = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f_in, \
             open(output_file, 'w', encoding='utf-8') as f_out:
            
            for line_num, line in enumerate(f_in, 1):
                total_count += 1
                
                try:
                    # JSON 파싱
                    data = json.loads(line.strip())
                    
                    # 원본 저장 (변경 여부 확인용)
                    original_input = data.get("input", "")
                    original_output = data.get("output", "")
                    
                    # input 필드에서 단어 교체
                    if "input" in data:
                        # 먼저 기본 단어 교체
                        for old_word, new_word in replacements.items():
                            data["input"] = data["input"].replace(old_word, new_word)
                        # 그 다음 이름+님 패턴 교체
                        data["input"] = name_pattern.sub("부장님", data["input"])
                    
                    # output 필드에서 단어 교체
                    if "output" in data:
                        # 먼저 기본 단어 교체
                        for old_word, new_word in replacements.items():
                            data["output"] = data["output"].replace(old_word, new_word)
                        # 그 다음 이름+님 패턴 교체
                        data["output"] = name_pattern.sub("부장님", data["output"])
                    
                    # 변경 여부 확인
                    if (data.get("input", "") != original_input or 
                        data.get("output", "") != original_output):
                        fixed_count += 1
                        print(f"라인 {line_num}: 수정됨")
                        if original_input != data.get("input", ""):
                            print(f"  INPUT 변경: {original_input[:50]}... → {data['input'][:50]}...")
                        if original_output != data.get("output", ""):
                            print(f"  OUTPUT 변경: {original_output[:50]}... → {data['output'][:50]}...")
                    
                    # 수정된 JSON을 파일에 저장
                    f_out.write(json.dumps(data, ensure_ascii=False) + '\n')
                    
                except json.JSONDecodeError as e:
                    print(f"❌ 라인 {line_num}: JSON 파싱 실패 - {e}")
                    # 원본 라인을 그대로 저장
                    f_out.write(line)
                except Exception as e:
                    print(f"❌ 라인 {line_num}: 처리 실패 - {e}")
                    # 원본 라인을 그대로 저장
                    f_out.write(line)
        
        print(f"\n=== 후처리 완료 ===")
        print(f"총 처리: {total_count}개")
        print(f"수정됨: {fixed_count}개")
        print(f"수정률: {fixed_count/total_count*100:.1f}%")
        print(f"입력 파일: {input_file}")
        print(f"출력 파일: {output_file}")
        
        return {"success": True, "total": total_count, "fixed": fixed_count}
        
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {input_file}")
        return {"success": False, "error": "파일 없음"}
    except Exception as e:
        print(f"❌ 처리 중 오류: {e}")
        return {"success": False, "error": str(e)}

def preview_changes(input_file="../../../data/processed/newbie/office_output_v2.jsonl", max_preview=5):
    """
    변경될 내용을 미리 확인하는 함수
    """
    replacements = {
        "부장님님": "부장님", "부장님가": "부장님이", "데이브님": "부장님", "同行": "동행", "선배": "부장님", "팀장": "부장님", "팀장님": "부장님"
    }
    
    # 정규표현식: "부장"이 아닌 이름 + "님" 패턴
    name_pattern = re.compile(r'(?<!부장)([가-힣]{2,4})님')
    
    preview_count = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if preview_count >= max_preview:
                    break
                    
                try:
                    data = json.loads(line.strip())
                    
                    # 변경 대상인지 확인
                    input_text = data.get("input", "")
                    output_text = data.get("output", "")
                    
                    has_changes = False
                    
                    # 기본 단어 변경 확인
                    for old_word in replacements.keys():
                        if old_word in input_text or old_word in output_text:
                            has_changes = True
                            break
                    
                    # 이름+님 패턴 변경 확인
                    if not has_changes:
                        if name_pattern.search(input_text) or name_pattern.search(output_text):
                            has_changes = True
                    
                    if has_changes:
                        preview_count += 1
                        print(f"\n=== 미리보기 {preview_count} (라인 {line_num}) ===")
                        print(f"INPUT: {input_text}")
                        print(f"OUTPUT: {output_text}")
                        
                        # 변경 후 모습 보여주기
                        new_input = input_text
                        new_output = output_text
                        
                        # 기본 단어 교체
                        for old_word, new_word in replacements.items():
                            new_input = new_input.replace(old_word, new_word)
                            new_output = new_output.replace(old_word, new_word)
                        
                        # 이름+님 패턴 교체
                        new_input = name_pattern.sub("부장님", new_input)
                        new_output = name_pattern.sub("부장님", new_output)
                        
                        if new_input != input_text:
                            print(f"INPUT 변경 후: {new_input}")
                        if new_output != output_text:
                            print(f"OUTPUT 변경 후: {new_output}")
                
                except:
                    continue
                    
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {input_file}")

if __name__ == "__main__":
    print("=== 대화 상대 수정 스크립트 ===\n")
    
    # 미리보기
    print("변경될 내용 미리보기:")
    preview_changes()
    
    # 실제 수정 진행 여부 확인
    print(f"\n계속 진행하시겠습니까? (y/n): ", end="")
    response = input().lower().strip()
    
    if response in ['y', 'yes', '네', 'ㅇ']:
        result = fix_speaker_references()
        if result["success"]:
            print(f"\n🎉 성공적으로 {result['fixed']}개 항목을 수정했습니다!")
        else:
            print(f"\n💥 실패: {result['error']}")
    else:
        print("취소되었습니다.")