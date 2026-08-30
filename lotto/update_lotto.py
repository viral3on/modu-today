from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
import json

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "results.json"

API = "https://www.dhlottery.co.kr/lt645/selectPstLt645Info.do?srchLtEpsd=all"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.dhlottery.co.kr/lt645/result",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

def intv(row, key, default=0):
    try:
        return int(row.get(key) or default)
    except (TypeError, ValueError):
        return default

def date_fmt(v):
    s = str(v or "")
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s

def normalize(row):
    return {
        "draw": intv(row, "ltEpsd"),
        "date": date_fmt(row.get("ltRflYmd")),
        "numbers": [intv(row, f"tm{i}WnNo") for i in range(1, 7)],
        "bonus": intv(row, "bnsWnNo"),
        "first_winners": intv(row, "rnk1WnNope"),
        "first_prize": intv(row, "rnk1WnAmt"),
        "second_winners": intv(row, "rnk2WnNope"),
        "second_prize": intv(row, "rnk2WnAmt"),
        "third_winners": intv(row, "rnk3WnNope"),
        "third_prize": intv(row, "rnk3WnAmt"),
        "fourth_winners": intv(row, "rnk4WnNope"),
        "fourth_prize": intv(row, "rnk4WnAmt"),
        "fifth_winners": intv(row, "rnk5WnNope"),
        "fifth_prize": intv(row, "rnk5WnAmt"),
        "sales": intv(row, "wholEpsdSumNtslAmt") or intv(row, "rlvtEpsdSumNtslAmt"),
    }

req = Request(API, headers=HEADERS)
with urlopen(req, timeout=30) as resp:
    payload = json.loads(resp.read().decode("utf-8"))

rows = payload.get("data", {}).get("list", [])
if not rows:
    raise RuntimeError("동행복권 응답에 추첨 데이터가 없습니다.")

normalized = [normalize(r) for r in rows]
normalized = [r for r in normalized if r["draw"] > 0 and len(r["numbers"]) == 6 and all(1 <= n <= 45 for n in r["numbers"])]
normalized.sort(key=lambda x: x["draw"], reverse=True)

if not normalized:
    raise RuntimeError("정상적인 로또 추첨 데이터를 찾지 못했습니다.")

latest = normalized[0]
draws = [
    {
        "draw": r["draw"],
        "date": r["date"],
        "numbers": r["numbers"],
        "bonus": r["bonus"],
    }
    for r in normalized[:100]
]

kst = timezone(timedelta(hours=9))
out = {
    "source": "동행복권 로또6/45 추첨결과",
    "source_url": "https://www.dhlottery.co.kr/lt645/result",
    "updated_at": datetime.now(kst).isoformat(timespec="seconds"),
    "latest": latest,
    "draws": draws,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Updated lotto results: latest={latest['draw']}회, rows={len(draws)}")
