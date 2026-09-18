"""Verify deployed public pages from a network-enabled CI runner; not an AdSense verdict."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import sys
import time

BASE = 'https://modu.today'
ROOT = Path(__file__).resolve().parent
REPORT = ROOT / 'docs' / 'deployment-smoke.md'
PAGES = {
    '/': ('MODU.TODAY', 'id="reading-guide"', '외부 기사'),
    '/ads.txt': ('google.com, pub-6122968996738347, DIRECT, f08c47fec0942fa0',),
    '/stock/guide/': ('증시 스캐너: 숫자가 만들어지는 과정',),
    '/stock/': ('KRX', 'SEO_STATIC_START'),
    '/calculator/': ('id="calc-original-guide"',),
    '/lotto/history/': ('최근 100회',),
    '/youtube/': ('YouTube',),
    '/apt/': ('실거래',),
    '/privacy/': ('개인정보처리방침',),
    '/sitemap.xml': ('https://modu.today/stock/guide/',),
}


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
    results = [(path, *check(path, phrases)) for path, phrases in PAGES.items()]
    good = sum(ok for _, _, ok in results)
    lines = ['# 배포 사이트 접근성 점검', '',
             f'검사 시각(UTC): {datetime.now(timezone.utc).isoformat(timespec="minutes")}',
             '', f'통과: {good}/{len(results)}. 접근성 검사이며 콘텐츠 정책·심사 결과를 대체하지 않습니다.', '',
             '| URL | 결과 | 상태 |', '|---|---|---|']
    for path, detail, ok in results:
        lines.append(f'| `{path}` | {"확인" if ok else "추가 확인 필요"} | {detail.replace("|", "/")} |')
    lines += ['', '검사가 실패해도 실제 사용자 브라우저에서 URL과 HTTP 상태를 다시 확인하세요. 검색엔진 색인 및 AdSense 내부 심사 페이지는 접근할 수 없습니다.', '']
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines))
    return 0 if good == len(results) else 1

if __name__ == '__main__':
    sys.exit(main())
