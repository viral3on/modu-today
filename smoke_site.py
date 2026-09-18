"""Verify deployed public pages from a network-enabled CI runner; not an AdSense verdict."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import sys
import time

from lotto_store_region_accuracy import is_online, region_of

BASE = 'https://modu.today'
ROOT = Path(__file__).resolve().parent
REPORT = ROOT / 'docs' / 'deployment-smoke.md'
PAGES = {
    '/': ('MODU.TODAY', 'id="reading-guide"', '외부 기사', '최근 거래일 숫자 읽기'),
    '/ads.txt': ('google.com, pub-6122968996738347, DIRECT, f08c47fec0942fa0',),
    '/stock/guide/': ('증시 스캐너: 숫자가 만들어지는 과정',),
    '/stock/': ('KRX', 'SEO_STATIC_START'),
    '/calculator/': ('id="calc-original-guide"',),
    '/lotto/history/': ('최근 100회', 'id="lotto-historical-context"'),
    '/youtube/': ('YouTube',),
    '/apt/': ('실거래',),
    '/games/': ('게임',),
    '/about/': ('MODU.TODAY',),
    '/contact/': ('문의',),
    '/privacy/': ('개인정보처리방침',),
    '/terms/': ('이용',),
    '/sitemap.xml': ('https://modu.today/stock/guide/',),
}


def lotto_stat_checks():
    """Use actual repository records; never hard-code a draw or invented totals."""
    draws = json.loads((ROOT / 'lotto/data/results.json').read_text(encoding='utf-8'))['draws'][:100]
    cache = json.loads((ROOT / 'lotto/data/stores.json').read_text(encoding='utf-8'))
    checks = []
    rows = [(int(row['draw']), cache.get(str(row['draw'])) or []) for row in draws]
    all_stores = [store for _, stores in rows for store in stores]
    online_total = sum(is_online(store) for store in all_stores)
    if online_total:
        checks.append(('/lotto/history/', (f'<b>온라인</b><span>{online_total}건</span>',
                                           '인터넷 구매는 실제 서울 매장이 아닌 온라인으로 분리합니다')))
    for draw, stores in rows:
        online = sum(is_online(store) for store in stores)
        if not online:
            continue
        physical_seoul = sum(region_of(store) == '서울' for store in stores)
        phrases = [f'<span>온라인 {online}건</span>', '인터넷 구매는 온라인으로 분리하며']
        if physical_seoul:
            phrases.append(f'<span>서울 {physical_seoul}건</span>')
        checks.append((f'/lotto/{draw}/', tuple(phrases)))
        break
    return checks


def check(path, phrases, retries=4):
    last = None
    for attempt in range(retries):
        try:
            url = BASE + path
            request = Request(url, headers={'User-Agent': 'MODU-site-quality-smoke/1.0', 'Cache-Control': 'no-cache'})
            with urlopen(request, timeout=18) as result:
                body = result.read().decode('utf-8', errors='replace')
                status = result.status
            missing = [phrase for phrase in phrases if phrase not in body]
            if status == 200 and not missing:
                return f'HTTP {status}, 필수 문구 확인 ({len(body):,}자)', True
            last = f'HTTP {status}; 미발견: {", ".join(missing)}'
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            last = f'{type(e).__name__}: {e}'
        if attempt < retries - 1:
            time.sleep(5)
    return last or 'Unknown error', False


def main():
    try:
        dynamic = lotto_stat_checks()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Lottery stat fixture unavailable: {type(exc).__name__}: {exc}')
        return 1
    results = [(path, *check(path, phrases)) for path, phrases in [*PAGES.items(), *dynamic]]
    good = sum(ok for _, _, ok in results)
    lines = ['# 배포 사이트 접근성 점검', '',
             f'검사 시각(UTC): {datetime.now(timezone.utc).isoformat(timespec="minutes")}',
             '', f'통과: {good}/{len(results)}. 접근성·로또 지역 통계 표기 검사이며 콘텐츠 정책·심사 결과를 대체하지 않습니다.', '',
             '| URL | 결과 | 상태 |', '|---|---|---|']
    for path, detail, ok in results:
        lines.append(f'| `{path}` | {"확인" if ok else "추가 확인 필요"} | {detail.replace("|", "/")} |')
    lines += ['', '동행복권 저장 자료를 기준으로 온라인 당첨을 물리적 지역에서 분리한 표시를 실제 배포 사이트와 대조합니다. 검색엔진 색인 및 AdSense 내부 심사 페이지는 접근할 수 없습니다.', '']
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines))
    return 0 if good == len(results) else 1

if __name__ == '__main__':
    sys.exit(main())
