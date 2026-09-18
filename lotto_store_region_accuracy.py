"""Keep lottery store-region labels faithful to the cached winning-store records.

Run after lotto/update_lotto.py and after SEO rerenders. Internet sales have
no physical Seoul shop; counts refer to winning records, not unique stores.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
STORES = ROOT / "lotto/data/stores.json"
DRAWS = ROOT / "lotto/data/results.json"
HISTORY = ROOT / "lotto/history/index.html"

DETAIL_SECTION = re.compile(
    r'(<h2>📍 (?P<draw>\d+)회 1등 당첨지역</h2>\s*)'
    r'<div class="sub">.*?</div>\s*'
    r'<div class="stats" style="margin-top:14px">.*?</div>\s*'
    r'<div class="sub" style="margin-top:12px">.*?</div>',
    re.S,
)
HISTORY_SECTION = re.compile(
    r'(<h2>📍 최근 100회 1등 당첨지역 통계</h2>\s*)'
    r'<div class="meta">.*?</div>\s*'
    r'<div class="region-stats">(?:<div class="statbox">.*?</div>)*</div>\s*'
    r'<div class="meta" style="margin-top:12px">.*?</div>',
    re.S,
)


def is_online(store: dict) -> bool:
    name = str(store.get("name") or "").lower()
    address = str(store.get("address") or "").lower()
    return "dhlottery.co.kr" in address or "인터넷 복권판매" in name


def region_of(store: dict) -> str:
    if is_online(store):
        return "온라인"
    region = str(store.get("region") or "").strip()
    if region == "전남광주":
        return "전남·광주(원자료 통합)"
    return region or "지역 미분류"


def counts(stores: list[dict]) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    regions = Counter(region_of(s) for s in stores)
    types = Counter(str(s.get("type") or "").strip() or "구분 미상" for s in stores)
    sort = lambda counter: sorted(counter.items(), key=lambda pair: (-pair[1], pair[0]))
    return sort(regions), sort(types)


def detail_html(html: str, draw: int, stores: list[dict]) -> str:
    if not stores:
        return html  # Keep the generator's explicit missing-data notice.
    regions, types = counts(stores)
    region_chips = "".join(f"<span>{escape(region)} {n}건</span>" for region, n in regions)
    type_text = " · ".join(f"{escape(kind)} {n}건" for kind, n in types)
    info = (f"확보한 1등 당첨 기록 {len(stores)}건의 지역 분포입니다. "
            "인터넷 구매는 온라인으로 분리하며, 동일 판매점의 당첨 기록을 각각 1건으로 셉니다.")

    def replace(match: re.Match) -> str:
        if int(match.group("draw")) != draw:
            raise ValueError(f"Unexpected draw heading in {draw} page")
        return (match.group(1) + f'<div class="sub">{info}</div>\n    '
                f'<div class="stats" style="margin-top:14px">{region_chips}</div>\n    '
                f'<div class="sub" style="margin-top:12px">{type_text}</div>')

    updated, n = DETAIL_SECTION.subn(replace, html)
    if n != 1:
        raise ValueError(f"Draw {draw}: expected exactly one store-region section, found {n}")
    return updated


def history_html(html: str, all_stores: list[dict], covered: int) -> str:
    regions, types = counts(all_stores)
    boxes = "".join(
        f'<div class="statbox"><b>{escape(region)}</b><span>{n}건</span></div>'
        for region, n in regions
    ) or '<div class="statbox"><b>지역 통계</b><span>자료 확인 중</span></div>'
    type_text = " · ".join(f"{escape(kind)} {n}건" for kind, n in types)
    info = (f"판매점 자료가 확보된 {covered}개 회차의 1등 당첨 기록 {len(all_stores)}건을 누적했습니다. "
            "동일 판매점이 여러 번 당첨되면 각각 세며, 인터넷 구매는 실제 서울 매장이 아닌 온라인으로 분리합니다. "
            "지역별 기록 수는 당첨 확률을 의미하지 않습니다.")

    def replace(match: re.Match) -> str:
        return (match.group(1) + f'<div class="meta">{info}</div>\n    '
                f'<div class="region-stats">{boxes}</div>\n    '
                f'<div class="meta" style="margin-top:12px">{type_text}</div>')

    updated, n = HISTORY_SECTION.subn(replace, html)
    if n != 1:
        raise ValueError(f"History: expected exactly one store-region section, found {n}")
    return updated


def update(check: bool = False) -> tuple[int, int]:
    cache = json.loads(STORES.read_text(encoding="utf-8"))
    draws = json.loads(DRAWS.read_text(encoding="utf-8")).get("draws", [])[:100]
    if not draws:
        raise ValueError("No verified lotto draw list")
    staged: dict[Path, str] = {}
    all_stores: list[dict] = []
    covered = 0
    for row in draws:
        draw = int(row["draw"])
        stores = cache.get(str(draw)) or []
        if not isinstance(stores, list) or any(not isinstance(s, dict) for s in stores):
            raise ValueError(f"Draw {draw}: malformed cached store records")
        page = ROOT / "lotto" / str(draw) / "index.html"
        if not page.is_file():
            raise ValueError(f"Draw {draw}: missing HTML page")
        before = page.read_text(encoding="utf-8")
        after = detail_html(before, draw, stores)
        if before != after:
            staged[page] = after
        if stores:
            all_stores.extend(stores)
            covered += 1
    old_history = HISTORY.read_text(encoding="utf-8")
    new_history = history_html(old_history, all_stores, covered)
    if old_history != new_history:
        staged[HISTORY] = new_history
    if check and staged:
        raise ValueError("Lottery store-region labeling is stale: " + ", ".join(str(p.relative_to(ROOT)) for p in list(staged)[:5]))
    if not check:
        for page, content in staged.items():
            page.write_text(content, encoding="utf-8")
    return len(draws), len(staged)


def test() -> None:
    stores = [
        {"name": "서울 판매점", "address": "서울 마포구", "region": "서울", "type": "자동"},
        {"name": "인터넷 복권판매사이트", "address": "동행복권(dhlottery.co.kr)", "region": "서울", "type": "수동"},
        {"name": "인터넷 복권판매사이트", "address": "동행복권(dhlottery.co.kr)", "region": "서울", "type": "자동"},
    ]
    fixture = ('<h2>📍 1241회 1등 당첨지역</h2><div class="sub">old</div>'
               '<div class="stats" style="margin-top:14px"><span>서울 3곳</span></div>'
               '<div class="sub" style="margin-top:12px">자동 2곳 · 수동 1곳</div>')
    once = detail_html(fixture, 1241, stores)
    assert "서울 1건" in once and "온라인 2건" in once and "서울 3곳" not in once
    assert once == detail_html(once, 1241, stores)
    assert detail_html(fixture, 1241, []) == fixture
    history = ('<h2>📍 최근 100회 1등 당첨지역 통계</h2>'
               '<div class="meta">old</div><div class="region-stats">'
               '<div class="statbox"><b>서울</b><span>3곳</span></div></div>'
               '<div class="meta" style="margin-top:12px">자동 2곳</div>')
    fixed = history_html(history, stores, 1)
    assert "서울</b><span>1건" in fixed and "온라인</b><span>2건" in fixed
    assert fixed == history_html(fixed, stores, 1)
    assert region_of({"region": "전남광주"}) == "전남·광주(원자료 통합)"
    print("Lottery online/physical classification, count units and idempotence: passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--check", action="store_true")
    options = parser.parse_args()
    if options.test:
        test()
    else:
        pages, changed = update(check=options.check)
        print(f"Lottery store regions: {pages} draws checked, {changed} pages updated")
