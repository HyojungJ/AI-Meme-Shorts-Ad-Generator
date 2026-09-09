import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import whisper
import librosa
import numpy as np
import json


class MemeVoiceProcessor:
    def __init__(self, model_size: str = "base"):
        self.output_dir = Path("data/raw/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("data/raw/temp_videos")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = whisper.load_model(model_size)
    
    def check_dependencies(self) -> bool:
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True, timeout=5)
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
            return True
        except:
            return False
    
    def download_video(self, url: str) -> Optional[str]:
        try:
            info_cmd = ['yt-dlp', '--print', 'id', url]
            result = subprocess.run(info_cmd, capture_output=True, text=True, check=True)
            video_id = result.stdout.strip()
            
            output_template = str(self.temp_dir / f"{video_id}.%(ext)s")
            download_cmd = [
                'yt-dlp', '-f', 'worst[ext=mp4]/worst', '-o', output_template, 
                '--no-playlist', url
            ]
            subprocess.run(download_cmd, check=True, capture_output=True)
            
            for ext in ['mp4', 'webm', 'mkv', '3gp']:
                potential_file = self.temp_dir / f"{video_id}.{ext}"
                if potential_file.exists():
                    return str(potential_file)
            return None
        except:
            return None
    
    def extract_audio_segment(self, video_file: str, start_time: float, end_time: float) -> Optional[str]:
        try:
            video_name = Path(video_file).stem
            output_name = f"{video_name}_{start_time:.1f}-{end_time:.1f}.wav"
            output_path = self.output_dir / output_name
            
            start_str = f"{int(start_time//3600):02d}:{int((start_time%3600)//60):02d}:{start_time%60:06.3f}"
            end_str = f"{int(end_time//3600):02d}:{int((end_time%3600)//60):02d}:{end_time%60:06.3f}"
            
            ffmpeg_cmd = [
                'ffmpeg', '-i', video_file, '-ss', start_str, '-to', end_str,
                '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', '-y', str(output_path)
            ]
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            
            return str(output_path) if output_path.exists() else None
        except:
            return None
    
    def find_meme_segments(self, video_file: str, search_text: str) -> List[str]:
        temp_audio = "temp_full_audio.wav"
        
        try:
            ffmpeg_cmd = [
                'ffmpeg', '-i', video_file, '-vn', '-acodec', 'pcm_s16le', 
                '-ar', '44100', '-ac', '2', '-y', temp_audio
            ]
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            
            result = self.model.transcribe(temp_audio, language="ko")
            
            matching_segments = []
            search_text_lower = search_text.lower().replace(" ", "")
            
            for segment in result.get('segments', []):
                segment_text_clean = segment['text'].lower().replace(" ", "")
                if search_text_lower in segment_text_clean:
                    extended_start = max(0, segment['start'] - 1.0)
                    extended_end = segment['end'] + 1.0
                    
                    audio_file = self.extract_audio_segment(video_file, extended_start, extended_end)
                    if audio_file:
                        matching_segments.append(audio_file)
            
            if not matching_segments:
                segments = result.get('segments', [])
                for i in range(len(segments)):
                    for j in range(i + 1, min(i + 4, len(segments) + 1)):
                        combined_text = "".join([seg['text'].lower().replace(" ", "") for seg in segments[i:j]])
                        if search_text_lower in combined_text:
                            extended_start = max(0, segments[i]['start'] - 1.0)
                            extended_end = segments[j-1]['end'] + 1.0
                            
                            audio_file = self.extract_audio_segment(video_file, extended_start, extended_end)
                            if audio_file:
                                matching_segments.append(audio_file)
                            break
                    if matching_segments:
                        break
            
            return matching_segments
        except:
            return []
        finally:
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
    
    def analyze_voice_simple(self, audio_file: str) -> Dict:
        y, sr = librosa.load(audio_file)
        
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = []
        
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if not pitch_values:
            pitch_values = [200.0]
        
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        rms = librosa.feature.rms(y=y, hop_length=512)[0]
        onsets = librosa.onset.onset_detect(y=y, sr=sr)
        
        duration = len(y) / sr
        speech_rate = len(onsets) / duration if duration > 0 else 0
        
        pitch_start = np.mean(pitch_values[:len(pitch_values)//3]) if len(pitch_values) >= 3 else pitch_values[0]
        pitch_end = np.mean(pitch_values[-len(pitch_values)//3:]) if len(pitch_values) >= 3 else pitch_values[-1]
        
        intonation = "falling" if pitch_end < pitch_start - 30 else "rising" if pitch_end > pitch_start + 30 else "flat"
        
        return {
            "pitch_mean": float(np.mean(pitch_values)),
            "pitch_std": float(np.std(pitch_values)),
            "pitch_min": float(np.min(pitch_values)),
            "pitch_max": float(np.max(pitch_values)),
            "tempo": float(tempo),
            "speech_rate": float(speech_rate),
            "energy_mean": float(np.mean(rms)),
            "energy_std": float(np.std(rms)),
            "duration": float(duration),
            "intonation_pattern": intonation
        }
    
    def convert_to_tts_parameters(self, analysis: Dict, text: str) -> Dict:
        # ElevenLabs Style 계산 (0.0 ~ 1.0)
        # 피치 변화가 클수록, 에너지 변화가 클수록 높은 style
        pitch_variation = analysis['pitch_std'] / analysis['pitch_mean'] if analysis['pitch_mean'] > 0 else 0
        energy_variation = analysis['energy_std'] / analysis['energy_mean'] if analysis['energy_mean'] > 0 else 0
        
        style = (pitch_variation + energy_variation) / 2
        style = max(0.0, min(1.0, style * 2))  # 0-1 범위로 정규화
        
        # ElevenLabs Stability 계산 (0.0 ~ 1.0)  
        # 말하기 속도가 일정하고, 억양이 평평할수록 높은 stability
        tempo_stability = 1.0 - (analysis['speech_rate'] / 10.0) if analysis['speech_rate'] < 10 else 0.0
        intonation_stability = 0.8 if analysis['intonation_pattern'] == 'flat' else 0.3
        
        stability = (tempo_stability + intonation_stability) / 2
        stability = max(0.0, min(1.0, stability))
        
        # 커스텀 TTS용 상세 파라미터도 포함
        pitch_change = ((analysis['pitch_mean'] - 200) / 200) * 100
        pitch_change = max(-50, min(50, pitch_change))
        
        speed_multiplier = analysis['tempo'] / 100
        speed_multiplier = max(0.5, min(2.0, speed_multiplier))
        
        energy_level = min(analysis['energy_mean'] * 10, 1.0)
        
        words = text.split()
        emphasis_positions = []
        if analysis['energy_std'] > analysis['energy_mean'] * 0.5:
            emphasis_positions = [0, len(words) - 1] if len(words) > 1 else [0]
        
        pause_positions = []
        if len(words) > 2 and analysis['speech_rate'] < 2.0:
            pause_positions = [len(words) // 2]
        
        return {
            "meme_text": text,
            
            # ElevenLabs 파라미터
            "elevenlabs_style": round(style, 3),
            "elevenlabs_stability": round(stability, 3),
            
            # 커스텀 TTS 파라미터  
            "pitch_shift": int(pitch_change),
            "speed_multiplier": round(speed_multiplier, 2),
            "energy_level": round(energy_level, 2),
            "emphasis_positions": ",".join(map(str, emphasis_positions)),
            "pause_after_words": ",".join(map(str, pause_positions)),
            "intonation_type": analysis['intonation_pattern'],
            
            # 메타데이터
            "duration": round(analysis['duration'], 2),
            "confidence": 0.8 if analysis['pitch_std'] > 50 else 0.6
        }
    
    def process_meme_to_tts_params(self, youtube_url: str, meme_text: str) -> Optional[Dict]:
        if not self.check_dependencies():
            return None
        
        video_file = self.download_video(youtube_url)
        if not video_file:
            return None
        
        audio_files = self.find_meme_segments(video_file, meme_text)
        if not audio_files:
            self.cleanup_temp_files()
            return None
        
        analysis = self.analyze_voice_simple(audio_files[0])
        tts_params = self.convert_to_tts_parameters(analysis, meme_text)
        tts_params["youtube_url"] = youtube_url
        
        self.cleanup_temp_files()
        return tts_params
    
    def cleanup_temp_files(self):
        try:
            for file in self.temp_dir.glob("*"):
                file.unlink()
        except:
            pass


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Meme Voice to TTS Parameters')
    parser.add_argument('url', help='YouTube URL')
    parser.add_argument('text', help='Meme text to find')
    parser.add_argument('--model-size', '-m', default='base', 
                       choices=['tiny', 'base', 'small', 'medium', 'large'])
    
    args = parser.parse_args()
    
    processor = MemeVoiceProcessor(args.model_size)
    result = processor.process_meme_to_tts_params(args.url, args.text)
    
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()