"""Browser smoke checks for public site UX. Not a Google crawler or AdSense review."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import sys

BASE = 'https://modu.today'
REPORT = Path(__file__).resolve().parent / 'docs/browser-smoke.md'
VIEWPORTS = {'desktop': {'width': 1366, 'height': 900}, 'mobile': {'width': 390, 'height': 844}}


def check_page(page, name, path, action=None):
    page.goto(BASE + path, wait_until='domcontentloaded', timeout=45000)
    if action:
        action(page)
    else:
        page.locator('h1').first.wait_for(state='visible', timeout=18000)
    return f'{path}: visible content' + (' and live interaction' if action else '')


def home(page):
    page.locator('h1').first.wait_for(state='visible', timeout=20000)
    page.locator('#latest-reading').wait_for(state='visible', timeout=15000)
    for selector in ['.essential[href="/apt/"]', '.essential[href="/lotto/"]', '#latest-news']:
        page.locator(selector).wait_for(state='visible')
    assert page.locator('.modu-primary-nav a').all_text_contents() == ['홈', '읽을거리', '아파트 실거래가', '로또', '유용한 도구', '뉴스']
    assert page.locator('#latest-news .news-item').count() <= 4
    assert page.locator('a[href="/admin/"], a[href="/stock/"]').count() == 0


def percentage(page):
    page.locator('#p1a').fill('200')
    page.locator('#p1b').fill('15')
    page.wait_for_function('() => document.querySelector("#p1r")?.textContent.trim() === "30"', timeout=10000)
    page.locator('#p3a').fill('80')
    page.locator('#p3b').fill('100')
    page.wait_for_function('() => document.querySelector("#p3r")?.textContent.trim() === "25%"', timeout=10000)


def stock(page):
    assert '일시 중단' in page.locator('h1').inner_text()
    assert 'noindex' in page.locator('meta[name="robots"]').get_attribute('content')


def apartment(page):
    page.locator('#query').fill('래미안')
    page.locator('#query').press('Enter')
    page.locator('#searchBtn').click()
    page.wait_for_function('() => document.querySelector("#rows").textContent.includes("래미안")')


def lottery(page):
    page.get_by_role('button', name='새 번호 생성', exact=True).click()
    numbers = page.locator('#mainNumbers .ball').all_text_contents()
    assert len(numbers) == 6 and len(set(numbers)) == 6
    assert all(1 <= int(number) <= 45 for number in numbers)
    page.get_by_role('button', name='5게임 한꺼번에', exact=True).click()
    assert page.locator('#fiveSets .ball').count() == 30


def admin(page):
    assert page.locator('#post-form').count() == 0
    assert page.locator('script[src*="insights"]').count() == 0
    assert 'noindex' in page.locator('meta[name="robots"]').get_attribute('content')


def lotto_history(page):
    page.locator('h1').first.wait_for(state='visible', timeout=18000)
    select = page.locator('#lotto-draw-select')
    select.wait_for(state='visible', timeout=10000)
    options = select.locator('option')
    if options.count() != 100:
        raise AssertionError(f'Expected 100 real draw choices; found {options.count()}')
    if select.locator('option[value="/lotto/1240/"]').count() != 1:
        raise AssertionError('Known 1240 draw is not in the history selector')
    select.select_option('/lotto/1240/')
    page.locator('#lotto-draw-jump button[type="submit"]').click()
    page.wait_for_url('**/lotto/1240/', timeout=18000)
    page.locator('h1').first.wait_for(state='visible', timeout=12000)
    if '1240' not in page.locator('h1').first.inner_text():
        raise AssertionError('Draw navigation opened an unexpected detail page')


def test():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        try:
            for name, viewport in VIEWPORTS.items():
                context = browser.new_context(viewport=viewport, device_scale_factor=1, is_mobile=name=='mobile', has_touch=name=='mobile')
                page = context.new_page()
                for path, func in (('/', home), ('/reading/', None), ('/tools/', None), ('/news/', None), ('/calculator/percent.html', percentage), ('/stock/', stock), ('/youtube/', None), ('/apt/', apartment), ('/lotto/', lottery), ('/lotto/history/', lotto_history), ('/admin/', admin)):
                    try:
                        result = check_page(page, name, path, func)
                        results.append((name, path, '확인', result))
                    except Exception as exc:
                        results.append((name, path, '추가 확인 필요', f'{type(exc).__name__}: {str(exc)[:180]}'))
                        try:
                            page.screenshot(path=f'/tmp/modu-{name}-{path.strip("/").replace("/", "-") or "home"}.png', full_page=False, timeout=7000)
                        except Exception:
                            pass
                context.close()
        finally:
            browser.close()
    return results


def main():
    try:
        results = test()
    except Exception as exc:
        results = [('environment', '-', '추가 확인 필요', f'Chromium test setup: {type(exc).__name__}: {exc}')]
    passed = sum(status == '확인' for _, _, status, _ in results)
    lines = ['# 공개 사이트 실제 브라우저 점검', '',
             f'검사 시각 (UTC): {datetime.now(timezone.utc).isoformat(timespec="minutes")}', '',
             f'확인: {passed}/{len(results)}. Chromium을 통한 일부 기능·가독성 검사이며 Google 크롤러나 AdSense 승인 결과를 대체하지 않습니다.', '',
             '| 화면 | 경로 | 결과 | 상세 |', '|---|---|---|---|']
    for viewport, path, status, detail in results:
        lines.append(f'| {viewport} | `{path}` | {status} | {detail.replace("|", "/")} |')
    lines += ['', '검사 항목: PC/모바일 자체 콘텐츠 홈, 아파트·로또 강조, 뉴스 축소, 실제 퍼센트 계산, 아파트 검색, 로또 6개/5게임 생성 및 100회 선택, 스캐너 비공개와 관리자 미인증 화면. 관리자 실발행은 이 공개 브라우저 검사에 포함하지 않습니다.', '']
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines))
    return 0 if passed == len(results) else 1

if __name__ == '__main__': sys.exit(main())
