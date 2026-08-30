import os, json, urllib.parse, urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

API_KEY=os.environ["YOUTUBE_API_KEY"]
BASE=Path(__file__).resolve().parent
DATA=BASE/"data"; HIST=DATA/"history"
DATA.mkdir(exist_ok=True); HIST.mkdir(exist_ok=True)
KST=timezone(timedelta(hours=9))
now=datetime.now(timezone.utc)
today=now.astimezone(KST).date().isoformat()

def api(endpoint, params):
    params["key"]=API_KEY
    url="https://www.googleapis.com/youtube/v3/"+endpoint+"?"+urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

# 후보군: 최근 30일 한국 관련 공개 영상 중 조회수 순 검색.
# 한 번의 검색 결과가 YouTube 전체를 완전하게 대표하지 않으므로 자체 후보군 랭킹으로 명시한다.
after=(now-timedelta(days=30)).isoformat().replace("+00:00","Z")
search=api("search",{
    "part":"snippet","type":"video","order":"viewCount","maxResults":50,
    "regionCode":"KR","relevanceLanguage":"ko","publishedAfter":after,
    "safeSearch":"moderate"
})
ids=[x["id"]["videoId"] for x in search.get("items",[]) if x.get("id",{}).get("videoId")]

# 기존 추적 영상도 계속 관찰하여 후보가 매일 통째로 바뀌는 문제를 줄인다.
latest_file=DATA/"latest.json"
if latest_file.exists():
    old=json.loads(latest_file.read_text(encoding="utf-8"))
    ids += [x["videoId"] for x in old.get("videos",[])]

ids=list(dict.fromkeys(ids))[:500]
videos=[]
for i in range(0,len(ids),50):
    res=api("videos",{"part":"snippet,statistics","id":",".join(ids[i:i+50]),"maxResults":50})
    for x in res.get("items",[]):
        s=x["snippet"]; st=x.get("statistics",{})
        videos.append({
          "videoId":x["id"],"title":s.get("title",""),"channelTitle":s.get("channelTitle",""),
          "publishedAt":s.get("publishedAt",""),"thumbnail":s.get("thumbnails",{}).get("medium",s.get("thumbnails",{}).get("default",{})).get("url",""),
          "viewCount":int(st.get("viewCount",0))
        })

snapshot={"date":today,"capturedAt":now.isoformat(),"videos":videos}
(HIST/f"{today}.json").write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding="utf-8")
latest_file.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding="utf-8")

def load_nearest(days):
    target=now.astimezone(KST).date()-timedelta(days=days)
    files=sorted(HIST.glob("*.json"))
    candidates=[]
    for f in files:
        try:
            d=datetime.strptime(f.stem,"%Y-%m-%d").date()
            diff=abs((d-target).days)
            if diff<=2: candidates.append((diff,d,f))
        except: pass
    if not candidates:return {}
    f=min(candidates,key=lambda x:(x[0],-x[1].toordinal()))[2]
    snap=json.loads(f.read_text(encoding="utf-8"))
    return {v["videoId"]:v for v in snap.get("videos",[])}

def ranking(days):
    past=load_nearest(days)
    rows=[]
    for v in videos:
        p=past.get(v["videoId"])
        if not p: continue
        gain=max(0,v["viewCount"]-int(p.get("viewCount",0)))
        row=dict(v); row["gain"]=gain
        try:
            dt=datetime.fromisoformat(v["publishedAt"].replace("Z","+00:00")).astimezone(KST)
            row["publishedAtText"]=dt.strftime("%Y.%m.%d")
        except: row["publishedAtText"]=""
        rows.append(row)
    rows.sort(key=lambda x:(x["gain"],x["viewCount"]),reverse=True)
    return rows[:100]

out={
 "updatedAtKST":now.astimezone(KST).strftime("%Y.%m.%d %H:%M"),
 "trackedVideos":len(videos),
 "rankings":{"daily":ranking(1),"weekly":ranking(7),"monthly":ranking(30)}
}
(DATA/"ranking.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"{today}: tracked={len(videos)}, daily={len(out['rankings']['daily'])}, weekly={len(out['rankings']['weekly'])}, monthly={len(out['rankings']['monthly'])}")
