from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

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


STORE_API = "https://www.dhlottery.co.kr/wnprchsplcsrch/selectLtWnShp.do"

def fetch_winning_stores(draw, rank=1):
    """동행복권 회차별 당첨 판매점 조회. 실패해도 본 당첨결과 갱신은 계속 진행."""
    try:
        query = urlencode({
            "srchWnShpRnk": str(rank),
            "srchLtEpsd": str(draw),
        })
        url = f"{STORE_API}?{query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.dhlottery.co.kr/wnprchsplcsrch/home",
        }

        req = Request(url, headers=headers)
        with urlopen(req, timeout=6) as resp:
            raw = resp.read().decode("utf-8")
        payload = json.loads(raw)

        rows = ((payload.get("data") or {}).get("list") or [])
        stores = []
        for x in rows:
            stores.append({
                "name": str(x.get("shpNm") or "").strip(),
                "region": str(x.get("region") or x.get("tm1ShpLctnAddr") or "").strip(),
                "address": str(x.get("shpAddr") or "").strip(),
                "type": str(x.get("atmtPsvYnTxt") or "").strip(),
            })

        print(f"Winning stores: draw={draw}, rank={rank}, rows={len(stores)}")
        return stores

    except Exception as e:
        print(f"[WARN] winning stores fetch failed: draw={draw}, rank={rank}, error={type(e).__name__}: {e}")
        return []

def store_region_summary(stores):
    c = Counter(s["region"] for s in stores if s.get("region"))
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))


def store_type_summary(stores):
    c = Counter(s["type"] for s in stores if s.get("type"))
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))

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

    stores = r.get("first_stores") or []
    region_summary = store_region_summary(stores)
    type_summary = store_type_summary(stores)
    region_chips = "".join(
        f'<span>{region} {count}곳</span>' for region, count in region_summary
    ) or '<span>판매점 지역 정보 확인 중</span>'
    type_text = " · ".join(f"{name} {count}곳" for name, count in type_summary)

    if stores:
        store_rows = "".join(
            f'<tr><td>{i}</td><td>{s["name"]}</td><td>{s["type"] or "-"}</td><td>{s["address"] or s["region"]}</td></tr>'
            for i, s in enumerate(stores, 1)
        )
        store_section = f"""
  <section class="box">
    <h2>📍 {draw}회 1등 당첨지역</h2>
    <div class="sub">1등 당첨 판매점이 어느 지역에서 나왔는지 확인해 보세요.</div>
    <div class="stats" style="margin-top:14px">{region_chips}</div>
    <div class="sub" style="margin-top:12px">{type_text}</div>
    <div style="overflow-x:auto;margin-top:12px">
      <table>
        <tr><th>번호</th><th>판매점</th><th>구분</th><th>소재지</th></tr>
        {store_rows}
      </table>
    </div>
  </section>
"""
    else:
        store_section = f"""
  <section class="box">
    <h2>📍 {draw}회 1등 당첨지역</h2>
    <div class="sub">판매점 정보를 불러오지 못했거나 공개 데이터가 없습니다. 당첨번호와 당첨금 정보는 정상적으로 표시됩니다.</div>
  </section>
"""

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

  {store_section}

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




def make_history_page(rows):
    all_stores = []
    for r in rows:
        all_stores.extend(r.get("first_stores") or [])

    reg = store_region_summary(all_stores)
    typ = store_type_summary(all_stores)
    reg_html = "".join(
        f'<div class="statbox"><b>{region}</b><span>{count}곳</span></div>'
        for region, count in reg
    ) or '<div class="statbox"><b>지역 통계</b><span>데이터 확인 중</span></div>'
    type_html = " · ".join(f"{name} {count}곳" for name, count in typ)

    cards = []
    for r in rows:
        nums = " · ".join(str(n) for n in r["numbers"])
        odd = sum(1 for n in r["numbers"] if n % 2)
        total = sum(r["numbers"])
        cards.append(
            f"""
            <a class="round-card" href="/lotto/{r['draw']}/">
              <div class="round-top">
                <strong>{r['draw']}회</strong>
                <span>{r['date']}</span>
              </div>
              <div class="nums">{nums} <em>+ {r['bonus']}</em></div>
              <div class="meta">홀짝 {odd}:{6-odd} · 합계 {total}</div>
              <div class="more">당첨금·당첨자·상세 통계 보기 →</div>
            </a>
            """
        )

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>로또 최근 100회 당첨번호 · 회차별 결과 | MODU.TODAY</title>
<meta name="description" content="로또 최근 100회 당첨번호를 회차별로 확인하세요. 원하는 회차를 선택하면 당첨번호, 보너스번호, 1~5등 당첨자와 당첨금, 홀짝 비율과 번호 합계를 자세히 볼 수 있습니다.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://modu.today/lotto/history/">
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#0b0e14;color:#eef2f7;font-family:Arial,"Noto Sans KR",sans-serif}}
a{{color:inherit;text-decoration:none}}
.wrap{{max-width:980px;margin:auto;padding:22px 16px 60px}}
.top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px}}
.top a:last-child{{border:1px solid #304158;background:#141a28;padding:9px 12px;border-radius:10px;font-size:13px}}
.hero{{background:linear-gradient(135deg,#14283a,#10231e);border:1px solid #28534a;border-radius:20px;padding:24px;margin-bottom:16px}}
.eyebrow{{font-size:12px;color:#59e5ac;font-weight:900}}
h1{{font-size:30px;margin:8px 0 10px}}
.hero p{{color:#9aa4b6;line-height:1.75;margin:0;max-width:780px}}
.guide{{background:#141a28;border:1px solid #283044;border-radius:16px;padding:16px;color:#aeb8c8;font-size:13px;line-height:1.7;margin-bottom:16px}}
.region-box{{background:#141a28;border:1px solid #283044;border-radius:16px;padding:18px;margin-bottom:16px}}
.region-box h2{{margin:0 0 7px;font-size:19px}}
.region-stats{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-top:13px}}
.statbox{{background:#0c1420;border:1px solid #26364b;border-radius:11px;padding:11px;text-align:center}}
.statbox b{{display:block;font-size:13px}}
.statbox span{{display:block;color:#61e4b0;font-size:12px;margin-top:4px}}

.list{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}
.round-card{{display:block;background:#141a28;border:1px solid #283044;border-radius:16px;padding:17px;transition:.18s}}
.round-card:hover{{border-color:#22c98b;transform:translateY(-1px)}}
.round-top{{display:flex;justify-content:space-between;align-items:center;gap:10px}}
.round-top strong{{font-size:20px;color:#fff}}
.round-top span{{font-size:12px;color:#8793a5}}
.nums{{font-weight:900;margin:14px 0 8px;letter-spacing:.2px}}
.nums em{{font-style:normal;color:#f5c84b}}
.meta{{font-size:12px;color:#93a0b3}}
.more{{margin-top:12px;color:#57e2ad;font-size:12px;font-weight:900}}
footer{{text-align:center;color:#707c8f;font-size:12px;margin-top:30px}}
@media(max-width:650px){{.list{{grid-template-columns:1fr}}h1{{font-size:25px}}.region-stats{{grid-template-columns:repeat(3,1fr)}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <a href="/"><b>MODU.TODAY</b></a>
    <a href="/lotto/">🍀 로또 홈</a>
  </div>

  <section class="hero">
    <div class="eyebrow">LOTTO 6/45 · ARCHIVE</div>
    <h1>최근 100회 로또 당첨결과</h1>
    <p>원하는 회차를 눌러 그때의 당첨번호만 확인하는 데서 끝나지 않고, 1~5등 당첨자 수와 1인당 당첨금, 홀짝 비율, 번호 합계까지 자세히 비교해 보세요.</p>
  </section>

  <div class="guide">
    💡 <b>이런 정보가 궁금할 때 유용합니다.</b><br>
    “지난 회차 1등은 몇 명이었나?”, “1등 당첨금은 얼마였나?”, “보너스 번호는 무엇이었나?”, “홀수·짝수 조합과 번호 합계는 어땠나?”를 회차별 상세 페이지에서 확인할 수 있습니다.
  </div>

  <section class="region-box">
    <h2>📍 최근 100회 1등 당첨지역 통계</h2>
    <div class="meta">회차별 1등 당첨 판매점 소재지를 누적한 통계입니다. 당첨 확률을 의미하지 않습니다.</div>
    <div class="region-stats">{reg_html}</div>
    <div class="meta" style="margin-top:12px">{type_html}</div>
  </section>

  <main class="list">
    {''.join(cards)}
  </main>

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


# 최근 100회 회차별 페이지 자동 생성 + 1등 당첨 판매점 데이터
# 안전 구조:
# 1) 최신 회차 1건을 먼저 조회한다.
# 2) 최신 회차 조회가 성공한 경우에만 미수집 과거 회차를 병렬 조회한다.
# 3) 최신 회차 조회가 실패하면 판매점 수집을 즉시 건너뛰고 기존 로또 페이지 생성은 계속한다.
# 4) 이미 stores.json에 저장된 회차는 다시 조회하지 않는다.

store_cache_path = ROOT / "data" / "stores.json"
try:
    store_cache = json.loads(store_cache_path.read_text(encoding="utf-8")) if store_cache_path.exists() else {}
except Exception:
    store_cache = {}

target_rows = normalized[:100]
latest_key = str(target_rows[0]["draw"])
probe_ok = False

if isinstance(store_cache.get(latest_key), list) and store_cache.get(latest_key):
    probe_ok = True
    print(f"Winning-store probe: latest draw {latest_key} already cached")
else:
    print(f"Winning-store probe: testing latest draw {latest_key} first...")
    probe = fetch_winning_stores(target_rows[0]["draw"], 1)
    if probe:
        store_cache[latest_key] = probe
        probe_ok = True
        print(f"Winning-store probe OK: draw={latest_key}, rows={len(probe)}")
    else:
        print("Winning-store probe FAILED: skipping remaining store requests so lotto update can finish quickly.")

if probe_ok:
    missing = [
        r for r in target_rows
        if not (isinstance(store_cache.get(str(r["draw"])), list) and store_cache.get(str(r["draw"])))
    ]

    if missing:
        print(f"Fetching winning stores in parallel: missing={len(missing)}, workers=8")
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_map = {
                executor.submit(fetch_winning_stores, r["draw"], 1): r["draw"]
                for r in missing
            }
            for future in as_completed(future_map):
                draw = future_map[future]
                try:
                    stores = future.result()
                except Exception as e:
                    print(f"[WARN] parallel store fetch failed: draw={draw}, error={type(e).__name__}: {e}")
                    stores = []
                if stores:
                    store_cache[str(draw)] = stores

store_cache_path.write_text(
    json.dumps(store_cache, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

generated = 0
for r in target_rows:
    key = str(r["draw"])
    r["first_stores"] = store_cache.get(key) or []

    draw_dir = ROOT / key
    draw_dir.mkdir(parents=True, exist_ok=True)
    (draw_dir / "index.html").write_text(make_draw_page(r), encoding="utf-8")
    generated += 1

print(f"Generated draw pages: {generated}, store-cache draws={len(store_cache)}")

# 최근 100회 전체보기 페이지 자동 생성
history_dir = ROOT / "history"
history_dir.mkdir(parents=True, exist_ok=True)
(history_dir / "index.html").write_text(
    make_history_page(normalized[:100]),
    encoding="utf-8",
)
print(f"Generated history page: {history_dir / 'index.html'}")

