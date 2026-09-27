import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {ROOT,build} from './build.mjs';
import handler from '../api/editor.js';
await build();
const root=path.join(ROOT,'public');
const types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.png':'image/png','.svg':'image/svg+xml','.xml':'application/xml','.txt':'text/plain'};
http.createServer(async(req,res)=>{
  const url=new URL(req.url,'http://localhost:4173');
  if(url.pathname==='/api/editor') {
    let raw='';for await (const chunk of req){raw+=chunk;if(raw.length>450000){res.writeHead(413);res.end();return;}}
    req.body=raw;res.status=code=>{res.statusCode=code;return res;};res.json=data=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(data));};return handler(req,res);
  }
  if(url.pathname==='/_vercel/insights/script.js'){res.writeHead(200,{'Content-Type':'text/javascript'});res.end('');return;}
  try {
    let relative=decodeURIComponent(url.pathname);if(relative.endsWith('/'))relative+='index.html';
    const file=path.resolve(root,'.'+relative);if(!file.startsWith(root+path.sep))throw new Error();
    const body=await fs.readFile(file);res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream'});res.end(body);
  }catch{res.writeHead(404,{'Content-Type':'text/html; charset=utf-8'});res.end(await fs.readFile(path.join(root,'404.html')));}
}).listen(4173,'127.0.0.1',()=>console.log('MODU preview: http://127.0.0.1:4173'));
