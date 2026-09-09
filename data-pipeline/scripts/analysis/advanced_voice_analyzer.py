import librosa
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import json


class AdvancedVoiceAnalyzer:
    def __init__(self):
        """고급 음성 분석기"""
        pass
    
    def analyze_prosody(self, audio_file: str) -> Dict:
        """운율(억양, 박자) 상세 분석"""
        y, sr = librosa.load(audio_file)
        
        # 1. 피치 윤곽선 (억양 패턴)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_contour = []
        times = []
        
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_contour.append(pitch)
                times.append(librosa.frames_to_time(t, sr=sr))
        
        # 2. 리듬 패턴 분석
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beats, sr=sr)
        
        # 3. 강세 패턴 (에너지 변화)
        rms = librosa.feature.rms(y=y, hop_length=512)[0]
        rms_times = librosa.frames_to_time(range(len(rms)), sr=sr, hop_length=512)
        
        # 4. 말 속도 변화 (음성 구간별)
        intervals = librosa.effects.split(y, top_db=20)
        speech_rates = []
        
        for start, end in intervals:
            duration = (end - start) / sr
            if duration > 0.1:  # 0.1초 이상인 구간만
                speech_rates.append({
                    'start_time': start / sr,
                    'end_time': end / sr,
                    'duration': duration,
                    'rate': len(librosa.onset.onset_detect(y=y[start:end], sr=sr)) / duration
                })
        
        # 5. 억양 패턴 분류
        intonation_pattern = self._classify_intonation(pitch_contour)
        
        return {
            'pitch_contour': {
                'times': [float(t) for t in times],
                'pitches': [float(p) for p in pitch_contour],
                'pattern': intonation_pattern
            },
            'rhythm': {
                'tempo': float(tempo),
                'beat_times': [float(t) for t in beat_times.tolist()],
                'beat_intervals': [float(t) for t in np.diff(beat_times).tolist()]
            },
            'stress_pattern': {
                'times': [float(t) for t in rms_times.tolist()],
                'energy': [float(e) for e in rms.tolist()],
                'peaks': self._find_stress_peaks(rms)
            },
            'speech_rate': speech_rates
        }
    
    def _classify_intonation(self, pitch_contour: List[float]) -> str:
        """억양 패턴 분류"""
        if len(pitch_contour) < 3:
            return "insufficient_data"
        
        # 시작, 중간, 끝 피치 비교
        start_pitch = np.mean(pitch_contour[:len(pitch_contour)//3])
        mid_pitch = np.mean(pitch_contour[len(pitch_contour)//3:2*len(pitch_contour)//3])
        end_pitch = np.mean(pitch_contour[2*len(pitch_contour)//3:])
        
        # 패턴 분류
        if end_pitch > start_pitch + 50:
            return "rising"  # 상승 억양 (의문문)
        elif end_pitch < start_pitch - 50:
            return "falling"  # 하강 억양 (평서문)
        elif mid_pitch > max(start_pitch, end_pitch) + 30:
            return "peak"  # 정점 억양 (강조)
        else:
            return "flat"  # 평평한 억양
    
    def _find_stress_peaks(self, rms: np.ndarray) -> List[int]:
        """강세 위치 찾기"""
        from scipy.signal import find_peaks
        
        # 에너지 피크 찾기
        peaks, _ = find_peaks(rms, height=np.mean(rms) + np.std(rms))
        return peaks.tolist()
    
    def generate_ssml_from_analysis(self, text: str, prosody_data: Dict) -> str:
        """분석 결과를 바탕으로 정교한 SSML 생성"""
        
        # 기본 SSML 구조
        ssml_parts = ['<speak>']
        
        # 한국어 텍스트 감지
        has_korean = any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in text)
        
        if has_korean:
            # 한국어 텍스트는 장음 효과를 위해 x-slow 사용
            rate = "x-slow"
        else:
            # 다른 언어는 템포 기반 설정
            tempo = prosody_data['rhythm']['tempo']
            if tempo > 120:
                rate = "fast"
            elif tempo < 80:
                rate = "slow"
            else:
                rate = "medium"
        
        # 억양 패턴에 따른 피치 설정
        pattern = prosody_data['pitch_contour']['pattern']
        if pattern == "rising":
            pitch_change = "+20%"
        elif pattern == "falling":
            pitch_change = "-10%"
        elif pattern == "peak":
            pitch_change = "+30%"
        else:
            pitch_change = "0%"
        
        # 평균 에너지에 따른 볼륨 설정
        avg_energy = np.mean(prosody_data['stress_pattern']['energy'])
        if avg_energy > 0.05:
            volume = "loud"
        elif avg_energy < 0.02:
            volume = "soft"
        else:
            volume = "medium"
        
        # SSML 생성
        ssml_parts.append(f'<prosody rate="{rate}" pitch="{pitch_change}" volume="{volume}">')
        
        # 텍스트를 단어별로 분할하여 강세 적용
        words = text.split()
        stress_peaks = prosody_data['stress_pattern']['peaks']
        
        for i, word in enumerate(words):
            # 강세 위치에 해당하는 단어는 강조
            if i < len(stress_peaks) and len(stress_peaks) > 0 and stress_peaks[i] > np.mean(stress_peaks):
                ssml_parts.append(f'<emphasis level="strong">{word}</emphasis>')
            else:
                ssml_parts.append(word)
            
            # 단어 사이 간격 (리듬 반영)
            if i < len(words) - 1:
                ssml_parts.append('<break time="0.2s"/>')
        
        ssml_parts.append('</prosody>')
        ssml_parts.append('</speak>')
        
        return ' '.join(ssml_parts)
    
    def create_prosody_visualization(self, prosody_data: Dict, output_path: str):
        """운율 분석 결과 시각화"""
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # 1. 피치 윤곽선
        pitch_data = prosody_data['pitch_contour']
        axes[0].plot(pitch_data['times'], pitch_data['pitches'], 'b-', linewidth=2)
        axes[0].set_title('피치 윤곽선 (억양 패턴)')
        axes[0].set_ylabel('피치 (Hz)')
        axes[0].grid(True)
        
        # 2. 에너지 패턴 (강세)
        stress_data = prosody_data['stress_pattern']
        axes[1].plot(stress_data['times'], stress_data['energy'], 'r-', linewidth=1)
        
        # 강세 피크 표시
        peak_times = [stress_data['times'][i] for i in stress_data['peaks']]
        peak_energies = [stress_data['energy'][i] for i in stress_data['peaks']]
        axes[1].scatter(peak_times, peak_energies, color='red', s=50, zorder=5)
        
        axes[1].set_title('에너지 패턴 (강세 위치)')
        axes[1].set_ylabel('에너지')
        axes[1].grid(True)
        
        # 3. 리듬 패턴
        rhythm_data = prosody_data['rhythm']
        beat_times = rhythm_data['beat_times']
        axes[2].vlines(beat_times, 0, 1, colors='g', linewidth=2)
        axes[2].set_title(f'리듬 패턴 (템포: {rhythm_data["tempo"]:.1f} BPM)')
        axes[2].set_ylabel('박자')
        axes[2].set_xlabel('시간 (초)')
        axes[2].grid(True)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()


def main():
    """고급 음성 분석 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description='고급 음성 운율 분석')
    parser.add_argument('audio_file', help='분석할 음성 파일')
    parser.add_argument('--text', '-t', required=True, help='대상 텍스트')
    parser.add_argument('--output', '-o', help='결과 저장 경로')
    
    args = parser.parse_args()
    
    analyzer = AdvancedVoiceAnalyzer()
    
    print(f"고급 음성 분석 시작: {args.audio_file}")
    
    # 운율 분석
    prosody_data = analyzer.analyze_prosody(args.audio_file)
    
    # SSML 생성
    ssml = analyzer.generate_ssml_from_analysis(args.text, prosody_data)
    
    # 결과 출력
    print("\n=== 운율 분석 결과 ===")
    print(f"억양 패턴: {prosody_data['pitch_contour']['pattern']}")
    print(f"템포: {prosody_data['rhythm']['tempo']:.1f} BPM")
    print(f"강세 위치: {len(prosody_data['stress_pattern']['peaks'])}개")
    
    print(f"\n=== 생성된 SSML ===")
    print(ssml)
    
    # 결과 저장
    if args.output:
        output_dir = Path(args.output).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON 저장
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump({
                'prosody_analysis': prosody_data,
                'generated_ssml': ssml,
                'target_text': args.text
            }, f, ensure_ascii=False, indent=2)
        
        # 시각화 저장
        viz_path = str(args.output).replace('.json', '_visualization.png')
        analyzer.create_prosody_visualization(prosody_data, viz_path)
        
        print(f"\n[SAVE] 결과 저장: {args.output}")
        print(f"[VIZ] 시각화 저장: {viz_path}")


if __name__ == "__main__":
    main()