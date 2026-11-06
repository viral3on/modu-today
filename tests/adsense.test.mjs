import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';
import {createHash} from 'node:crypto';
import {adsEnabled, applyAdsense, ADSENSE_CLIENT, ADSENSE_URL, ADS_TXT, READING_BOOTSTRAP, READING_HASH, READING_CSP, validateAdsenseConfig} from '../lib/adsense.mjs';

test('monetization is limited to published content and working tools',()=>{
  for(const file of ['index.html','reading/index.html','reading/new-post/index.html','calculator/loan.html','apt/index.html','lotto/draw/1234/index.html','games/2048.html','youtube/index.html','tools/index.html'])assert.equal(adsEnabled(file),true,file);
  for(const file of ['404.html','admin/index.html','admin/preview.html','news/index.html','stock/index.html','stock/guide/index.html','privacy/index.html','terms/index.html','about/index.html','contact/index.html','yasun.html','skhynix-split-analysis.html','googleverify.html'])assert.equal(adsEnabled(file),false,file);
});

test('existing single- or multiline ad tags are normalized and never duplicated',()=>{
  const original=`<html><head><meta content="old" name="google-adsense-account"><script async\n src="${ADSENSE_URL}" crossorigin="anonymous"></script><script src="${ADSENSE_URL}"></script></head><body><script src="/calculator/calculator.js"></script></body></html>`;
  const normalized=applyAdsense(original,'calculator/loan.html');
  assert.equal(normalized.split(ADSENSE_URL).length-1,1);
  assert.equal(normalized.split('name="google-adsense-account"').length-1,1);
  assert.ok(normalized.includes(ADSENSE_CLIENT));
  assert.ok(normalized.includes('/calculator/calculator.js'));
  assert.equal(applyAdsense(normalized,'calculator/loan.html'),normalized);
  assert.ok(!applyAdsense(original,'admin/index.html').includes('adsbygoogle'));
});

test('reading bootstrap and enforced policy stay in sync; mismatched publisher fails closed',async()=>{
  const config=JSON.parse(await fs.readFile(new URL('../vercel.json',import.meta.url),'utf8'));
  const ads=await fs.readFile(new URL('../ads.txt',import.meta.url),'utf8');
  validateAdsenseConfig(config,ads);
  assert.equal(READING_HASH,`sha256-${createHash('sha256').update(READING_BOOTSTRAP).digest('base64')}`);
  assert.ok(READING_CSP.includes(`'${READING_HASH}' 'strict-dynamic'`));
  assert.ok(!READING_CSP.includes("'unsafe-inline'"));
  assert.throws(()=>validateAdsenseConfig({headers:[]},ADS_TXT),/CSP/);
  assert.throws(()=>validateAdsenseConfig(config,'google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0'),/publisher/);
  const admin=config.headers.find(rule=>rule.source==='/admin(.*)').headers.find(h=>h.key==='Content-Security-Policy').value;
  assert.ok(admin.includes("script-src 'self'"));assert.ok(!admin.includes('unsafe-eval'));
});

test('reading keeps one trusted bootstrap and loads local scripts through it',()=>{
  const html='<html><head></head><body><script type="module" src="/assets/reading.js"></script><script defer src="/_vercel/insights/script.js"></script></body></html>';
  const output=applyAdsense(html,'reading/index.html');
  assert.equal(output.split('data-modu-reading-bootstrap').length-1,1);
  assert.ok(!output.includes('src="/assets/reading.js"'));
  assert.ok(!output.includes('src="/_vercel/insights/script.js"'));
  assert.equal(applyAdsense(output,'reading/index.html'),output);
});

test('bootstrap starts ads immediately and waits for DOM before search and analytics',()=>{
  for(const hasSearch of [false,true]) {
    const appended=[],callbacks=[];
    const document={readyState:'loading',head:{appendChild:node=>appended.push(node)},createElement:tag=>({tag}),getElementById:id=>hasSearch&&id==='reading-query'?{}:null,addEventListener:(event,callback,options)=>callbacks.push({event,callback,options})};
    vm.runInNewContext(READING_BOOTSTRAP,{document});
    assert.equal(appended.length,1);assert.equal(appended[0].src,ADSENSE_URL);assert.equal(appended[0].async,true);assert.equal(appended[0].crossOrigin,'anonymous');
    assert.equal(callbacks[0].event,'DOMContentLoaded');assert.equal(callbacks[0].options.once,true);
    callbacks[0].callback();
    assert.equal(appended.filter(s=>s.src===ADSENSE_URL).length,1);
    assert.equal(appended.filter(s=>s.src==='/assets/reading.js'&&s.type==='module').length,Number(hasSearch));
    assert.equal(appended.filter(s=>s.src==='/_vercel/insights/script.js').length,1);
  }
});
