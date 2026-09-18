"""Fix verified dead links and add genuine guide to calculator hub, idempotently."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
GUIDE = '''<section class="calc-original-guide" id="calc-original-guide" aria-labelledby="calc-guide-title">
<style>.calc-original-guide{max-width:1060px;margin:28px auto;padding:26px;background:#fff;border:1px solid #dbe3ef;border-radius:20px;color:#273445;line-height:1.8}.calc-original-guide h2{margin:0 0 14px;font-size:23px}.calc-original-guide h3{margin:20px 0 6px;font-size:17px}.calc-original-guide p{margin:8px 0;color:#405269}.calc-original-guide a{color:#3154bf;text-decoration:underline}.calc-original-guide .example{padding:15px;background:#f0f5ff;border-radius:12px}</style>
<h2 id="calc-guide-title">계산 결과를 제대로 비교하는 방법</h2>
<p>같은 숫자를 입력해도 기준값과 수수료, 적용 기간이 달라지면 결과가 달라집니다. 여기의 계산기는 값을 입력하면 즉시 참고 결과를 보여 주지만, 실제 계약금액이나 세금·급여 지급액까지 확정하는 도구는 아닙니다. 계산을 시작할 때 아래 세 가지 질문을 먼저 확인해 보세요.</p>
<h3>1. 증가율은 어느 숫자를 기준으로 하나요?</h3>
<p>80에서 100으로 바뀌면 증가율은 (100−80)÷80×100 = 25%입니다. 반대로 100에서 80으로 되돌아가면 감소율은 (80−100)÷100×100 = −20%입니다. 출발점이 달라서 25% 상승 뒤 25% 하락이 원래 값으로 돌아오는 것은 아닙니다. <a href="/calculator/percent.html">퍼센트 계산기</a>에서 기준값을 바꿔 직접 확인할 수 있습니다.</p>
<div class="example"><strong>비교 예시:</strong> 정가 10만원에서 20% 할인한 가격은 8만원입니다. 할인된 8만원을 다시 20% 올려도 9만6천원으로, 정가와 같지 않습니다.</div>
<h3>2. 평균값만 보지 말고 총투입금도 함께 보세요</h3>
<p>주식 100주를 주당 1만원에 보유하다가 50주를 주당 1만6천원에 추가하면, 총 150주에 들어간 매수금액은 180만원입니다. 평균 매입단가는 180만원÷150주 = 1만2천원입니다. <a href="/calculator/average-price.html">평단가 계산기</a>로 값을 재확인하되 수수료를 포함했는지 별도로 살펴야 합니다.</p>
<h3>3. 추정치가 실제 납부액과 다를 수 있는 이유</h3>
<p>대출의 월 상환금은 원리금균등·원금균등·만기일시 방식마다 다르고, 이자 계산과 중도상환 조건에 따라 총 비용도 달라질 수 있습니다. <a href="/calculator/loan.html">대출 계산기</a>는 방식별 금액을 비교하는 용도로 이용하고 최종 계약 금액은 금융기관 상환표로 확인하세요. 세금·급여 계산 역시 개인의 공제 조건과 적용 시점의 공식 기준을 따로 확인해야 합니다.</p>
</section>'''

LINK = re.compile(r'<a\b[^>]*\bhref=["\']/(?:vat|counter|dday)\.html["\'][^>]*>.*?</a>', re.I | re.S)

def repair_html(text, relative):
    # Remove navigation to files verified absent in the site inventory; preserve working calculators.
    text = LINK.sub('', text)
    if relative == 'skhynix-split-analysis.html':
        text = text.replace('href="/stock.html"', 'href="/stock/"').replace('href="/dividend.html"', 'href="/calculator/dividend.html"')
    if relative == 'calculator/index.html' and 'id="calc-original-guide"' not in text:
        anchor = '<section class="calc-trust">'
        if anchor not in text: raise ValueError('Calculator hub changed: guide not injected')
        text = text.replace(anchor, GUIDE + anchor, 1)
    return text

def main():
    count = 0
    for path in (ROOT / 'calculator').glob('*.html'):
        orig = path.read_text(encoding='utf-8')
        new = repair_html(orig, path.relative_to(ROOT).as_posix())
        if orig != new:
            path.write_text(new, encoding='utf-8')
            print('REPAIRED', path.relative_to(ROOT))
            count += 1
    legacy = ROOT / 'skhynix-split-analysis.html'
    if legacy.exists():
        orig = legacy.read_text(encoding='utf-8')
        new = repair_html(orig, legacy.name)
        if orig != new:
            legacy.write_text(new, encoding='utf-8')
            print('REPAIRED', legacy.name)
            count += 1
    print('Modified HTML files:', count)

if __name__ == '__main__': main()
