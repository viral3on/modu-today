"""Replace the homepage generic reading guide with source-grounded market breadth."""
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
HOME = ROOT / 'index.html'
DATA = ROOT / 'stock/data/scanner.json'
START = '<section class="section" id="reading-guide">'
KST = timezone(timedelta(hours=9))


def brief(data):
    try:
        day = date.fromisoformat(data['trade_date'])
        age = (datetime.now(KST).date() - day).days
        m = data['market']
        up, down, flat, total = [int(m[k]) for k in ('up', 'down', 'flat', 'total_stocks')]
        if not (0 <= age <= 10 and total >= 100 and up + down + flat == total):
            return None
    except (KeyError, TypeError, ValueError):
        return None
    pct = lambda n: f'{100*n/total:.1f}%'
    example = ''
    for stock in data.get('signals', {}).get('watch_top', []):
        try:
            name = escape(str(stock['name']))
            volume, avg = int(stock['volume']), int(stock['avg_volume_20d'])
            if avg > 0 and volume > 0 and len(name) < 60:
                example = (f'<p style="margin:0 0 10px;color:#475467">실제 계산 예: {name}의 해당 거래일 거래량은 '
                           f'{volume:,}주, 직전 최대 20거래일 평균은 {avg:,}주입니다. '
                           f'당일 거래량 ÷ 평균은 <strong>{volume/avg:.2f}배</strong>입니다. '
                           '이는 과거 대비 거래 규모를 뜻하며 미래 가격 상승을 예측하는 수치가 아닙니다.</p>')
                break
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
    return f'''<section class="section" id="reading-guide"><div class="wrap"><div class="card" style="padding:24px 28px;line-height:1.8">
<h2 style="margin:0 0 10px;font-size:22px">최근 거래일 숫자 읽기 · {day.isoformat()}</h2>
<p style="margin:0 0 10px;color:#475467">KRX 일별 데이터로 집계한 {total:,}개 종목 가운데 상승 {up:,}개({pct(up)}), 하락 {down:,}개({pct(down)}), 보합 {flat:,}개({pct(flat)})입니다. 이 비율은 집계 종목의 분포로, 지수 등락률이나 이후 시장 방향을 나타내지 않습니다.</p>
{example}
<p style="margin:0 0 10px;color:#475467">거래량 배수, 신고가 판정, 자체 관심도의 계산식은 <a href="/stock/guide/" style="color:#4f46e5;font-weight:800;text-decoration:underline">스캐너 계산법과 예제</a>에서 확인할 수 있습니다. 이 데이터는 실시간 호가가 아니므로 화면에 표시된 거래일을 함께 확인하세요.</p>
<p style="margin:0;color:#475467">아래 뉴스는 외부 언론사의 기사 제목과 원문 링크 목록입니다. 직접 취재하거나 기사 내용을 검증한 자체 보도물이 아닙니다. 주요 사실과 보도 시점은 원문을 확인해 주세요.</p>
</div></div></section>'''


def apply(text, new_section):
    if not new_section or START not in text:
        return text
    pattern = r'<section class="section" id="reading-guide">.*?</section>'
    out, n = re.subn(pattern, lambda _: new_section, text, count=1, flags=re.S)
    if n != 1: raise ValueError('Homepage reading-guide markup changed')
    return out


def main():
    try:
        data = json.loads(DATA.read_text(encoding='utf-8'))
        section = brief(data)
        original = HOME.read_text(encoding='utf-8')
    except (OSError, json.JSONDecodeError) as err:
        print('Market brief skipped; existing homepage preserved:', type(err).__name__)
        return
    result = apply(original, section)
    if original != result:
        HOME.write_text(result, encoding='utf-8')
        print('Added source-grounded market breadth to homepage')
    else:
        print('Market brief unchanged or no validated current data')

if __name__ == '__main__': main()
