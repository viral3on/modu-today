"""Provide historical context and a usable draw lookup from verified stored results."""
from pathlib import Path
from collections import Counter
import json
import re

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'lotto/data/results.json'
STORES = ROOT / 'lotto/data/stores.json'
PAGE = ROOT / 'lotto/history/index.html'
START = '<!-- HISTORY_CONTEXT_START -->'
END = '<!-- HISTORY_CONTEXT_END -->'


def render(data, stores=None):
    rows = (data.get('draws') or [])[:100]
    valid = []
    draws = []
    seen_draws = set()
    for row in rows:
        nums = row.get('numbers') or []
        draw = row.get('draw')
        if len(nums) != 6 or any(type(n) is not int or not 1 <= n <= 45 for n in nums) or len(set(nums)) != 6:
            continue
        if type(draw) is not int or draw <= 0 or draw in seen_draws:
            continue
        valid.append(nums)
        draws.append(draw)
        seen_draws.add(draw)
    if len(valid) < 20:
        return ''
    n = len(valid)
    odd = Counter(sum(x % 2 for x in nums) for nums in valid)
    balanced = odd[3]
    avg = sum(map(sum, valid)) / n
    first, last = draws[0], draws[-1]

    store_note = ''
    if isinstance(stores, dict):
        available = [stores[str(draw)] for draw in draws
                     if isinstance(stores.get(str(draw)), list) and stores[str(draw)]]
        covered, entries = len(available), sum(map(len, available))
        if covered == n:
            store_note = (f'<p>위의 당첨지역 통계는 {n}개 회차의 판매점 당첨 기록 {entries}건을 누적했습니다. '
                          '같은 판매점이 여러 회차에 당첨되면 각각 1건으로 집계하므로 고유 판매점 수와 다릅니다.</p>')
        else:
            store_note = (f'<p>위의 당첨지역 통계는 전체 {n}개 회차 중 판매점 목록이 확보된 '
                          f'{covered}개 회차의 당첨 기록 {entries}건만 누적했습니다. '
                          '판매점 자료가 없는 회차는 집계에서 제외되며, 고유 판매점 수와 다릅니다.</p>')

    options = '\n'.join(f'<option value="/lotto/{draw}/">{draw}회</option>' for draw in draws)
    return f'''{START}
<section class="region-box" id="lotto-historical-context" aria-label="과거 추첨 결과를 읽는 방법">
<h2>과거 추첨 숫자를 비교할 때</h2>
<p>동행복권 결과에서 가져온 최근 {n}개 회차({first}회~{last}회)의 당첨번호 6개만 계산했습니다. 보너스 번호는 이 집계에서 제외했습니다. 홀수 3개·짝수 3개인 회차는 {balanced}회였으며, 당첨번호 6개의 합계 평균은 {avg:.1f}입니다.</p>
<p>이 수치는 이미 발표된 결과의 분포를 설명합니다. 특정 홀짝 비율이나 번호 합계가 앞으로 더 자주 나타난다는 뜻이 아니며, 모든 6개 번호 조합의 1등 당첨 확률은 같습니다. 추첨 결과는 <a href="https://www.dhlottery.co.kr/lt645/result" target="_blank" rel="noopener noreferrer" style="color:#79edbf">동행복권 공식 결과</a>를 최종 기준으로 확인하세요.</p>
{store_note}
</section>
<section class="region-box" aria-label="로또 회차 바로 찾기">
<h2>원하는 회차 바로 찾기</h2>
<p class="meta" style="margin:0 0 12px">목록에 있는 회차를 선택하면 당첨번호·당첨금 상세 페이지로 이동합니다. 아래 전체 회차 목록에서도 선택할 수 있습니다.</p>
<form id="lotto-draw-jump" style="display:flex;flex-wrap:wrap;gap:10px;align-items:center">
<label for="lotto-draw-select" style="font-size:13px">회차 선택</label>
<select id="lotto-draw-select" style="min-height:38px;max-width:200px;padding:7px 10px;border-radius:8px;color:#eef2f7;background:#0c1420;border:1px solid #50627a">{options}</select>
<button type="submit" style="min-height:38px;padding:7px 14px;border-radius:8px;background:#146c55;color:white;border:1px solid #2b9072;cursor:pointer">상세 보기</button>
</form>
<noscript><p class="meta">자바스크립트를 사용하지 않는 경우 아래 회차 목록에서 직접 선택해 주세요.</p></noscript>
</section>
<script>
document.getElementById('lotto-draw-jump').addEventListener('submit', function(event) {{
  event.preventDefault();
  var path = document.getElementById('lotto-draw-select').value;
  if (/^\\/lotto\\/\\d+\\/$/.test(path)) window.location.assign(path);
}});
</script>
{END}'''


def clarify_region_summary(html):
    """A repeated winning shop counts once per draw, not once as a unique shop."""
    region = re.compile(r'(<section class="region-box">\s*<h2>📍 최근 100회 1등 당첨지역 통계</h2>)(.*?)(</section>)', re.S)

    def label(match):
        body = match.group(2)
        body = body.replace(
            '회차별 1등 당첨 판매점 소재지를 누적한 통계입니다. 당첨 확률을 의미하지 않습니다.',
            '회차별 1등 당첨 판매점 기록을 누적한 통계입니다. 동일 판매점이 여러 번 당첨되면 각각 집계합니다. 당첨 확률을 의미하지 않습니다.')
        body = re.sub(r'(\d+)곳', r'\1건', body)
        body = body.replace('<b>전남광주</b>', '<b>전남·광주(원자료 통합)</b>')
        return match.group(1) + body + match.group(3)

    return region.sub(label, html, count=1)


def apply(html, section):
    if not section: return html
    html = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\s*', '', html, flags=re.S)
    target = '<main class="list">'
    if target not in html: raise ValueError('Historical listing markup changed')
    return clarify_region_summary(html.replace(target, section + '\n' + target, 1))


def main():
    source = json.loads(DATA.read_text(encoding='utf-8'))
    stores = json.loads(STORES.read_text(encoding='utf-8')) if STORES.is_file() else None
    old = PAGE.read_text(encoding='utf-8')
    new = apply(old, render(source, stores))
    if new != old:
        PAGE.write_text(new, encoding='utf-8')
    print('History analysis, draw lookup, and shop-count labels:', 'updated' if new != old else 'unchanged')

if __name__ == '__main__': main()
