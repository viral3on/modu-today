import os,json,urllib.parse,urllib.request
from pathlib import Path
from datetime import datetime,timezone,timedelta

KEY=os.environ["YOUTUBE_API_KEY"]; BASE=Path(__file__).resolve().parent
DATA=BASE/"data"; HIST=DATA/"history"; DATA.mkdir(exist_ok=True); HIST.mkdir(exist_ok=True)
KST=timezone(timedelta(hours=9)); now=datetime.now(timezone.utc); today=now.astimezone(KST).date().isoformat()

def api(ep,p):
    p=dict(p); p["key"]=KEY
    u="https://www.googleapis.com/youtube/v3/"+ep+"?"+urllib.parse.urlencode(p)
    with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"MODU-TODAY/1.0"}),timeout=30) as r:return json.load(r)
def add(ids,items):
    for x in items:
        v=x.get("id"); v=v.get("videoId") if isinstance(v,dict) else v
        if v and v not in ids: ids.append(v)

ids=[]
try:add(ids,api("videos",{"part":"id","chart":"mostPopular","regionCode":"KR","maxResults":50}).get("items",[]))
except Exception as e:print("mostPopular:",e)

after=(now-timedelta(days=30)).isoformat().replace("+00:00","Z")
for q in ["한국","뉴스","음악","게임","예능","스포츠","쇼츠"]:
    try:add(ids,api("search",{"part":"snippet","type":"video","q":q,"order":"date","maxResults":50,"regionCode":"KR","relevanceLanguage":"ko","publishedAfter":after,"safeSearch":"moderate"}).get("items",[]))
    except Exception as e:print("search",q,e)

latest=DATA/"latest.json"
if latest.exists():
    try:
        for x in json.loads(latest.read_text(encoding="utf-8")).get("videos",[]): add(ids,[{"id":x.get("videoId")}])
    except Exception as e:print("latest:",e)
ids=ids[:500]

videos=[]
for i in range(0,len(ids),50):
    try:r=api("videos",{"part":"snippet,statistics,status","id":",".join(ids[i:i+50]),"maxResults":50})
    except Exception as e:print("stats:",e);continue
    for x in r.get("items",[]):
        if x.get("status",{}).get("privacyStatus")!="public":continue
        s=x.get("snippet",{}); st=x.get("statistics",{}); th=s.get("thumbnails",{})
        thumb=(th.get("medium") or th.get("high") or th.get("default") or {}).get("url","")
        videos.append({"videoId":x["id"],"title":s.get("title",""),"channelTitle":s.get("channelTitle",""),"publishedAt":s.get("publishedAt",""),"thumbnail":thumb,"viewCount":int(st.get("viewCount",0))})
videos.sort(key=lambda x:x["viewCount"],reverse=True); videos=videos[:500]
snap={"date":today,"capturedAt":now.isoformat(),"videos":videos}
(HIST/f"{today}.json").write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding="utf-8")
latest.write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding="utf-8")

def past(days):
    target=now.astimezone(KST).date()-timedelta(days=days); c=[]
    for f in HIST.glob("*.json"):
        try:
            d=datetime.strptime(f.stem,"%Y-%m-%d").date(); diff=abs((d-target).days)
            if diff<=2:c.append((diff,-d.toordinal(),f))
        except:pass
    if not c:return {}
    return {v["videoId"]:v for v in json.loads(min(c)[2].read_text(encoding="utf-8")).get("videos",[])}

def rank(days):
    old=past(days); rows=[]
    for v in videos:
        if v["videoId"] not in old:continue
        z=dict(v); z["gain"]=max(0,v["viewCount"]-int(old[v["videoId"]].get("viewCount",0)))
        try:z["publishedAtText"]=datetime.fromisoformat(v["publishedAt"].replace("Z","+00:00")).astimezone(KST).strftime("%Y.%m.%d")
        except:z["publishedAtText"]=""
        rows.append(z)
    return sorted(rows,key=lambda x:(x["gain"],x["viewCount"]),reverse=True)[:100]

out={"updatedAtKST":now.astimezone(KST).strftime("%Y.%m.%d %H:%M"),"trackedVideos":len(videos),"rankings":{"daily":rank(1),"weekly":rank(7),"monthly":rank(30)}}
(DATA/"ranking.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"{today}: candidates={len(ids)}, tracked={len(videos)}")
if not videos:raise RuntimeError("No YouTube videos collected; check API access/quota.")
