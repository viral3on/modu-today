import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {build,ROOT} from '../scripts/build.mjs';
import {home,article,reading} from '../lib/site.mjs';

const post={id:'sample-article-123',title:'샘플 테스트 글',category:'생활',description:'검색 결과와 메인 화면에서 확인할 글 요약입니다.',image:'',imageAlt:'',body:'# 소제목\n\n테스트로 작성한 본문이며 실제 발행할 글이 아닙니다. 생성 결과를 확인하는 테스트 전용 내용입니다.',tags:['기록'],status:'published',createdAt:'2026-09-01T00:00:00Z',publishedAt:'2026-09-01T00:00:00Z',updatedAt:'2026-09-02T00:00:00Z'};
test('home order retains prominent apartment and lotto links; news stays last',()=>{
  const html=home([post],{items:[]},{draw:100,numbers:[1,2,3,4,5,6],bonus:7});
  const ids=['latest-reading','everyday-shortcuts','life-economy','useful-tools','latest-news'];
  const indexes=ids.map(id=>html.indexOf(`id="${id}"`));assert.ok(indexes.every((n,i)=>n>0&&(!i||n>indexes[i-1])));
  assert.match(html,/class="essential apt-feature" href="\/apt\/"/);assert.match(html,/class="essential lotto-feature" href="\/lotto\/"/);
  assert.ok(!html.includes('/stock/'));assert.ok(!html.includes('/admin/'));assert.ok(html.includes(`/reading/${post.id}/`));
});
test('article metadata and visible dates reflect the same content',()=>{
  const html=article({...post,title:'A <script> & "quoted"'});
  assert.ok(html.includes('https://modu.today/reading/sample-article-123/'));
  assert.ok(html.includes('article:modified_time'));assert.ok(html.includes('2026.09.02'));assert.ok(html.includes('BlogPosting'));assert.ok(!html.includes('<h1>A <script>'));
  assert.ok(reading([post]).includes('data-category="생활"'));
});
test('build preserves existing tool assets, excludes source and drafts, adds published URLs',async()=>{
  const temp=await fs.mkdtemp(path.join(os.tmpdir(),'modu-build-'));
  try {
    for(const dir of ['apt','lotto','calculator','games','youtube','assets','admin','lib','news','content','about','contact','privacy','terms'])await fs.cp(path.join(ROOT,dir),path.join(temp,dir),{recursive:true});
    for(const file of ['sitemap.xml','robots.txt','ads.txt','yasun.html','skhynix-split-analysis.html'])await fs.copyFile(path.join(ROOT,file),path.join(temp,file));
    await fs.writeFile(path.join(temp,`content/posts/${post.id}.json`),JSON.stringify(post));
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
  }finally{await fs.rm(temp,{recursive:true,force:true});}
});
