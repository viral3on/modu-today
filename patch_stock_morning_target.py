from pathlib import Path

p = Path('stock/update_stock.py')
s = p.read_text(encoding='utf-8')
old = '''def monitor_target_date(stamp):
    # 예약 실행은 18:30/21:30 KST에는 당일 장을, 00:30 KST에는 직전 날짜의 장을 확인한다.
    d=stamp.date()
    if stamp.hour < 6:
        d=d-timedelta(days=1)
    return d.strftime("%Y%m%d")
'''
new = '''def previous_weekday(d):
    """직전 평일(월~금)을 반환한다. 월요일이면 직전 금요일."""
    d=d-timedelta(days=1)
    while d.weekday()>=5:
        d=d-timedelta(days=1)
    return d

def monitor_target_date(stamp):
    # 장 종료 후 저녁에는 당일 거래일을 확인한다.
    # 자정 이후~오전 재확인에서는 반드시 직전 평일을 다시 확인한다.
    # 예: 화요일 07:30 -> 월요일, 월요일 07:30 -> 직전 금요일.
    d=stamp.date()
    if stamp.hour < 12:
        d=previous_weekday(d)
    return d.strftime("%Y%m%d")
'''
if old not in s:
    raise SystemExit('target block not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('patched stock/update_stock.py morning target logic')
