import test from 'node:test';
import assert from 'node:assert/strict';
import {calculateSalary} from '../calculator/salary-model.mjs';

test('2026 salary example distinguishes missing income tax from confirmed zero',()=>{
  const input={annualSalary:36000000,nonTaxable:200000};
  const result=calculateSalary(input);
  assert.equal(result.nps,133000);
  assert.equal(result.nhic,100660);
  assert.equal(result.lti,13220);
  assert.equal(result.ei,25200);
  assert.equal(result.netPay,2727920);
  assert.equal(result.taxIncluded,false);
  assert.equal(result.incomeTax,null);
  const taxed=calculateSalary({...input,incomeTax:50000});
  assert.equal(taxed.netPay,2672920);
  assert.equal(taxed.localTax,5000);
  assert.equal(taxed.taxIncluded,true);
  assert.equal(calculateSalary({...input,incomeTax:0}).taxIncluded,true);
});
test('pension bounds switch in July and income is truncated to thousands',()=>{
  assert.equal(calculateSalary({annualSalary:120000000,period:'2026-01'}).nps,302570);
  assert.equal(calculateSalary({annualSalary:120000000}).nps,313020);
  assert.equal(calculateSalary({annualSalary:3600000,period:'2026-01'}).nps,19000);
  assert.equal(calculateSalary({annualSalary:3600000}).nps,19470);
  assert.equal(calculateSalary({annualSalary:50000000,nonTaxable:200000}).pensionBase,3966000);
});
test('health insurance employee floor and cap are bounded',()=>{
  assert.equal(calculateSalary({annualSalary:2400000}).nhic,10080);
  assert.equal(calculateSalary({annualSalary:2400000000}).nhic,4591740);
});
test('invalid values cannot return misleading take-home pay',()=>{
  for (const input of [{annualSalary:NaN},{annualSalary:Infinity},{annualSalary:-100},
    {annualSalary:36000000,nonTaxable:3000000},{annualSalary:36000000,nonTaxable:-1},
    {annualSalary:36000000,incomeTax:-1},{annualSalary:36000000,incomeTax:3000000},
    {annualSalary:36000000,period:'2027-01'}]) assert.throws(()=>calculateSalary(input));
});
