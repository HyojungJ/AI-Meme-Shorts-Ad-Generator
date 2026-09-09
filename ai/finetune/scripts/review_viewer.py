"""Phase 2 Step 2 리뷰어 — 생성된 시나리오를 HTML로 변환하여 브라우저에서 검토

사용법:
    uv run python finetune/scripts/review_viewer.py finetune/data/raw/phase2_step1_200.jsonl

브라우저에서 열고:
- 각 시나리오를 카드로 확인
- 좋은 것에 체크 표시
- "Export Seeds" 버튼으로 선별된 항목을 seeds.jsonl로 다운로드
"""

import json
import re
import sys
from html import escape
from pathlib import Path


def strip_emotion_tag(dialogue: str) -> str:
    return re.sub(r'\([^)]+\)\s*', '', dialogue)


def extract_scenario(response: str) -> dict | None:
    code_block = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass

    start = response.find('{')
    if start == -1:
        return None
    depth = 0
    for i, c in enumerate(response[start:], start):
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(response[start:i+1])
                except json.JSONDecodeError:
                    return None
    return None


def extract_thinking(response: str) -> str:
    match = re.search(r'<thinking>(.*?)</thinking>', response, re.DOTALL)
    return match.group(1).strip() if match else ""


def build_html(input_path: Path) -> str:
    items = []
    with open(input_path, encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            items.append((i, data))

    cards_html = []
    for idx, data in items:
        meta = data.get("metadata", {})
        messages = data.get("messages", [])
        assistant_msg = messages[2]["content"] if len(messages) > 2 else ""

        scenario = extract_scenario(assistant_msg)
        if not scenario:
            continue

        thinking = extract_thinking(assistant_msg)
        meme_name = escape(meta.get("meme_name", "?"))
        company = escape(meta.get("company_name", "?"))
        voice = escape(meta.get("voice_design_prompt", ""))

        # Scene cards
        scenes_html = ""
        for sn in range(1, 5):
            key = f"scene{sn}"
            scene = scenario.get(key, {})
            dialogue = scene.get("dialogue", "")
            clean = strip_emotion_tag(dialogue)
            char_count = len(clean)
            length_class = "length-ok" if 15 <= char_count <= 25 else "length-warn"

            scenes_html += f"""
            <div class="scene">
                <div class="scene-header">
                    <span class="scene-label">{key}</span>
                    <span class="scene-type">{escape(scene.get('scene_type', ''))}</span>
                    <span class="{length_class}">{char_count}자</span>
                </div>
                <div class="dialogue">{escape(dialogue)}</div>
                <div class="action">{escape(scene.get('action', ''))}</div>
                <div class="visual">{escape(scene.get('visual_description', ''))}</div>
            </div>"""

        title = escape(scenario.get("title", ""))
        desc = escape(scenario.get("description", ""))
        hashtags = " ".join(f"#{t}" for t in scenario.get("hashtags", []))

        # Thinking (collapsible)
        thinking_html = ""
        if thinking:
            thinking_escaped = escape(thinking).replace("\n", "<br>")
            thinking_html = f"""
            <details class="thinking">
                <summary>Thinking 펼치기</summary>
                <div class="thinking-content">{thinking_escaped}</div>
            </details>"""

        # Full JSONL for export
        jsonl_escaped = escape(json.dumps(data, ensure_ascii=False))

        cards_html.append(f"""
        <div class="card" data-index="{idx}" data-jsonl='{jsonl_escaped}'>
            <div class="card-header">
                <label class="checkbox-label">
                    <input type="checkbox" class="seed-check" data-index="{idx}">
                    <span class="card-title">#{idx+1} {meme_name} × {company}</span>
                </label>
                <span class="voice-tag">{voice}</span>
            </div>
            <div class="meta-row">
                <span class="title-tag">{title}</span>
                <span class="hashtags">{hashtags}</span>
            </div>
            <div class="desc">{desc}</div>
            <div class="scenes-grid">{scenes_html}</div>
            {thinking_html}
        </div>""")

    total = len(cards_html)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>Scenario Review — {total}개</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; color: #333; padding: 20px; }}

.toolbar {{
    position: sticky; top: 0; z-index: 100; background: #fff; padding: 12px 20px;
    border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px;
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
}}
.toolbar button {{
    padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer;
    font-size: 14px; font-weight: 600;
}}
.btn-export {{ background: #2563eb; color: #fff; }}
.btn-export:hover {{ background: #1d4ed8; }}
.btn-filter {{ background: #e5e7eb; color: #333; }}
.btn-filter.active {{ background: #10b981; color: #fff; }}
.counter {{ font-size: 14px; color: #666; }}

.card {{
    background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08); border-left: 4px solid #e5e7eb;
    transition: border-color 0.2s;
}}
.card.selected {{ border-left-color: #10b981; background: #f0fdf4; }}
.card-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 8px; }}
.checkbox-label {{ display: flex; align-items: center; gap: 8px; cursor: pointer; }}
.seed-check {{ width: 18px; height: 18px; cursor: pointer; }}
.card-title {{ font-size: 16px; font-weight: 700; }}
.voice-tag {{ font-size: 12px; color: #888; background: #f3f4f6; padding: 2px 8px; border-radius: 4px; }}
.meta-row {{ display: flex; gap: 12px; margin-bottom: 6px; align-items: center; flex-wrap: wrap; }}
.title-tag {{ font-weight: 600; color: #2563eb; }}
.hashtags {{ font-size: 13px; color: #6b7280; }}
.desc {{ font-size: 13px; color: #555; margin-bottom: 12px; }}

.scenes-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }}
@media (max-width: 900px) {{ .scenes-grid {{ grid-template-columns: repeat(2, 1fr); }} }}

.scene {{
    background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px;
    font-size: 13px;
}}
.scene-header {{ display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }}
.scene-label {{ font-weight: 700; color: #374151; }}
.scene-type {{ font-size: 11px; color: #9ca3af; background: #f3f4f6; padding: 1px 6px; border-radius: 3px; }}
.length-ok {{ font-size: 11px; color: #10b981; font-weight: 600; }}
.length-warn {{ font-size: 11px; color: #ef4444; font-weight: 600; }}
.dialogue {{ color: #111; font-weight: 500; margin-bottom: 4px; }}
.action {{ color: #6b7280; font-size: 12px; margin-bottom: 2px; }}
.visual {{ color: #9ca3af; font-size: 11px; font-style: italic; }}

.thinking {{ margin-top: 10px; }}
.thinking summary {{ font-size: 13px; color: #6b7280; cursor: pointer; }}
.thinking-content {{ font-size: 12px; color: #555; background: #f9fafb; padding: 10px; border-radius: 4px; margin-top: 6px; line-height: 1.6; }}
</style>
</head>
<body>

<div class="toolbar">
    <button class="btn-export" onclick="exportSeeds()">Export Seeds (JSONL)</button>
    <button class="btn-filter" onclick="toggleFilter('selected')" id="btn-selected">선택된 것만</button>
    <button class="btn-filter" onclick="toggleFilter('warn')" id="btn-warn">길이 경고만</button>
    <span class="counter">총 {total}개 | 선택: <span id="selected-count">0</span>개</span>
</div>

{''.join(cards_html)}

<script>
const cards = document.querySelectorAll('.card');
const checks = document.querySelectorAll('.seed-check');
const counter = document.getElementById('selected-count');
let filterMode = null;

checks.forEach(cb => {{
    cb.addEventListener('change', () => {{
        const card = cb.closest('.card');
        card.classList.toggle('selected', cb.checked);
        counter.textContent = document.querySelectorAll('.seed-check:checked').length;
    }});
}});

function toggleFilter(mode) {{
    if (filterMode === mode) {{
        filterMode = null;
        cards.forEach(c => c.style.display = '');
        document.getElementById('btn-selected').classList.remove('active');
        document.getElementById('btn-warn').classList.remove('active');
        return;
    }}
    filterMode = mode;
    document.getElementById('btn-selected').classList.toggle('active', mode === 'selected');
    document.getElementById('btn-warn').classList.toggle('active', mode === 'warn');

    cards.forEach(card => {{
        if (mode === 'selected') {{
            card.style.display = card.querySelector('.seed-check').checked ? '' : 'none';
        }} else if (mode === 'warn') {{
            card.style.display = card.querySelector('.length-warn') ? '' : 'none';
        }}
    }});
}}

function exportSeeds() {{
    const selected = [];
    checks.forEach(cb => {{
        if (cb.checked) {{
            const card = cb.closest('.card');
            const jsonl = card.getAttribute('data-jsonl');
            selected.push(jsonl);
        }}
    }});
    if (selected.length === 0) {{ alert('선택된 항목이 없습니다.'); return; }}

    const blob = new Blob([selected.join('\\n') + '\\n'], {{ type: 'text/plain' }});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'seeds.jsonl';
    a.click();
    URL.revokeObjectURL(a.href);
}}
</script>
</body>
</html>"""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python finetune/scripts/review_viewer.py <input.jsonl>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"File not found: {input_path}")
        sys.exit(1)

    output_path = input_path.with_suffix(".html")
    html = build_html(input_path)
    output_path.write_text(html, encoding="utf-8")
    print(f"Generated: {output_path}")
    print(f"Open in browser: open {output_path}")
