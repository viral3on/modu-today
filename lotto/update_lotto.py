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

def ball_color(n):
    if n <= 10:
        return "#f2b720"
    if n <= 20:
        return "#4f8dd8"
    if n <= 30:
        return "#e85c5c"
    if n <= 40:
        return "#7f8c9a"
    return "#42a66c"


def make_draw_page(r):
    draw = r["draw"]
    nums = r["numbers"]
    bonus = r["bonus"]
    odd = sum(1 for n in nums if n % 2)
    even = 6 - odd
    total = sum(nums)

    balls = "".join(
        f'<span class="ball" style="background:{ball_color(n)}">{n}</span>'
        for n in nums
    )
    bonus_ball = f'<span class="ball" style="background:{ball_color(bonus)}">{bonus}</span>'

    desc = (
        f"로또 {draw}회 당첨번호 {', '.join(map(str, nums))}, 보너스 {bonus}. "
        f"추첨일 {r['date']}, 1등 당첨자 {r['first_winners']}명, "
        f"1인당 당첨금 {r['first_prize']:,}원."
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>로또 {draw}회 당첨번호 · 당첨금 | MODU.TODAY</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://modu.today/lotto/{draw}/">
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#0b0e14;color:#eef2f7;font-family:Arial,"Noto Sans KR",sans-serif}}
a{{color:inherit;text-decoration:none}}
.wrap{{max-width:900px;margin:auto;padding:22px 16px 60px}}
.top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}}
.box{{background:#141a28;border:1px solid #283044;border-radius:18px;padding:22px;margin-top:16px}}
h1{{font-size:28px;margin:8px 0}}
.sub{{color:#9aa4b6;font-size:13px}}
.balls{{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin:22px 0}}
.ball{{width:46px;height:46px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:900;color:white}}
.plus{{font-size:22px;color:#8792a5}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:11px;border-bottom:1px solid #293247;text-align:right}}
th:first-child,td:first-child{{text-align:left}}
.stats{{display:flex;gap:10px;flex-wrap:wrap}}
.stats span{{background:#0d1320;padding:10px 14px;border-radius:10px}}
footer{{text-align:center;color:#778197;margin-top:30px;font-size:12px}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <a href="/"><b>MODU.TODAY</b></a>
    <a href="/lotto/">🍀 로또 홈</a>
  </div>

  <section class="box">
    <div class="sub">LOTTO 6/45 · 회차별 당첨결과</div>
    <h1>로또 {draw}회 당첨번호</h1>
    <div class="sub">추첨일 {r['date']}</div>
    <div class="balls">
      {balls}
      <span class="plus">+</span>
      {bonus_ball}
    </div>
    <div class="sub">보너스 번호: {bonus}</div>
  </section>

  <section class="box">
    <h2>🏆 당첨금 및 당첨자</h2>
    <table>
      <tr><th>등수</th><th>당첨자</th><th>1인당 당첨금</th></tr>
      <tr><td>1등</td><td>{r['first_winners']:,}명</td><td>{r['first_prize']:,}원</td></tr>
      <tr><td>2등</td><td>{r['second_winners']:,}명</td><td>{r['second_prize']:,}원</td></tr>
      <tr><td>3등</td><td>{r['third_winners']:,}명</td><td>{r['third_prize']:,}원</td></tr>
      <tr><td>4등</td><td>{r['fourth_winners']:,}명</td><td>{r['fourth_prize']:,}원</td></tr>
      <tr><td>5등</td><td>{r['fifth_winners']:,}명</td><td>{r['fifth_prize']:,}원</td></tr>
    </table>
  </section>

  <section class="box">
    <h2>📊 번호 통계</h2>
    <div class="stats">
      <span>홀수 {odd}개</span>
      <span>짝수 {even}개</span>
      <span>번호 합계 {total}</span>
    </div>
  </section>

  <p class="sub">※ 당첨결과 데이터는 동행복권 정보를 바탕으로 자동 갱신합니다. 번호 통계는 당첨을 예측하거나 보장하지 않습니다.</p>

  <footer>© MODU.TODAY · Jae-Hyun Kim.</footer>
</div>

<script>
window.va = window.va || function () {{
  (window.vaq = window.vaq || []).push(arguments);
}};
</script>
<script defer src="/_vercel/insights/script.js"></script>
</body>
</html>
"""


# 최근 100회 회차별 페이지 자동 생성
generated = 0
for r in normalized[:100]:
    draw_dir = ROOT / str(r["draw"])
    draw_dir.mkdir(parents=True, exist_ok=True)
    (draw_dir / "index.html").write_text(make_draw_page(r), encoding="utf-8")
    generated += 1

print(f"Generated draw pages: {generated}")

