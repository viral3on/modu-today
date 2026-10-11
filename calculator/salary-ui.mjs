import {calculateSalary} from './salary-model.mjs';
const byId = id => document.getElementById(id);
const inputs = ['annualSalary','nonTaxable','incomeTaxInput'];
const readMoney = id => {
  const raw = byId(id).value.trim();
  if (!/^(?:\d+|\d{1,3}(?:,\d{3})+)$/.test(raw)) return NaN;
  return Number(raw.replaceAll(',',''));
};
for (const id of inputs) byId(id).addEventListener('blur',()=>{
  const value=readMoney(id);
  if (Number.isSafeInteger(value)) byId(id).value=value.toLocaleString('ko-KR');
});
byId('salaryForm').addEventListener('input',()=>{byId('resultBox').classList.add('hidden');byId('salaryError').textContent='';});
byId('salaryForm').addEventListener('submit',event=>{
  event.preventDefault();
  try {
    const result=calculateSalary({annualSalary:readMoney('annualSalary'),nonTaxable:readMoney('nonTaxable'),period:byId('period').value,incomeTax:byId('incomeTaxInput').value.trim()===''?null:readMoney('incomeTaxInput')});
    for (const id of ['grossMonthly','nps','nhic','lti','ei','incomeTax','localTax','totalDeduction']) byId(id).textContent=result[id]===null?'미입력 · 공제 제외':`${result[id].toLocaleString('ko-KR')} 원`;
    byId('netPayMonthly').textContent=`${result.netPay.toLocaleString('ko-KR')} 원`;
    byId('resultLabel').textContent=result.taxIncluded?'입력한 소득세를 반영한 월 예상 실수령액':'보험료 공제 후 금액 · 소득세 공제 전';
    byId('resultNote').textContent=result.taxIncluded?'입력 세액과 지방소득세 10%를 반영했습니다. 회사의 보험 신고 기준·정산·기타 공제에 따라 실제 입금액은 달라질 수 있습니다.':'소득세가 빠지지 않은 금액입니다. 실수령액을 보려면 급여명세서 또는 홈택스에서 확인한 월 근로소득세를 입력하세요.';
    byId('salaryError').textContent='';
    byId('resultBox').classList.remove('hidden');
  } catch(error) {
    byId('resultBox').classList.add('hidden');
    byId('salaryError').textContent=error.message;
  }
});
