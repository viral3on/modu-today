import test from 'node:test';
import assert from 'node:assert/strict';
import {createHandler} from '../api/editor.js';
import {decodeImage, storeImage} from '../lib/image-upload.mjs';
import {MAX_IMAGE_BYTES, MAX_IMAGE_REQUEST_BYTES, validateImageFile} from '../lib/image-policy.mjs';
import {markdown, articleBody} from '../lib/content.mjs';

const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aP2kAAAAASUVORK5CYII=', 'base64');
const valid={action:'uploadImage',name:'photo.png',type:'image/png',data:png.toString('base64')};
const env={MODU_IMAGE_BLOB_READ_WRITE_TOKEN:'private-test-blob-token',VERCEL_ENV:'production'};
const request=(body=valid,headers={})=>({method:'POST',body,headers:{origin:'https://modu.today','content-type':'application/json',authorization:'Bearer github_pat_abcdefghijklmnopqrstuvwxyz',...headers}});
const response=()=>({headers:{},setHeader(k,v){this.headers[k]=v;},status(code){this.code=code;return this;},json(data){this.data=data;}});
function fixture({admin=true,status=200,environment=env,fail=false}={}) {
  const writes=[],calls=[];
  const fetcher=async(url,options)=>{calls.push({url,options});return {ok:status===200,status,json:async()=>url.endsWith('/user')?{id:123}:{permissions:{admin},archived:false}};};
  const put=async(path,bytes,options)=>{writes.push({path,bytes,options});if(fail)throw new Error('SECRET-UPSTREAM-DETAIL');return {url:`https://teststore.public.blob.vercel-storage.com/${path}`};};
  return {writes,calls,handler:createHandler(fetcher,environment,put)};
}

test('authenticated image upload writes only to Blob and returns usable URL without secrets',async()=>{
  const f=fixture(),res=response();await f.handler(request(),res);
  assert.equal(res.code,200);assert.equal(f.writes.length,1);assert.deepEqual(f.writes[0].bytes,png);
  assert.match(f.writes[0].path,/^modu-today\/images\/production\/[a-f0-9-]+\.png$/);
  assert.equal(f.writes[0].options.access,'public');assert.equal(f.writes[0].options.allowOverwrite,false);
  assert.equal(f.writes[0].options.token,env.MODU_IMAGE_BLOB_READ_WRITE_TOKEN);
  assert.equal(res.data.contentType,'image/png');assert.equal(res.data.size,png.length);
  assert.ok(f.calls.every(c=>!c.options.method));assert.ok(!JSON.stringify(res.data).includes('token'));
  assert.equal(res.headers['Cache-Control'],'private, no-store');
});

test('upload checks origin, method, authentication and repository admin on every request',async()=>{
  for(const [req,options,expected] of [
    [request(valid,{origin:'https://evil.example'}),{},403],
    [request(valid,{authorization:''}),{},401],
    [{...request(),method:'GET'},{},405],
    [request(),{admin:false},403],
    [request(),{status:401},401],
    [request(),{status:403},403],
  ]) {
    const f=fixture(options),res=response();await f.handler(req,res);
    assert.equal(res.code,expected);assert.equal(f.writes.length,0);
  }
});

test('extension, MIME, byte signature, empty data and invalid base64 are all rejected',async()=>{
  for(const body of [
    {...valid,name:'a.svg',type:'image/svg+xml'}, {...valid,name:'a.jpg'},
    {...valid,type:'image/webp'}, {...valid,data:''}, {...valid,data:'%%%invalid'},
    {...valid,data:Buffer.from('<html>not an image</html>').toString('base64')},
    {...valid,data:Buffer.alloc(MAX_IMAGE_BYTES+1).toString('base64')}
  ]) {
    const f=fixture(),res=response();await f.handler(request(body),res);
    assert.equal(res.code,400);assert.equal(f.writes.length,0);
  }
  assert.throws(()=>validateImageFile({name:'image.png',type:'image/png',size:0}));
  assert.throws(()=>validateImageFile({name:'image.png',type:'image/png',size:MAX_IMAGE_BYTES+1}));
});

test('3MB binary fits the Vercel request limit, oversized bodies and malformed JSON fail cleanly',async()=>{
  const bytes=Buffer.alloc(MAX_IMAGE_BYTES);png.copy(bytes);
  const body={...valid,data:bytes.toString('base64')};
  assert.ok(Buffer.byteLength(JSON.stringify(body))<4_500_000);
  const f=fixture(),res=response();await f.handler(request(body),res);assert.equal(res.code,200);
  for(const req of [request(valid,{'content-length':MAX_IMAGE_REQUEST_BYTES+1}),request('x'.repeat(MAX_IMAGE_REQUEST_BYTES+1))]) {
    const f=fixture(),res=response();await f.handler(req,res);assert.equal(res.code,413);assert.equal(f.writes.length,0);
  }
  const malformed=response();await f.handler(request('{bad JSON'),malformed);assert.equal(malformed.code,400);
  const originalLimit=response();await f.handler(request({action:'publish',post:{body:'a'.repeat(150001)}}),originalLimit);assert.equal(originalLimit.code,400);
});

test('JPEG and WebP signatures match their declared types',()=>{
  for(const [name,type,bytes] of [['test.jpg','image/jpeg',Buffer.from([255,216,255,224,0,0])],['test.webp','image/webp',Buffer.from('RIFF0000WEBPVP8 ')]])
    assert.deepEqual(decodeImage({name,type,data:bytes.toString('base64')}),bytes);
});

test('missing storage and Blob errors preserve actionable errors without leaking credentials',async()=>{
  for(const [options,code,message] of [[{environment:{}},503,/연결되지/],[{fail:true},502,/업로드에 실패/]]) {
    const f=fixture(options),res=response();await f.handler(request(),res);
    assert.equal(res.code,code);assert.match(res.data.error,message);assert.ok(!JSON.stringify(res.data).includes('SECRET'));
  }
});

test('dedicated token wins and production, preview and development use distinct prefixes',async()=>{
  for(const scope of ['production','preview','development']) {
    const f=fixture({environment:{...env,VERCEL_ENV:scope,BLOB_READ_WRITE_TOKEN:'other-token'}}),res=response();
    await f.handler(request(),res);assert.equal(res.code,200);assert.ok(f.writes[0].path.includes(`/images/${scope}/`));
    assert.equal(f.writes[0].options.token,env.MODU_IMAGE_BLOB_READ_WRITE_TOKEN);
  }
  const f=fixture({environment:{BLOB_READ_WRITE_TOKEN:'fallback-token'}}),res=response();await f.handler(request(),res);
  assert.equal(res.code,200);assert.equal(f.writes[0].options.token,'fallback-token');
});

test('storage uses unique paths and rejects unexpected non-Blob response URLs',async()=>{
  const f=fixture();for(let i=0;i<2;i++)await f.handler(request(),response());
  assert.notEqual(f.writes[0].path,f.writes[1].path);
  await assert.rejects(storeImage(valid,env,async()=>({url:'javascript:alert(1)'})),/업로드에 실패/);
});

test('uploaded images render safely in both modes and in the existing preview renderer',()=>{
  const url='https://teststore.public.blob.vercel-storage.com/photo.png';
  const output=markdown(`Before\n\n![image & caption](${url})\n\nAfter`);
  assert.ok(output.includes(`<img src="${url}" alt="image &amp; caption" loading="lazy"`));
  assert.ok(output.includes('<p>Before</p>'));assert.ok(output.includes('<p>After</p>'));
  assert.ok(!markdown('![bad](javascript:alert(1))').includes('<img'));
  assert.ok(!markdown('```\n![code](https://example.com/a.png)\n```').includes('<img'));
  assert.ok(!markdown('<img src="https://example.com/a.png" onerror="alert(1)">').includes('<img'));
  assert.ok(articleBody({format:'html',body:`<p>Text</p><img src="${url}" alt="image" loading="lazy">`,image:''}).includes(`<img src="${url}"`));
});
