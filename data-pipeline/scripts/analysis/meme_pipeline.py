"""
밈 음성 분석 파이프라인 (고급 분석 전용)
YouTube URL + 밈 텍스트 → 고급 TTS 생성까지 자동화

사용법:
python scripts/analysis/meme_pipeline.py "https://youtube.com/watch?v=..." "매끈매끈하다"
python scripts/analysis/meme_pipeline.py "https://youtube.com/watch?v=..." "나니가 스키" --custom-voice "voice-abc123"
"""

import os
import sys
import subprocess
import json
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List


class AdvancedMemePipeline:
    def __init__(self):
        """고급 밈 처리 파이프라인 초기화"""
        self.scripts_dir = Path(".")  # 현재 디렉토리 (scripts/analysis)
        self.output_dir = Path("../../data/analysis")
        self.audio_dir = Path("../../data/raw/audio")
        self.tts_dir = Path("../../data/analysis/tts_tests")
        
        # 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.tts_dir.mkdir(parents=True, exist_ok=True)
    
    def check_dependencies(self) -> bool:
        """필요한 스크립트들이 존재하는지 확인"""
        required_scripts = [
            "youtube_voice_analysis.py",
            "advanced_voice_analyzer.py",
            "advanced_tts_generator.py"
        ]
        
        for script in required_scripts:
            script_path = self.scripts_dir / script
            if not script_path.exists():
                print(f"필수 스크립트가 없습니다: {script_path}")
                return False
        
        print("모든 필수 스크립트 확인됨")
        return True
    
    def get_latest_audio_file(self) -> Optional[Path]:
        """가장 최근에 생성된 음성 파일 찾기"""
        audio_files = list(self.audio_dir.glob("*.wav"))
        if not audio_files:
            return None
        
        # 생성 시간 기준으로 가장 최근 파일
        latest_file = max(audio_files, key=lambda f: f.stat().st_ctime)
        return latest_file
    
    def extract_audio(self, youtube_url: str, meme_text: str) -> Optional[Path]:
        """1-2단계: YouTube에서 음성 추출"""
        print("1단계: YouTube 음성 추출 시작...")
        print(f"   URL: {youtube_url}")
        print(f"   찾을 텍스트: '{meme_text}'")
        
        # 기존 파일 개수 확인 (새로 생성된 파일 구분용)
        existing_files = set(self.audio_dir.glob("*.wav"))
        
        # youtube_voice_analysis.py 실행
        extract_cmd = [
            sys.executable,  # 현재 Python 인터프리터
            str(self.scripts_dir / "youtube_voice_analysis.py"),
            youtube_url,
            "--search-text", meme_text
        ]
        
        try:
            print("   YouTube 다운로드 및 음성 인식 중...")
            result = subprocess.run(
                extract_cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5분 타임아웃
            )
            
            if result.returncode != 0:
                print(f"음성 추출 실패:")
                print(f"   오류: {result.stderr}")
                return None
            
            # 새로 생성된 파일 찾기
            new_files = set(self.audio_dir.glob("*.wav")) - existing_files
            
            if not new_files:
                print("새로운 음성 파일이 생성되지 않았습니다.")
                return None
            
            # 가장 최근 파일 선택
            latest_file = max(new_files, key=lambda f: f.stat().st_ctime)
            print(f"음성 추출 완료: {latest_file.name}")
            
            return latest_file
            
        except subprocess.TimeoutExpired:
            print("음성 추출 시간 초과 (5분)")
            return None
        except Exception as e:
            print(f"음성 추출 중 오류: {e}")
            return None
    
    def analyze_voice_advanced(self, audio_file: Path, meme_text: str) -> Optional[Path]:
        """고급 음성 분석 및 운율 분석"""
        print("2단계: 고급 음성 분석 시작...")
        print(f"   음성 파일: {audio_file.name}")
        print(f"   대상 텍스트: '{meme_text}'")
        
        # advanced_voice_analyzer.py 실행
        text_filename = self._sanitize_filename(meme_text)
        output_json = self.output_dir / f"prosody_analysis_{text_filename}.json"
        
        analyze_cmd = [
            sys.executable,
            str(self.scripts_dir / "advanced_voice_analyzer.py"),
            str(audio_file),
            "--text", meme_text,
            "--output", str(output_json)
        ]
        
        try:
            print("   운율 및 고급 특성 분석 중...")
            result = subprocess.run(
                analyze_cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3분 타임아웃
            )
            
            if result.returncode != 0:
                print(f"고급 음성 분석 실패:")
                print(f"   오류: {result.stderr}")
                return None
            
            # 생성된 JSON 파일 확인
            if not output_json.exists():
                print(f"고급 분석 JSON 파일이 생성되지 않았습니다: {output_json}")
                return None
            
            print(f"고급 음성 분석 완료: {output_json.name}")
            return output_json
            
        except subprocess.TimeoutExpired:
            print("고급 음성 분석 시간 초과 (3분)")
            return None
        except Exception as e:
            print(f"고급 음성 분석 중 오류: {e}")
            return None
    
    def generate_advanced_tts(self, audio_file: Path, meme_text: str, custom_voice: str = None) -> Optional[Path]:
        """고급 TTS 생성"""
        print("3단계: 고급 TTS 생성 시작...")
        print(f"   음성 파일: {audio_file.name}")
        print(f"   대상 텍스트: '{meme_text}'")
        if custom_voice:
            print(f"   커스텀 음성: {custom_voice}")
        
        # advanced_tts_generator.py 실행
        tts_cmd = [
            sys.executable,
            str(self.scripts_dir / "advanced_tts_generator.py"),
            str(audio_file),
            meme_text
        ]
        
        # 커스텀 음성이 있으면 추가
        if custom_voice:
            tts_cmd.extend(["--custom-voice", custom_voice])
        
        try:
            print("   억양 분석 및 TTS 생성 중...")
            result = subprocess.run(
                tts_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5분 타임아웃
            )
            
            if result.returncode != 0:
                print(f"고급 TTS 생성 실패:")
                print(f"   오류: {result.stderr}")
                return None
            
            # 생성된 TTS 파일 찾기
            text_filename = self._sanitize_filename(meme_text)
            voice_name = custom_voice if custom_voice else "coral"  # 기본값
            tts_file = self.tts_dir / f"advanced_openai_{voice_name}_{text_filename}.mp3"
            
            if not tts_file.exists():
                print(f"TTS 파일이 생성되지 않았습니다: {tts_file}")
                return None
            
            print(f"고급 TTS 생성 완료: {tts_file.name}")
            return tts_file
            
        except subprocess.TimeoutExpired:
            print("고급 TTS 생성 시간 초과 (5분)")
            return None
        except Exception as e:
            print(f"고급 TTS 생성 중 오류: {e}")
            return None
    
    def _sanitize_filename(self, text: str) -> str:
        """파일명으로 사용할 수 있도록 텍스트 정리"""
        sanitized = re.sub(r'[^\w\s-]', '', text)
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        return sanitized.strip('_')
    
    def process_meme(self, youtube_url: str, meme_text: str, custom_voice: str = None) -> Optional[dict]:
        """전체 파이프라인 실행: URL + 텍스트 → 고급 TTS 생성"""
        print("=" * 60)
        print("고급 밈 음성 분석 파이프라인 시작")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # 의존성 확인
        if not self.check_dependencies():
            return None
        
        # 1단계: 음성 추출
        audio_file = self.extract_audio(youtube_url, meme_text)
        if not audio_file:
            return None
        
        # 2단계: 고급 음성 분석
        json_file = self.analyze_voice_advanced(audio_file, meme_text)
        if not json_file:
            return None
        
        # 3단계: 고급 TTS 생성
        tts_file = self.generate_advanced_tts(audio_file, meme_text, custom_voice)
        if not tts_file:
            return None
        
        # 결과 로드
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                analysis_result = json.load(f)
        except Exception as e:
            print(f"JSON 파일 읽기 실패: {e}")
            return None
        
        # 완료 정보
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("고급 파이프라인 완료!")
        print("=" * 60)
        print(f"음성 파일: {audio_file}")
        print(f"분석 결과: {json_file}")
        print(f"TTS 파일: {tts_file}")
        print(f"소요 시간: {duration:.1f}초")
        
        # 고급 분석 결과 요약
        prosody_analysis = analysis_result.get('prosody_analysis', {})
        pitch_contour = prosody_analysis.get('pitch_contour', {})
        rhythm = prosody_analysis.get('rhythm', {})
        stress_pattern = prosody_analysis.get('stress_pattern', {})
        generated_ssml = analysis_result.get('generated_ssml', 'N/A')
        
        print(f"\n고급 분석 요약:")
        print(f"   밈 텍스트: '{analysis_result.get('target_text', 'N/A')}'")
        print(f"   억양 패턴: {pitch_contour.get('pattern', 'N/A')}")
        print(f"   템포: {rhythm.get('tempo', 'N/A')} BPM")
        print(f"   강세 위치: {len(stress_pattern.get('peaks', []))}개")
        print(f"   생성된 SSML: {generated_ssml[:100]}{'...' if len(generated_ssml) > 100 else ''}")
        
        if custom_voice:
            print(f"   사용된 커스텀 음성: {custom_voice}")
        
        return {
            'audio_file': str(audio_file),
            'json_file': str(json_file),
            'tts_file': str(tts_file),
            'analysis_result': analysis_result,
            'duration': duration,
            'custom_voice': custom_voice
        }
    
def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='고급 밈 음성 분석 파이프라인 (TTS 생성까지 자동화)')
    parser.add_argument('youtube_url', help='YouTube URL')
    parser.add_argument('meme_text', help='찾을 밈 텍스트')
    parser.add_argument('--custom-voice', help='파인튜닝된 커스텀 음성 ID (예: voice-abc123)')
    
    args = parser.parse_args()
    
    pipeline = AdvancedMemePipeline()
    
    result = pipeline.process_meme(args.youtube_url, args.meme_text, args.custom_voice)
    
    if result:
        print(f"\n완료된 파일들:")
        print(f"   원본 음성: {result['audio_file']}")
        print(f"   분석 결과: {result['json_file']}")
        print(f"   생성된 TTS: {result['tts_file']}")
        
        if result.get('custom_voice'):
            print(f"\n파인튜닝된 음성 '{result['custom_voice']}'를 사용했습니다!")
        else:
            print(f"\n팁: 파인튜닝된 음성을 사용하려면 --custom-voice 옵션을 추가하세요")
            print(f"   python scripts/analysis/meme_pipeline.py \"{args.youtube_url}\" \"{args.meme_text}\" --custom-voice \"voice-abc123\"")
    else:
        print("파이프라인 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()