import os
import json
import requests
import numpy as np
from pathlib import Path
from typing import Dict, Optional
import argparse
from datetime import datetime
import re
from advanced_voice_analyzer import AdvancedVoiceAnalyzer


def sanitize_filename(text: str) -> str:
    """텍스트를 파일명으로 사용할 수 있게 정리"""
    sanitized = re.sub(r'[<>:"/\\|?*]', '', text)
    sanitized = re.sub(r'\s+', '_', sanitized)
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    return sanitized


class AdvancedTTSGenerator:
    def __init__(self, openai_key: str = None):
        """고급 TTS 생성기 초기화"""
        self.openai_key = openai_key
        self.voice_analyzer = AdvancedVoiceAnalyzer()
        
        # OpenAI TTS 설정
        if openai_key:
            self.openai_headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
    
    def generate_tts_from_text_only(self, text: str, voice: str = None, custom_voice_id: str = None) -> Optional[str]:
        """텍스트만으로 TTS 생성 (음성 파일 분석 없이)"""
        print(f"텍스트 기반 TTS 생성: '{text}'")
        
        # 한국어 감지
        has_korean = any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in text)
        
        if has_korean:
            # 한국어 텍스트용 기본 SSML 생성
            ssml = f'<speak><prosody rate="x-slow" pitch="0%" volume="medium">{text}</prosody></speak>'
            recommended_voice = voice or 'coral'  # 한국어는 기본적으로 coral
        else:
            # 다른 언어용 기본 SSML
            ssml = f'<speak><prosody rate="medium" pitch="0%" volume="medium">{text}</prosody></speak>'
            recommended_voice = voice or 'nova'
        
        print(f"  생성된 SSML: {ssml}")
        print(f"  사용할 음성: {recommended_voice}")
        
        # TTS 생성
        if custom_voice_id:
            output_file = self.generate_openai_tts_with_ssml(text, ssml, custom_voice_id=custom_voice_id)
        else:
            output_file = self.generate_openai_tts_with_ssml(text, ssml, voice=recommended_voice)
        
        return output_file

    def analyze_and_generate_ssml(self, audio_file: str, text: str) -> Dict:
        """음성 파일을 분석하고 SSML 생성"""
        print(f"고급 음성 분석 시작: {audio_file}")
        
        # 운율 분석
        prosody_data = self.voice_analyzer.analyze_prosody(audio_file)
        
        # SSML 생성
        ssml = self.voice_analyzer.generate_ssml_from_analysis(text, prosody_data)
        
        # 음성 특성 분석 (간단한 피치 기반 추천)
        pitch_values = prosody_data['pitch_contour']['pitches']
        avg_pitch = np.mean(pitch_values) if pitch_values else 300
        
        # 피치 기반 음성 특성 분류
        if avg_pitch > 800:
            pitch_level = 'high'
        elif avg_pitch < 400:
            pitch_level = 'low'
        else:
            pitch_level = 'medium'
        
        characteristics = {
            'pitch_level': pitch_level,
            'pitch_desc': f'{pitch_level} 음성',
            'avg_pitch': avg_pitch
        }
        
        # OpenAI 음성 추천
        voice_mapping = {
            'low': 'onyx',      # 낮은 음성
            'medium': 'nova',   # 중간 음성  
            'high': 'coral'     # 높은 음성 (coral로 변경)
        }
        
        pitch_level = characteristics.get('pitch_level', 'medium')
        recommended_voice = voice_mapping.get(pitch_level, 'nova')
        
        print(f"분석 완료")
        print(f"  억양 패턴: {prosody_data['pitch_contour']['pattern']}")
        print(f"  템포: {prosody_data['rhythm']['tempo']:.1f} BPM")
        print(f"  강세 위치: {len(prosody_data['stress_pattern']['peaks'])}개")
        print(f"  추천 음성: {recommended_voice} (피치 레벨: {pitch_level})")
        print(f"  생성된 SSML: {ssml}")
        
        return {
            'prosody_analysis': prosody_data,
            'generated_ssml': ssml,
            'recommended_voice': recommended_voice,
            'voice_characteristics': characteristics,
            'target_text': text
        }
    
    def generate_openai_tts_with_ssml(self, text: str, ssml: str, voice: str = "shimmer", 
                                     model: str = "tts-1-hd", output_path: str = None, 
                                     custom_voice_id: str = None) -> Optional[str]:
        """OpenAI TTS로 SSML 기반 음성 생성 (파인튜닝 지원)"""
        if not self.openai_key:
            print("OpenAI API 키가 설정되지 않았습니다.")
            return None
        
        try:
            # OpenAI TTS는 SSML을 직접 지원하지 않으므로 텍스트 기반으로 처리
            # SSML에서 추출한 정보를 텍스트 전처리에 활용
            processed_text = self._process_text_from_ssml(text, ssml)
            
            # 출력 파일 경로 설정
            if not output_path:
                text_filename = sanitize_filename(text)
                voice_name = custom_voice_id if custom_voice_id else voice
                output_path = f"data/analysis/tts_tests/advanced_openai_{voice_name}_{text_filename}.mp3"
            
            # API 요청 데이터 (파인튜닝된 음성 지원)
            data = {
                "model": model,
                "input": processed_text,
                "response_format": "mp3"
            }
            
            # 파인튜닝된 커스텀 음성 ID가 있으면 사용, 없으면 기본 음성 사용
            if custom_voice_id:
                data["voice"] = custom_voice_id
                print(f"파인튜닝된 커스텀 음성 사용: {custom_voice_id}")
            else:
                data["voice"] = voice
                print(f"기본 OpenAI 음성 사용: {voice}")
            
            print(f"OpenAI TTS 생성 중 (고급 분석 적용)...")
            print(f"  원본 텍스트: '{text}'")
            print(f"  처리된 텍스트: '{processed_text}'")
            print(f"  모델: {model}")
            
            # API 호출
            response = requests.post(
                "https://api.openai.com/v1/audio/speech", 
                headers=self.openai_headers, 
                json=data
            )
            
            if response.status_code == 200:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"OpenAI TTS 생성 완료: {output_path}")
                return output_path
            else:
                print(f"OpenAI TTS 생성 실패: {response.status_code}")
                print(f"  오류: {response.text}")
                return None
                
        except Exception as e:
            print(f"OpenAI TTS 오류: {e}")
            return None
    
    def _process_text_from_ssml(self, text: str, ssml: str) -> str:
        """SSML 정보를 바탕으로 텍스트 전처리 - 자동화된 한국어 장음 처리"""
        processed_text = text
        
        # 한국어 장음 자동 처리 (한국어가 포함되고 x-slow 또는 slow인 경우)
        has_korean = any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in text)
        is_slow_rate = 'rate="x-slow"' in ssml or 'rate="slow"' in ssml
        
        if has_korean and is_slow_rate:
            # 한국어가 포함된 경우 자동 장음 처리
            processed_text = self._add_korean_vowel_extension(text, ssml)
            print(f"  자동 장음 변환: '{text}' → '{processed_text}'")
            return processed_text
        
        # SSML에서 rate 정보 추출
        if 'rate="fast"' in ssml:
            # 빠른 속도를 위한 텍스트 조정 (단어 사이 간격 줄이기)
            processed_text = re.sub(r'\s+', ' ', processed_text)
        elif 'rate="slow"' in ssml or 'rate="x-slow"' in ssml:
            # 느린 속도를 위한 텍스트 조정 (단어 사이 간격 늘리기)
            processed_text = re.sub(r'\s+', '  ', processed_text)
        
        # 강조 표시된 단어 처리
        if '<emphasis' in ssml:
            # 강조된 단어는 대문자로 변환하거나 반복
            words = processed_text.split()
            if len(words) >= 2:
                # 첫 번째 단어 강조
                words[0] = words[0] + "!"
        
        # 한국어 발음 개선
        processed_text = self._improve_korean_pronunciation(processed_text)
        
        return processed_text
    
    def _add_korean_vowel_extension(self, text: str, ssml: str) -> str:
        """한국어 텍스트에 자동으로 장음 효과 추가"""
        # 한국어 모음 매핑 (받침 없는 글자 → 장음 글자)
        vowel_extensions = {
            '가': '가아', '나': '나아', '다': '다아', '라': '라아', '마': '마아', '바': '바아', '사': '사아', '자': '자아', '차': '차아', '카': '카아', '타': '타아', '파': '파아', '하': '하아',
            '거': '거어', '너': '너어', '더': '더어', '러': '러어', '머': '머어', '버': '버어', '서': '서어', '저': '저어', '처': '처어', '커': '커어', '터': '터어', '퍼': '퍼어', '허': '허어',
            '고': '고오', '노': '노오', '도': '도오', '로': '로오', '모': '모오', '보': '보오', '소': '소오', '조': '조오', '초': '초오', '코': '코오', '토': '토오', '포': '포오', '호': '호오',
            '구': '구우', '누': '누우', '두': '두우', '루': '루우', '무': '무우', '부': '부우', '수': '수우', '주': '주우', '추': '추우', '쿠': '쿠우', '투': '투우', '푸': '푸우', '후': '후우',
            '기': '기이', '니': '니이', '디': '디이', '리': '리이', '미': '미이', '비': '비이', '시': '시이', '지': '지이', '치': '치이', '키': '키이', '티': '티이', '피': '피이', '히': '히이',
            '게': '게에', '네': '네에', '데': '데에', '레': '레에', '메': '메에', '베': '베에', '세': '세에', '제': '제에', '체': '체에', '케': '케에', '테': '테에', '페': '페에', '헤': '헤에'
        }
        
        processed_text = text
        
        # 각 글자에 대해 장음 처리
        for original, extended in vowel_extensions.items():
            if original in processed_text:
                processed_text = processed_text.replace(original, extended)
        
        # 억양에 따른 추가 처리
        if 'pitch="+' in ssml and 'volume="loud"' in ssml:
            # 상승 억양인 경우 의문문 추가
            if not processed_text.endswith('?'):
                processed_text += '?!'
        elif 'pitch="-' in ssml:
            # 하강 억양인 경우 여운 추가
            if not processed_text.endswith('...'):
                processed_text += '...'
        
        return processed_text
    
    def _improve_korean_pronunciation(self, text: str) -> str:
        """한국어 발음 개선"""
        # 받침 'ㅇ' 강조
        improved_text = re.sub(r'([아-힣])앙', r'\1아앙', text)
        # 공백 정규화
        improved_text = re.sub(r'\s+', ' ', improved_text.strip())
        return improved_text
    
    def generate_tts_from_json(self, json_file: str, text: str = None, output_dir: str = "data/analysis/tts_tests", 
                              custom_voice_id: str = None) -> Dict:
        """JSON 파일에서 분석 데이터를 읽어서 TTS 생성"""
        print("=" * 60)
        print("JSON 기반 TTS 생성")
        if custom_voice_id:
            print(f"파인튜닝된 커스텀 음성 사용: {custom_voice_id}")
        print("=" * 60)
        
        # JSON 파일 읽기
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            print(f"JSON 파일 로드: {json_file}")
        except Exception as e:
            print(f"JSON 파일 읽기 실패: {e}")
            return None
        
        # JSON에서 분석 데이터 추출
        if 'prosody_analysis' in json_data:
            analysis_result = json_data
        elif 'analysis_result' in json_data:
            analysis_result = json_data['analysis_result']
        else:
            print("JSON 파일에 분석 데이터가 없습니다.")
            return None
        
        # 텍스트 결정 (파라미터 > JSON > 에러)
        if text:
            target_text = text
        elif 'target_text' in analysis_result:
            target_text = analysis_result['target_text']
        else:
            print("생성할 텍스트가 지정되지 않았습니다.")
            return None
        
        # SSML과 음성 정보 추출
        ssml = analysis_result.get('generated_ssml', '')
        recommended_voice = analysis_result.get('recommended_voice', 'nova')
        
        print(f"대상 텍스트: '{target_text}'")
        print(f"생성된 SSML: {ssml}")
        print(f"추천 음성: {recommended_voice}")
        
        results = {
            'analysis_result': analysis_result,
            'generated_files': {},
            'timestamp': datetime.now().isoformat(),
            'custom_voice_used': custom_voice_id is not None,
            'custom_voice_id': custom_voice_id,
            'source': 'json_file'
        }
        
        # OpenAI TTS 생성
        if self.openai_key:
            print(f"\nOpenAI TTS 생성 (JSON 기반)")
            
            if custom_voice_id:
                # 파인튜닝된 커스텀 음성 사용
                openai_file = self.generate_openai_tts_with_ssml(
                    target_text, ssml, custom_voice_id=custom_voice_id
                )
            else:
                # JSON에서 추천된 음성 사용
                openai_file = self.generate_openai_tts_with_ssml(target_text, ssml, voice=recommended_voice)
            
            if openai_file:
                results['generated_files']['openai'] = openai_file
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("JSON 기반 TTS 생성 결과")
        print("=" * 60)
        print(f"원본 텍스트: '{target_text}'")
        print(f"억양 패턴: {analysis_result['prosody_analysis']['pitch_contour']['pattern']}")
        print(f"생성된 SSML: {ssml}")
        
        if 'openai' in results['generated_files']:
            print(f"OpenAI TTS: {results['generated_files']['openai']}")
        
        return results

    def generate_advanced_tts(self, audio_file: str, text: str, output_dir: str = "data/analysis/tts_tests", 
                             custom_voice_id: str = None) -> Dict:
        """고급 분석 기반 TTS 생성 (파인튜닝 지원)"""
        print("=" * 60)
        print("고급 음성 분석 기반 TTS 생성")
        if custom_voice_id:
            print(f"파인튜닝된 커스텀 음성 사용: {custom_voice_id}")
        print("=" * 60)
        
        # 1. 음성 분석 및 SSML 생성
        analysis_result = self.analyze_and_generate_ssml(audio_file, text)
        ssml = analysis_result['generated_ssml']
        
        results = {
            'analysis_result': analysis_result,
            'generated_files': {},
            'timestamp': datetime.now().isoformat(),
            'custom_voice_used': custom_voice_id is not None,
            'custom_voice_id': custom_voice_id
        }
        
        # 2. OpenAI TTS 생성 (파인튜닝 지원)
        if self.openai_key:
            print(f"\nOpenAI TTS 생성 (고급 분석 적용)")
            
            if custom_voice_id:
                # 파인튜닝된 커스텀 음성 사용
                openai_file = self.generate_openai_tts_with_ssml(
                    text, ssml, custom_voice_id=custom_voice_id
                )
            else:
                # 기본 추천 음성 사용
                recommended_voice = analysis_result.get('recommended_voice', 'shimmer')
                openai_file = self.generate_openai_tts_with_ssml(text, ssml, voice=recommended_voice)
            
            if openai_file:
                results['generated_files']['openai'] = openai_file
        
        # 3. 시각화 생성
        text_filename = sanitize_filename(text)
        viz_path = f"{output_dir}/advanced_prosody_analysis_{text_filename}_visualization.png"
        self.voice_analyzer.create_prosody_visualization(analysis_result['prosody_analysis'], viz_path)
        results['visualization'] = viz_path
        
        # 4. 결과 요약
        print("\n" + "=" * 60)
        print("고급 TTS 생성 결과")
        print("=" * 60)
        print(f"원본 텍스트: '{text}'")
        print(f"억양 패턴: {analysis_result['prosody_analysis']['pitch_contour']['pattern']}")
        print(f"생성된 SSML: {ssml}")
        
        if 'openai' in results['generated_files']:
            print(f"OpenAI TTS: {results['generated_files']['openai']}")
        print(f"시각화: {viz_path}")
        
        return results


def load_api_keys():
    """환경변수 또는 .env 파일에서 API 키 로드"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"\'')
    
    return os.getenv('OPENAI_API_KEY')


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='고급 음성 분석 기반 TTS 생성기 (파인튜닝 지원)')
    parser.add_argument('input_file', nargs='?', help='분석할 원본 음성 파일 또는 JSON 파일')
    parser.add_argument('text', nargs='?', help='생성할 텍스트')
    parser.add_argument('--json-file', help='JSON 파일에서 분석 데이터 읽기')
    parser.add_argument('--openai-key', help='OpenAI API 키')
    parser.add_argument('--custom-voice', help='파인튜닝된 커스텀 음성 ID (예: voice-abc123)')
    parser.add_argument('--voice', help='사용할 기본 음성 (예: coral, nova, onyx)')
    parser.add_argument('--output-dir', '-o', default='data/analysis/tts_tests', help='출력 디렉토리')
    
    args = parser.parse_args()
    
    # API 키 로드
    openai_key = args.openai_key
    
    if not openai_key:
        openai_key = load_api_keys()
    
    # OpenAI API 키는 필수
    if not openai_key:
        print("OpenAI API 키가 필요합니다.")
        print("OpenAI API 키를 설정하세요.")
        return
    
    # TTS 생성기 초기화
    generator = AdvancedTTSGenerator(openai_key)
    
    # JSON 파일 모드
    if args.json_file:
        if not os.path.exists(args.json_file):
            print(f"오류: JSON 파일을 찾을 수 없습니다: {args.json_file}")
            return
        
        print("JSON 파일 기반 TTS 생성")
        results = generator.generate_tts_from_json(
            args.json_file,
            args.text,
            args.output_dir,
            custom_voice_id=args.custom_voice
        )
        
        if results:
            if args.text:
                text_filename = sanitize_filename(args.text)
            else:
                text_filename = sanitize_filename(results['analysis_result'].get('target_text', 'unknown'))
            
            results_file = f"{args.output_dir}/advanced_tts_results_{text_filename}.json"
            Path(results_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"\n결과 저장: {results_file}")
    
    # 음성 파일 모드 (기존 방식)
    elif args.input_file and args.text:
        # 파일 타입 자동 감지
        if args.input_file.endswith('.json'):
            print("JSON 파일 자동 감지")
            results = generator.generate_tts_from_json(
                args.input_file,
                args.text,
                args.output_dir,
                custom_voice_id=args.custom_voice
            )
        else:
            # 음성 파일 존재 확인
            if not os.path.exists(args.input_file):
                print(f"오류: 음성 파일을 찾을 수 없습니다: {args.input_file}")
                return
            
            print("음성 파일 기반 고급 TTS 생성")
            results = generator.generate_advanced_tts(
                args.input_file, 
                args.text, 
                args.output_dir,
                custom_voice_id=args.custom_voice
            )
        
        # 결과 저장
        if results:
            text_filename = sanitize_filename(args.text)
            results_file = f"{args.output_dir}/advanced_tts_results_{text_filename}.json"
            Path(results_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"\n결과 저장: {results_file}")
    
    # 텍스트만으로 TTS 생성
    elif args.text:
        print("텍스트 기반 TTS 생성")
        output_file = generator.generate_tts_from_text_only(
            args.text, 
            voice=args.voice,
            custom_voice_id=args.custom_voice
        )
        
        if output_file:
            print(f"TTS 생성 완료: {output_file}")
        else:
            print("TTS 생성 실패")
    
    else:
        print("사용법:")
        print("  음성 파일 기반: python script.py audio.wav '텍스트'")
        print("  JSON 파일 기반: python script.py --json-file analysis.json ['텍스트']")
        print("  텍스트만: python script.py --text '텍스트'")


if __name__ == "__main__":
    main()