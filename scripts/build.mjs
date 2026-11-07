import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {rollup} from 'rollup';
import {nodeResolve} from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import replace from '@rollup/plugin-replace';
import {ID, SITE, validatePost, articleBody, escape as e} from '../lib/content.mjs';
import {header, page, home, reading, article, toolsPage, newsPage} from '../lib/site.mjs';
import {applyAdsense, validateAdsenseConfig} from '../lib/adsense.mjs';
import {applyToolGuide} from '../lib/tool-guides.mjs';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ALLOWED = new Set(['.html','.css','.js','.mjs','.json','.png','.jpg','.jpeg','.webp','.gif','.svg','.ico','.woff','.woff2','.txt']);
export async function build(root=ROOT, output=path.join(root,'public')) {
  // Only the generated output inside this checkout may be replaced.
  if(path.resolve(output)!==path.join(path.resolve(root),'public')) throw new Error('Unsafe output directory');
  validateAdsenseConfig(JSON.parse(await fs.readFile(path.join(root,'vercel.json'),'utf8')),await fs.readFile(path.join(root,'ads.txt'),'utf8'));
  await fs.rm(output,{recursive:true,force:true}); await fs.mkdir(output,{recursive:true});
  const toolGuides=JSON.parse(await fs.readFile(path.join(root,'content/tool-guides.json'),'utf8'));
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
            html=html.replace('<section class="dashboard">',`<aside class="info" aria-label="이용 가이드"><div><strong>아파트 실거래가 이용 가이드</strong><p>검색 조건을 맞추는 방법과 평균·최고·최저 금액을 읽는 법을 안내합니다. 면적·층이 다른 거래가 섞였을 때 생기는 차이를 예제로 확인하세요.</p><a href="/apt/guide/">검색 방법과 거래 비교 예제 보기 →</a></div></aside><section class="dashboard">`);
          }
          html=applyToolGuide(html,sub.replaceAll(path.sep,'/'),toolGuides);
          // Preserve all application scripts, input IDs and data sources.
          html=html.replace(/class="topbar"/,'class="topbar modu-legacy-nav"')
            .replace(/<(div|nav) class="modu-nav">/,'<$1 class="modu-nav modu-legacy-nav">')
            .replace(/class="top"(?=><a class="brand")/,'class="top modu-legacy-nav"');
          html=html.replace(/<a\b[^>]*href=["']\/stock\/(?:guide\/)?["'][^>]*>.*?<\/a>/gs,'');
          html=html.replace('</head>','<link rel="stylesheet" href="/assets/nav.css"></head>');
          html=html.replace(/(<body\b[^>]*>)/,`$1${header(rel.startsWith('apt')?'/apt/':rel.startsWith('lotto')?'/lotto/':rel.startsWith('youtube')?'/youtube/':'/tools/')}`);
          if(!html.includes('id="main-content"')) {
            if(/<main\b/.test(html))html=html.replace('<main','<main id="main-content"');
            else html=html.replace(/<(div|section) class="(?:wrap|panel|hero)"/,match=>match+' id="main-content"');
          }
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
    validatePost(post, {requireImage:true});
    if(!ID.test(post.id)||filename!==`${post.id}.json`)throw new Error('Invalid article path');
    for(const date of [post.publishedAt,post.updatedAt,post.createdAt])if(!date||Number.isNaN(Date.parse(date)))throw new Error('Invalid article date');
    posts.push(post);
  }
  posts.sort((a,b)=>b.publishedAt.localeCompare(a.publishedAt));
  const lotto=JSON.parse(await fs.readFile(path.join(root,'lotto/data/results.json'),'utf8')).latest;
  await write('index.html',home(posts,lotto));
  await write('reading/index.html',reading(posts));
  await write('tools/index.html',toolsPage());
  await write('news/index.html',newsPage());
  for(const post of posts)await write(`reading/${post.id}/index.html`,article(post));
  // Product help lives with the apartment tool, outside the editorial post collection.
  const aptGuide=JSON.parse(await fs.readFile(path.join(root,'content/guides/apt.json'),'utf8'));
  validatePost(aptGuide);
  await write('apt/guide/index.html',page({title:aptGuide.title,description:aptGuide.description,path:'/apt/guide/',body:`<article class="info-article"><a class="text-link" href="/apt/">← 아파트 실거래가 검색</a><header class="article-heading"><span class="eyebrow">이용 가이드</span><h1>${e(aptGuide.title)}</h1><p>${e(aptGuide.description)}</p><p class="meta">검색·표시 방식 확인: 2026.11.07</p></header>${articleBody(aptGuide)}<aside class="article-end"><a href="/apt/">아파트 실거래가 검색으로 돌아가기 →</a><a href="/contact/">문의 및 오류 제보 →</a></aside></article>`}));
  const about=`<h1>일상을 읽고, 생활을 더 편리하게</h1><p>MODU.TODAY는 일상에서 생기는 궁금함을 직접 확인하고 정리하는 읽을거리와 자주 쓰는 생활 도구를 함께 제공하는 공간입니다. 생활·IT·자동차·부동산·경제·주식·취미 등 주제의 경계를 두지 않습니다.</p><h2>읽을거리를 만드는 기준</h2><p>직접 작성한 설명과 경험, 비교 기준을 담습니다. 외부 자료를 인용할 때는 출처와 확인 시점을 밝히고, 확인된 사실과 의견을 구분합니다. 외부 기사 본문을 옮겨 붙이거나 자동으로 대량 생산한 글을 발행하지 않습니다.</p><p>글마다 작성일과 수정일을 표시합니다. 내용이 잘못되었거나 달라졌다면 문의 채널로 알려주세요. 확인 후 내용을 수정하고 필요한 경우 변경 이유를 본문에 남깁니다.</p><h2>생활에 바로 쓰는 정보</h2><h3><a href="/apt/">아파트 실거래가</a></h3><p>국토교통부 공개 자료를 바탕으로 지역·단지별 신고 거래를 찾을 수 있습니다. 면적·층·거래일을 함께 비교하고, 신고 지연·정정·계약 해제 가능성을 고려하세요.</p><h3><a href="/lotto/">로또 당첨정보</a></h3><p>동행복권 공개 결과를 기준으로 당첨번호, 회차별 기록, 당첨지역과 판매점 정보를 제공합니다. 번호 생성은 무작위이며 당첨을 예측하거나 확률을 높이지 않습니다. 최종 결과는 동행복권 공식 발표를 확인하세요.</p><h3><a href="/tools/">계산기와 기타 도구</a></h3><p>생활 계산기, 웹게임, YouTube 조회수 변화를 제공합니다. 계산 결과는 각 도구에 표시한 가정에 따른 참고값이며, YouTube 순위는 추적 대상의 관측값으로 공식 전체 순위가 아닙니다.</p><h2>자체 글과 공개 데이터의 구분</h2><p><a href="/reading/">읽을거리</a>는 해설·의견·가상 예제를 담는 공간이며, 도구 사용법은 해당 도구의 안내 영역에 둡니다. 외부 뉴스 제목의 자동 수집·나열은 2026년 11월 7일 종료했습니다. 공개 데이터 도구는 원자료를 찾고 비교할 수 있게 가공하며, 출처·기준 시점·집계 범위를 함께 안내합니다.</p><h2>작성 책임과 자료 확인</h2><p>자체 글은 MODU.TODAY 편집부 명의로 발행하며, 내용에 대한 문의와 정정 요청은 운영자가 받습니다. 외부 전문가의 검토를 받은 것으로 표시하지 않습니다. 직접 해본 경험, 제공사의 발표, 편집부의 해석, 설명용 가상 예제는 본문에서 구분합니다.</p><p>시장가격·제품 사양처럼 바뀌는 정보는 자료 기준일과 원문 링크를 확인해 주세요. 작성일과 수정일은 다른 의미이며, 글이 수정되었다고 모든 수치가 수정일의 최신값인 것은 아닙니다.</p><h2>문의와 정정</h2><p><a href="/contact/">문의 페이지</a>에서 이메일과 공개 오류 제보 경로를 확인할 수 있습니다. 개인정보를 포함한 문의는 공개 게시판에 올리지 마세요.</p>`;
  await write('about/index.html',page({title:'사이트 소개',description:'MODU.TODAY의 읽을거리 편집 기준, 생활 도구의 데이터 출처, 오류 정정과 운영 방식을 안내합니다.',path:'/about/',body:`<article class="info-article">${about}</article>`}));
  for(const [slug,title] of [['contact','문의 및 오류 제보'],['privacy','개인정보처리방침'],['terms','이용안내']]) {
    const original=await fs.readFile(path.join(root,slug,'index.html'),'utf8');
    let body=original.match(/<article\b[^>]*>([\s\S]*?)<\/article>/)?.[1];
    if(!body)throw new Error(`Missing information page: ${slug}`);
    if(slug==='privacy')body+=`<h2>콘텐츠 관리자 기능</h2><p>관리자 인증에는 GitHub 액세스 토큰을 사용합니다. 토큰은 현재 탭의 메모리에만 보관하며 관리자 권한 확인과 글 발행을 위해 사이트 서버를 거쳐 GitHub로 전달됩니다. 서버 로그나 브라우저 영구 저장소에 토큰을 기록하지 않습니다. 관리자 화면에는 방문 분석·광고 스크립트를 포함하지 않습니다.</p><p>미발행 초안은 관리자 기기의 브라우저 저장소에 남으며 서버나 공개 저장소에 업로드하지 않습니다. 브라우저 사이트 데이터를 삭제하면 초안이 삭제됩니다. 발행한 글과 수정 이력은 공개 GitHub 저장소 및 배포 서비스에서 처리됩니다.</p><p>관리 기능 안내 추가: 2026년 9월 27일</p>`;
    if(slug==='terms')body+=`<h2>읽을거리와 출처</h2><p>자체 콘텐츠의 작성일·수정일과 출처를 함께 확인하세요. 글을 인용할 때는 원문 링크와 출처를 표시해 주세요. 인용한 외부 자료의 권리는 해당 제공자에게 있습니다. 외부 뉴스 제목을 자동으로 모아 제공하던 기능은 운영을 종료했습니다.</p><h2>오류 정정 요청</h2><p>틀린 정보나 기능 오류는 <a href="/contact/">문의 페이지</a>로 알려주세요. 해당 페이지 주소와 확인 가능한 근거를 함께 보내주시면 검토에 도움이 됩니다.</p>`;
    const description=original.match(/<meta name="description" content="([^"]*)"/)?.[1]||title;
    await write(`${slug}/index.html`,page({title,description,path:`/${slug}/`,body:`<article class="info-article">${body}</article>`}));
  }
  const suspended=page({title:'증시 스캐너 일시 중단',description:'현재 공개 제공을 중단한 기능입니다.',path:'/stock/',noindex:true,body:'<div class="page-intro"><h1>증시 스캐너 일시 중단</h1><p>현재 공개 제공을 중단했습니다. 다른 생활 도구는 계속 이용할 수 있습니다.</p><a href="/tools/">유용한 도구 보기 →</a></div>'});
  await write('stock/index.html',suspended);await write('stock/guide/index.html',suspended.replaceAll('https://modu.today/stock/','https://modu.today/stock/guide/'));
  await write('404.html',page({title:'페이지를 찾을 수 없습니다',description:'요청한 페이지가 없거나 주소가 변경되었습니다.',path:'/404.html',noindex:true,body:'<div class="page-intro"><h1>페이지를 찾을 수 없습니다.</h1><p>주소를 다시 확인하거나 홈에서 원하는 정보를 찾아보세요.</p><a href="/">홈으로 →</a></div>'}));
  // Retain existing crawler preferences. Allow admin fetching to see noindex headers.
  await write('robots.txt',await fs.readFile(path.join(root,'robots.txt')));
  const originalSitemap=await fs.readFile(path.join(root,'sitemap.xml'),'utf8');
  let entries=[...originalSitemap.matchAll(/<url>([\s\S]*?)<\/url>/g)].map(m=>m[1]).filter(xml=>!/<loc>https:\/\/modu.today\/(?:stock|news|reading|admin|tools)(?:\/|<)/.test(xml));
  entries=entries.filter(xml=>!xml.includes(`<loc>${SITE}/apt/guide/</loc>`));
  entries.push(`<loc>${SITE}/reading/</loc>`,`<loc>${SITE}/tools/</loc>`,`<loc>${SITE}/apt/guide/</loc><lastmod>${e(aptGuide.updatedAt)}</lastmod>`);
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
