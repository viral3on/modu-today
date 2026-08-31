#!/usr/bin/env python3
import os, json, time, urllib.parse, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
REGIONS = json.loads((DATA / "regions.json").read_text(encoding="utf-8"))
KEY = os.environ.get("MOLIT_API_KEY", "").strip()
if not KEY:
    raise SystemExit("MOLIT_API_KEY secret is missing")

# 국토교통부 아파트 매매 실거래가 공식 operation URL.
# 기존 MOLIT_APT_ENDPOINT Secret은 더 이상 사용하지 않음.
ENDPOINT = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
ROWS_PER_PAGE = 1000

now = datetime.now()
y, m = now.year, now.month
MONTHS = []
for _ in range(3):
    MONTHS.append(f"{y:04d}{m:02d}")
    m -= 1
    if m == 0:
        y -= 1
        m = 12

REGION_BY_CODE = {r["code"]: r for r in REGIONS}

def text(item, *names):
    for name in names:
        v = item.findtext(name)
        if v is not None and v.strip():
            return v.strip()
    return ""

def encoded_key():
    # 공공데이터포털 Encoding 키는 %2F, %2B 등이 이미 포함될 수 있다.
    # 이미 인코딩된 키는 재인코딩하지 않고, Decoding 키는 안전하게 URL 인코딩한다.
    return KEY if "%" in KEY else urllib.parse.quote(KEY, safe="")

def make_url(code, ym, page):
    q = urllib.parse.urlencode({
        "LAWD_CD": code,
        "DEAL_YMD": ym,
        "pageNo": page,
        "numOfRows": ROWS_PER_PAGE,
    })
    return f"{ENDPOINT}?serviceKey={encoded_key()}&{q}"

def request_xml(code, ym, page):
    url = make_url(code, ym, page)
    req = urllib.request.Request(url, headers={"User-Agent": "MODU.TODAY apt collector/3.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        # 키/전체 URL은 로그에 절대 출력하지 않는다.
        body = e.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"HTTP {e.code}: {body}") from None

    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        raise RuntimeError("API returned non-XML response") from None

    result_code = (root.findtext(".//resultCode") or "").strip()
    result_msg = (root.findtext(".//resultMsg") or "").strip()
    if result_code not in ("", "000", "00", "0"):
        raise RuntimeError(f"API {result_code}: {result_msg}")

    total = int((root.findtext(".//totalCount") or "0").strip() or 0)
    return root, total

def parse_items(root, code):
    reg = REGION_BY_CODE[code]
    out = []
    for i in root.findall(".//item"):
        price_raw = text(i, "dealAmount", "거래금액").replace(",", "").replace(" ", "")
        try:
            price = int(price_raw)
        except:
            price = 0

        yy, mm, dd = text(i, "dealYear", "년"), text(i, "dealMonth", "월"), text(i, "dealDay", "일")
        try:
            date = f"{int(yy):04d}-{int(mm):02d}-{int(dd):02d}"
        except:
            date = ""

        out.append({
            "region_code": code,
            "sido": reg["sido"],
            "sigungu": reg["sigungu"],
            "region": reg["name"],
            "apt": text(i, "aptNm", "아파트"),
            "dong": text(i, "umdNm", "법정동"),
            "jibun": text(i, "jibun", "지번"),
            "area": text(i, "excluUseAr", "전용면적"),
            "floor": text(i, "floor", "층"),
            "date": date,
            "price_manwon": price,
            "build_year": text(i, "buildYear", "건축년도"),
            "deal_type": text(i, "dealingGbn", "거래유형"),
        })
    return out

def fetch_one(code, ym):
    last = None
    for attempt in range(3):
        try:
            root, total = request_xml(code, ym, 1)
            rows = parse_items(root, code)
            pages = max(1, (total + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
            for page in range(2, pages + 1):
                r, _ = request_xml(code, ym, page)
                rows.extend(parse_items(r, code))
                time.sleep(0.08)
            return rows
        except Exception as e:
            last = e
            if attempt < 2:
                time.sleep(1.2 * (attempt + 1))
    raise last

jobs = [(r["code"], ym) for r in REGIONS for ym in MONTHS]
rows, errors = [], []
success_calls = 0

print(f"Fetching nationwide apartment trades: regions={len(REGIONS)}, months={len(MONTHS)}, calls={len(jobs)}")
print(f"Endpoint: {ENDPOINT}")
print(f"Rows per page: {ROWS_PER_PAGE}")

# 과도한 초당 호출을 피하기 위해 4 workers
with ThreadPoolExecutor(max_workers=4) as ex:
    futures = {ex.submit(fetch_one, c, ym): (c, ym) for c, ym in jobs}
    for f in as_completed(futures):
        c, ym = futures[f]
        try:
            got = f.result()
            rows.extend(got)
            success_calls += 1
            print("OK", REGION_BY_CODE[c]["name"], ym, len(got))
        except Exception as e:
            errors.append((c, ym, str(e)))
            print("WARN", REGION_BY_CODE[c]["name"], ym, e)

# 전부 실패했다면 빈 파일을 저장하지 않고 Action 자체를 실패 처리
if success_calls == 0:
    raise SystemExit("FATAL: all API calls failed. Existing JSON files were preserved.")

# 성공률이 비정상적으로 낮아도 기존 데이터 보호 + Action 실패
if success_calls < max(10, len(jobs) // 4):
    raise SystemExit(f"FATAL: only {success_calls}/{len(jobs)} API calls succeeded. Existing JSON files were preserved.")

trade_file = DATA / "trades.json"
try:
    old = json.loads(trade_file.read_text(encoding="utf-8")).get("trades", [])
except:
    old = []

# 실패한 지역/월은 이전 정상 데이터 유지
failed_pairs = {(c, ym) for c, ym, _ in errors}
for x in old:
    ym = (x.get("date") or "")[:7].replace("-", "")
    if (x.get("region_code"), ym) in failed_pairs and ym in MONTHS:
        rows.append(x)

seen, clean = set(), []
for x in rows:
    k = (x.get("region_code"), x.get("apt"), x.get("dong"), x.get("area"),
         x.get("floor"), x.get("date"), x.get("price_manwon"))
    if k not in seen:
        seen.add(k)
        clean.append(x)

clean.sort(key=lambda x: (x.get("date", ""), x.get("price_manwon", 0)), reverse=True)
stamp = datetime.now().astimezone().isoformat(timespec="minutes")

trade_file.write_text(json.dumps({
    "updated_at": stamp,
    "months": MONTHS,
    "trades": clean
}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

# 자동완성 단지목록 누적
apt_file = DATA / "apartments.json"
try:
    old_apts = json.loads(apt_file.read_text(encoding="utf-8")).get("apartments", [])
except:
    old_apts = []

aptmap = {}
for a in old_apts:
    k = (a.get("region_code"), a.get("apt"), a.get("dong"))
    if all(k):
        aptmap[k] = a

for x in clean:
    if not x.get("apt"):
        continue
    k = (x.get("region_code"), x.get("apt"), x.get("dong"))
    aptmap[k] = {
        "region_code": x.get("region_code"),
        "sido": x.get("sido"),
        "sigungu": x.get("sigungu"),
        "region": x.get("region"),
        "dong": x.get("dong"),
        "apt": x.get("apt"),
    }

apts = sorted(aptmap.values(), key=lambda x: (
    x.get("sido", ""), x.get("sigungu", ""), x.get("dong", ""), x.get("apt", "")
))
apt_file.write_text(json.dumps({
    "updated_at": stamp,
    "apartments": apts
}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

print(f"SAVED trades={len(clean)}, apartments={len(apts)}, success_calls={success_calls}, failed_calls={len(errors)}")
