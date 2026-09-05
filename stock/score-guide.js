(()=>{
  const css=`
  .score-guide{margin:0 0 24px;border:1px solid #2b4160;background:linear-gradient(145deg,#101c2e,#0d1726);border-radius:18px;padding:18px;color:#b9c7d9}
  .score-guide h2{margin:0 0 8px;color:#fff;font-size:18px}.score-guide p{margin:0;color:#93a7c1;font-size:13px;line-height:1.7}
  .score-guide details{margin-top:12px;border-top:1px solid #263a55;padding-top:12px}.score-guide summary{cursor:pointer;color:#cdd8e8;font-weight:900;font-size:13px}
  .score-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}.score-item{border:1px solid #263a55;border-radius:12px;padding:10px;background:#0b1523}
  .score-item strong{display:block;color:#fff;font-size:12px}.score-item span{display:block;margin-top:4px;color:#8095af;font-size:11px;line-height:1.5}.score-level{margin-top:12px;color:#9fb0c5;font-size:11px;line-height:1.7}
  @media(max-width:800px){.score-grid{grid-template-columns:repeat(2,1fr)}}`;
  const style=document.createElement('style');style.textContent=css;document.head.appendChild(style);
  const panel=[...document.querySelectorAll('.panel')][0]; if(!panel)return;
  const box=document.createElement('section');box.className='score-guide';
  box.innerHTML=`<h2>MODU 관심도 점수란?</h2><p><b style="color:#fff">매수 추천 점수가 아니라</b>, 전 거래일에 평소보다 얼마나 눈에 띄는 변화가 겹쳤는지를 0~100점으로 압축한 자체 지표입니다. 점수가 높을수록 거래량·거래대금·가격 추세·신고가 등 여러 신호가 동시에 강했다는 뜻입니다.</p><details><summary>점수 계산 기준 자세히 보기</summary><div class="score-grid"><div class="score-item"><strong>거래량 · 거래대금 비율</strong><span>최근 20일 평균보다 얼마나 늘었는지. 각각 최대 18점</span></div><div class="score-item"><strong>실제 거래대금</strong><span>비율만 높은 저유동성 종목을 걸러내기 위한 항목. 최대 18점</span></div><div class="score-item"><strong>당일 가격 강도</strong><span>전일 대비 상승 강도. 최대 10점</span></div><div class="score-item"><strong>5일 · 20일 추세</strong><span>단발성 급등보다 상승 흐름의 지속성을 확인. 합계 최대 16점</span></div><div class="score-item"><strong>신고가</strong><span>20·60·120일 신고가 중 가장 강한 조건 하나만 반영. 최대 12점</span></div><div class="score-item"><strong>시가총액 보조</strong><span>극소형주 쏠림을 완화하기 위한 안정성 보조점수. 최대 8점</span></div><div class="score-item"><strong>과열 패널티</strong><span>저유동성·과도한 당일 급등·높은 회전율·단기 과열은 점수 차감</span></div><div class="score-item"><strong>주목 TOP 통과조건</strong><span>55점 이상 + 거래대금 30억원 이상 + 수급·신고가·추세 중 강한 신호 필요</span></div></div><div class="score-level">해석 예시: 70점대 이상 = 여러 강한 신호가 겹친 종목 · 55~69점 = 주목 조건을 통과한 종목. 점수는 상승 확률이나 기대수익률을 의미하지 않으며 다음 거래일에 확인할 후보를 좁히기 위한 참고값입니다.</div></details>`;
  panel.parentNode.insertBefore(box,panel);
})();
