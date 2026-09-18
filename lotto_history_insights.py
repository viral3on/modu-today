"""Provide verifiable historical context from actual draw results; never lottery predictions."""
from pathlib import Path
from collections import Counter
import json
import re

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'lotto/data/results.json'
PAGE = ROOT / 'lotto/history/index.html'
START = '<!-- HISTORY_CONTEXT_START -->'
END = '<!-- HISTORY_CONTEXT_END -->'


def render(data):
    rows = (data.get('draws') or [])[:100]
    valid = []
    for row in rows:
        nums = row.get('numbers') or []
        if len(nums) != 6 or any(type(n) is not int or not 1 <= n <= 45 for n in nums) or len(set(nums)) != 6:
            continue
        valid.append(nums)
    if len(valid) < 20:
        return ''
    n = len(valid)
    odd = Counter(sum(x % 2 for x in nums) for nums in valid)
    balanced = odd[3]
    avg = sum(map(sum, valid)) / n
    first = rows[0].get('draw')
    last = rows[-1].get('draw')
    return f'''{START}
<section class="region-box" id="lotto-historical-context" aria-label="과거 추첨 결과를 읽는 방법">
<h2>과거 추첨 숫자를 비교할 때</h2>
<p>동행복권 결과에서 가져온 최근 {n}개 회차({first}회~{last}회)의 당첨번호 6개만 계산했습니다. 보너스 번호는 이 집계에서 제외했습니다. 홀수 3개·짝수 3개인 회차는 {balanced}회였으며, 당첨번호 6개의 합계 평균은 {avg:.1f}입니다.</p>
<p>이 수치는 이미 발표된 결과의 분포를 설명합니다. 특정 홀짝 비율이나 번호 합계가 앞으로 더 자주 나타난다는 뜻이 아니며, 모든 6개 번호 조합의 1등 당첨 확률은 같습니다. 추첨 결과는 <a href="https://www.dhlottery.co.kr/lt645/result" target="_blank" rel="noopener noreferrer" style="color:#79edbf">동행복권 공식 결과</a>를 최종 기준으로 확인하세요.</p>
</section>
{END}'''


def apply(html, section):
    if not section: return html
    html = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\s*', '', html, flags=re.S)
    target = '<main class="list">'
    if target not in html: raise ValueError('Historical listing markup changed')
    return html.replace(target, section + '\n' + target, 1)


def main():
    source = json.loads(DATA.read_text(encoding='utf-8'))
    old = PAGE.read_text(encoding='utf-8')
    new = apply(old, render(source))
    if new != old:
        PAGE.write_text(new, encoding='utf-8')
    print('History analysis:', 'updated' if new != old else 'unchanged or insufficient data')

if __name__ == '__main__': main()
