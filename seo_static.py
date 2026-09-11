from pathlib import Path
import json, html, re

ROOT=Path(__file__).resolve().parent
START='<!-- SEO_STATIC_START -->'
END='<!-- SEO_STATIC_END -->'

def load_json(path):
    try:
        text=path.read_text(encoding='utf-8').strip()
        return json.loads(text) if text else None
    except Exception as e:
        print(f'SKIP JSON {path}: {e}')
        return None

def esc(v): return html.escape(str(v if v is not None else ''))
def nf(v):
    try: return f'{int(float(v)):,}'
    except: return '0'

def replace_block(path, block):
    text=path.read_text(encoding='utf-8')
    text=re.sub(r'\n?'+re.escape(START)+r'.*?'+re.escape(END)+r'\n?', '', text, flags=re.S)
    insert=f'\n{START}\n{block}\n{END}\n'
    lower=text.lower()
    pos=lower.rfind('</main>')
    if pos<0: pos=lower.rfind('<footer')
    if pos<0: pos=lower.rfind('</body>')
    if pos<0: pos=len(text)
    text=text[:pos]+insert+text[pos:]
    if path.read_text(encoding='utf-8') != text:
        path.write_text(text,encoding='utf-8')
    print('UPDATED',path.relative_to(ROOT))

def style():
    return '''<style>
.seo-static{max-width:1180px;margin:28px auto;padding:0 20px}.seo-static-card{background:#fff;color:#172033;border:1px solid #e6eaf2;border-radius:20px;padding:24px;box-shadow:0 8px 28px rgba(17,24,39,.05)}.seo-static h2{margin:0 0 8px;font-size:22px;letter-spacing:-.5px}.seo-static h3{margin:24px 0 8px;font-size:17px;letter-spacing:-.3px}.seo-static p{margin:0 0 16px;color:#667085;line-height:1.75;font-size:13px}.seo-static-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.seo-static-item{border:1px solid #edf0f5;border-radius:14px;padding:13px;background:#fafbfe}.seo-static-item strong{display:block;font-size:14px}.seo-static-item span{display:block;margin-top:4px;color:#7b8798;font-size:11px;line-height:1.5}.seo-static-balls{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}.seo-static-ball{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;background:#eef2ff;color:#4338ca;font-weight:900}.seo-static-note{margin-top:14px;padding:12px 14px;border-radius:12px;background:#f6f8ff;color:#667085;font-size:11px;line-height:1.65}.seo-static-info{margin-top:18px;padding:18px;border:1px solid #edf0f5;border-radius:16px;background:#fbfcff}.seo-static-info p:last-child{margin-bottom:0}.seo-static-links{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}.seo-static-links a{display:inline-flex;align-items:center;padding:9px 12px;border-radius:999px;background:#eef2ff;color:#4338ca;font-size:12px;font-weight:800;text-decoration:none}@media(max-width:700px){.seo-static-grid{grid-template-columns:1fr}}
</style>'''

def stock():
    d=load_json(ROOT/'stock/data/scanner.json')
    if not d: return
    rows=(d.get('signals',{}).get('watch_top') or [])[:10]
    items=''.join(f'<div class="seo-static-item"><strong>{i+1}. {esc(r.get("name"))} <small>{esc(r.get("ticker"))}</small></strong><span>{esc(r.get("market"))} · 종가 {nf(r.get("close"))}원 · 등락 {float(r.get("change_pct",0)):+.2f}% · MODU {float(r.get("modu_score",0)):.1f}점</span></div>' for i,r in enumerate(rows))
    s=d.get('summary',{})
    block=style()+f'''<section class="seo-static"><div class="seo-static-card"><h2>{esc(d.get('trade_date'))} 기준 증시 스캐너 요약</h2><p>KRX 공식 일별 데이터를 최근 거래이력과 비교해 거래량·거래대금·신고가·추세가 평소와 달라진 종목을 압축한 정적 요약입니다. 화면의 실시간 스크립트가 실행되지 않아도 주요 정보가 검색엔진에 전달됩니다.</p><div class="seo-static-grid">{items}</div><div class="seo-static-note">MODU 주목 {nf(s.get('watch_top'))}종목 · 이상거래 {nf(s.get('unusual_activity'))}종목 · 거래량 급증 {nf(s.get('volume_surge'))}종목 · 60일 신고가 {nf(s.get('new_high_60d'))}종목. 본 정보는 투자추천이 아닌 데이터 기반 참고자료입니다.</div></div></section>'''
    replace_block(ROOT/'stock/index.html',block)

def youtube():
    d=load_json(ROOT/'youtube/data/ranking.json')
    if not d: return
    rows=(d.get('rankings',{}).get('daily') or d.get('rankings',{}).get('weekly') or [])[:10]
    items=''.join(f'<div class="seo-static-item"><strong>{i+1}. {esc(r.get("title"))}</strong><span>{esc(r.get("channelTitle"))} · 조회수 증가 +{nf(r.get("gain"))}회</span></div>' for i,r in enumerate(rows))
    links='''<div class="seo-static-links"><a href="/">MODU.TODAY 홈</a><a href="/stock/">증시 스캐너</a><a href="/apt/">아파트 실거래가</a><a href="/calculator/">생활 계산기</a><a href="/lotto/">로또 정보</a><a href="/about/">서비스 소개</a></div>'''
    info='''<div class="seo-static-info">
<h3>유튜브 순위는 어떻게 계산하나요?</h3>
<p>MODU.TODAY는 특정 시점의 누적 조회수만 나열하지 않습니다. 추적 대상 공개 영상의 조회수를 일정한 간격으로 저장한 뒤, 이전에 저장한 값과 최신 값을 비교해 실제로 얼마나 조회수가 늘었는지를 계산합니다. 이렇게 하면 오래전에 큰 조회수를 기록한 영상보다 최근에 빠르게 관심을 받고 있는 영상을 찾기 쉽습니다.</p>
<h3>일간·주간·월간 순위의 차이</h3>
<p>일간 순위는 최근 하루 동안의 조회수 증가량을, 주간 순위는 최근 여러 날의 변화를, 월간 순위는 더 긴 기간 동안 누적된 증가량을 비교합니다. 같은 영상이라도 짧은 기간에 급상승했는지, 꾸준히 조회수가 늘고 있는지에 따라 기간별 순위가 달라질 수 있습니다.</p>
<h3>왜 누적 조회수가 아니라 증가량을 사용하나요?</h3>
<p>누적 조회수만 기준으로 하면 과거에 수억 회 이상 조회된 영상이 오랫동안 상위권을 차지해 현재의 관심도를 파악하기 어렵습니다. 조회수 증가량은 최근 이용자들이 실제로 많이 본 영상의 변화를 상대적으로 더 잘 보여주기 때문에, 현재 화제성을 살펴보는 참고 지표로 활용하기 좋습니다.</p>
<h3>데이터는 언제 업데이트되나요?</h3>
<p>조회수 데이터는 자동 수집 작업을 통해 주기적으로 갱신합니다. YouTube 공식 화면의 수치와는 수집 시점, 캐시, 집계 반영 시간 차이 때문에 일시적으로 값이 다를 수 있습니다. 순위는 참고용이며 YouTube의 공식 인기 급상승 순위나 추천 알고리즘과는 별개의 MODU.TODAY 자체 집계입니다.</p>
<h3>이용할 때 참고할 점</h3>
<p>조회수 증가는 영상의 품질이나 신뢰도를 의미하지 않으며, 영상 삭제·비공개 전환·조회수 조정 등에 따라 수치가 변할 수 있습니다. 제목과 채널명은 공개된 영상 정보를 기반으로 표시하며, 최신 상태는 해당 YouTube 영상 페이지에서 함께 확인하는 것이 좋습니다.</p>
</div>'''
    block=style()+f'''<section class="seo-static"><div class="seo-static-card"><h2>YouTube 조회수 상승 TOP 10</h2><p>MODU.TODAY가 저장한 영상 조회수 스냅샷의 차이를 기준으로 최근 조회수가 빠르게 증가한 영상을 정리합니다. 단순 누적 조회수 순위가 아니라 기간별 증가량을 비교해 현재 관심이 커지는 영상을 쉽게 확인할 수 있도록 구성했습니다.</p><div class="seo-static-grid">{items}</div><div class="seo-static-note">최종 집계 {esc(d.get('updatedAtKST'))} · 추적 영상 {nf(d.get('trackedVideos'))}개. YouTube 공식 화면의 수치와 집계 시점 차이가 있을 수 있습니다.</div>{info}{links}</div></section>'''
    replace_block(ROOT/'youtube/index.html',block)

def lotto():
    d=load_json(ROOT/'lotto/data/results.json')
    if not d: return
    latest=d.get('latest') or {}
    nums=latest.get('numbers') or []
    balls=''.join(f'<span class="seo-static-ball">{esc(n)}</span>' for n in nums)+f'<span class="seo-static-ball">+{esc(latest.get("bonus"))}</span>'
    draws=(d.get('draws') or [])[:8]
    items=''.join(f'<div class="seo-static-item"><strong>{esc(r.get("draw"))}회 · {esc(r.get("date"))}</strong><span>{" · ".join(map(str,r.get("numbers") or []))} + 보너스 {esc(r.get("bonus"))}</span></div>' for r in draws)
    block=style()+f'''<section class="seo-static"><div class="seo-static-card"><h2>{esc(latest.get('draw'))}회 로또6/45 당첨 결과</h2><p>{esc(latest.get('date'))} 추첨 결과와 최근 회차를 검색엔진에서도 바로 읽을 수 있도록 정적 HTML로 제공합니다.</p><div class="seo-static-balls">{balls}</div><p>1등 {nf(latest.get('first_winners'))}명 · 1인당 {nf(latest.get('first_prize'))}원</p><div class="seo-static-grid">{items}</div><div class="seo-static-note">출처: 동행복권 로또6/45 추첨결과. 당첨금 및 판매점 정보는 공식 발표를 최종 기준으로 확인하세요.</div></div></section>'''
    replace_block(ROOT/'lotto/index.html',block)

def apt():
    d=load_json(ROOT/'apt/data/trades.json')
    if not d:
        print('SKIP apt: trades.json empty or invalid; existing page preserved')
        return
    rows=d.get('trades') if isinstance(d,dict) else d
    rows=(rows or [])[:20]
    items=[]
    for r in rows[:12]:
        name=r.get('apt') or r.get('apt_name') or r.get('apartment') or r.get('name') or r.get('아파트') or '아파트'
        region=r.get('region_name') or r.get('region') or r.get('sgg_nm') or r.get('시군구') or ''
        price=r.get('price_manwon') or r.get('deal_amount') or r.get('price') or r.get('거래금액') or 0
        date=r.get('deal_date') or r.get('date') or r.get('거래일') or ''
        items.append(f'<div class="seo-static-item"><strong>{esc(name)}</strong><span>{esc(region)} · {esc(date)} · 거래금액 {nf(price)}</span></div>')
    block=style()+f'''<section class="seo-static"><div class="seo-static-card"><h2>최근 아파트 실거래 요약</h2><p>국토교통부 공개 아파트 매매 실거래 데이터를 지역·단지별로 찾기 쉽게 정리합니다. 아래 내용은 수집된 최신 데이터 중 일부를 정적 HTML로 제공합니다.</p><div class="seo-static-grid">{"".join(items)}</div><div class="seo-static-note">실거래 자료는 신고·정정·해제 등에 따라 추후 변경될 수 있으므로 중요한 의사결정 전에는 국토교통부 실거래가 공개시스템의 최신 자료를 함께 확인하세요.</div></div></section>'''
    replace_block(ROOT/'apt/index.html',block)

stock();youtube();lotto();apt()
