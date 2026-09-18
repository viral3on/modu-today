"""Add sourced, per-draw comparisons to generated Lotto result pages.

Runs AFTER lotto/update_lotto.py and can be rerun safely after any SEO rebuild.
Only analyzes the six main winning numbers; bonus balls do not enter counts.
"""
from collections import Counter
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "lotto" / "data" / "results.json"
START = "<!-- DRAW_CONTEXT_START -->"
END = "<!-- DRAW_CONTEXT_END -->"
ANCHOR = '  <p class="sub">※ 당첨결과 데이터는'


def valid_rows(data):
    rows = []
    seen = set()
    for row in (data.get("draws") or [])[:100]:
        draw, nums = row.get("draw"), row.get("numbers")
        if (type(draw) is not int or draw <= 0 or draw in seen
                or not isinstance(nums, list) or len(nums) != 6
                or any(type(n) is not int or not 1 <= n <= 45 for n in nums)
                or len(set(nums)) != 6):
            continue
        seen.add(draw)
        rows.append(row)
    return rows


def render(draw, rows):
    """Render one factual comparison; return empty for missing/invalid samples."""
    by_draw = {r["draw"]: r for r in rows}
    current = by_draw.get(draw)
    if current is None or len(rows) < 2:
        return ""
    nums = sorted(current["numbers"])
    freq = Counter(n for r in rows for n in r["numbers"])
    average_sum = sum(sum(r["numbers"]) for r in rows) / len(rows)
    actual_sum = sum(nums)
    delta = actual_sum - average_sum
    comparison = (f"표본 평균 {average_sum:.1f}보다 {abs(delta):.1f} "
                  + ("높습니다" if delta > 0 else "낮습니다" if delta < 0 else "같습니다"))
    prev = by_draw.get(draw - 1)
    nxt = by_draw.get(draw + 1)
    if prev:
        common = sorted(set(nums) & set(prev["numbers"]))
        common_text = ", ".join(map(str, common)) if common else "없음"
        prev_text = (f'<a href="/lotto/{draw-1}/" style="color:#7dd3fc">{draw-1}회</a>와 '
                     f"겹치는 당첨번호는 {len(common)}개({common_text})입니다.")
    else:
        prev_text = "이번 집계에 직전 회차가 없어 번호 중복을 계산하지 않았습니다."
    next_link = (f'<a href="/lotto/{draw+1}/" style="color:#7dd3fc">다음 {draw+1}회 →</a>'
                 if nxt else "")
    previous_link = (f'<a href="/lotto/{draw-1}/" style="color:#7dd3fc">← 이전 {draw-1}회</a>'
                     if prev else "")
    frequency = ", ".join(f"{n}번 {freq[n]}회" for n in nums)
    first = max(by_draw)
    last = min(by_draw)
    return f'''{START}
  <section class="box" id="draw-context">
    <h2>🔎 {draw}회 결과를 앞뒤 회차와 비교</h2>
    <p style="line-height:1.75">이 회차의 당첨번호 6개 합계는 <b>{actual_sum}</b>입니다. 집계에 포함된 최근 {len(rows)}회({last}~{first}회) 당첨번호 합계의 {comparison}. 보너스 번호는 계산에서 제외했습니다.</p>
    <p style="line-height:1.75">{prev_text}</p>
    <p style="line-height:1.75">위 6개 번호가 같은 {len(rows)}개 회차의 <b>본번호</b>에 나온 횟수: {frequency}.</p>
    <p class="sub" style="line-height:1.75">이 숫자는 공개된 과거 추첨 결과를 비교한 기록입니다. 다음 회차의 번호나 당첨 확률을 예측하지 않습니다. 원본은 <a href="https://www.dhlottery.co.kr/lt645/result" target="_blank" rel="noopener noreferrer" style="color:#7dd3fc">동행복권 공식 당첨결과</a>에서 확인하세요.</p>
    <nav aria-label="회차 이동" style="display:flex;gap:18px;flex-wrap:wrap;margin-top:16px">{previous_link} <a href="/lotto/history/" style="color:#7dd3fc">최근 100회 목록</a> {next_link}</nav>
  </section>
{END}'''


def apply(html, section):
    """Replace our own block, preserving every other part of the draw page."""
    if html.count(START) != html.count(END) or html.count(START) > 1:
        raise ValueError("Unexpected context markers; refusing to rewrite")
    if START in html:
        return re.sub(re.escape(START) + r".*?" + re.escape(END), section,
                      html, count=1, flags=re.S)
    if not section:
        return html
    if ANCHOR not in html:
        raise ValueError("Expected draw-page note missing; refusing to rewrite")
    return html.replace(ANCHOR, "  " + section + "\n\n" + ANCHOR, 1)


def main():
    rows = valid_rows(json.loads(DATA.read_text(encoding="utf-8")))
    if len(rows) < 20:
        raise ValueError("Insufficient verified draw history; leaving pages unchanged")
    changed = 0
    for row in rows:
        target = ROOT / "lotto" / str(row["draw"]) / "index.html"
        if not target.is_file():
            continue
        original = target.read_text(encoding="utf-8")
        updated = apply(original, render(row["draw"], rows))
        if updated != original:
            target.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"Per-draw verified comparisons: {changed} updated, {len(rows)} sampled")


if __name__ == "__main__":
    main()
