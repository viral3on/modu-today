// Employee estimates for 2026. Sources and limitations are displayed on salary.html.
const cut10 = value => Math.floor(value / 10) * 10;
export function calculateSalary({annualSalary, nonTaxable = 0, period = '2026-07', incomeTax = null}) {
  if (!Number.isSafeInteger(annualSalary) || annualSalary <= 0 || annualSalary > 12000000000) throw new Error('연봉은 1원부터 120억원까지 정수로 입력해 주세요.');
  const grossMonthly = Math.floor(annualSalary / 12);
  if (!Number.isSafeInteger(nonTaxable) || nonTaxable < 0 || nonTaxable >= grossMonthly) throw new Error('월 비과세액은 0원 이상, 세전 월 급여보다 작게 입력해 주세요.');
  if (!['2026-01','2026-07'].includes(period)) throw new Error('2026년 적용 기간을 선택해 주세요.');
  if (incomeTax !== null && (!Number.isSafeInteger(incomeTax) || incomeTax < 0)) throw new Error('월 근로소득세를 0원 이상의 정수로 입력해 주세요.');
  const taxable = grossMonthly - nonTaxable;
  const [lower,upper] = period === '2026-01' ? [400000,6370000] : [410000,6590000];
  const pensionBase = Math.min(upper,Math.max(lower,Math.floor(taxable/1000)*1000));
  const nps = cut10(pensionBase * 475 / 10000);
  const nhic = cut10(Math.min(4591740,Math.max(10080,taxable*3595/100000)));
  const lti = cut10(nhic * 9448 / 71900);
  const ei = cut10(taxable * 9 / 1000);
  const insurance = nps + nhic + lti + ei;
  const localTax = incomeTax === null ? null : cut10(incomeTax / 10);
  const totalDeduction = insurance + (incomeTax ?? 0) + (localTax ?? 0);
  if (totalDeduction > grossMonthly) throw new Error('공제액이 월 급여보다 큽니다. 세액·급여와 가입 조건을 확인해 주세요.');
  return {grossMonthly,taxable,pensionBase,nps,nhic,lti,ei,insurance,incomeTax,localTax,totalDeduction,netPay:grossMonthly-totalDeduction,taxIncluded:incomeTax!==null};
}
