import pytest

from meme_collector.state import MemeState, get_initial_state


class TestMemeState:
    def test_get_initial_state(self):
        state = get_initial_state("무야호")

        assert state["meme_name"] == "무야호"
        assert state["messages"] == []
        assert state["attempt"] == 0
        assert state["verification_decision"] == ""

    def test_initial_state_defaults(self):
        state = get_initial_state("테스트밈")

        assert state["collected_info"] == {}
        assert state["analysis"] == {}
        assert state["reflections"] == []
        assert state["verification_score"] == 0.0
        assert state["meme_output"] == {}

    def test_state_is_dict(self):
        state = get_initial_state("test")
        assert isinstance(state, dict)

    def test_different_meme_names(self):
        state1 = get_initial_state("무야호")
        state2 = get_initial_state("랫댄스")

        assert state1["meme_name"] != state2["meme_name"]
        assert state1["meme_name"] == "무야호"
        assert state2["meme_name"] == "랫댄스"
