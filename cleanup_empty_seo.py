from pathlib import Path
import json, re

ROOT = Path(__file__).resolve().parent
START = '<!-- SEO_STATIC_START -->'
END = '<!-- SEO_STATIC_END -->'

trade_file = ROOT / 'apt/data/trades.json'
apt_page = ROOT / 'apt/index.html'

valid = False
try:
    raw = trade_file.read_text(encoding='utf-8').strip()
    data = json.loads(raw) if raw else None
    rows = data.get('trades', []) if isinstance(data, dict) else []
    valid = bool(rows)
except Exception:
    valid = False

if not valid and apt_page.exists():
    text = apt_page.read_text(encoding='utf-8')
    cleaned = re.sub(r'\s*' + re.escape(START) + r'.*?' + re.escape(END) + r'\s*', '\n', text, flags=re.S)
    if cleaned != text:
        apt_page.write_text(cleaned, encoding='utf-8')
        print('REMOVED stale apt SEO snapshot: source trades.json is empty or invalid')
    else:
        print('OK: no stale apt SEO snapshot found')
else:
    print('OK: apartment source data contains trades')
