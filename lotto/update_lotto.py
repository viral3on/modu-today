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


def render_page(r):
    d=r["draw"]; nums=r["numbers"]; bonus=r["bonus"]
    balls=" ".join(f"<b>{n}</b>" for n in nums)
    odd=sum(n%2 for n in nums); total=sum(nums)
    title=f"로또 {d}회 당첨번호 · 당첨금 · 당첨자 수 | MODU.TODAY"
    desc=f"로또 {d}회 당첨번호 {', '.join(map(str,nums))}, 보너스 {bonus}. 추첨일 {r['date']}, 1등 {r['first_winners']}명, 1인당 {r['first_prize']:,}원."
    return f"""<!doctype html><html lang='ko'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{{title}}</title><meta name='description' content='{{desc}}'><meta name='robots' content='index,follow'><link rel='canonical' href='https://modu.today/lotto/{{d}}/'><style>body{{margin:0;background:#0b0e14;color:#eee;font-family:Arial,sans-serif}}a{{color:inherit}}.w{{max-width:820px;margin:auto;padding:24px 16px}}.top{{display:flex;justify-content:space-between}}.box{{background:#141a28;border:1px solid #293247;border-radius:18px;padding:22px;margin-top:18px}}h1{{font-size:28px}}.balls{{display:flex;gap:9px;flex-wrap:wrap;margin:22px 0}}.balls b{{width:46px;height:46px;border-radius:50%;background:#2563eb;display:flex;align-items:center;justify-content:center;font-size:18px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:11px;border-bottom:1px solid #293247;text-align:right}}td:first-child,th:first-child{{text-align:left}}.stats{{display:flex;gap:10px;flex-wrap:wrap}}.stats span{{background:#0d1320;padding:10px 14px;border-radius:10px}}footer{{text-align:center;color:#778197;margin-top:30px;font-size:12px}}</style></head><body><div class='w'><div class='top'><a href='/'><b>MODU.TODAY</b></a><a href='/lotto/'>🍀 로또 홈</a></div><main><section class='box'><div>LOTTO 6/45 · 회차별 당첨결과</div><h1>로또 {{d}}회 당첨번호</h1><div>추첨일 {{r['date']}}</div><div class='balls'>{{balls}} <b>{{bonus}}</b></div><div>보너스 번호: {{bonus}}</div></section><section class='box'><h2>당첨금 및 당첨자</h2><table><tr><th>등수</th><th>당첨자</th><th>1인당 당첨금</th></tr><tr><td>1등</td><td>{{r['first_winners']:,}}명</td><td>{{r['first_prize']:,}}원</td></tr><tr><td>2등</td><td>{{r['second_winners']:,}}명</td><td>{{r['second_prize']:,}}원</td></tr><tr><td>3등</td><td>{{r['third_winners']:,}}명</td><td>{{r['third_prize']:,}}원</td></tr><tr><td>4등</td><td>{{r['fourth_winners']:,}}명</td><td>{{r['fourth_prize']:,}}원</td></tr><tr><td>5등</td><td>{{r['fifth_winners']:,}}명</td><td>{{r['fifth_prize']:,}}원</td></tr></table></section><section class='box'><h2>번호 통계</h2><div class='stats'><span>홀수 {{odd}}개</span><span>짝수 {{6-odd}}개</span><span>번호 합계 {{total}}</span></div></section><p>※ 당첨번호 통계는 해당 회차 결과를 단순 분석한 정보이며 당첨을 예측하거나 보장하지 않습니다.</p></main><footer>© MODU.TODAY · Jae-Hyun Kim.</footer></div><script>window.va=window.va||function(){{(window.vaq=window.vaq||[]).push(arguments);}};</script><script defer src='/_vercel/insights/script.js'></script></body></html>"""

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
