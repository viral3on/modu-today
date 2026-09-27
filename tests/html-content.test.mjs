import test from 'node:test';
import assert from 'node:assert/strict';
import {htmlArticle,sanitizeStylesheet,sanitizeInlineStyle} from '../lib/html-content.mjs';
import {articleBody,validatePost} from '../lib/content.mjs';
import {article,home} from '../lib/site.mjs';

const post={id:'html-example-123',title:'HTML 테스트 글',category:'생활',description:'HTML 글의 이미지와 표, 스타일을 확인하는 테스트입니다.',image:'',imageAlt:'',tags:[],format:'html',css:'.card > p { color: rgb(20, 60, 30) }',body:'<style>:root{--paper:#eef5ee}body{background:var(--paper)}@media(max-width:600px){.card{display:block}}</style><section class="card"><h2>직접 작성한 기록</h2><p>이 글은 HTML 이미지와 표가 올바르게 표시되는지 확인하기 위해 작성한 테스트 본문입니다.</p><figure><img src="/assets/og.png" alt="테스트 이미지"><figcaption>이미지 설명</figcaption></figure><table><tr><th>항목</th><td>값</td></tr></table></section>',publishedAt:'2026-09-28T00:00:00Z',createdAt:'2026-09-28T00:00:00Z',updatedAt:'2026-09-28T00:00:00Z'};
test('HTML preserves semantic content, images, tables and scoped responsive styles in static article HTML',()=>{
  const html=article(validatePost(post) && post);
  assert.match(html,/<figure><img src="\/assets\/og.png" alt="테스트 이미지"/);
  assert.match(html,/<table><tr><th>항목<\/th><td>값<\/td>/);
  assert.match(html,/\.modu-html-content \.card>p\{color:rgb\(20,60,30\)\}/);
  assert.match(html,/@media \(max-width:600px\)\{\.modu-html-content \.card/);
  assert.match(html,/\.modu-html-content \.modu-html-html\{--paper:#eef5ee\}/);
  assert.match(html,/contain:layout paint style/);
  assert.match(html,/rel="canonical" href="https:\/\/modu.today\/reading\/html-example-123\//);
  assert.ok(!html.includes('<iframe'));
});
test('full HTML documents keep body styles and omit document metadata',()=>{
  const html=htmlArticle('<!doctype html><html lang="ko"><head><title>Unwanted title</title><base href="https://evil.example"><style>body{color:red}</style></head><body style="padding:20px"><p>본문</p></body></html>');
  assert.match(html,/<p>본문<\/p>/);assert.match(html,/style="padding:20px"/);assert.match(html,/\.modu-html-body\{color:red\}/);
  for(const unwanted of ['<html','<head','<title','<base','Unwanted title'])assert.ok(!html.includes(unwanted));
});
test('active HTML, event handlers, dangerous URLs and clobbering attributes are removed',()=>{
  const html=htmlArticle(`<script>alert(1)</script><iframe srcdoc="bad"></iframe><form action="https://evil.example">secret</form><svg><a onload="alert(1)">svg</a></svg><math><mtext>math</mtext></math><template shadowrootmode="open">bad</template><img src="https://example.com/a.png" onerror="alert(1)" srcset="https://evil.example/2.png 2x"><a href="java&#x09;script:alert(1)" onclick="alert(1)">bad</a><a href="//evil.example">bad</a><img src="data:image/svg+xml,bad"><img src="/\\evil.example/x"><p id="status" name="location">safe</p><a href="#status">jump</a>`);
  for(const unwanted of ['<script','<iframe','<form','<svg','<math','<template','onerror','onclick','srcdoc','srcset','javascript:','data:image','//evil.example','name="location"','id="status"'])assert.ok(!html.includes(unwanted),unwanted);
  assert.match(html,/id="modu-post-status"/);assert.match(html,/href="#modu-post-status"/);assert.match(html,/rel="noopener noreferrer"/);
});
test('CSS cannot import resources, execute expressions, close a style element or select outside the article',()=>{
  const css=sanitizeStylesheet('@import "https://evil.example/x.css";@font-face{font-family:evil;src:url(https://evil.example/font)}body, .modu-header, #status{color:red;background:url(https://evil.example);width:expression(alert(1));position:fixed;behavior:url(x)}@keyframes spin{to{color:red}}.ok{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));content:"</style><script>"}');
  assert.ok(!css.includes('https://'));assert.ok(!css.includes('expression'));assert.ok(!css.includes('position:fixed'));assert.ok(!css.includes('@import'));assert.ok(!css.includes('@font-face'));assert.ok(!css.includes('</style>'));
  assert.ok(css.includes('.modu-html-content .modu-header'));assert.ok(css.includes('.modu-html-content #modu-post-status'));assert.ok(css.includes('display:grid'));
  assert.equal(sanitizeStylesheet('.x{background:u\\72l(https://evil.example)}'),'');
  assert.equal(sanitizeInlineStyle('color:blue; background-image:url(https://evil.example); width:expression(alert(1)); position:fixed'),'color:blue');
  assert.equal(sanitizeStylesheet('@supports(display:grid){body{color:red}}'),'');
});
test('legacy posts stay Markdown, new format is validated and drafts retain CSS',()=>{
  const old={...post};delete old.format;delete old.css;
  assert.equal(validatePost(old).format,'markdown');assert.equal(validatePost(old).css,'');
  assert.ok(articleBody(old).includes('&lt;section'));
  assert.equal(validatePost(post).css,post.css);
  assert.throws(()=>validatePost({...post,format:'unsafe'}));
  assert.throws(()=>validatePost({...post,css:'x'.repeat(30001)}));
  assert.throws(()=>validatePost({...post,body:'<script>'+ 'bad'.repeat(40)+'</script>'}));
  const html=home([],{items:[]},null);assert.ok(html.includes('MODU.TODAY 소개 →'));assert.ok(!html.includes('우리가 만드는 공간'));
});
