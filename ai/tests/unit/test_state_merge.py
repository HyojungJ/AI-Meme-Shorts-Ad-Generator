"""merge_dicts 함수 테스트 (병렬 업데이트 지원 검증)"""
import pytest

from meme_collector.state import merge_dicts


class TestMergeDictsBasic:
    """기본 동작 테스트"""

    def test_empty_left(self):
        """왼쪽이 비어있으면 오른쪽 반환"""
        result = merge_dicts({}, {"a": 1})
        assert result == {"a": 1}

    def test_empty_right(self):
        """오른쪽이 비어있으면 왼쪽 반환"""
        result = merge_dicts({"a": 1}, {})
        assert result == {"a": 1}

    def test_both_empty(self):
        """둘 다 비어있으면 빈 딕셔너리"""
        result = merge_dicts({}, {})
        assert result == {}

    def test_none_left(self):
        """왼쪽이 None이면 오른쪽 반환"""
        result = merge_dicts(None, {"a": 1})
        assert result == {"a": 1}

    def test_none_right(self):
        """오른쪽이 None이면 왼쪽 반환"""
        result = merge_dicts({"a": 1}, None)
        assert result == {"a": 1}


class TestMergeDictsNonOverlapping:
    """겹치지 않는 키 테스트"""

    def test_non_overlapping_keys_preserved(self):
        """겹치지 않는 키는 모두 보존"""
        left = {"a": 1, "b": 2}
        right = {"c": 3, "d": 4}
        result = merge_dicts(left, right)
        assert result == {"a": 1, "b": 2, "c": 3, "d": 4}

    def test_original_not_modified(self):
        """원본 딕셔너리는 수정되지 않음"""
        left = {"a": 1}
        right = {"b": 2}
        merge_dicts(left, right)
        assert left == {"a": 1}
        assert right == {"b": 2}


class TestMergeDictsOverwrite:
    """값 덮어쓰기 테스트"""

    def test_right_overwrites_left(self):
        """같은 키는 오른쪽이 덮어씀"""
        left = {"a": 1}
        right = {"a": 2}
        result = merge_dicts(left, right)
        assert result == {"a": 2}

    def test_different_types_overwrite(self):
        """다른 타입은 덮어씀 (dict가 아닌 경우)"""
        left = {"a": "string"}
        right = {"a": 123}
        result = merge_dicts(left, right)
        assert result == {"a": 123}


class TestMergeDictsNestedDict:
    """중첩 딕셔너리 병합 테스트"""

    def test_nested_dict_merge(self):
        """중첩 딕셔너리는 재귀적으로 병합"""
        left = {"outer": {"a": 1}}
        right = {"outer": {"b": 2}}
        result = merge_dicts(left, right)
        assert result == {"outer": {"a": 1, "b": 2}}

    def test_nested_dict_overwrite(self):
        """중첩 딕셔너리 내에서도 같은 키는 덮어씀"""
        left = {"outer": {"a": 1}}
        right = {"outer": {"a": 2}}
        result = merge_dicts(left, right)
        assert result == {"outer": {"a": 2}}

    def test_deep_nested_merge_3_levels(self):
        """3단계 이상 중첩도 병합"""
        left = {"l1": {"l2": {"l3": {"a": 1}}}}
        right = {"l1": {"l2": {"l3": {"b": 2}}}}
        result = merge_dicts(left, right)
        assert result == {"l1": {"l2": {"l3": {"a": 1, "b": 2}}}}

    def test_deep_nested_merge_4_levels(self):
        """4단계 중첩 병합"""
        left = {"l1": {"l2": {"l3": {"l4": {"a": 1, "b": 2}}}}}
        right = {"l1": {"l2": {"l3": {"l4": {"c": 3}}}}}
        result = merge_dicts(left, right)
        assert result == {"l1": {"l2": {"l3": {"l4": {"a": 1, "b": 2, "c": 3}}}}}

    def test_nested_with_non_overlapping_at_different_levels(self):
        """서로 다른 레벨에서 겹치지 않는 키"""
        left = {"l1": {"a": 1}, "x": 10}
        right = {"l1": {"b": 2}, "y": 20}
        result = merge_dicts(left, right)
        assert result == {"l1": {"a": 1, "b": 2}, "x": 10, "y": 20}


class TestMergeDictsListConcat:
    """리스트 병합(연결) 테스트"""

    def test_list_concatenation(self):
        """같은 키의 리스트는 연결"""
        left = {"items": [1, 2]}
        right = {"items": [3, 4]}
        result = merge_dicts(left, right)
        assert result == {"items": [1, 2, 3, 4]}

    def test_empty_list_left(self):
        """왼쪽 리스트가 비어있어도 연결"""
        left = {"items": []}
        right = {"items": [1, 2]}
        result = merge_dicts(left, right)
        assert result == {"items": [1, 2]}

    def test_empty_list_right(self):
        """오른쪽 리스트가 비어있어도 연결"""
        left = {"items": [1, 2]}
        right = {"items": []}
        result = merge_dicts(left, right)
        assert result == {"items": [1, 2]}

    def test_list_with_dicts(self):
        """딕셔너리 요소가 있는 리스트도 연결"""
        left = {"items": [{"a": 1}]}
        right = {"items": [{"b": 2}]}
        result = merge_dicts(left, right)
        assert result == {"items": [{"a": 1}, {"b": 2}]}

    def test_list_order_preserved(self):
        """리스트 순서 보존 (왼쪽 먼저)"""
        left = {"items": ["first", "second"]}
        right = {"items": ["third", "fourth"]}
        result = merge_dicts(left, right)
        assert result["items"] == ["first", "second", "third", "fourth"]


class TestMergeDictsMixedTypes:
    """혼합 타입 테스트"""

    def test_dict_overwrites_non_dict(self):
        """dict가 아닌 값을 dict로 덮어씀"""
        left = {"a": "string"}
        right = {"a": {"nested": 1}}
        result = merge_dicts(left, right)
        assert result == {"a": {"nested": 1}}

    def test_non_dict_overwrites_dict(self):
        """dict를 dict가 아닌 값으로 덮어씀"""
        left = {"a": {"nested": 1}}
        right = {"a": "string"}
        result = merge_dicts(left, right)
        assert result == {"a": "string"}

    def test_list_overwrites_non_list(self):
        """list가 아닌 값을 list로 덮어씀"""
        left = {"a": "string"}
        right = {"a": [1, 2, 3]}
        result = merge_dicts(left, right)
        assert result == {"a": [1, 2, 3]}


class TestMergeDictsRealWorld:
    """실제 사용 시나리오 테스트 (병렬 Researcher 업데이트)"""

    def test_parallel_researcher_update(self):
        """병렬 Researcher들이 각자 결과를 업데이트하는 시나리오"""
        # 초기 상태
        initial = {"research_notes": {}}

        # TextResearcher 결과
        text_update = {"research_notes": {"text": "정의와 유래 정보"}}
        state = merge_dicts(initial, text_update)

        # MediaResearcher 결과
        media_update = {"research_notes": {"media": "영상 분석 결과"}}
        state = merge_dicts(state, media_update)

        # UsageResearcher 결과
        usage_update = {"research_notes": {"usage": "활용 예시들"}}
        state = merge_dicts(state, usage_update)

        assert state == {
            "research_notes": {
                "text": "정의와 유래 정보",
                "media": "영상 분석 결과",
                "usage": "활용 예시들",
            }
        }

    def test_collected_info_accumulation(self):
        """collected_info에 데이터가 누적되는 시나리오"""
        initial = {"collected_info": {}}

        # 나무위키 결과
        update1 = {"collected_info": {"namuwiki_content": "밈 설명..."}}
        state = merge_dicts(initial, update1)

        # YouTube 결과
        update2 = {"collected_info": {"youtube_videos": [{"video_id": "abc"}]}}
        state = merge_dicts(state, update2)

        # Naver 결과
        update3 = {"collected_info": {"naver_results": [{"content": "블로그 내용"}]}}
        state = merge_dicts(state, update3)

        assert state == {
            "collected_info": {
                "namuwiki_content": "밈 설명...",
                "youtube_videos": [{"video_id": "abc"}],
                "naver_results": [{"content": "블로그 내용"}],
            }
        }

    def test_youtube_videos_list_merge(self):
        """YouTube 영상 목록이 누적되는 시나리오"""
        left = {"collected_info": {"youtube_videos": [{"video_id": "1"}]}}
        right = {"collected_info": {"youtube_videos": [{"video_id": "2"}]}}
        result = merge_dicts(left, right)

        assert len(result["collected_info"]["youtube_videos"]) == 2
        assert result["collected_info"]["youtube_videos"][0]["video_id"] == "1"
        assert result["collected_info"]["youtube_videos"][1]["video_id"] == "2"

    def test_researcher_status_update(self):
        """Researcher 상태가 개별적으로 업데이트되는 시나리오"""
        initial = {"researcher_status": {"text": "pending", "media": "pending", "usage": "pending"}}

        # text만 running으로 변경
        update = {"researcher_status": {"text": "running"}}
        state = merge_dicts(initial, update)

        assert state["researcher_status"]["text"] == "running"
        assert state["researcher_status"]["media"] == "pending"
        assert state["researcher_status"]["usage"] == "pending"
