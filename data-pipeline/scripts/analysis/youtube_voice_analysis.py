import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import argparse
import whisper


class YouTubeVoiceExtractor:
    def __init__(self, output_dir: str = "data/raw/audio", model_size: str = "base"):
        """YouTube 음성 추출기 초기화"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("data/raw/temp_videos")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Whisper 모델 로딩 (음성 분석용)
        print(f"Whisper {model_size} 모델 로딩 중...")
        self.model = whisper.load_model(model_size)
        print("모델 로딩 완료!")
    
    def check_dependencies(self) -> bool:
        """필요한 의존성 도구들이 설치되어 있는지 확인"""
        print("의존성 확인 중...")
        
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True, timeout=5)
            print("OK yt-dlp 설치됨")
        except:
            print("X yt-dlp 설치되지 않음 (설치: uv add yt-dlp)")
            return False
        
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
            print("OK ffmpeg 설치됨")
        except:
            print("X ffmpeg 설치되지 않음 (설치: winget install ffmpeg)")
            return False
        
        return True
    
    def download_video(self, url: str) -> Optional[str]:
        """YouTube 영상 다운로드"""
        try:
            # 비디오 정보 가져오기
            info_cmd = ['yt-dlp', '--print', 'id,title', url]
            result = subprocess.run(info_cmd, capture_output=True, text=True, check=True)
            
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                video_id = lines[0]
                title = lines[1]
                print(f"비디오 정보: {title}")
            
            # 비디오 다운로드
            output_template = str(self.temp_dir / f"{video_id}.%(ext)s")
            download_cmd = [
                'yt-dlp', '-f', 'worst[ext=mp4]/worst', '-o', output_template, '--no-playlist', 
                '--js-runtimes', 'node', '--remote-components', 'ejs:github', url
            ]
            
            print(f"비디오 다운로드 중: {url}")
            subprocess.run(download_cmd, check=True)
            
            # 다운로드된 파일 찾기
            for ext in ['mp4', 'webm', 'mkv', '3gp']:
                potential_file = self.temp_dir / f"{video_id}.{ext}"
                if potential_file.exists():
                    print(f"다운로드 완료: {potential_file}")
                    return str(potential_file)
            
            print("다운로드된 파일을 찾을 수 없습니다.")
            return None
                
        except subprocess.CalledProcessError as e:
            print(f"다운로드 실패: {e}")
            return None
    
    def extract_audio_segment(self, video_file: str, start_time: str, end_time: str) -> Optional[str]:
        """비디오에서 특정 구간의 음성 추출"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_name = Path(video_file).stem
            output_name = f"{video_name}_{start_time.replace(':', '')}-{end_time.replace(':', '')}_{timestamp}.wav"
            output_path = self.output_dir / output_name
            
            ffmpeg_cmd = [
                'ffmpeg', '-i', video_file, '-ss', start_time, '-to', end_time,
                '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', '-y', str(output_path)
            ]
            
            print(f"음성 추출 중: {start_time} ~ {end_time}")
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            
            if output_path.exists():
                print(f"음성 추출 완료: {output_path}")
                return str(output_path)
            return None
                
        except subprocess.CalledProcessError as e:
            print(f"음성 추출 실패: {e}")
            return None
    
    def transcribe_and_find_segments(self, video_file: str, search_text: str) -> List[str]:
        """음성 인식으로 특정 텍스트가 포함된 구간 찾아서 추출"""
        temp_audio = "temp_full_audio.wav"
        
        try:
            # 전체 음성 임시 추출
            ffmpeg_cmd = [
                'ffmpeg', '-i', video_file, '-vn', '-acodec', 'pcm_s16le', 
                '-ar', '44100', '-ac', '2', '-y', temp_audio
            ]
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            
            # 음성 인식
            print(f"음성 인식 중: {temp_audio}")
            result = self.model.transcribe(temp_audio, language="ko")
            
            print(f"\n전체 텍스트: {result['text']}")
            print("\n세그먼트별 결과:")
            for i, segment in enumerate(result.get('segments', [])):
                print(f"{i+1}. {segment['start']:.1f}s - {segment['end']:.1f}s: {segment['text']}")
            
            # 매칭 세그먼트 찾기
            matching_segments = []
            search_text_lower = search_text.lower().replace(" ", "")  # 공백 제거
            
            # 1. 단일 세그먼트에서 찾기
            for segment in result.get('segments', []):
                segment_text_clean = segment['text'].lower().replace(" ", "")
                if search_text_lower in segment_text_clean:
                    extended_start = max(0, segment['start'] - 2.0)
                    extended_end = segment['end'] + 2.0
                    matching_segments.append({
                        'start': extended_start,
                        'end': extended_end,
                        'text': segment['text'],
                        'match_type': 'single'
                    })
            
            # 2. 연속된 세그먼트에서 찾기 (단일 세그먼트에서 못 찾은 경우)
            if not matching_segments:
                segments = result.get('segments', [])
                for i in range(len(segments)):
                    # 현재 세그먼트부터 최대 5개 세그먼트까지 결합해서 검색
                    for j in range(i + 1, min(i + 6, len(segments) + 1)):
                        combined_text = "".join([seg['text'].lower().replace(" ", "") for seg in segments[i:j]])
                        if search_text_lower in combined_text:
                            extended_start = max(0, segments[i]['start'] - 2.0)
                            extended_end = segments[j-1]['end'] + 2.0
                            combined_display_text = " ".join([seg['text'] for seg in segments[i:j]])
                            matching_segments.append({
                                'start': extended_start,
                                'end': extended_end,
                                'text': combined_display_text,
                                'match_type': 'multi'
                            })
                            break  # 첫 번째 매치만 사용
                    if matching_segments:
                        break
            
            if not matching_segments:
                print(f"'{search_text}'가 포함된 구간을 찾을 수 없습니다.")
                return []
            
            print(f"\n'{search_text}'가 포함된 {len(matching_segments)}개 구간을 찾았습니다:")
            for i, segment in enumerate(matching_segments):
                print(f"  {i+1}. {segment['start']:.1f}s - {segment['end']:.1f}s: {segment['text']}")
            
            # 매칭된 구간들을 개별 음성 파일로 추출
            extracted_files = []
            for i, segment in enumerate(matching_segments):
                start_time = f"{int(segment['start']//3600):02d}:{int((segment['start']%3600)//60):02d}:{segment['start']%60:06.3f}"
                end_time = f"{int(segment['end']//3600):02d}:{int((segment['end']%3600)//60):02d}:{segment['end']%60:06.3f}"
                
                audio_file = self.extract_audio_segment(video_file, start_time, end_time)
                if audio_file:
                    extracted_files.append(audio_file)
            
            return extracted_files
            
        except subprocess.CalledProcessError as e:
            print(f"오류 발생: {e}")
            return []
        finally:
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
    
    def process_by_time_segments(self, url: str, segments: List[Tuple[str, str]]) -> List[str]:
        """시간 구간 기반으로 음성 추출"""
        video_file = self.download_video(url)
        if not video_file:
            return []
        
        extracted_files = []
        for i, (start, end) in enumerate(segments):
            print(f"\n구간 {i+1}/{len(segments)} 처리 중...")
            audio_file = self.extract_audio_segment(video_file, start, end)
            if audio_file:
                extracted_files.append(audio_file)
        
        self.cleanup_temp_files()
        return extracted_files
    
    def process_by_speech_content(self, url: str, search_text: str) -> List[str]:
        """음성 내용 기반으로 구간 찾아서 추출"""
        print(f"YouTube 음성 내용 분석 시작: {url}")
        print(f"찾을 내용: '{search_text}'")
        
        video_file = self.download_video(url)
        if not video_file:
            return []
        
        extracted_files = self.transcribe_and_find_segments(video_file, search_text)
        self.cleanup_temp_files()
        
        print(f"\n총 {len(extracted_files)}개 음성 구간 추출 완료")
        return extracted_files
    
    def cleanup_temp_files(self):
        """임시 파일들 정리"""
        try:
            for file in self.temp_dir.glob("*"):
                file.unlink()
            print("임시 파일 정리 완료")
        except Exception as e:
            print(f"임시 파일 정리 중 오류: {e}")


def parse_time_format(time_str: str) -> str:
    """시간 형식을 ffmpeg 형식으로 변환"""
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:  # MM:SS
            return f"00:{parts[0].zfill(2)}:{parts[1].zfill(2)}"
        elif len(parts) == 3:  # HH:MM:SS
            return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"
    else:
        # 초 단위 입력 (소수점 포함)
        total_seconds = float(time_str)
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    
    return time_str


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='YouTube 음성 추출 및 분석 도구')
    parser.add_argument('url', help='YouTube URL')
    parser.add_argument('--search-text', '-t', help='찾을 음성 내용 (예: "아기 맹수")')
    parser.add_argument('--segments', '-s', nargs='+', help='추출할 구간들 (예: "1:30-2:00" "3:15-4:30")')
    parser.add_argument('--output-dir', '-o', default='data/raw/audio', help='출력 디렉토리')
    parser.add_argument('--model-size', '-m', default='base', 
                       choices=['tiny', 'base', 'small', 'medium', 'large'], help='Whisper 모델 크기')
    
    args = parser.parse_args()
    
    # 추출기 초기화
    extractor = YouTubeVoiceExtractor(args.output_dir, args.model_size)
    
    if not extractor.check_dependencies():
        sys.exit(1)
    
    extracted_files = []
    
    # 음성 내용 기반 추출
    if args.search_text:
        speech_files = extractor.process_by_speech_content(args.url, args.search_text)
        extracted_files.extend(speech_files)
    
    # 시간 구간 기반 추출
    if args.segments:
        segments = []
        for segment in args.segments:
            if '-' in segment:
                start, end = segment.split('-', 1)
                start = parse_time_format(start.strip())
                end = parse_time_format(end.strip())
                segments.append((start, end))
        
        if segments:
            time_files = extractor.process_by_time_segments(args.url, segments)
            extracted_files.extend(time_files)
    
    # 대화형 모드
    if not args.search_text and not args.segments:
        print("\n추출 방법을 선택하세요:")
        print("1. 음성 내용으로 찾기")
        print("2. 시간 구간으로 찾기")
        
        choice = input("선택 (1 또는 2): ").strip()
        
        if choice == "1":
            search_text = input("찾을 음성 내용을 입력하세요: ").strip()
            if search_text:
                speech_files = extractor.process_by_speech_content(args.url, search_text)
                extracted_files.extend(speech_files)
        elif choice == "2":
            segments = []
            print("구간을 입력하세요 (예: 1:30-2:00). 완료하려면 빈 줄을 입력하세요.")
            while True:
                segment_input = input("구간: ").strip()
                if not segment_input:
                    break
                
                if '-' in segment_input:
                    start, end = segment_input.split('-', 1)
                    start = parse_time_format(start.strip())
                    end = parse_time_format(end.strip())
                    segments.append((start, end))
                    print(f"추가됨: {start} ~ {end}")
            
            if segments:
                time_files = extractor.process_by_time_segments(args.url, segments)
                extracted_files.extend(time_files)
    
    # 결과 출력
    if extracted_files:
        print(f"\n=== 최종 결과 ===")
        print(f"총 {len(extracted_files)}개 파일 추출 완료:")
        for file in extracted_files:
            print(f"  - {file}")
    else:
        print("추출된 파일이 없습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()