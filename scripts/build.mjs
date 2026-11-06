import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {rollup} from 'rollup';
import {nodeResolve} from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import replace from '@rollup/plugin-replace';
import {ID, SITE, validatePost, escape as e} from '../lib/content.mjs';
import {header, page, home, reading, article, toolsPage, newsPage} from '../lib/site.mjs';
import {applyAdsense, validateAdsenseConfig} from '../lib/adsense.mjs';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ALLOWED = new Set(['.html','.css','.js','.mjs','.json','.png','.jpg','.jpeg','.webp','.gif','.svg','.ico','.woff','.woff2','.txt']);
export async function build(root=ROOT, output=path.join(root,'public')) {
  // Only the generated output inside this checkout may be replaced.
  if(path.resolve(output)!==path.join(path.resolve(root),'public')) throw new Error('Unsafe output directory');
  validateAdsenseConfig(JSON.parse(await fs.readFile(path.join(root,'vercel.json'),'utf8')),await fs.readFile(path.join(root,'ads.txt'),'utf8'));
  await fs.rm(output,{recursive:true,force:true}); await fs.mkdir(output,{recursive:true});
  const write=async(rel,text)=>{const target=path.join(output,rel);await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target,rel.endsWith('.html')?applyAdsense(String(text),rel.replaceAll(path.sep,'/')):text);};
  const copy=async(rel)=>{
    const entries=await fs.readdir(path.join(root,rel),{withFileTypes:true});
    for(const entry of entries) {
      if(entry.name.startsWith('.') || entry.name==='__pycache__')continue;
      const sub=path.join(rel,entry.name);
      if(entry.isDirectory()) await copy(sub);
      else if(ALLOWED.has(path.extname(entry.name))) {
        if(entry.name.endsWith('.html') && !rel.startsWith('admin')) {
          let html=await fs.readFile(path.join(root,sub),'utf8');
          // Keep reading guidance outside the generated market-data summary.
          if(sub.replaceAll(path.sep,'/')==='apt/index.html') {
            html=html.replace('<section class="dashboard">',`<aside class="info" aria-label="�ŷ� �� �ȳ�"><div><strong>����� ���ϱ� ����</strong><p>�˻� ������� ���������� �ٸ� �ŷ��� �Բ� ���Ե� �� �ֽ��ϴ�. �귣������� ã�Ҵٸ� ������ �������� Ȯ���ϼ���. �ŷ� ����� �ִ� 300���̸� ����� ���� �˻� ������ ��ü ����� �������� �մϴ�.</p><a href="/reading/6f88af15-31a0-4c06-9009-fc63f1a7ac18/">��ա��߾Ӱ��� ����ϴ� �ǰŷ� �� ���� ��</a></div></aside><section class="dashboard">`);
          }
          // Preserve all application scripts, input IDs and data sources.
          html=html.replace(/class="topbar"/,'class="topbar modu-legacy-nav"')
            .replace(/<(div|nav) class="modu-nav">/,'<$1 class="modu-nav modu-legacy-nav">')
            .replace(/class="top"(?=><a class="brand")/,'class="top modu-legacy-nav"');
          html=html.replace(/<a\b[^>]*href=["']\/stock\/(?:guide\/)?["'][^>]*>.*?<\/a>/gs,'');
          html=html.replace('</head>','<link rel="stylesheet" href="/assets/nav.css"></head>');
          html=html.replace(/(<body\b[^>]*>)/,`$1${header(rel.startsWith('apt')?'/apt/':rel.startsWith('lotto')?'/lotto/':rel.startsWith('youtube')?'/youtube/':'/tools/')}`);
          if(!html.includes('id="main-content"')) html=html.replace('<main','<main id="main-content"');
          await write(sub,html);
        } else await write(sub,await fs.readFile(path.join(root,sub)));
      }
    }
  };
  for(const dir of ['apt','lotto','calculator','games','youtube','assets','admin']) await copy(dir);
  const browserContent=await rollup({input:path.join(root,'lib/content.mjs'),plugins:[nodeResolve({browser:true,modulePaths:[path.join(ROOT,'node_modules')]}),commonjs(),replace({preventAssignment:true,'process.env.NODE_ENV':JSON.stringify('production')})]});
  try {
    const {output}=await browserContent.generate({format:'es'});
    await write('assets/content.mjs',output[0].code);
  } finally {await browserContent.close();}
  for(const entry of await fs.readdir(root)) {
    if(/^(google|naver).*\.html$/.test(entry)||entry==='ads.txt') await write(entry,await fs.readFile(path.join(root,entry)));
  }
  // Legacy URLs remain reachable as dated, ad-free educational guides.
  for(const filename of ['yasun.html','skhynix-split-analysis.html']) {
    const html=await fs.readFile(path.join(root,filename),'utf8');
    if(/adsbygoogle|googlesyndication/i.test(html))throw new Error(`Unexpected ad code in legacy guide: ${filename}`);
    const body=html.match(/<article\b[^>]*>([\s\S]*?)<\/article>/)?.[1];
    // The analytics workflow may append scripts outside the article. The shared page adds analytics once.
    if(body && /<iframe|<script/i.test(body))throw new Error(`Unexpected embedded script in legacy guide: ${filename}`);
    const title=html.match(/<h1>(.*?)<\/h1>/)?.[1];
    const description=html.match(/<meta name="description" content="([^"]*)"/)?.[1];
    if(!body||!title||!description)throw new Error(`Missing legacy guide content: ${filename}`);
    await write(filename,page({title,description,path:`/${filename}`,noindex:true,body:`<article class="info-article">${body}</article>`}));
  }
  const posts=[];
  for(const filename of await fs.readdir(path.join(root,'content/posts'))) {
    if(!filename.endsWith('.json'))continue;
    const post=JSON.parse(await fs.readFile(path.join(root,'content/posts',filename),'utf8'));
    // Fail closed: private drafts must never be copied into a deployment.
    if(post.status!=='published')continue;
    validatePost(post);
    if(!ID.test(post.id)||filename!==`${post.id}.json`)throw new Error('Invalid article path');
    for(const date of [post.publishedAt,post.updatedAt,post.createdAt])if(!date||Number.isNaN(Date.parse(date)))throw new Error('Invalid article date');
    posts.push(post);
  }
  posts.sort((a,b)=>b.publishedAt.localeCompare(a.publishedAt));
  const news=JSON.parse(await fs.readFile(path.join(root,'news/data.json'),'utf8'));
  const lotto=JSON.parse(await fs.readFile(path.join(root,'lotto/data/results.json'),'utf8')).latest;
  await write('index.html',home(posts,news,lotto));
  await write('reading/index.html',reading(posts));
  await write('tools/index.html',toolsPage());
  await write('news/index.html',newsPage(news));
  for(const post of posts)await write(`reading/${post.id}/index.html`,article(post));
  const about=`<h1>�ϻ��� �а�, ��Ȱ�� �� �����ϰ�</h1><p>MODU.TODAY�� �ϻ󿡼� ����� �ñ����� ���� Ȯ���ϰ� �����ϴ� �����Ÿ��� ���� ���� ��Ȱ ������ �Բ� �����ϴ� �����Դϴ�. ��Ȱ��IT���ڵ������ε��ꡤ�������ֽġ���� �� ������ ��踦 ���� �ʽ��ϴ�.</p><h2>�����Ÿ��� ����� ����</h2><p>���� �ۼ��� ������ ����, �� ������ ����ϴ�. �ܺ� �ڷḦ �ο��� ���� ��ó�� Ȯ�� ������ ������, Ȯ�ε� ��ǰ� �ǰ��� �����մϴ�. �ܺ� ��� ������ �Ű� ���̰ų� �ڵ����� �뷮 ������ ���� �������� �ʽ��ϴ�.</p><p>�۸��� �ۼ��ϰ� �������� ǥ���մϴ�. ������ �߸��Ǿ��ų� �޶����ٸ� ���� ä�η� �˷��ּ���. Ȯ�� �� ������ �����ϰ� �ʿ��� ��� ���� ������ ������ ����ϴ�.</p><h2>��Ȱ�� �ٷ� ���� ����</h2><h3><a href="/apt/">����Ʈ �ǰŷ���</a></h3><p>���䱳��� ���� �ڷḦ �������� ������������ �Ű� �ŷ��� ã�� �� �ֽ��ϴ�. �����������ŷ����� �Բ� ���ϰ�, �Ű� ��������������� ���� ���ɼ��� �����ϼ���.</p><h3><a href="/lotto/">�ζ� ��÷����</a></h3><p>���ູ�� ���� ����� �������� ��÷��ȣ, ȸ���� ���, ��÷������ �Ǹ��� ������ �����մϴ�. ��ȣ ������ �������̸� ��÷�� �����ϰų� Ȯ���� ������ �ʽ��ϴ�. ���� ����� ���ູ�� ���� ��ǥ�� Ȯ���ϼ���.</p><h3><a href="/tools/">����� ��Ÿ ����</a></h3><p>��Ȱ ����, ������, YouTube ��ȸ�� ��ȭ�� �����մϴ�. ��� ����� �� ������ ǥ���� ������ ���� �������̸�, YouTube ������ ���� ����� ���������� ���� ��ü ������ �ƴմϴ�.</p><h2>��ü �۰� �ܺ� ������ ����</h2><p><a href="/reading/">�����Ÿ�</a>�� ����Ʈ�� ���� �ۼ��� �������Դϴ�. <a href="/news/">����</a>�� �ܺ� ����� ����� ���� ��ũ�� �ڵ� �����ϴ� ���� ����̸� ���������� ������ ��簡 �ƴմϴ�.</p><h2>�ۼ� å�Ӱ� �ڷ� Ȯ��</h2><p>��ü ���� MODU.TODAY ������ ���Ƿ� �����ϸ�, ���뿡 ���� ���ǿ� ���� ��û�� ��ڰ� �޽��ϴ�. �ܺ� �������� ���並 ���� ������ ǥ������ �ʽ��ϴ�. ���� �غ� ����, �������� ��ǥ, �������� �ؼ�, ������ ���� ������ �������� �����մϴ�.</p><p>���尡�ݡ���ǰ ���ó�� �ٲ�� ������ �ڷ� �����ϰ� ���� ��ũ�� Ȯ���� �ּ���. �ۼ��ϰ� �������� �ٸ� �ǹ��̸�, ���� �����Ǿ��ٰ� ��� ��ġ�� �������� �ֽŰ��� ���� �ƴմϴ�.</p><h2>���ǿ� ����</h2><p><a href="/contact/">���� ������</a>���� �̸��ϰ� ���� ���� ���� ��θ� Ȯ���� �� �ֽ��ϴ�. ���������� ������ ���Ǵ� ���� �Խ��ǿ� �ø��� ������.</p>`;
  await write('about/index.html',page({title:'����Ʈ �Ұ�',description:'MODU.TODAY�� �����Ÿ� ���� ����, ��Ȱ ������ ������ ��ó, ���� ������ � ����� �ȳ��մϴ�.',path:'/about/',body:`<article class="info-article">${about}</article>`}));
  for(const [slug,title] of [['contact','���� �� ���� ����'],['privacy','��������ó����ħ'],['terms','�̿�ȳ�']]) {
    const original=await fs.readFile(path.join(root,slug,'index.html'),'utf8');
    let body=original.match(/<article\b[^>]*>([\s\S]*?)<\/article>/)?.[1];
    if(!body)throw new Error(`Missing information page: ${slug}`);
    if(slug==='privacy')body+=`<h2>������ ������ ���</h2><p>������ �������� GitHub �׼��� ��ū�� ����մϴ�. ��ū�� ���� ���� �޸𸮿��� �����ϸ� ������ ���� Ȯ�ΰ� �� ������ ���� ����Ʈ ������ ���� GitHub�� ���޵˴ϴ�. ���� �α׳� ������ ���� ����ҿ� ��ū�� ������� �ʽ��ϴ�. ������ ȭ�鿡�� �湮 �м������� ��ũ��Ʈ�� �������� �ʽ��ϴ�.</p><p>�̹��� �ʾ��� ������ ����� ������ ����ҿ� ������ ������ ���� ����ҿ� ���ε����� �ʽ��ϴ�. ������ ����Ʈ �����͸� �����ϸ� �ʾ��� �����˴ϴ�. ������ �۰� ���� �̷��� ���� GitHub ����� �� ���� ���񽺿��� ó���˴ϴ�.</p><p>���� ��� �ȳ� �߰�: 2026�� 9�� 27��</p>`;
    if(slug==='terms')body+=`<h2>�����Ÿ��� ��ó</h2><p>��ü �������� �ۼ��ϡ������ϰ� ��ó�� �Բ� Ȯ���ϼ���. ���� �ο��� ���� ���� ��ũ�� ��ó�� ǥ���� �ּ���. �ܺ� ���� ��ũ�� ���۱��� �ش� �����ڿ��� ������ ��� ������ �������� �ʽ��ϴ�.</p><h2>���� ���� ��û</h2><p>Ʋ�� ������ ��� ������ <a href="/contact/">���� ������</a>�� �˷��ּ���. �ش� ������ �ּҿ� Ȯ�� ������ �ٰŸ� �Բ� �����ֽø� ���信 ������ �˴ϴ�.</p>`;
    const description=original.match(/<meta name="description" content="([^"]*)"/)?.[1]||title;
    await write(`${slug}/index.html`,page({title,description,path:`/${slug}/`,body:`<article class="info-article">${body}</article>`}));
  }
  const suspended=page({title:'���� ��ĳ�� �Ͻ� �ߴ�',description:'���� ���� ������ �ߴ��� ����Դϴ�.',path:'/stock/',noindex:true,body:'<div class="page-intro"><h1>���� ��ĳ�� �Ͻ� �ߴ�</h1><p>���� ���� ������ �ߴ��߽��ϴ�. �ٸ� ��Ȱ ������ ��� �̿��� �� �ֽ��ϴ�.</p><a href="/tools/">������ ���� ���� ��</a></div>'});
  await write('stock/index.html',suspended);await write('stock/guide/index.html',suspended.replaceAll('https://modu.today/stock/','https://modu.today/stock/guide/'));
  await write('404.html',page({title:'�������� ã�� �� �����ϴ�',description:'��û�� �������� ���ų� �ּҰ� ����Ǿ����ϴ�.',path:'/404.html',noindex:true,body:'<div class="page-intro"><h1>�������� ã�� �� �����ϴ�.</h1><p>�ּҸ� �ٽ� Ȯ���ϰų� Ȩ���� ���ϴ� ������ ã�ƺ�����.</p><a href="/">Ȩ���� ��</a></div>'}));
  // Retain existing crawler preferences. Allow admin fetching to see noindex headers.
  await write('robots.txt',await fs.readFile(path.join(root,'robots.txt')));
  const originalSitemap=await fs.readFile(path.join(root,'sitemap.xml'),'utf8');
  let entries=[...originalSitemap.matchAll(/<url>([\s\S]*?)<\/url>/g)].map(m=>m[1]).filter(xml=>!/<loc>https:\/\/modu.today\/(?:stock|news|reading|admin|tools)(?:\/|<)/.test(xml));
  entries.push(`<loc>${SITE}/reading/</loc>`,`<loc>${SITE}/tools/</loc>`);
  for(const post of posts)entries.push(`<loc>${SITE}/reading/${post.id}/</loc><lastmod>${e(post.updatedAt)}</lastmod>`);
  // Validate every retained URL has an emitted page and is not noindex.
  const checked=[];
  for(const xml of entries) {
    const url=xml.match(/<loc>(.*?)<\/loc>/)?.[1];if(!url?.startsWith(SITE+'/'))continue;
    const rel=decodeURIComponent(url.slice(SITE.length+1));const file=rel.endsWith('/')?rel+'index.html':rel||'index.html';
    try {const html=await fs.readFile(path.join(output,file),'utf8');if(!/<meta[^>]*name="robots"[^>]*content="[^"]*noindex/i.test(html))checked.push(xml);}catch{}
  }
  await write('sitemap.xml',`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${checked.map(xml=>`<url>${xml}</url>`).join('\n')}</urlset>\n`);
  console.log(`Build complete: ${posts.length} published articles; ${checked.length} sitemap URLs. Existing tool data retained.`);
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await build();
