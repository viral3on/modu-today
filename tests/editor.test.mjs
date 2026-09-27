import test from 'node:test';
import assert from 'node:assert/strict';
import {createHandler} from '../api/editor.js';
import {markdown,validatePost} from '../lib/content.mjs';

const valid={title:'직접 써 본 기록',category:'생활',description:'생활에서 확인한 내용을 차근차근 기록한 글입니다.',image:'',imageAlt:'',tags:['기록'],body:'# 시작하기\n\n이 글은 테스트용 본문입니다. 실제 사용자에게 발행하지 않습니다. 입력과 저장의 흐름을 확인합니다.'};
const request=(body,headers={})=>({method:'POST',body,headers:{origin:'https://modu.today','content-type':'application/json',authorization:'Bearer github_pat_abcdefghijklmnopqrstuvwxyz',...headers}});
function response(){return {headers:{},setHeader(key,value){this.headers[key]=value;},status(code){this.code=code;return this;},json(value){this.data=value;}};}
function github({admin=true,existing=null,status=200}={}) {
  const calls=[];
  const fetcher=async(url,options)=>{
    calls.push({url,options});
    let data;
    if(url.endsWith('/repos/viral3on/modu-today'))data={permissions:{admin},archived:false};
    else if(url.endsWith('/user'))data={id:123};
    else if(options.method==='PUT')data={content:{sha:'new-sha'},commit:{sha:'commit-sha'}};
    else if(existing)data={sha:'old-sha',content:Buffer.from(JSON.stringify(existing)).toString('base64')};
    else return {ok:false,status:404};
    return {ok:status===200,status,json:async()=>data};
  };return {calls,fetcher};
}
test('unauthenticated, cross-origin and wrong-method requests never reach GitHub',async()=>{
  const gh=github();const handler=createHandler(gh.fetcher,{});
  for(const [req,code] of [[request({action:'verify'},{authorization:''}),401],[request({action:'publish'},{origin:'https://evil.example'}),403],[{...request({}),method:'GET'},405]]) {
    const res=response();await handler(req,res);assert.equal(res.code,code);assert.equal(res.headers['Cache-Control'],'private, no-store');
  }assert.equal(gh.calls.length,0);
});
test('non-admin cannot verify, load or publish',async()=>{
  const gh=github({admin:false});
  for(const action of ['verify','list','load','publish']){const res=response();await createHandler(gh.fetcher,{})(request({action,id:'article-123',post:valid}),res);assert.equal(res.code,403);}
  assert.ok(gh.calls.every(c=>!c.options.method));
});
test('publishing validates content and sets identity and dates server-side',async()=>{
  const gh=github(),res=response();await createHandler(gh.fetcher,{})(request({action:'publish',id:'article-123',post:{...valid,author:'untrusted',publishedAt:'1900-01-01',status:'draft'}}),res);
  assert.equal(res.code,200);assert.equal(res.data.deployment,'pending');
  const put=JSON.parse(gh.calls.find(c=>c.options.method==='PUT').options.body);
  const stored=JSON.parse(Buffer.from(put.content,'base64').toString('utf8'));
  assert.equal(stored.author,'MODU.TODAY 편집부');assert.equal(stored.status,'published');assert.equal(stored.id,'article-123');assert.equal(put.branch,'main');
  assert.notEqual(stored.publishedAt,'1900-01-01');assert.ok(!JSON.stringify(stored).includes('github_pat'));
});
test('stale revisions and duplicate IDs are rejected without overwriting',async()=>{
  const gh=github({existing:{...valid,id:'article-123'}}),res=response();
  await createHandler(gh.fetcher,{})(request({action:'publish',id:'article-123',sha:'stale',post:valid}),res);
  assert.equal(res.code,409);assert.ok(!gh.calls.some(c=>c.options.method==='PUT'));
});
test('editing retains original publication date and updates modified date',async()=>{
  const old={...valid,id:'article-123',publishedAt:'2020-01-02T00:00:00Z',createdAt:'2020-01-01T00:00:00Z'};
  const gh=github({existing:old}),res=response();await createHandler(gh.fetcher,{})(request({action:'publish',id:old.id,sha:'old-sha',post:valid}),res);
  assert.equal(res.code,200);assert.equal(res.data.post.publishedAt,old.publishedAt);assert.equal(res.data.post.createdAt,old.createdAt);assert.notEqual(res.data.post.updatedAt,old.publishedAt);
});
test('preview writes only into its own Git branch',async()=>{
  const gh=github(),res=response();await createHandler(gh.fetcher,{VERCEL_ENV:'preview',VERCEL_GIT_COMMIT_REF:'feature/editor',VERCEL_URL:'preview.example'})(request({action:'publish',id:'article-123',post:valid},{origin:'https://preview.example'}),res);
  assert.equal(res.code,200);assert.equal(JSON.parse(gh.calls.find(c=>c.options.method==='PUT').options.body).branch,'feature/editor');
});
test('path traversal and oversized body are rejected',async()=>{
  for(const data of [{action:'publish',id:'../../root',post:valid},{action:'publish',id:'article-123',post:{...valid,body:'a'.repeat(100001)}}]) {
    const gh=github(),res=response();await createHandler(gh.fetcher,{})(request(data),res);assert.equal(res.code,400);assert.ok(!gh.calls.some(c=>c.options.method==='PUT'));
  }
});
test('HTML and malicious URLs cannot execute in renderer',()=>{
  const output=markdown('<script>alert(1)</script>\n\n[bad](javascript:alert)\n\n[good](https://example.com)\n\n**strong**');
  assert.ok(!output.includes('<script>'));assert.ok(!output.includes('href="javascript'));assert.ok(output.includes('href="https://example.com/"'));assert.ok(output.includes('<strong>strong</strong>'));
  for(const image of ['javascript:alert(1)','data:image/svg+xml,<svg>','//evil.example/image.png','/\\evil.example'])assert.throws(()=>validatePost({...valid,image,imageAlt:'test'}));
});
test('invalid GitHub credentials do not leak upstream errors or token',async()=>{
  const gh=github({status:401}),res=response();await createHandler(gh.fetcher,{})(request({action:'verify'}),res);assert.equal(res.code,401);assert.ok(!JSON.stringify(res.data).includes('github_pat'));
});
