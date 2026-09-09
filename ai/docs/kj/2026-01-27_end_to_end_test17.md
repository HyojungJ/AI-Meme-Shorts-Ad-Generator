# Ad 17 End-to-End 생성 테스트 (DB 연동 포함)

- 작업 기간: 2026.01.27
- 작업자: 김진
- 관련 이슈 / PR: #58

---

## 0) 입력 조건
- ad_id: 17
- 제품 이미지: `data/images/yoga_mat.jpg`
- ComfyUI: 로컬 `http://127.0.0.1:8188` (실모드)
- DB 연동: ad_requests의 ad_id=17 → company_id=11, character_id=9
- scenario_scripts: script_id=37 ("완벽한 요가 매트")

DB 조회 결과
- ad_requests: `(17, 11, 9, '프리미엄 요가 매트', '스포츠용품', '완벽한 그립감, 완벽한 균형')`
- scenario_scripts: `(37, '완벽한 요가 매트', '프리미엄 요가 매트로 완벽한 균형을 경험하세요.')`
- company_characters: `('차분한 곰', '차분하고 신뢰감 있는', '사실적인 3D 스타일')`



### 1) 캐릭터 이미지 생성 (DB 프롬프트)
```powershell
uv run python -m scripts.image_generate_test --mode character --script-id 37 --character-id 9 --scene-number 1 --output-dir data/images
```
- status: ok
- character image path: data\images\character_1769499428.png
- DB: image_generations image_id=4 (script_id=37, character_id=9)

### 2) 씬 이미지 생성 (DB 프롬프트 + DB 상품 이미지 URL)
```powershell
uv run python -m scripts.image_generate_test --mode scene --script-id 37 --character-id 9 --scene-number 1 --product-image-url "https://example.com/products/yoga_mat.jpg" --character-image-path "data/images/character_1769499428.png" --output-dir data/images
```
- status: failed
- error: 404 Client Error (DB ad_requests.item_images URL이 예시 주소라 실패)
- scene image path: None

### 3) 음성 생성 (DB 텍스트 + DB 캐릭터 정보 기반 voice_description/design_text)
```powershell
uv run python -m scripts.voice_generate_test --script-id 37 --character-id 9 --scene-number 1 --voice-description "차분한 곰, 차분하고 신뢰감 있는, 사실적인 3D 스타일, 중저음 남성 목소리" --voice-name "차분한 곰" --design-text "밝은 조명 아래, 주인공이 요가 매트를 펼치며 카메라를 향해 미소 짓는다. 배경에는 자연광이 비치는 창문이 보인다. 요가 매트를 펼치며 당당하게 포즈를 취하고 자신감 있는 분위기. 대사: 이제 귀엽지 않아, 완벽해!"
```
- status: failed
- error: ElevenLabs voice_limit_reached (custom voices 30/30)
- audio_url/storage_path: None

### 4) 비디오 생성/병합 (DB scene_assets 사용)
DB에서 사용한 입력:
- scenario_scripts.scene1.visual_description → 프롬프트
- scene_assets (script_id=37, scene_key=intro) → reference_image_path/audio_path

scenes 파일 생성:
```json
{"prompt":"","reference_image_path":"data\\images\\nanobanana_1769495542.png","audio_path":"data\\voice\\test-user\\fDndpSwipIzv6sqek7qT\\2026-01-27T063355.363010+0000_2f3691a05712.mp3","duration_seconds":4.0,"output_path":"data/video/ad17_scene_01_from_db.mp4"}
```

실행:
```powershell
uv run python -m scripts.video_graph_from_scenes --scenes data/scenes/scenes_script37_db.jsonl --script-id 37 --company-id 11 --ad-id 17 --title "완벽한 요가 매트" --description "프리미엄 요가 매트로 완벽한 균형을 경험하세요." --merged-output-path data/video/ad17_merged_from_db.mp4
```
- status: ok
- merged_output_path: data\video\ad17_merged_from_db.mp4
