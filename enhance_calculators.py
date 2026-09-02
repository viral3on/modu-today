from pathlib import Path
import re, json
ROOT=Path(__file__).resolve().parent
CALC=ROOT/'calculator'
CSS='<link rel="stylesheet" href="/calculator/theme.css">'
JS='<script defer src="/calculator/theme.js"></script>'
SKIP={'index.html'}
DESCS={
'loan':'대출 원금과 금리, 기간, 상환방식을 입력해 월 납입액과 총 이자를 비교합니다.','deposit':'예금·적금의 납입액과 금리, 기간을 기준으로 만기 이자와 세후 수령액을 계산합니다.','compound':'초기 원금과 추가 납입액, 수익률을 기준으로 복리 성장 결과를 계산합니다.','salary':'세전 연봉과 비과세액, 부양가족을 기준으로 4대보험과 세금을 반영한 예상 실수령액을 계산합니다.','annual-leave':'입사일과 근속기간을 기준으로 예상 연차 발생일수와 관련 값을 계산합니다.','severance':'근속기간과 평균임금을 기준으로 예상 퇴직금을 계산합니다.','parttime':'시급과 근로시간을 기준으로 주휴수당과 예상 급여를 계산합니다.','unemployment':'고용보험 가입기간과 임금 등을 기준으로 예상 구직급여를 계산합니다.','realtor':'거래 유형과 금액을 기준으로 부동산 중개보수 상한액을 계산합니다.','area':'제곱미터와 평 단위를 빠르게 양방향 환산합니다.','registration-tax':'부동산 거래금액을 기준으로 이전등기 관련 예상 비용을 계산합니다.','rent-tax':'월세 납부액과 조건을 기준으로 예상 세액공제액을 계산합니다.','car-tax':'차량 가격과 조건을 기준으로 자동차 취득 관련 예상 세금을 계산합니다.','electricity':'전력 사용량을 기준으로 주택용 누진제 예상 전기요금을 계산합니다.','exchange':'환율과 환전 우대율을 반영해 통화별 예상 환전금액을 계산합니다.','customs':'해외직구 금액과 품목 조건을 기준으로 예상 관세와 부가세를 계산합니다.','dividend':'배당금과 보유수량 등을 기준으로 세전·세후 예상 배당 수령액을 계산합니다.','average-price':'기존 매수와 추가 매수 가격·수량을 합산해 새로운 평균 매입단가를 계산합니다.','bmi':'키와 몸무게를 기준으로 BMI와 참고용 체중 지표를 계산합니다.','percent':'비율, 증감률, 할인율, 목표값 등 자주 쓰는 퍼센트 계산을 빠르게 처리합니다.','stock-return':'매수가·매도가·수량과 비용을 반영해 주식 투자 손익과 수익률을 계산합니다.'}
for p in sorted(CALC.glob('*.html')):
    if p.name in SKIP: continue
    slug=p.stem; text=p.read_text(encoding='utf-8'); changed=False
    if CSS not in text:
        text=text.replace('</head>',f'  {CSS}\n</head>'); changed=True
    if JS not in text:
        text=text.replace('</body>',f'  {JS}\n</body>'); changed=True
    canonical=f'https://modu.today/calculator/{p.name}'
    if 'rel="canonical"' not in text:
        text=text.replace('</head>',f'  <link rel="canonical" href="{canonical}">\n</head>'); changed=True
    if 'name="robots"' not in text:
        text=text.replace('</head>','  <meta name="robots" content="index,follow,max-image-preview:large">\n</head>'); changed=True
    desc=DESCS.get(slug,'입력값을 기준으로 예상 결과를 빠르게 계산하는 무료 온라인 계산기입니다.')
    if 'modu-seo' not in text:
        block=f'''<section class="modu-seo"><div class="modu-seo-in"><h2>이 계산기는 어떻게 사용하나요?</h2><p>{desc} 계산 결과는 입력한 값과 페이지에 표시된 계산 기준을 바탕으로 한 참고용 예상치입니다. 실제 적용 금액은 제도 변경, 개인 조건, 금융기관·기관별 기준에 따라 달라질 수 있으므로 중요한 의사결정 전에는 최신 공식 기준을 함께 확인하세요.</p></div></section>'''
        pos=text.lower().rfind('<footer')
        text=text[:pos]+block+'\n'+text[pos:] if pos!=-1 else text.replace('</body>',block+'\n</body>'); changed=True
    if 'application/ld+json' not in text:
        title=re.search(r'<title>(.*?)</title>',text,re.S); name=re.sub(r'\s*\|.*','',title.group(1)).strip() if title else slug
        data={'@context':'https://schema.org','@type':'WebApplication','name':name,'url':canonical,'applicationCategory':'UtilitiesApplication','operatingSystem':'Any','offers':{'@type':'Offer','price':'0','priceCurrency':'KRW'},'description':desc}
        text=text.replace('</head>',f'  <script type="application/ld+json">{json.dumps(data,ensure_ascii=False)}</script>\n</head>'); changed=True
    if changed:p.write_text(text,encoding='utf-8');print('UPDATED',p.relative_to(ROOT))
