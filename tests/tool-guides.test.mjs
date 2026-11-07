import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';
import {applyToolGuide} from '../lib/tool-guides.mjs';

const root = new URL('../',import.meta.url);
const read = file=>fs.readFile(new URL(file,root),'utf8');

test('original guides replace generated filler without changing tool scripts or controls',async()=>{
  const guides=JSON.parse(await read('content/tool-guides.json'));
  for(const file of Object.keys(guides)) {
    const before=await read(file),after=applyToolGuide(before,file,guides);
    const scripts=html=>[...html.matchAll(/<script\b[^>]*>[\s\S]*?<\/script>/g)].map(m=>m[0]);
    const controls=html=>[...html.matchAll(/<(?:input|button|canvas|select)\b[^>]*>/g)].map(m=>m[0]);
    assert.deepEqual(scripts(after),scripts(before),file);
    assert.deepEqual(controls(after),controls(before),file);
    assert.equal(after.split('id="tool-guide"').length-1,1,file);
    assert.ok(!after.includes('<section class="detail-seo"'),file);
    assert.ok(!after.includes('실제 적용 금액은 제도 변경'),file);
    assert.throws(()=>applyToolGuide(before.replace('data-static-seo="1"',''),file,guides),/anchor/,file);
  }
});

// Run the real inline calculator scripts with a small DOM surface. These examples
// pin the promises made in the guides, including rounding and contribution timing.
async function calculator(file,values,entry='') {
  const elements=new Map();
  const get=id=>{
    if(!elements.has(id))elements.set(id,{value:String(values[id]??''),textContent:'',innerText:'',classList:{add(){},remove(){}},addEventListener(){}});
    return elements.get(id);
  };
  const document={getElementById:get};
  const context=vm.createContext({document,console,alert:message=>{throw new Error(message)}});
  const source=await read(file);
  for(const match of source.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)) {
    if(match[1].includes('document.getElementById'))vm.runInContext(match[1],context);
  }
  if(entry)vm.runInContext(entry,context);
  return get;
}

test('discount and reverse-percentage guide examples match the real calculator',async()=>{
  const get=await calculator('calculator/percent.html',{p1a:80000,p1b:15,p2a:68000,p2b:80000,p3a:80000,p3b:68000,p7target:68000,p7pct:85});
  assert.equal(get('p1r').textContent,'12,000');
  assert.equal(get('p2r').textContent,'85%');
  assert.equal(get('p3r').textContent,'-15%');
  assert.equal(get('p7r').textContent,'80,000');
});

test('area guide examples retain the documented conversion precision',async()=>{
  let get=await calculator('calculator/area.html',{m2Input:84},'convertFromM2()');
  assert.equal(get('pyeongInput').value,'25.41');
  get=await calculator('calculator/area.html',{pyeongInput:30},'convertFromPyeong()');
  assert.equal(get('m2Input').value,'99.17');
});

test('weighted-average examples and higher-price labels are correct',async()=>{
  let get=await calculator('calculator/average-price.html',{currentPrice:10000,currentQty:10,addPrice:8000,addQty:30},'calculateAverage()');
  assert.equal(get('finalAvgPrice').innerText,'8,500 원');
  assert.equal(get('displayGrandTotal').innerText,'340,000 원');
  assert.match(get('priceDiffNote').innerText,/인하$/);
  get=await calculator('calculator/average-price.html',{currentPrice:10000,currentQty:10,addPrice:12000,addQty:10},'calculateAverage()');
  assert.equal(get('finalAvgPrice').innerText,'11,000 원');
  assert.equal(get('priceDiffNote').innerText,'기존 대비 평단가 1,000원 (10%) 상승');
});

test('compound examples reflect monthly compounding and end-of-month contributions',async()=>{
  let get=await calculator('calculator/compound.html',{initPrincipal:1000000,monthlyContribution:0,annualReturn:12,investYears:1},'calculateCompound()');
  assert.equal(get('totalAsset').innerText,'1,126,825 원');
  get=await calculator('calculator/compound.html',{initPrincipal:0,monthlyContribution:100000,annualReturn:12,investYears:1},'calculateCompound()');
  assert.equal(get('totalAsset').innerText,'1,268,250 원');
  assert.equal(get('displayTotalPrincipal').innerText,'1,200,000 원');
});

test('net-return example includes both fees and the extra cost in its base',async()=>{
  const get=await calculator('calculator/stock-return.html',{buyPrice:10000,sellPrice:11000,qty:10,buyFee:0.1,sellFee:0.1,sellTax:0,extraCost:1000});
  assert.equal(get('profit').textContent,'8,790원');
  assert.equal(get('returnRate').textContent,'8.69%');
  assert.equal(get('breakEven').textContent,'10,120원');
});
