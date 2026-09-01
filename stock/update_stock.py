#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MODU.TODAY KRX 공식 OPEN API 증시 스캐너.

필수 GitHub Secret: KRX_API_KEY
필수 활용승인: 유가증권 일별매매정보(stk_bydd_trd), 코스닥 일별매매정보(ksq_bydd_trd)
추가 승인된 API는 자동으로 최대한 수집하고 snapshot.json에 함께 저장한다.
"""
from __future__ import annotations
import json, os, time, math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"; DATA.mkdir(parents=True, exist_ok=True)
OUT = DATA / "scanner.json"
SNAP = DATA / "snapshot.json"
KST = timezone(timedelta(hours=9))
API_BASE = "https://data-dbg.krx.co.kr/svc/apis"
KEY = os.environ.get("KRX_API_KEY", "").strip()
NEEDED_SESSIONS = 21
LOOKBACK_DAYS = 45
TOP_N = 50
CACHE = {}

CORE = {
    "KOSPI": ("sto", "stk_bydd_trd"),
    "KOSDAQ": ("sto", "ksq_bydd_trd"),
}
OPTIONAL = {
    "KONEX": ("sto", "knx_bydd_trd"),
    "KOSPI_BASE": ("sto", "stk_isu_base_info"),
    "KOSDAQ_BASE": ("sto", "ksq_isu_base_info"),
    "KONEX_BASE": ("sto", "knx_isu_base_info"),
    "KRX_INDEX": ("idx", "krx_dd_trd"),
    "KOSPI_INDEX": ("idx", "kospi_dd_trd"),
    "KOSDAQ_INDEX": ("idx", "kosdaq_dd_trd"),
    "BOND_INDEX": ("idx", "bon_dd_trd"),
    "DERIV_INDEX": ("idx", "drvprod_dd_trd"),
    "ETF": ("etp", "etf_bydd_trd"),
    "ETN": ("etp", "etn_bydd_trd"),
    "ELW": ("etp", "elw_bydd_trd"),
    "GOV_BOND": ("bon", "kts_bydd_trd"),
    "BOND": ("bon", "bnd_bydd_trd"),
    "SMALL_BOND": ("bon", "smb_bydd_trd"),
    "FUTURES": ("drv", "fut_bydd_trd"),
    "STOCK_FUT_KOSPI": ("drv", "eqsfu_stk_bydd_trd"),
    "STOCK_FUT_KOSDAQ": ("drv", "eqkfu_ksq_bydd_trd"),
    "OPTIONS": ("drv", "opt_bydd_trd"),
    "STOCK_OPT_KOSPI": ("drv", "eqsop_bydd_trd"),
    "STOCK_OPT_KOSDAQ": ("drv", "eqkop_bydd_trd"),
    "OIL": ("gen", "oil_bydd_trd"),
    "GOLD": ("gen", "gold_bydd_trd"),
    "EMISSIONS": ("gen", "ets_bydd_trd"),
}

def log(*a): print(*a, flush=True)
def n(v, default=0.0):
    try:
        s=str(v).replace(",","").strip()
        return float(s) if s not in ("", "-") else default
    except Exception: return default

def i(v): return int(n(v, 0))
def r2(v): return round(float(v), 2)
def fmt_day(d): return f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d)==8 else d

class AccessError(RuntimeError): pass

def extract_rows(obj):
    if isinstance(obj, dict):
        if isinstance(obj.get("OutBlock_1"), list): return obj["OutBlock_1"]
        for v in obj.values():
            rows=extract_rows(v)
            if rows is not None: return rows
    return None

def call(category, api_id, day, required=False):
    ck=(category,api_id,day)
    if ck in CACHE: return CACHE[ck]
    url=f"{API_BASE}/{category}/{api_id}?{urlencode({'basDd':day})}"
    last=None
    for attempt in range(3):
        try:
            req=Request(url, headers={"AUTH_KEY":KEY,"User-Agent":"MODU.TODAY-KRX/1.0","Accept":"application/json"})
            with urlopen(req, timeout=25) as res:
                raw=res.read().decode("utf-8","replace")
            obj=json.loads(raw)
            rows=extract_rows(obj)
            if rows is None: raise RuntimeError(f"Unexpected JSON keys: {list(obj)[:6] if isinstance(obj,dict) else type(obj)}")
            CACHE[ck]=rows
            return rows
        except HTTPError as e:
            last=e
            if e.code in (401,403):
                msg=f"{api_id}: HTTP {e.code} - 해당 API 활용승인/인증키를 확인하세요."
                if required: raise AccessError(msg)
                log("OPTIONAL SKIP", msg); CACHE[ck]=[]; return []
        except (URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as e:
            last=e
        time.sleep(1.2*(attempt+1))
    if required: raise RuntimeError(f"{api_id} 호출 실패: {type(last).__name__}: {last}")
    log(f"OPTIONAL WARN {api_id}: {type(last).__name__}: {last}")
    CACHE[ck]=[]; return []

def fetch_core(day):
    rows=[]; ok=0; denied=[]
    for market,(cat,api) in CORE.items():
        try:
            part=call(cat,api,day,required=True)
            if part:
                ok+=1
                for x in part:
                    y=dict(x); y["_MARKET"]=market; rows.append(y)
        except AccessError as e:
            denied.append(str(e)); log("CORE ACCESS", e)
    if ok==0 and denied: raise AccessError(" / ".join(denied))
    return rows

def find_sessions():
    today=datetime.now(KST).date(); sessions=[]
    for back in range(LOOKBACK_DAYS):
        day=(today-timedelta(days=back)).strftime("%Y%m%d")
        rows=fetch_core(day)
        if not rows: continue
        sessions.append((day,rows)); log(f"SESSION OK {day}: {len(rows):,} rows")
        if len(sessions)>=NEEDED_SESSIONS: break
    sessions.reverse()
    if len(sessions)<6: raise RuntimeError(f"거래일 데이터가 부족합니다: {len(sessions)}일")
    return sessions

def key_of(x): return str(x.get("ISU_CD") or x.get("ISU_SRT_CD") or x.get("ISU_NM") or "").strip()
def by_key(rows): return {key_of(x):x for x in rows if key_of(x)}

def base_row(x, short_map):
    code=key_of(x); short=short_map.get(code) or short_map.get(str(x.get("ISU_NM",""))) or code
    return {
        "ticker":short, "code":code, "name":str(x.get("ISU_NM") or x.get("ISU_ABBRV") or code),
        "market":x.get("_MARKET") or x.get("MKT_NM", ""), "section":x.get("SECT_TP_NM", ""),
        "close":i(x.get("TDD_CLSPRC")), "change":i(x.get("CMPPREVDD_PRC")), "change_pct":r2(n(x.get("FLUC_RT"))),
        "open":i(x.get("TDD_OPNPRC")), "high":i(x.get("TDD_HGPRC")), "low":i(x.get("TDD_LWPRC")),
        "volume":i(x.get("ACC_TRDVOL")), "trading_value":i(x.get("ACC_TRDVAL")),
        "market_cap":i(x.get("MKTCAP")), "listed_shares":i(x.get("LIST_SHRS")),
    }

def pct(a,b): return (a/b-1)*100 if b else 0.0

def calc_signals(sessions, short_map):
    latest_day, latest_rows=sessions[-1]; latest=by_key(latest_rows)
    hist=[(d,by_key(rows)) for d,rows in sessions]
    result={k:[] for k in ["top_gainers","top_losers","trading_value_top","volume_top","volume_surge","value_surge","up_streak_5d","down_streak_5d","return_5d","return_20d","new_high_20d","new_low_20d","turnover_top","gap_up","intraday_range"]}
    for code,x in latest.items():
        row=base_row(x,short_map)
        if row["close"]<=0: continue
        series=[]
        for d,m in hist:
            z=m.get(code)
            if z: series.append((d,z))
        prev=series[-2][1] if len(series)>=2 else None
        prev_close=n(prev.get("TDD_CLSPRC")) if prev else 0
        prev20=series[-21:-1]
        vols=[n(z.get("ACC_TRDVOL")) for _,z in prev20 if n(z.get("ACC_TRDVOL"))>0]
        vals=[n(z.get("ACC_TRDVAL")) for _,z in prev20 if n(z.get("ACC_TRDVAL"))>0]
        closes=[n(z.get("TDD_CLSPRC")) for _,z in series if n(z.get("TDD_CLSPRC"))>0]
        highs=[n(z.get("TDD_HGPRC")) for _,z in prev20 if n(z.get("TDD_HGPRC"))>0]
        lows=[n(z.get("TDD_LWPRC")) for _,z in prev20 if n(z.get("TDD_LWPRC"))>0]
        avgvol=sum(vols)/len(vols) if vols else 0; avgval=sum(vals)/len(vals) if vals else 0
        rr=dict(row)
        rr["volume_ratio"]=r2(row["volume"]/avgvol) if avgvol else 0; rr["avg_volume_20d"]=int(avgvol)
        rr["value_ratio"]=r2(row["trading_value"]/avgval) if avgval else 0; rr["avg_value_20d"]=int(avgval)
        rr["turnover_pct"]=r2(row["volume"]/row["listed_shares"]*100) if row["listed_shares"] else 0
        rr["gap_pct"]=r2(pct(row["open"],prev_close)) if prev_close else 0
        rr["range_pct"]=r2((row["high"]-row["low"])/prev_close*100) if prev_close else 0
        if len(closes)>=6: rr["return_5d"]=r2(pct(closes[-1],closes[-6]))
        if len(closes)>=21: rr["return_20d"]=r2(pct(closes[-1],closes[-21]))
        result["top_gainers"].append(rr); result["top_losers"].append(rr); result["trading_value_top"].append(rr); result["volume_top"].append(rr)
        result["turnover_top"].append(rr); result["gap_up"].append(rr); result["intraday_range"].append(rr)
        if rr["volume_ratio"]>=3: result["volume_surge"].append(rr)
        if rr["value_ratio"]>=3: result["value_surge"].append(rr)
        if "return_5d" in rr: result["return_5d"].append(rr)
        if "return_20d" in rr: result["return_20d"].append(rr)
        if highs and row["close"]>=max(highs): result["new_high_20d"].append(rr)
        if lows and row["close"]<=min(lows): result["new_low_20d"].append(rr)
        if len(closes)>=6:
            tail=closes[-6:]
            if all(tail[j]<tail[j+1] for j in range(5)): result["up_streak_5d"].append(rr)
            if all(tail[j]>tail[j+1] for j in range(5)): result["down_streak_5d"].append(rr)
    sorters={
        "top_gainers":("change_pct",True),"top_losers":("change_pct",False),"trading_value_top":("trading_value",True),"volume_top":("volume",True),
        "volume_surge":("volume_ratio",True),"value_surge":("value_ratio",True),"up_streak_5d":("return_5d",True),"down_streak_5d":("return_5d",False),
        "return_5d":("return_5d",True),"return_20d":("return_20d",True),"new_high_20d":("change_pct",True),"new_low_20d":("change_pct",False),
        "turnover_top":("turnover_pct",True),"gap_up":("gap_pct",True),"intraday_range":("range_pct",True),
    }
    for k,(field,rev) in sorters.items(): result[k]=sorted(result[k],key=lambda z:z.get(field,0),reverse=rev)[:TOP_N]
    return latest_day,result,latest_rows

def market_summary(latest_rows):
    bymarket={}
    for market in ("KOSPI","KOSDAQ"):
        xs=[x for x in latest_rows if x.get("_MARKET")==market]
        if not xs: continue
        bymarket[market]={"count":len(xs),"up":sum(n(x.get("FLUC_RT"))>0 for x in xs),"down":sum(n(x.get("FLUC_RT"))<0 for x in xs),"flat":sum(n(x.get("FLUC_RT"))==0 for x in xs),"trading_value":sum(i(x.get("ACC_TRDVAL")) for x in xs),"market_cap":sum(i(x.get("MKTCAP")) for x in xs)}
    allx=[x for x in latest_rows if i(x.get("TDD_CLSPRC"))>0]
    return {"markets":bymarket,"total_stocks":len(allx),"up":sum(n(x.get("FLUC_RT"))>0 for x in allx),"down":sum(n(x.get("FLUC_RT"))<0 for x in allx),"flat":sum(n(x.get("FLUC_RT"))==0 for x in allx),"trading_value":sum(i(x.get("ACC_TRDVAL")) for x in allx)}

def fetch_optional(latest_day):
    out={}; status={}
    for label,(cat,api) in OPTIONAL.items():
        rows=call(cat,api,latest_day,required=False)
        status[label]={"api_id":api,"rows":len(rows),"available":bool(rows)}
        if rows: out[label]=rows
    return out,status

def short_code_map(extras):
    m={}
    for label in ("KOSPI_BASE","KOSDAQ_BASE","KONEX_BASE"):
        for x in extras.get(label,[]):
            short=str(x.get("ISU_SRT_CD") or "")
            if not short: continue
            for key in (x.get("ISU_CD"),x.get("ISU_NM"),x.get("ISU_ABBRV")):
                if key: m[str(key)]=short
    return m

def compact_extra(extras):
    # scanner.json에는 화면에 필요한 주요 부가시장만 축약. 전체 최신 원문행은 snapshot.json에 저장.
    out={}
    for label in ("KRX_INDEX","KOSPI_INDEX","KOSDAQ_INDEX","ETF","ETN","GOLD","FUTURES"):
        rows=extras.get(label,[])
        if not rows: continue
        if label in ("ETF","ETN"):
            rows=sorted(rows,key=lambda x:n(x.get("ACC_TRDVAL")),reverse=True)[:30]
        elif label=="FUTURES": rows=sorted(rows,key=lambda x:n(x.get("ACC_TRDVOL")),reverse=True)[:30]
        out[label]=rows[:100]
    return out

def main():
    if not KEY: raise RuntimeError("GitHub Secret KRX_API_KEY가 없습니다.")
    log("KRX OPEN API collector START")
    sessions=find_sessions(); latest_day=sessions[-1][0]
    log("LATEST TRADING DAY", latest_day)
    extras,status=fetch_optional(latest_day)
    smap=short_code_map(extras)
    latest_day,signals,latest_rows=calc_signals(sessions,smap)
    ms=market_summary(latest_rows)
    stamp=datetime.now(KST)
    payload={
        "source":"KRX OPEN API","trade_date":fmt_day(latest_day),"trade_date_raw":latest_day,
        "updated_at":stamp.isoformat(timespec="minutes"),"updated_at_text":stamp.strftime("%Y.%m.%d %H:%M KST"),
        "sessions":[fmt_day(d) for d,_ in sessions],"market":ms,
        "summary":{k:len(v) for k,v in signals.items()},"signals":signals,"extras":compact_extra(extras),"api_status":status,
        "notes":["KRX 공식 OPEN API 일별 데이터 기반","실시간 호가가 아닌 거래일 단위 스캐너","추가 활용승인 API는 자동 수집"]
    }
    snap={"source":"KRX OPEN API","trade_date":fmt_day(latest_day),"updated_at_text":payload["updated_at_text"],"api_status":status,"datasets":extras}
    # 정상 데이터 검증 후에만 기존 파일 교체
    if ms.get("total_stocks",0)<100: raise RuntimeError(f"수집 종목 수가 비정상적으로 적습니다: {ms.get('total_stocks')}")
    tmp=OUT.with_suffix(".json.tmp"); tmp.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8"); tmp.replace(OUT)
    tmp2=SNAP.with_suffix(".json.tmp"); tmp2.write_text(json.dumps(snap,ensure_ascii=False,separators=(",",":")),encoding="utf-8"); tmp2.replace(SNAP)
    log(f"SUCCESS trade_date={latest_day} stocks={ms['total_stocks']:,} updated={payload['updated_at_text']}")
    log("AVAILABLE OPTIONAL:", ", ".join(k for k,v in status.items() if v["available"]) or "none")

if __name__=="__main__":
    main()
