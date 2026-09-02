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
    text=re.sub(re.escape(START)+r'.*?'+re.escape(END), '', text, flags=re.S)
    insert=f'\n{START}\n{block}\n{END}\n'
    lower=text.lower()
    pos=lower.rfind('</main>')
    if pos<0: pos=lower.rfind('<footer')
    if pos<0: pos=lower.rfind('</body>')
    if pos<0: pos=len(text)
    text=text[:pos]+insert+text[pos:]
    path.write_text(text,encoding='utf-8')
    print('UPDATED',path.relative_to(ROOT))

def style():
    return '''<style>
.seo-static{max-width:1180px;margin:28px auto;padding:0 20px}.seo-static-card{background:#fff;color:#172033;border:1px solid #e6eaf2;border-radius:20px;padding:24px;box-shadow:0 8px 28px rgba(17,24,39,.05)}.seo-static h2{margin:0 0 8px;font-size:22px;letter-spacing:-.5px}.seo-static p{margin:0 0 16px;color:#667085;line-height:1.7;font-size:13px}.seo-static-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.seo-static-item{border:1px solid #edf0f5;border-radius:14px;padding:13px;background:#fafbfe}.seo-static-item strong{display:block;font-size:14px}.seo-static-item span{display:block;margin-top:4px;color:#7b8798;font-size:11px;line-height:1.5}.seo-static-balls{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}.seo-static-ball{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;background:#eef2ff;color:#4338ca;font-weight:900}.seo-static-note{margin-top:14px;padding:12px 14px;border-radius:12px;background:#f6f8ff;color:#667085;font-size:11px;line-height:1.65}@media(max-width:700px){.seo-static-grid{grid-template-columns:1fr}}
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
    block=style()+f'''<section class="seo-static"><div class="seo-static-card"><h2>YouTube 조회수 상승 TOP 10</h2><p>MODU.TODAY가 저장한 영상 조회수 스냅샷의 차이를 기준으로 최근 조회수가 빠르게 증가한 영상을 정리합니다. 단순 누적 조회수 순위가 아니라 기간별 증가량을 비교합니다.</p><div class="seo-static-grid">{items}</div><div class="seo-static-note">최종 집계 {esc(d.get('updatedAtKST'))} · 추적 영상 {nf(d.get('trackedVideos'))}개. YouTube 공식 화면의 수치와 집계 시점 차이가 있을 수 있습니다.</div></div></section>'''
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
        name=r.get('apt_name') or r.get('apartment') or r.get('name') or r.get('아파트') or '아파트'
        region=r.get('region_name') or r.get('region') or r.get('sgg_nm') or r.get('시군구') or ''
        price=r.get('deal_amount') or r.get('price') or r.get('거래금액') or 0
        date=r.get('deal_date') or r.get('date') or r.get('거래일') or ''
        items.append(f'<div class="seo-static-item"><strong>{esc(name)}</strong><span>{esc(region)} · {esc(date)} · 거래금액 {nf(price)}</span></div>')
    block=style()+f'''<section class="seo-static"><div class="seo-static-card"><h2>최근 아파트 실거래 요약</h2><p>국토교통부 공개 아파트 매매 실거래 데이터를 지역·단지별로 찾기 쉽게 정리합니다. 아래 내용은 수집된 최신 데이터 중 일부를 정적 HTML로 제공합니다.</p><div class="seo-static-grid">{"".join(items)}</div><div class="seo-static-note">실거래 자료는 신고·정정·해제 등에 따라 추후 변경될 수 있으므로 중요한 의사결정 전에는 국토교통부 실거래가 공개시스템의 최신 자료를 함께 확인하세요.</div></div></section>'''
    replace_block(ROOT/'apt/index.html',block)

stock();youtube();lotto();apt()
