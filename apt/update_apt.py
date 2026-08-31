#!/usr/bin/env python3
import os,json,time,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed

BASE=Path(__file__).resolve().parent
DATA=BASE/"data"
REGIONS=json.loads((DATA/"regions.json").read_text(encoding="utf-8"))
KEY=os.environ.get("MOLIT_API_KEY","").strip()
END=os.environ.get("MOLIT_APT_ENDPOINT","").strip()
if not KEY: raise SystemExit("MOLIT_API_KEY secret is missing")
if not END: raise SystemExit("MOLIT_APT_ENDPOINT secret is missing")

# 최근 3개월. 전국 약 250개 지역이어도 일일 10,000 호출보다 충분히 낮게 유지.
now=datetime.now(); y,m=now.year,now.month; MONTHS=[]
for _ in range(3):
    MONTHS.append(f"{y:04d}{m:02d}"); m-=1
    if m==0:y-=1;m=12

REGION_BY_CODE={r["code"]:r for r in REGIONS}

def val(item,*names):
    for n in names:
        v=item.findtext(n)
        if v is not None and v.strip(): return v.strip()
    return ""

def make_url(code,ym):
    # 공공데이터포털 키는 인코딩 키/디코딩 키 형태가 있을 수 있으므로 serviceKey는 그대로 붙인다.
    q=urllib.parse.urlencode({"LAWD_CD":code,"DEAL_YMD":ym,"pageNo":"1","numOfRows":"9999"})
    sep="&" if "?" in END else "?"
    return END+sep+q+"&serviceKey="+KEY

def fetch_one(code,ym):
    req=urllib.request.Request(make_url(code,ym),headers={"User-Agent":"MODU.TODAY apt collector/2.0"})
    last=None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req,timeout=18) as resp: raw=resp.read()
            root=ET.fromstring(raw)
            rc=(root.findtext(".//resultCode") or "").strip()
            if rc not in ("","000","00","0"):
                raise RuntimeError((root.findtext(".//resultMsg") or "API error")+" / "+rc)
            reg=REGION_BY_CODE[code]; out=[]
            for i in root.findall(".//item"):
                p=val(i,"dealAmount","거래금액").replace(",","").replace(" ","")
                try:p=int(p)
                except:p=0
                yy,mm,dd=val(i,"dealYear","년"),val(i,"dealMonth","월"),val(i,"dealDay","일")
                try:date=f"{int(yy):04d}-{int(mm):02d}-{int(dd):02d}"
                except:date=""
                out.append({
                    "region_code":code,"sido":reg["sido"],"sigungu":reg["sigungu"],"region":reg["name"],
                    "apt":val(i,"aptNm","아파트"),"dong":val(i,"umdNm","법정동"),"jibun":val(i,"jibun","지번"),
                    "area":val(i,"excluUseAr","전용면적"),"floor":val(i,"floor","층"),"date":date,
                    "price_manwon":p,"build_year":val(i,"buildYear","건축년도"),
                    "deal_type":val(i,"dealingGbn","거래유형")
                })
            return out
        except Exception as e:
            last=e
            if attempt==0: time.sleep(.5)
    raise last

jobs=[(r["code"],ym) for r in REGIONS for ym in MONTHS]
rows=[]
errors=[]
print(f"Fetching nationwide apartment trades: regions={len(REGIONS)}, months={len(MONTHS)}, calls={len(jobs)}")
with ThreadPoolExecutor(max_workers=8) as ex:
    futures={ex.submit(fetch_one,c,y):(c,y) for c,y in jobs}
    for f in as_completed(futures):
        c,y=futures[f]
        try:
            a=f.result(); rows.extend(a)
            print("OK",REGION_BY_CODE[c]["name"],y,len(a))
        except Exception as e:
            errors.append((c,y,str(e))); print("WARN",REGION_BY_CODE[c]["name"],y,e)

# 한 번의 일부 API 실패 때문에 기존 데이터가 사라지지 않도록 기존 결과와 병합
trade_file=DATA/"trades.json"
try: old=json.loads(trade_file.read_text(encoding="utf-8")).get("trades",[])
except: old=[]
failed_pairs={(c,y) for c,y,_ in errors}
for x in old:
    ym=(x.get("date") or "")[:7].replace("-","")
    if (x.get("region_code"),ym) in failed_pairs and ym in MONTHS:
        rows.append(x)

seen=set(); clean=[]
for x in rows:
    k=(x.get("region_code"),x.get("apt"),x.get("dong"),x.get("area"),x.get("floor"),x.get("date"),x.get("price_manwon"))
    if k not in seen:
        seen.add(k); clean.append(x)
clean.sort(key=lambda x:(x.get("date",""),x.get("price_manwon",0)),reverse=True)

stamp=datetime.now().astimezone().isoformat(timespec="minutes")
trade_file.write_text(json.dumps({"updated_at":stamp,"months":MONTHS,"trades":clean},ensure_ascii=False,separators=(",",":")),encoding="utf-8")

# 자동완성용 아파트 목록은 누적 저장: 최근 3개월 거래가 없어져도 과거에 발견된 단지는 남는다.
apt_file=DATA/"apartments.json"
try: old_apts=json.loads(apt_file.read_text(encoding="utf-8")).get("apartments",[])
except: old_apts=[]
aptmap={}
for a in old_apts:
    k=(a.get("region_code"),a.get("apt"),a.get("dong"))
    if all(k): aptmap[k]=a
for x in clean:
    if not x.get("apt"): continue
    k=(x.get("region_code"),x.get("apt"),x.get("dong"))
    aptmap[k]={"region_code":x.get("region_code"),"sido":x.get("sido"),"sigungu":x.get("sigungu"),
               "region":x.get("region"),"dong":x.get("dong"),"apt":x.get("apt")}
apts=sorted(aptmap.values(),key=lambda x:(x.get("sido",""),x.get("sigungu",""),x.get("dong",""),x.get("apt","")))
apt_file.write_text(json.dumps({"updated_at":stamp,"apartments":apts},ensure_ascii=False,separators=(",",":")),encoding="utf-8")
print(f"SAVED trades={len(clean)}, apartments={len(apts)}, failed_calls={len(errors)}")
