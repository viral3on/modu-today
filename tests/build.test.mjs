import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {build,ROOT} from '../scripts/build.mjs';
import {home,article,reading,newsPage,validNewsItems,header} from '../lib/site.mjs';

test('news migration artifacts cannot become news headings or generic article links',()=>{
  const valid={category:'국내 증시 / 코스피 코스닥',title:'정상 기사 제목',source:'정상 언론사',url:'https://news.google.com/articles/valid'};
  const malformed={category:'무료 웹게임',title:'기사 보기',source:'제목이 출처로 잘못 옮겨진 항목',url:'https://news.google.com/articles/legacy'};
  const news={items:[malformed,{...valid,title:'기사 보기'},valid]};
  assert.deepEqual(validNewsItems(news),[valid]);
  for(const html of [newsPage(news),home([],news,null)]) {
    assert.ok(html.includes('정상 기사 제목'));
    assert.ok(html.includes('정상 언론사 · 외부 기사'));
    assert.ok(!html.includes('무료 웹게임'));
    assert.ok(!html.includes('>기사 보기<'));
    assert.ok(!html.includes('/articles/legacy'));
  }
});

const post={id:'sample-article-123',title:'샘플 테스트 글',category:'생활',description:'검색 결과와 메인 화면에서 확인할 글 요약입니다.',image:'',imageAlt:'',body:'# 소제목\n\n테스트로 작성한 본문이며 실제 발행할 글이 아닙니다. 생성 결과를 확인하는 테스트 전용 내용입니다.',tags:['기록'],status:'published',createdAt:'2026-09-01T00:00:00Z',publishedAt:'2026-09-01T00:00:00Z',updatedAt:'2026-09-02T00:00:00Z'};
test('home keeps reading categories in the reading section; news stays last',()=>{
  const html=home([post],{items:[]},{draw:100,numbers:[1,2,3,4,5,6],bonus:7});
  const ids=['latest-reading','everyday-shortcuts','useful-tools','latest-news'];
  const indexes=ids.map(id=>html.indexOf(`id="${id}"`));assert.ok(indexes.every((n,i)=>n>0&&(!i||n>indexes[i-1])));
  assert.match(html,/class="essential apt-feature" href="\/apt\/"/);assert.match(html,/class="essential lotto-feature" href="\/lotto\/"/);\n  assert.ok(html.includes('/reading/?category=%EC%83%9D%EC%83%9D%ED%99%9C') || html.includes('/reading/?category=%EC%83%9D%ED%99%9C'));\n  assert.ok(!html.includes('id="life-economy"'));
  assert.ok(!html.includes('/stock/'));assert.ok(!html.includes('/admin/'));assert.ok(html.includes(`/reading/${post.id}/`));
});
test('article metadata and visible dates reflect the same content',()=>{
  const html=article({...post,title:'A <script> & "quoted"'});
  assert.ok(html.includes('https://modu.today/reading/sample-article-123/'));
  assert.ok(html.includes('article:modified_time'));assert.ok(html.includes('2026.09.02'));assert.ok(html.includes('BlogPosting'));assert.ok(!html.includes('<h1>A <script>'));
  assert.ok(reading([post]).includes('data-category="생활"'));
});
test('home and reading share custom categories and the main navigation links to YouTube',()=>{
  const posts=[{...post,category:'AI·테크'},{...post,category:'AI·테크'},{...post,category:'새 주제 & <정보>'}];
  const html=home(posts,{items:[]},null);
  assert.equal(html.split(`href="/reading/?category=${encodeURIComponent('AI·테크')}"`).length-1,1);
  assert.ok(html.includes('새 주제 &amp; &lt;정보&gt;'));
  assert.ok(reading(posts).includes('data-filter="AI·테크"'));
  assert.ok(header('/youtube/').includes('<a href="/youtube/" aria-current="page">유튜브 순위</a>'));
});
test('build preserves existing tool assets, excludes source and drafts, adds published URLs',async()=>{
  const temp=await fs.mkdtemp(path.join(os.tmpdir(),'modu-build-'));
  try {
    for(const dir of ['apt','lotto','calculator','games','youtube','assets','admin','lib','news','content','about','contact','privacy','terms'])await fs.cp(path.join(ROOT,dir),path.join(temp,dir),{recursive:true});
    for(const file of ['sitemap.xml','robots.txt','ads.txt','yasun.html','skhynix-split-analysis.html'])await fs.copyFile(path.join(ROOT,file),path.join(temp,file));
    await fs.writeFile(path.join(temp,`content/posts/${post.id}.json`),JSON.stringify(post));
    await fs.writeFile(path.join(temp,'content/posts/html-article-123.json'),JSON.stringify({...post,id:'html-article-123',format:'html',css:'body{color:red}',body:'<h2>HTML 발행 확인</h2><p>이미지와 표를 포함한 글을 서버에서 정리하여 출력하고 검색에서도 본문을 읽을 수 있는지 확인합니다.</p><img src="/assets/og.png" alt="확인용 이미지" onerror="alert(1)"><script>alert(1)</script>'}));
    await fs.writeFile(path.join(temp,'content/posts/private-draft.json'),JSON.stringify({...post,status:'draft',body:'SECRET DRAFT'}));
    await build(temp);
    const read=rel=>fs.readFile(path.join(temp,'public',rel),'utf8');
    const sitemap=await read('sitemap.xml');assert.ok(sitemap.includes(`/reading/${post.id}/`));
    for(const hidden of ['/admin/','/stock/','/news/','private-draft'])assert.ok(!sitemap.includes(hidden));
    assert.ok(!(await read('reading/index.html')).includes('SECRET DRAFT'));
    for(const file of ['apt/data/trades.json','lotto/data/results.json','calculator/theme.css'])assert.deepEqual(await fs.readFile(path.join(ROOT,file)),await fs.readFile(path.join(temp,'public',file)));
    await assert.rejects(read('content/posts/private-draft.json'));await assert.rejects(read('stock/data/scanner.json'));await assert.rejects(read('apt/update_apt.py'));
    assert.ok(!(await read('admin/index.html')).includes('/_vercel/insights'));
    assert.ok((await read('stock/index.html')).includes('noindex'));
    assert.ok((await read('apt/index.html')).includes('주요 메뉴'));
    const htmlArticle=await read('reading/html-article-123/index.html');
    assert.ok(htmlArticle.includes('<h2>HTML 발행 확인</h2>'));assert.ok(htmlArticle.includes('.modu-html-content .modu-html-body{color:red}'));
    assert.ok(!htmlArticle.includes('onerror'));assert.ok(!htmlArticle.includes('alert(1)'));assert.ok(sitemap.includes('/reading/html-article-123/'));
    assert.ok((await read('assets/content.mjs')).includes('sanitizeStylesheet'));assert.ok((await read('admin/editor.js')).includes('HTML + CSS'));
  }finally{await fs.rm(temp,{recursive:true,force:true});}
});
