import os,json,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
B=Path(__file__).parent; D=B/"data"
R=json.loads((D/"regions.json").read_text(encoding="utf-8"))
KEY=os.environ["MOLIT_API_KEY"]
END=os.environ["MOLIT_APT_ENDPOINT"]
now=datetime.now(); y,m=now.year,now.month; months=[]
for _ in range(3):
    months.append(f"{y:04d}{m:02d}"); m-=1
    if m==0:y-=1;m=12
def val(i,*names):
    for n in names:
        v=i.findtext(n)
        if v and v.strip(): return v.strip()
    return ""
def get(code,ym):
    q=urllib.parse.urlencode({"LAWD_CD":code,"DEAL_YMD":ym,"pageNo":1,"numOfRows":9999})
    url=END+"?"+q+"&serviceKey="+KEY
    req=urllib.request.Request(url,headers={"User-Agent":"MODU.TODAY/1.0"})
    with urllib.request.urlopen(req,timeout=20) as r: root=ET.fromstring(r.read())
    rc=root.findtext(".//resultCode") or ""
    if rc not in ("","000","00","0"): raise RuntimeError((root.findtext(".//resultMsg") or "API error")+" "+rc)
    out=[]
    for i in root.findall(".//item"):
        p=val(i,"dealAmount","거래금액").replace(",","").replace(" ","")
        try:p=int(p)
        except:p=0
        yy,mm,dd=val(i,"dealYear","년"),val(i,"dealMonth","월"),val(i,"dealDay","일")
        try:date=f"{int(yy):04d}-{int(mm):02d}-{int(dd):02d}"
        except:date=""
        out.append({"region_code":code,"region":next(x["name"] for x in R if x["code"]==code),
        "apt":val(i,"aptNm","아파트"),"dong":val(i,"umdNm","법정동"),"area":val(i,"excluUseAr","전용면적"),
        "floor":val(i,"floor","층"),"date":date,"price_manwon":p,"build_year":val(i,"buildYear","건축년도")})
    return out
allrows=[]
for r in R:
    for ym in months:
        try:
            a=get(r["code"],ym); allrows+=a; print(r["name"],ym,len(a))
        except Exception as e: print("WARN",r["name"],ym,e)
seen=set(); rows=[]
for x in allrows:
    k=(x["region_code"],x["apt"],x["dong"],x["area"],x["floor"],x["date"],x["price_manwon"])
    if k not in seen:seen.add(k);rows.append(x)
rows.sort(key=lambda x:(x["date"],x["price_manwon"]),reverse=True)
(D/"trades.json").write_text(json.dumps({"updated_at":datetime.now().astimezone().isoformat(timespec="minutes"),"months":months,"trades":rows},ensure_ascii=False,separators=(",",":")),encoding="utf-8")
print("SAVED",len(rows))
