#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MODU.TODAY - 한국 증시 조건검색 스캐너 데이터 생성기

- 실시간 호가 서비스가 아니라 일별 시장 데이터를 조합해 '찾기 귀찮은 조건'을 자동 계산합니다.
- 수집 실패 시 기존 scanner.json을 보존합니다.
- 공개/상업 운영 전에는 사용 데이터의 이용·재배포 조건을 반드시 확인하세요.
"""
from __future__ import annotations

import json
import math
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from pykrx import stock

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)
OUT_FILE = DATA / "scanner.json"
KST = timezone(timedelta(hours=9))

MAX_LOOKBACK_CALENDAR_DAYS = 45
NEEDED_SESSIONS = 21
SIGNAL_LIMIT = 50


def log(*args):
    print(*args, flush=True)


def as_num(v, default=0):
    try:
        if pd.isna(v):
            return default
        return float(v)
    except Exception:
        return default


def as_int(v, default=0):
    try:
        if pd.isna(v):
            return default
        return int(v)
    except Exception:
        return default


def fetch_market_frame(day: str) -> pd.DataFrame:
    """KOSPI + KOSDAQ 전 종목 OHLCV를 하나의 DataFrame으로 반환."""
    frames = []
    for market in ("KOSPI", "KOSDAQ"):
        try:
            df = stock.get_market_ohlcv_by_ticker(day, market=market)
            if df is None or df.empty:
                continue
            df = df.copy()
            df["시장"] = market
            df.index = df.index.astype(str)
            frames.append(df)
        except Exception as e:
            log(f"OHLCV WARN {day} {market}: {type(e).__name__}: {e}")
        time.sleep(0.20)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, axis=0)


def collect_sessions() -> list[tuple[str, pd.DataFrame]]:
    now = datetime.now(KST)
    sessions = []
    seen = set()
    for back in range(MAX_LOOKBACK_CALENDAR_DAYS):
        day = (now.date() - timedelta(days=back)).strftime("%Y%m%d")
        df = fetch_market_frame(day)
        if df.empty:
            continue
        # 같은 영업일이 중복 반환되는 예외를 방지
        if day in seen:
            continue
        seen.add(day)
        sessions.append((day, df))
        log(f"SESSION OK {day}: {len(df):,} stocks")
        if len(sessions) >= NEEDED_SESSIONS:
            break
    sessions.sort(key=lambda x: x[0])
    return sessions


def fetch_investor(day: str, investor: str) -> tuple[pd.Series, dict[str, str]]:
    """해당 날짜 투자자별 종목 순매수 거래대금 + 종목명. 실패 시 빈 값."""
    try:
        df = stock.get_market_net_purchases_of_equities_by_ticker(
            day, day, market="ALL", investor=investor
        )
        if df is None or df.empty or "순매수거래대금" not in df.columns:
            return pd.Series(dtype="float64"), {}
        df = df.copy()
        df.index = df.index.astype(str)
        s = pd.to_numeric(df["순매수거래대금"], errors="coerce").fillna(0)
        names = {}
        if "종목명" in df.columns:
            names = {str(t): str(n) for t, n in df["종목명"].items()}
        return s, names
    except Exception as e:
        log(f"INVESTOR WARN {day} {investor}: {type(e).__name__}: {e}")
        return pd.Series(dtype="float64"), {}
    finally:
        time.sleep(0.25)


def pct(a, b):
    if not b:
        return 0.0
    return (a / b - 1.0) * 100.0


def safe_name(ticker: str, cache: dict[str, str]) -> str:
    if ticker in cache:
        return cache[ticker]
    try:
        name = stock.get_market_ticker_name(ticker) or ticker
    except Exception:
        name = ticker
    cache[ticker] = name
    time.sleep(0.03)
    return name


def build():
    sessions = collect_sessions()
    if len(sessions) < 6:
        raise RuntimeError(f"Not enough trading sessions: {len(sessions)}")

    latest_day, latest = sessions[-1]
    latest = latest.copy()
    previous = sessions[-2][1]

    # 최근 20거래일 평균 거래량
    hist_for_avg = sessions[-21:-1] if len(sessions) >= 21 else sessions[:-1]
    volume_df = pd.DataFrame({d: pd.to_numeric(df.get("거래량"), errors="coerce") for d, df in hist_for_avg})
    avg_volume = volume_df.mean(axis=1, skipna=True).fillna(0)

    # 5거래일 연속 상승 판정용 종가
    streak_sessions = sessions[-6:]
    close_df = pd.DataFrame({d: pd.to_numeric(df.get("종가"), errors="coerce") for d, df in streak_sessions})

    # 최근 5거래일 투자자 순매수 거래대금
    last5_days = [d for d, _ in sessions[-5:]]
    foreign_by_day = {}
    inst_by_day = {}
    for day in last5_days:
        log(f"INVESTOR START {day}")
        fs, fnames = fetch_investor(day, "외국인")
        ins, inames = fetch_investor(day, "기관합계")
        foreign_by_day[day] = fs
        inst_by_day[day] = ins
        if day == latest_day:
            latest_names = {**fnames, **inames}

    latest_foreign = foreign_by_day.get(latest_day, pd.Series(dtype="float64"))
    latest_inst = inst_by_day.get(latest_day, pd.Series(dtype="float64"))

    tickers = list(latest.index.astype(str))
    name_cache = locals().get("latest_names", {})

    def base_row(ticker: str) -> dict:
        r = latest.loc[ticker]
        close = as_int(r.get("종가", 0))
        chg = as_num(r.get("등락률", 0))
        vol = as_int(r.get("거래량", 0))
        value = as_int(r.get("거래대금", 0))
        market = str(r.get("시장", ""))
        return {
            "ticker": ticker,
            "name": safe_name(ticker, name_cache),
            "market": market,
            "close": close,
            "change_pct": round(chg, 2),
            "volume": vol,
            "trading_value": value,
        }

    # 1) 오늘 상승률 TOP
    top_gainers = []
    if "등락률" in latest.columns:
        for ticker, r in latest.sort_values("등락률", ascending=False).head(SIGNAL_LIMIT * 2).iterrows():
            if as_int(r.get("종가", 0)) <= 0 or as_int(r.get("거래대금", 0)) <= 0:
                continue
            top_gainers.append(base_row(str(ticker)))
            if len(top_gainers) >= SIGNAL_LIMIT:
                break

    # 2) 거래량 평균 3배 이상 급증
    volume_surge = []
    current_volume = pd.to_numeric(latest.get("거래량"), errors="coerce").fillna(0)
    ratios = (current_volume / avg_volume.replace(0, math.nan)).replace([math.inf, -math.inf], math.nan).dropna()
    ratios = ratios[ratios >= 3.0].sort_values(ascending=False)
    for ticker, ratio in ratios.head(SIGNAL_LIMIT).items():
        if ticker not in latest.index:
            continue
        row = base_row(str(ticker))
        row["volume_ratio"] = round(float(ratio), 2)
        row["avg_volume_20d"] = as_int(avg_volume.get(ticker, 0))
        volume_surge.append(row)

    # 3) 5거래일 연속 상승
    up_streak_5d = []
    if close_df.shape[1] >= 6:
        valid = close_df.dropna()
        for ticker, vals in valid.iterrows():
            seq = [as_num(v) for v in vals.tolist()]
            if all(seq[i] < seq[i + 1] for i in range(len(seq) - 1)) and seq[0] > 0:
                row = base_row(str(ticker))
                row["return_5d"] = round(pct(seq[-1], seq[0]), 2)
                up_streak_5d.append(row)
        up_streak_5d.sort(key=lambda x: x.get("return_5d", 0), reverse=True)
        up_streak_5d = up_streak_5d[:SIGNAL_LIMIT]

    # 4) 외국인 5거래일 연속 순매수
    foreign_5d = []
    for ticker in tickers:
        vals = [as_num(foreign_by_day[d].get(ticker, 0)) for d in last5_days]
        if len(vals) == 5 and all(v > 0 for v in vals):
            row = base_row(ticker)
            row["foreign_net_5d"] = as_int(sum(vals))
            row["foreign_net_today"] = as_int(vals[-1])
            foreign_5d.append(row)
    foreign_5d.sort(key=lambda x: x.get("foreign_net_5d", 0), reverse=True)
    foreign_5d = foreign_5d[:SIGNAL_LIMIT]

    # 5) 기관 5거래일 연속 순매수
    institution_5d = []
    for ticker in tickers:
        vals = [as_num(inst_by_day[d].get(ticker, 0)) for d in last5_days]
        if len(vals) == 5 and all(v > 0 for v in vals):
            row = base_row(ticker)
            row["institution_net_5d"] = as_int(sum(vals))
            row["institution_net_today"] = as_int(vals[-1])
            institution_5d.append(row)
    institution_5d.sort(key=lambda x: x.get("institution_net_5d", 0), reverse=True)
    institution_5d = institution_5d[:SIGNAL_LIMIT]

    # 6) 오늘 외국인 + 기관 동시 순매수
    double_buy = []
    common = set(latest_foreign.index.astype(str)) & set(latest_inst.index.astype(str)) & set(tickers)
    for ticker in common:
        f = as_num(latest_foreign.get(ticker, 0))
        i = as_num(latest_inst.get(ticker, 0))
        if f > 0 and i > 0:
            row = base_row(ticker)
            row["foreign_net_today"] = as_int(f)
            row["institution_net_today"] = as_int(i)
            row["combined_net_today"] = as_int(f + i)
            double_buy.append(row)
    double_buy.sort(key=lambda x: x.get("combined_net_today", 0), reverse=True)
    double_buy = double_buy[:SIGNAL_LIMIT]

    now = datetime.now(KST)
    payload = {
        "updated_at": now.isoformat(timespec="minutes"),
        "updated_at_text": now.strftime("%Y.%m.%d %H:%M KST"),
        "trade_date": datetime.strptime(latest_day, "%Y%m%d").strftime("%Y-%m-%d"),
        "source_note": "KRX 일별 시장데이터 기반 조건검색(실시간 호가 아님)",
        "summary": {
            "universe": len(latest),
            "foreign_5d": len(foreign_5d),
            "institution_5d": len(institution_5d),
            "double_buy": len(double_buy),
            "volume_surge": len(volume_surge),
            "up_streak_5d": len(up_streak_5d),
        },
        "signals": {
            "foreign_5d": foreign_5d,
            "institution_5d": institution_5d,
            "double_buy": double_buy,
            "volume_surge": volume_surge,
            "up_streak_5d": up_streak_5d,
            "top_gainers": top_gainers,
        },
    }

    tmp = OUT_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(OUT_FILE)
    log(f"SAVED {OUT_FILE} / trade_date={payload['trade_date']} / universe={len(latest):,}")


if __name__ == "__main__":
    try:
        build()
    except Exception as e:
        log(f"FATAL: {type(e).__name__}: {e}")
        log("Existing scanner.json was preserved.")
        raise
