import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {build,ROOT} from '../scripts/build.mjs';
import {home,article,reading,newsPage,header} from '../lib/site.mjs';

test('retired news never republishes external headlines or a news navigation item',()=>{
  const news={items:[{title:'EXTERNAL_HEADLINE_SENTINEL',url:'https://news.google.com/articles/sample',source:'External'}]};
  const html=newsPage(news);
  assert.ok(html.includes('자동 뉴스 모음 운영을 종료했습니다'));
  assert.ok(html.includes('noindex,follow'));
  assert.ok(!html.includes('EXTERNAL_HEADLINE_SENTINEL'));
  assert.ok(!header().includes('href="/news/"'));
});

const post={id:'sample-article-123',title:'샘플 테스트 글',category:'생활',description:'검색 결과와 메인 화면에서 확인할 글 요약입니다.',image:'',imageAlt:'',body:'# 소제목\n\n테스트로 작성한 본문이며 실제 발행할 글이 아닙니다. 생성 결과를 확인하는 테스트 전용 내용입니다.',tags:['기록'],status:'published',createdAt:'2026-09-01T00:00:00Z',publishedAt:'2026-09-01T00:00:00Z',updatedAt:'2026-09-02T00:00:00Z'};
test('home leads with original reading and tools instead of syndicated news',()=>{
  const html=home([post],{draw:100,numbers:[1,2,3,4,5,6],bonus:7});
  const ids=['latest-reading','everyday-shortcuts','useful-tools','use-with-confidence'];
  const indexes=ids.map(id=>html.indexOf(`id="${id}"`));assert.ok(indexes.every((n,i)=>n>0&&(!i||n>indexes[i-1])));
  assert.match(html,/class="essential apt-feature" href="\/apt\/"/);assert.match(html,/class="essential lotto-feature" href="\/lotto\/"/);
  assert.ok(html.includes('/reading/?category=%EC%83%9D%ED%99%9C'));
  assert.ok(!html.includes('id="life-economy"'));
  assert.ok(!html.includes('/stock/'));assert.ok(!html.includes('/admin/'));assert.ok(html.includes(`/reading/${post.id}/`));
});
test('article metadata and visible dates reflect the same content',()=>{
  const html=article({...post,title:'A <script> & "quoted"'});
  assert.ok(html.includes('https://modu.today/reading/sample-article-123/'));
  assert.ok(html.includes('article:modified_time'));assert.ok(html.includes('2026.09.02'));assert.ok(html.includes('BlogPosting'));assert.ok(!html.includes('<h1>A <script>'));
  assert.ok(reading([post]).includes('data-category="생활"'));
});

test('public category navigation only includes categories with published posts',()=>{
  const html=home([post],null);
  assert.ok(html.includes('/reading/?category=%EC%83%9D%ED%99%9C'));
  assert.ok(!html.includes('/reading/?category=IT'));
  assert.ok(!reading([post]).includes('data-filter="IT"'));
  assert.ok(!home([],null).includes('/reading/?category='));
});
test('visible article dates use Korea time while machine timestamps retain the original instant',()=>{
  const crossing={...post,publishedAt:'2026-11-06T23:00:00Z',updatedAt:'2026-11-06T23:30:00Z'};
  for(const html of [article(crossing),reading([crossing]),home([crossing],null)]) {
    assert.ok(html.includes('2026.11.07'));
    assert.ok(!html.includes('2026.11.06'));
  }
  assert.ok(article(crossing).includes('datetime="2026-11-06T23:00:00Z"'));
});
test('home and reading share custom categories and the main navigation links to YouTube',()=>{
  const posts=[{...post,category:'AI·테크'},{...post,category:'AI·테크'},{...post,category:'새 주제 & <정보>'}];
  const html=home(posts,null);
  assert.equal(html.split(`href="/reading/?category=${encodeURIComponent('AI·테크')}"`).length-1,1);
  assert.ok(html.includes('새 주제 &amp; &lt;정보&gt;'));
  assert.ok(reading(posts).includes('data-filter="AI·테크"'));
  assert.ok(header('/youtube/').includes('<a href="/youtube/" aria-current="page">유튜브 순위</a>'));
});
test('build preserves existing tool assets, excludes source and drafts, adds published URLs',async()=>{
  const temp=await fs.mkdtemp(path.join(os.tmpdir(),'modu-build-'));
  try {
    for(const dir of ['apt','lotto','calculator','games','youtube','assets','admin','lib','news','content','about','contact','privacy','terms'])await fs.cp(path.join(ROOT,dir),path.join(temp,dir),{recursive:true});
    for(const file of ['sitemap.xml','robots.txt','ads.txt','vercel.json','yasun.html','skhynix-split-analysis.html'])await fs.copyFile(path.join(ROOT,file),path.join(temp,file));
    // Reproduce the existing analytics-injection workflow, which edits source HTML after pushes.
    for(const file of ['yasun.html','skhynix-split-analysis.html'])await fs.appendFile(path.join(temp,file),'<script>window.va=window.va||function(){};</script><script defer src="/_vercel/insights/script.js"></script>');
    await fs.writeFile(path.join(temp,`content/posts/${post.id}.json`),JSON.stringify(post));
    await fs.writeFile(path.join(temp,'content/posts/html-article-123.json'),JSON.stringify({...post,id:'html-article-123',format:'html',css:'body{color:red}',body:'<h2>HTML 발행 확인</h2><p>이미지와 표를 포함한 글을 서버에서 정리하여 출력하고 검색에서도 본문을 읽을 수 있는지 확인합니다.</p><img src="/assets/og.png" alt="확인용 이미지" onerror="alert(1)"><script>alert(1)</script>'}));
    await fs.writeFile(path.join(temp,'content/posts/private-draft.json'),JSON.stringify({...post,status:'draft',body:'SECRET DRAFT'}));
    await fs.unlink(path.join(temp,'news/data.json')); // No dependence on retired RSS data.
    await build(temp);
    const read=rel=>fs.readFile(path.join(temp,'public',rel),'utf8');
    await assert.rejects(read('news/data.json'));
    assert.ok(!(await read('index.html')).includes('id="latest-news"'));
    const sitemap=await read('sitemap.xml');assert.ok(sitemap.includes(`/reading/${post.id}/`));
    for(const hidden of ['/admin/','/stock/','/news/','private-draft'])assert.ok(!sitemap.includes(hidden));
    assert.ok(!(await read('reading/index.html')).includes('SECRET DRAFT'));
    for(const file of ['apt/data/trades.json','lotto/data/results.json','calculator/theme.css'])assert.deepEqual(await fs.readFile(path.join(ROOT,file)),await fs.readFile(path.join(temp,'public',file)));
    await assert.rejects(read('content/posts/private-draft.json'));await assert.rejects(read('stock/data/scanner.json'));await assert.rejects(read('apt/update_apt.py'));
    assert.ok(!(await read('admin/index.html')).includes('/_vercel/insights'));
    for(const file of ['index.html','reading/index.html',`reading/${post.id}/index.html`,'apt/index.html','lotto/index.html','youtube/index.html','games/index.html','tools/index.html','calculator/loan.html']) {
      const html=await read(file);
      assert.equal(html.split('pagead/js/adsbygoogle.js?client=ca-pub-6122968996738347').length-1,1,file);
      assert.equal(html.split('name="google-adsense-account"').length-1,1,file);
    }
    for(const file of ['admin/index.html','news/index.html','stock/index.html','stock/guide/index.html','404.html','privacy/index.html','terms/index.html','contact/index.html','about/index.html'])assert.ok(!(await read(file)).includes('adsbygoogle'),file);
    assert.ok((await read('stock/index.html')).includes('noindex'));
    assert.ok((await read('apt/index.html')).includes('주요 메뉴'));
    const guidePath='/apt/guide/';
    const oldGuidePath='/reading/6f88af15-31a0-4c06-9009-fc63f1a7ac18/';
    assert.ok((await read('apt/index.html')).includes(guidePath));
    assert.equal(sitemap.split(`<loc>https://modu.today${guidePath}</loc>`).length-1,1);
    assert.ok(!sitemap.includes(oldGuidePath));
    for(const file of ['index.html','reading/index.html','apt/index.html'])assert.ok(!(await read(file)).includes(oldGuidePath),file);
    for(const file of ['index.html','reading/index.html'])assert.ok(!(await read(file)).includes('아파트 실거래가 이용 가이드'),file);
    await assert.rejects(read(oldGuidePath.slice(1)+'index.html'));
    const aptGuide=await read('apt/guide/index.html');
    assert.ok(aptGuide.includes('<h1>아파트 실거래가 이용 가이드</h1>'));
    assert.ok(aptGuide.includes('href="https://modu.today/apt/guide/"'));
    assert.ok(aptGuide.includes('href="/apt/" aria-current="page"'));
    assert.ok(aptGuide.includes('가상의 동일 단지 거래'));
    assert.ok(!aptGuide.includes('BlogPosting'));
    assert.equal(aptGuide.split('pagead/js/adsbygoogle.js?client=').length-1,1);
    const config=JSON.parse(await fs.readFile(path.join(temp,'vercel.json'),'utf8'));
    for(const source of [oldGuidePath.slice(0,-1),oldGuidePath,oldGuidePath+'index.html'])assert.ok(config.redirects.some(r=>r.source===source&&r.destination===guidePath&&r.permanent===true));
    for(const file of ['yasun.html','skhynix-split-analysis.html']) {
      const guide=await read(file);
      assert.ok(guide.includes('주요 메뉴'));
      assert.ok(guide.includes('noindex,follow'));
      assert.ok(!/adsbygoogle|googlesyndication|<iframe|href="\/stock\//i.test(guide));
      assert.ok(!sitemap.includes(file));
      assert.equal(guide.split('src="/_vercel/insights/script.js"').length-1,1);
    }
    assert.ok(!(await read('yasun.html')).includes('711.37'));
    const htmlArticle=await read('reading/html-article-123/index.html');
    assert.ok(htmlArticle.includes('<h2>HTML 발행 확인</h2>'));assert.ok(htmlArticle.includes('.modu-html-content .modu-html-body{color:red}'));
    assert.ok(!htmlArticle.includes('onerror'));assert.ok(!htmlArticle.includes('alert(1)'));assert.ok(sitemap.includes('/reading/html-article-123/'));
    assert.ok((await read('assets/content.mjs')).includes('sanitizeStylesheet'));assert.ok((await read('admin/editor.js')).includes('HTML + CSS'));
    await fs.appendFile(path.join(temp,'yasun.html'),'<script src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>');
    await assert.rejects(build(temp),/Unexpected ad code in legacy guide/);
  }finally{await fs.rm(temp,{recursive:true,force:true});}
});
