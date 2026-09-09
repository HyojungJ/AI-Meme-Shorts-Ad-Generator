# Ad 13 End-to-End 생성 테스트 (DB 연동 포함)

- 작업 기간: 2026.01.27
- 작업자: 김진
- 관련 이슈 / PR: #58

---

## 0) 입력 조건
- ad_id: 13
- 제품 이미지: `data/images/premium_airpod.jpg`
- ComfyUI: 로컬 `http://127.0.0.1:8188` (실모드)
- 스크립트/DB 연동: script_id=19, company_id=11, character_id=8

DB 조회 결과
- ad_requests: `(13, company_id=11, character_id=8, item_name='프리미엄 무선 이어폰', item_category='전자제품', item_keymessage='완벽한 음질, 완벽한 자유')`
- scenario_scripts: `(19, '프리미엄 무선 이어폰 - 밈 시나리오', '완벽한 음질을 강조하는 재미있는 밈 영상')`
- company_characters: `('밝은 토끼', '밝고 활기찬', '귀여운 3D 스타일', elevenlabs_voice_id=None)`

---

## 1) 캐릭터 이미지 생성
명령
```powershell
python scripts\image_generate_test.py `
    --mode character `
    --character-prompt "밝고 활기찬, 귀여운 3D 스타일의 토끼 캐릭터, 선명한 조명, 심플한 배경" `
    --script-id 19 --character-id 8
```

결과
- status: ok
- character image path: character_1769489688.png
- DB: image_generations에 저장됨
    - image_id=3, script_id=19, character_id=8, image_url=로컬 경로

---

## 2) 씬 이미지 생성
명령
```powershell
python scripts\image_generate_test.py 
    --mode scene 
    --scenario-prompt "프리미엄 무선 이어폰을 공원에서 소개하는 장면, 밝은 낮 햇살, 선명한 색감, 제품 강조" `
    --product-image-path "data\images\premium_airpod.jpg" `
    --character-image-path "data\images\character_1769489688.png" `
    --script-id 19 --scene-key intro --character-id 8
```

결과
- status: ok
- scene image path: nanobanana_1769489708.png
- DB: scene_assets 업데이트됨
    - asset_id=16, script_id=19, scene_key='intro'
    ㄴ- character_image_url/storage_path=로컬 경로

---

## 3) 보이스 생성 + 음성 합성 (ElevenLabs)
명령
```powershell
python scripts\voice_generate_test.py `
    --text "안녕하세요! 프리미엄 무선 이어폰의 완벽한 음질과 자유로운 착용감을 소개합니다. 바쁜 일상에서도 선명한 사운드와 안정적인 연결로 집중력을 높여 보세요. 오늘 이 순간, 최고의 사운드를 경험해보세요." `
    --voice-description "A bright, energetic Korean voice with a friendly and cheerful tone." `
    --voice-name "BrightRabbit" --script-id 19 --character-id 8 --scene-key intro
```

결과
- status: ok
- audio_url/storage_path: 2026-01-27T045559.625224+0000_90eabe08d27f.mp3
- size_bytes: 251656
- DB: voice_generations 저장됨
    - voice_gen_id=7, script_id=19, character_id=8, scene_key='intro', audio_url=로컬 경로

---

## 4) 비디오 생성 + 병합 (ComfyUI 실모드)
준비: scenes.jsonl 생성
```powershell
{"prompt":"프리미엄 무선 이어폰을 공원에서 소개하는 장면, 밝은 낮 햇살, 선명한 색감, 제품 강조","audio_path":"data/voice/test-user/27Z6ZkCv41Qlh8i4ZrpY/2026-01-27T045559.625224+0000_90eabe08d27f.mp3","reference_image_path":"data/images/nanobanana_1769489708.png","duration_seconds":5.0,"output_path":"data/video/ad13_scene_01.mp4","scene_key":"intro","voice_gen_id":7,"image_id":3}
```

실행
```powershell
python scripts\video_graph_from_scenes.py 
    --scenes data\scenes\ad13_scenes.jsonl `
    --script-id 19 --company-id 11 --ad-id 13 `
    --title "프리미엄 무선 이어폰 - 밈 시나리오" `
    --description "완벽한 음질을 강조하는 재미있는 밈 영상" `
    --merged-output-path data\video\ad13_merged.mp4
```

결과
- merged_output_path: ad13_merged.mp4

DB 확인
- scene_videos
- ad13_scene_01.mp4', 5.0, 1666255, 2026-01-27 05:04:46+00:00
- scene_assets
- (16, 19, 'intro', audio_url=로컬 경로, character_image_url=로컬 경로, scene_video_url=로컬 경로, 2026-01-27 05:04:46+00:00)
- videos
    - ad13_merged.mp4', 'completed', 19, 2026-01-27 05:04:46+00:00

---

## 5) 이슈 및 해결

ComfyUI /upload/audio 미지원으로 오류 발생 → ComfyUI/input/에 오디오 파일 직접 복사 후 재시도 → 성공

```powershell
VHS_LoadAudioUpload: Invalid file path .../input/<audio>.mp3
```

---

## 6) 최종 결과

- s이미지/음성/영상 생성 및 DB 적재 전부 정상 확인
- sscene_assets / scene_videos / voice_generations / image_generations / videos 모두 연동 성공