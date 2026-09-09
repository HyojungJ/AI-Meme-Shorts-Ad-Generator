"""Context Builder: research_notes 또는 collected_info에서 컨텍스트 생성"""
from meme_collector.state import MemeState


class ContextBuilder:
    """Analyzer에 전달할 컨텍스트를 빌드하는 클래스"""

    def build(self, state: MemeState) -> str:
        """research_notes 또는 collected_info에서 컨텍스트 생성"""
        research_notes = state.get("research_notes", {})
        collected_info = state.get("collected_info", {})

        # Deep Research 패턴: research_notes 기반
        if research_notes:
            return self._build_from_research_notes(research_notes, collected_info)

        # 레거시 호환: collected_info 기반
        return self._build_from_collected_info(collected_info)

    def _build_from_research_notes(self, research_notes: dict, collected_info: dict) -> str:
        """research_notes 기반 컨텍스트 생성 (Deep Research 패턴)"""
        parts = []

        # Text Research (정의, 유래, 키프레이즈)
        if research_notes.get("text"):
            parts.append(f"=== 텍스트 분석 ===\n{research_notes['text']}")

        # Media Research (영상 분석)
        if research_notes.get("media"):
            parts.append(f"=== 영상 분석 ===\n{research_notes['media']}")

        # Usage Research (활용 예시)
        if research_notes.get("usage"):
            parts.append(f"=== 활용 예시 ===\n{research_notes['usage']}")

        # 구조화 데이터 (collected_info에서 추출)
        structured_parts = self._extract_structured_data(collected_info)
        if structured_parts:
            parts.append(f"=== 구조화된 데이터 ===\n{structured_parts}")

        if not parts:
            return "수집된 정보 없음"

        return "\n\n".join(parts)

    def _build_from_collected_info(self, collected_info: dict) -> str:
        """collected_info 기반 컨텍스트 생성 (레거시 호환)"""
        parts = []

        if collected_info.get("namuwiki_content"):
            parts.append(f"[나무위키]\n{collected_info['namuwiki_content'][:3000]}")

        if collected_info.get("naver_results"):
            naver_text = "\n".join([r.get("content", "")[:800] for r in collected_info["naver_results"][:3]])
            if naver_text.strip():
                parts.append(f"[네이버]\n{naver_text}")

        if collected_info.get("youtube_videos"):
            yt_text = "\n".join([
                f"- {v.get('title', '')} (views: {v.get('view_count', 0):,})"
                for v in collected_info["youtube_videos"][:5]
            ])
            parts.append(f"[YouTube]\n{yt_text}")

        if collected_info.get("video_analysis"):
            va = collected_info["video_analysis"]
            if not va.get("error"):
                video_text = f"""[Video Analysis - Gemini Vision]
Motion Analysis:
{va.get('motion_analysis', 'N/A')}

Duration: {va.get('duration', 'N/A')} seconds
Frames Analyzed: {va.get('frame_count', 'N/A')}
Source: {va.get('source_url', 'N/A')}"""
                parts.append(video_text)

        if collected_info.get("usage_examples"):
            examples_text = "[Usage Examples]\n"
            for ex in collected_info["usage_examples"]:
                examples_text += f"- 상황: {ex.get('context', '')}\n  사용: {ex.get('usage', '')}\n  톤: {ex.get('tone', 'playful')}\n"
            parts.append(examples_text)

        if collected_info.get("summary"):
            parts.append(f"[Collector Summary]\n{collected_info['summary']}")

        return "\n\n".join(parts) if parts else "수집된 정보 없음"

    def _extract_structured_data(self, collected_info: dict) -> str:
        """collected_info에서 구조화된 핵심 데이터 추출"""
        lines = []

        text_data = collected_info.get("_text_researcher", {})
        if text_data:
            if text_data.get("key_phrase"):
                lines.append(f"[핵심 대사] {text_data['key_phrase']}")
            if text_data.get("creator"):
                lines.append(f"[인물] {text_data['creator']}")
            if text_data.get("risk_info"):
                lines.append(f"[주의사항] {text_data['risk_info']}")

        video_analysis = collected_info.get("video_analysis", {})
        if video_analysis and not video_analysis.get("error"):
            if video_analysis.get("motion_analysis"):
                lines.append(f"[영상 동작 분석] {video_analysis['motion_analysis']}")

        return "\n".join(lines)
