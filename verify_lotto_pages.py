"""Verify generated historical draw pages match their retained result snapshots."""
from __future__ import annotations
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'lotto/data/results.json'
REPORT = ROOT / 'docs/lotto-page-consistency.md'
BALLS = re.compile(r'<div class="balls">(.*?)</div>', flags=re.S)
NUMBER = re.compile(r'<span class="ball"[^>]*>\s*(\d+)\s*</span>')


def audit(data, root=ROOT):
    issues = []
    draws = data.get('draws') or []
    if len(draws) < 20:
        issues.append('최근 추첨 스냅샷이 20회 미만이어서 검사 범위가 부족합니다.')
    seen = set()
    for result in draws:
        draw = result.get('draw')
        if not isinstance(draw, int) or draw in seen:
            issues.append(f'회차 번호 누락·중복: {draw!r}')
            continue
        seen.add(draw)
        expected = result.get('numbers') or []
        bonus = result.get('bonus')
        if len(expected) != 6 or len(set(expected)) != 6 or any(type(x) is not int or not 1 <= x <= 45 for x in expected) or type(bonus) is not int or not 1 <= bonus <= 45 or bonus in expected:
            issues.append(f'{draw}회: 데이터의 기본 번호·보너스가 유효하지 않습니다.')
            continue
        path = root / f'lotto/{draw}/index.html'
        if not path.exists():
            issues.append(f'{draw}회: 상세 페이지 파일이 없습니다.')
            continue
        text = path.read_text(encoding='utf-8')
        balls = BALLS.search(text)
        actual = [int(x) for x in NUMBER.findall(balls.group(1))] if balls else []
        if actual != expected + [bonus]:
            issues.append(f'{draw}회: 화면의 당첨번호·보너스가 데이터와 다릅니다. 기대 {expected + [bonus]}, 실제 {actual}')
        if f'추첨일 {result.get("date")}' not in text:
            issues.append(f'{draw}회: 화면 추첨일이 데이터와 다릅니다.')
        if f'<h1>로또 {draw}회 당첨번호</h1>' not in text:
            issues.append(f'{draw}회: 회차 제목이 맞지 않습니다.')
    latest = data.get('latest') or {}
    draw = latest.get('draw')
    latest_path = root / f'lotto/{draw}/index.html'
    if latest_path.exists() and latest.get('first_winners') is not None and latest.get('first_prize') is not None:
        text = latest_path.read_text(encoding='utf-8')
        if f'<tr><td>1등</td><td>{int(latest["first_winners"]):,}명</td><td>{int(latest["first_prize"]):,}원</td></tr>' not in text:
            issues.append(f'{draw}회: 1등 당첨자수/당첨금이 최신 결과와 다릅니다.')
    return len(draws), issues


def main():
    data = json.loads(SOURCE.read_text(encoding='utf-8'))
    total, issues = audit(data)
    lines = ['# 로또 회차 상세페이지 데이터 일치 검사', '',
             '저장된 동행복권 결과 스냅샷과 사이트가 생성한 회차별 HTML의 **내부 일치 여부**만 검사합니다. 외부 발표의 진위, 판매점 세부 내용, 콘텐츠 독창성 또는 애드센스 승인 여부를 검증하는 것은 아닙니다.', '',
             f'- 확인 대상: {total}개 회차', f'- 데이터 불일치·누락: {len(issues)}건', '',
             '## 확인 결과', '']
    lines.extend(f'- {msg}' for msg in issues[:100])
    if not issues:
        lines.append('저장된 회차별 번호·보너스·날짜·제목과 최신 1등 당첨금 데이터가 생성된 HTML과 일치합니다.')
    lines += ['', '판매점 주소의 최신 여부, 데이터 출처 제공 조건과 사용자 관점의 페이지별 부가 가치는 별도 확인이 필요합니다.', '']
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines))
    return 0 if not issues else 1

if __name__ == '__main__': sys.exit(main())
