// Local-only test fixture: uses the real API handler; only GitHub and Blob are faked.
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHandler} from '../../api/editor.js';
import {MAX_IMAGE_REQUEST_BYTES} from '../../lib/image-policy.mjs';
const root=fileURLToPath(new URL('../../public/',import.meta.url));
const blobs=new Map(),posts=new Map();
let failNext=false,uploads=0;
const github=async(url,options)=>{
  const data=url.endsWith('/user')?{id:987654}:url.endsWith('/repos/viral3on/modu-today')?{permissions:{admin:true}}:null;
  if(data)return {ok:true,status:200,json:async()=>data};
  const id=/\/posts\/([^/?]+)\.json/.exec(url)?.[1];
  if(options.method==='PUT'){
    const input=JSON.parse(options.body), post=JSON.parse(Buffer.from(input.content,'base64'));
    posts.set(id,post);return {ok:true,status:200,json:async()=>({content:{sha:'test-sha'},commit:{sha:'test-commit'}})};
  }
  if(!id)return {ok:true,status:200,json:async()=>[...posts.keys()].map(id=>({type:'file',name:id+'.json'}))};
  if(posts.has(id))return {ok:true,status:200,json:async()=>({sha:'test-sha',content:Buffer.from(JSON.stringify(posts.get(id))).toString('base64')})};
  return {ok:false,status:404};
};
const handler=createHandler(github,{MODU_IMAGE_BLOB_READ_WRITE_TOKEN:'test-only',VERCEL_ENV:'development'},async(name,bytes,options)=>{
  uploads++;await new Promise(resolve=>setTimeout(resolve,180));
  if(failNext){failNext=false;throw new Error('Simulated storage error');}
  blobs.set(name,{bytes,type:options.contentType});
  return {url:`https://teststore.public.blob.vercel-storage.com/${name}`};
});
const types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.mjs':'text/javascript','.png':'image/png','.json':'application/json'};
http.createServer(async(req,res)=>{
  const url=new URL(req.url,'http://127.0.0.1:4173');
  const json=(code,data)=>{res.writeHead(code,{'Content-Type':'application/json'});res.end(JSON.stringify(data));};
  if(url.pathname==='/_test/fail-next'){failNext=true;return json(200,{ok:true});}
  if(url.pathname==='/_test/state')return json(200,{uploads,posts:[...posts.values()]});
  if(url.pathname.startsWith('/_test/blob/')){
    const blob=blobs.get(url.pathname.slice('/_test/blob/'.length));if(!blob)return json(404,{});
    res.writeHead(200,{'Content-Type':blob.type});return res.end(blob.bytes);
  }
  if(url.pathname==='/api/editor'){
    const chunks=[];let length=0;
    for await(const chunk of req){length+=chunk.length;if(length>MAX_IMAGE_REQUEST_BYTES)return json(413,{error:'Too large'});chunks.push(chunk);}
    req.body=Buffer.concat(chunks).toString();res.status=code=>{res.statusCode=code;return res;};res.json=data=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(data));};return handler(req,res);
  }
  const id=/^\/reading\/([^/]+)\/$/.exec(url.pathname)?.[1];
  if(id&&posts.has(id)){res.writeHead(200,{'Content-Type':'text/html'});return res.end(`<meta content="${posts.get(id).updatedAt}">`);}
  if(url.pathname==='/_vercel/insights/script.js'){res.writeHead(200,{'Content-Type':'text/javascript'});return res.end('');}
  try{
    const relative=decodeURIComponent(url.pathname)+(url.pathname.endsWith('/')?'index.html':'');
    const file=path.resolve(root,'.'+relative);if(!file.startsWith(path.resolve(root)+path.sep))throw new Error();
    const bytes=await fs.readFile(file);
    const headers={'Content-Type':types[path.extname(file)]||'application/octet-stream'};
    if(url.pathname.startsWith('/admin'))headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' https:; frame-src 'self' about:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'";
    res.writeHead(200,headers);res.end(bytes);
  }catch{json(404,{error:'Not found'});}
}).listen(4173,'127.0.0.1',()=>console.log('Image upload test fixture on http://127.0.0.1:4173'));
