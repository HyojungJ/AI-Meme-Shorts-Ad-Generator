"""Seed 통합 리뷰어 — 여러 JSONL을 병합하여 편집 가능한 HTML 생성

사용법:
    uv run python finetune/scripts/seed_reviewer.py finetune/data/seeds/seeds.jsonl finetune/data/seeds/seeds_sw.jsonl

기능:
- 여러 JSONL 파일을 하나의 HTML로 병합 (출처 태그 표시)
- 대사/action/visual 인라인 편집
- 체크된 항목만 Export (수정 내용 반영)
- 길이 경고, 다중인물 경고 필터
"""

import json
import re
import sys
from html import escape
from pathlib import Path


def strip_emotion_tag(dialogue: str) -> str:
    return re.sub(r'\([^)]+\)\s*', '', dialogue)


MULTI_KEYWORDS = [
    '두 사람', '두 명', '상대방이', '친구가', '동료가', '파트너',
    '옆에서', '함께 대화', '친구와', '친구를', '친구에게', '친구의',
]


def has_multi_person(scene: dict) -> bool:
    text = ' '.join([
        scene.get('dialogue', ''),
        scene.get('action', ''),
        scene.get('visual_description', ''),
    ])
    return any(kw in text for kw in MULTI_KEYWORDS)


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
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(response[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def extract_thinking(response: str) -> str:
    match = re.search(r'<thinking>(.*?)</thinking>', response, re.DOTALL)
    return match.group(1).strip() if match else ""


def build_html(input_paths: list[Path]) -> str:
    items = []
    for path in input_paths:
        source = path.stem
        with open(path) as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                items.append((len(items), source, data))

    # 중복 감지: 밈×회사 조합이 여러 파일에 걸쳐 존재
    combo_seen = {}  # (meme, company) -> first idx
    dup_indices = set()
    for idx, source, data in items:
        meta = data.get("metadata", {})
        combo = (meta.get("meme_name", ""), meta.get("company_name", ""))
        if combo in combo_seen:
            dup_indices.add(idx)
            dup_indices.add(combo_seen[combo])
        else:
            combo_seen[combo] = idx

    cards_html = []
    for idx, source, data in items:
        meta = data.get("metadata", {})
        messages = data.get("messages", [])
        assistant_msg = messages[2]["content"] if len(messages) > 2 else ""

        scenario = extract_scenario(assistant_msg)
        if not scenario:
            continue

        is_dup = idx in dup_indices
        thinking = extract_thinking(assistant_msg)
        meme_name = escape(meta.get("meme_name", "?"))
        company = escape(meta.get("company_name", "?"))
        voice = escape(meta.get("voice_design_prompt", ""))

        # Scene cards (editable)
        scenes_html = ""
        card_has_warn = False
        card_has_multi = False
        for sn in range(1, 5):
            key = f"scene{sn}"
            scene = scenario.get(key, {})
            dialogue = scene.get("dialogue", "")
            action = scene.get("action", "")
            visual = scene.get("visual_description", "")
            clean = strip_emotion_tag(dialogue)
            char_count = len(clean)
            length_ok = 15 <= char_count <= 25
            if not length_ok:
                card_has_warn = True
            multi = has_multi_person(scene)
            if multi:
                card_has_multi = True

            length_class = "length-ok" if length_ok else "length-warn"
            multi_class = " multi-warn" if multi else ""

            scenes_html += f"""
            <div class="scene{multi_class}" data-scene="{key}">
                <div class="scene-header">
                    <span class="scene-label">{key}</span>
                    <span class="scene-type">{escape(scene.get('scene_type', ''))}</span>
                    <span class="{length_class} char-count">{char_count}자</span>
                    {"<span class='multi-tag'>다중인물</span>" if multi else ""}
                </div>
                <div class="field-group">
                    <label>대사</label>
                    <input type="text" class="edit-dialogue" data-field="dialogue" value="{escape(dialogue, quote=True)}" />
                </div>
                <div class="field-group">
                    <label>행동</label>
                    <input type="text" class="edit-action" data-field="action" value="{escape(action, quote=True)}" />
                </div>
                <div class="field-group">
                    <label>비주얼</label>
                    <input type="text" class="edit-visual" data-field="visual_description" value="{escape(visual, quote=True)}" />
                </div>
            </div>"""

        title = escape(scenario.get("title", ""))
        desc = escape(scenario.get("description", ""))
        hashtags = " ".join(f"#{t}" for t in scenario.get("hashtags", []))

        thinking_html = ""
        if thinking:
            thinking_escaped = escape(thinking).replace("\n", "<br>")
            thinking_html = f"""
            <details class="thinking">
                <summary>Thinking</summary>
                <div class="thinking-content">{thinking_escaped}</div>
            </details>"""

        jsonl_escaped = escape(json.dumps(data, ensure_ascii=False))

        warn_attr = ' data-has-warn="1"' if card_has_warn else ''
        multi_attr = ' data-has-multi="1"' if card_has_multi else ''
        dup_attr = ' data-has-dup="1"' if is_dup else ''

        source_color = "#3b82f6" if source == "seeds" else "#f59e0b"
        dup_tag = '<span class="dup-tag">중복</span>' if is_dup else ''

        cards_html.append(f"""
        <div class="card" data-index="{idx}"{warn_attr}{multi_attr}{dup_attr} data-jsonl='{jsonl_escaped}'>
            <div class="card-header">
                <label class="checkbox-label">
                    <input type="checkbox" class="seed-check" data-index="{idx}">
                    <span class="card-title">#{idx+1} {meme_name} × {company}</span>
                </label>
                <div class="header-tags">
                    <span class="source-tag" style="background:{source_color}">{escape(source)}</span>
                    {dup_tag}
                    <span class="voice-tag">{voice}</span>
                </div>
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
<title>Seed Review — {total}개</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; color: #333; padding: 20px; }}

.toolbar {{
    position: sticky; top: 0; z-index: 100; background: #fff; padding: 12px 20px;
    border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px;
    display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
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
    transition: border-color 0.2s, background 0.2s;
}}
.card.selected {{ border-left-color: #10b981; background: #f0fdf4; }}
.card-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 8px; }}
.checkbox-label {{ display: flex; align-items: center; gap: 8px; cursor: pointer; }}
.seed-check {{ width: 18px; height: 18px; cursor: pointer; }}
.card-title {{ font-size: 16px; font-weight: 700; }}
.header-tags {{ display: flex; gap: 6px; align-items: center; }}
.source-tag {{ font-size: 11px; color: #fff; padding: 2px 8px; border-radius: 4px; font-weight: 600; }}
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
.scene.multi-warn {{ border-color: #f97316; background: #fff7ed; }}
.scene-header {{ display: flex; gap: 6px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }}
.scene-label {{ font-weight: 700; color: #374151; }}
.scene-type {{ font-size: 11px; color: #9ca3af; background: #f3f4f6; padding: 1px 6px; border-radius: 3px; }}
.length-ok {{ font-size: 11px; color: #10b981; font-weight: 600; }}
.length-warn {{ font-size: 11px; color: #ef4444; font-weight: 600; }}
.multi-tag {{ font-size: 10px; color: #fff; background: #f97316; padding: 1px 6px; border-radius: 3px; }}
.dup-tag {{ font-size: 10px; color: #fff; background: #8b5cf6; padding: 2px 8px; border-radius: 4px; font-weight: 600; }}
.char-count {{ min-width: 30px; }}

.field-group {{ margin-bottom: 4px; }}
.field-group label {{ font-size: 11px; color: #9ca3af; display: block; margin-bottom: 2px; }}
.field-group input {{
    width: 100%; border: 1px solid #e5e7eb; border-radius: 4px; padding: 4px 6px;
    font-size: 13px; font-family: inherit; color: #333;
    transition: border-color 0.2s;
}}
.field-group input:focus {{ outline: none; border-color: #3b82f6; }}
.field-group input.modified {{ border-color: #f59e0b; background: #fffbeb; }}

.thinking {{ margin-top: 10px; }}
.thinking summary {{ font-size: 13px; color: #6b7280; cursor: pointer; }}
.thinking-content {{ font-size: 12px; color: #555; background: #f9fafb; padding: 10px; border-radius: 4px; margin-top: 6px; line-height: 1.6; }}
</style>
</head>
<body>

<div class="toolbar">
    <button class="btn-export" onclick="exportSeeds()">Export Seeds (JSONL)</button>
    <button class="btn-filter" onclick="toggleFilter('selected')" id="btn-selected">선택된 것만</button>
    <button class="btn-filter" onclick="toggleFilter('warn')" id="btn-warn">길이 경고</button>
    <button class="btn-filter" onclick="toggleFilter('multi')" id="btn-multi">다중인물</button>
    <button class="btn-filter" onclick="toggleFilter('nodup')" id="btn-nodup">중복 제외</button>
    <button class="btn-filter" onclick="toggleFilter('dup')" id="btn-dup">중복만</button>
    <span class="counter">총 {total}개 | 선택: <span id="selected-count">0</span>개</span>
</div>

{''.join(cards_html)}

<script>
const cards = document.querySelectorAll('.card');
const checks = document.querySelectorAll('.seed-check');
const counter = document.getElementById('selected-count');
let filterMode = null;

// Checkbox toggle
checks.forEach(cb => {{
    cb.addEventListener('change', () => {{
        cb.closest('.card').classList.toggle('selected', cb.checked);
        counter.textContent = document.querySelectorAll('.seed-check:checked').length;
    }});
}});

// Live char count + modified highlight on dialogue edit
document.querySelectorAll('.edit-dialogue').forEach(input => {{
    const original = input.value;
    input.addEventListener('input', () => {{
        const clean = input.value.replace(/\\([^)]+\\)\\s*/g, '');
        const countEl = input.closest('.scene').querySelector('.char-count');
        const len = clean.length;
        countEl.textContent = len + '자';
        countEl.className = 'char-count ' + (len >= 15 && len <= 25 ? 'length-ok' : 'length-warn');
        input.classList.toggle('modified', input.value !== original);
    }});
}});

// Modified highlight for action/visual
document.querySelectorAll('.edit-action, .edit-visual').forEach(input => {{
    const original = input.value;
    input.addEventListener('input', () => {{
        input.classList.toggle('modified', input.value !== original);
    }});
}});

// Filter
function toggleFilter(mode) {{
    if (filterMode === mode) {{
        filterMode = null;
        cards.forEach(c => c.style.display = '');
        document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
        return;
    }}
    filterMode = mode;
    document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
    document.getElementById('btn-' + mode).classList.add('active');

    cards.forEach(card => {{
        if (mode === 'selected') card.style.display = card.querySelector('.seed-check').checked ? '' : 'none';
        else if (mode === 'warn') card.style.display = card.dataset.hasWarn ? '' : 'none';
        else if (mode === 'multi') card.style.display = card.dataset.hasMulti ? '' : 'none';
        else if (mode === 'nodup') card.style.display = card.dataset.hasDup ? 'none' : '';
        else if (mode === 'dup') card.style.display = card.dataset.hasDup ? '' : 'none';
    }});
}}

// Export with edits applied
function exportSeeds() {{
    const selected = [];
    checks.forEach(cb => {{
        if (!cb.checked) return;
        const card = cb.closest('.card');
        const data = JSON.parse(card.dataset.jsonl);

        // Apply edits to scenario JSON in assistant message
        const assistantMsg = data.messages[2].content;

        // Extract and parse scenario JSON
        let scenarioMatch = assistantMsg.match(/```json\\s*([\\s\\S]*?)\\s*```/);
        let scenario;
        if (scenarioMatch) {{
            scenario = JSON.parse(scenarioMatch[1]);
        }} else {{
            // Brace matching fallback
            const start = assistantMsg.indexOf('{{');
            let depth = 0, end = start;
            for (let i = start; i < assistantMsg.length; i++) {{
                if (assistantMsg[i] === '{{') depth++;
                else if (assistantMsg[i] === '}}') {{ depth--; if (depth === 0) {{ end = i; break; }} }}
            }}
            scenario = JSON.parse(assistantMsg.substring(start, end + 1));
        }}

        // Apply field edits
        card.querySelectorAll('.scene').forEach(sceneEl => {{
            const key = sceneEl.dataset.scene;
            if (!scenario[key]) return;
            scenario[key].dialogue = sceneEl.querySelector('.edit-dialogue').value;
            scenario[key].action = sceneEl.querySelector('.edit-action').value;
            scenario[key].visual_description = sceneEl.querySelector('.edit-visual').value;
        }});

        // Rebuild assistant message with updated JSON
        const newJson = JSON.stringify(scenario, null, 2);
        let newAssistant;
        if (scenarioMatch) {{
            newAssistant = assistantMsg.replace(/```json\\s*[\\s\\S]*?\\s*```/, '```json\\n' + newJson + '\\n```');
        }} else {{
            const start = assistantMsg.indexOf('{{');
            let depth = 0, end = start;
            for (let i = start; i < assistantMsg.length; i++) {{
                if (assistantMsg[i] === '{{') depth++;
                else if (assistantMsg[i] === '}}') {{ depth--; if (depth === 0) {{ end = i; break; }} }}
            }}
            newAssistant = assistantMsg.substring(0, start) + newJson + assistantMsg.substring(end + 1);
        }}

        data.messages[2].content = newAssistant;
        selected.push(JSON.stringify(data));
    }});

    if (selected.length === 0) {{ alert('선택된 항목이 없습니다.'); return; }}

    const blob = new Blob([selected.join('\\n') + '\\n'], {{ type: 'text/plain' }});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'seeds_final.jsonl';
    a.click();
    URL.revokeObjectURL(a.href);
    alert(selected.length + '개 저장 완료 (seeds_final.jsonl)');
}}
</script>
</body>
</html>"""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python finetune/scripts/seed_reviewer.py <file1.jsonl> [file2.jsonl ...]")
        sys.exit(1)

    paths = [Path(p) for p in sys.argv[1:]]
    for p in paths:
        if not p.exists():
            print(f"File not found: {p}")
            sys.exit(1)

    output_path = paths[0].parent / "seed_review.html"
    html = build_html(paths)
    output_path.write_text(html, encoding="utf-8")
    print(f"Generated: {output_path}")
    print(f"Files merged: {[p.name for p in paths]}")
    print(f"Open in browser: open {output_path}")
