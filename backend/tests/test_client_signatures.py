"""
AI 파이프라인 클라이언트 시그니처 일관성 테스트

Mock / Direct / HTTP 3개 클라이언트가 동일한 메서드 시그니처를 갖는지 검증.
GPU나 DB 없이 실행 가능.
"""
import inspect
import pytest


def _get_async_methods(cls):
    """클래스의 public async 메서드 이름 → 파라미터 목록 매핑"""
    methods = {}
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        if inspect.iscoroutinefunction(method):
            sig = inspect.signature(method)
            # self 제외
            params = {
                k: {
                    "default": v.default if v.default is not inspect.Parameter.empty else "__REQUIRED__",
                    "annotation": v.annotation,
                }
                for k, v in sig.parameters.items()
                if k != "self"
            }
            methods[name] = params
    return methods


@pytest.fixture(scope="module")
def client_classes():
    from app.services.ai_pipeline_mock import AIPipelineMockClient
    from app.services.ai_pipeline_client import AIPipelineClient
    from app.services.ai_pipeline_direct import AIPipelineDirectClient

    return {
        "mock": AIPipelineMockClient,
        "http": AIPipelineClient,
        "direct": AIPipelineDirectClient,
    }


class TestMethodExistence:
    """3개 클라이언트에 동일 메서드가 존재하는지 검증"""

    REQUIRED_METHODS = [
        "generate_character_image",
        "generate_voice",
        "generate_scenario",
        "generate_scene_image",
        "generate_video",
        "regenerate_video",
        "regenerate_character_image",
        "revise_scenario",
        "revise_video",
    ]

    @pytest.mark.parametrize("method_name", REQUIRED_METHODS)
    def test_mock_has_method(self, client_classes, method_name):
        assert hasattr(client_classes["mock"], method_name), (
            f"AIPipelineMockClient is missing method: {method_name}"
        )

    @pytest.mark.parametrize("method_name", REQUIRED_METHODS)
    def test_http_has_method(self, client_classes, method_name):
        assert hasattr(client_classes["http"], method_name), (
            f"AIPipelineClient is missing method: {method_name}"
        )

    @pytest.mark.parametrize("method_name", REQUIRED_METHODS)
    def test_direct_has_method(self, client_classes, method_name):
        assert hasattr(client_classes["direct"], method_name), (
            f"AIPipelineDirectClient is missing method: {method_name}"
        )


class TestSignatureConsistency:
    """3개 클라이언트의 메서드 파라미터가 동일한지 검증"""

    def test_all_methods_have_same_params(self, client_classes):
        """모든 공통 메서드의 파라미터 이름이 일치하는지 확인"""
        mock_methods = _get_async_methods(client_classes["mock"])
        http_methods = _get_async_methods(client_classes["http"])
        direct_methods = _get_async_methods(client_classes["direct"])

        common_methods = set(mock_methods) & set(http_methods) & set(direct_methods)
        assert common_methods, "No common methods found across 3 clients"

        mismatches = []
        for method_name in sorted(common_methods):
            mock_params = set(mock_methods[method_name].keys())
            http_params = set(http_methods[method_name].keys())
            direct_params = set(direct_methods[method_name].keys())

            if not (mock_params == http_params == direct_params):
                mismatches.append(
                    f"{method_name}: mock={sorted(mock_params)}, "
                    f"http={sorted(http_params)}, direct={sorted(direct_params)}"
                )

        assert not mismatches, (
            f"Parameter name mismatches:\n" + "\n".join(mismatches)
        )

    def test_regenerate_character_image_signature(self, client_classes):
        """regenerate_character_image 시그니처 세부 검증"""
        expected_params = [
            "character_id", "original_image_url", "revision_notes",
            "character_prompt", "company_id", "aspect_ratio",
        ]
        for name, cls in client_classes.items():
            sig = inspect.signature(cls.regenerate_character_image)
            param_names = [k for k in sig.parameters if k != "self"]
            assert param_names == expected_params, (
                f"{name} client regenerate_character_image params: "
                f"expected {expected_params}, got {param_names}"
            )

    def test_revise_video_signature(self, client_classes):
        """revise_video 시그니처 세부 검증"""
        expected_params = ["video_id", "scene_revisions", "company_id"]
        for name, cls in client_classes.items():
            sig = inspect.signature(cls.revise_video)
            param_names = [k for k in sig.parameters if k != "self"]
            assert param_names == expected_params, (
                f"{name} client revise_video params: "
                f"expected {expected_params}, got {param_names}"
            )


class TestAsyncMethods:
    """모든 public 메서드가 async인지 검증"""

    def test_all_public_methods_are_async(self, client_classes):
        non_async = []
        for client_name, cls in client_classes.items():
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                if name.startswith("_"):
                    continue
                if not inspect.iscoroutinefunction(method):
                    non_async.append(f"{client_name}.{name}")

        assert not non_async, (
            f"Non-async public methods found: {non_async}"
        )
