import {CATEGORIES, escape as e, articleBody, validatePost} from '/assets/content.mjs';
const status = document.querySelector('#status');
const workspace = document.querySelector('#workspace');
let token = '', accountId = null, current = null, sha = null, dirty = false, timer = null, busy = false;
const message = (value, error=false) => {status.textContent=value;status.classList.toggle('error',error);};
const draftKey = () => `modu.editor.drafts.v1.${accountId}`;
function drafts() { try {return JSON.parse(localStorage.getItem(draftKey()) || '{}');} catch {throw new Error('초안 저장소를 읽을 수 없습니다. 브라우저 저장 설정을 확인하세요.');} }
async function api(action, fields={}) {
  const response = await fetch('/api/editor',{method:'POST',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:JSON.stringify({action,...fields})});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || '요청에 실패했습니다.');
  return data;
}
document.querySelector('#login-form').addEventListener('submit',async event=>{
  event.preventDefault(); const button=event.submitter; button.disabled=true;
  token=document.querySelector('#access-token').value.trim();
  try {
    const result=await api('verify'); accountId=result.accountId;
    document.querySelector('#access-token').value='';
    document.querySelector('#login-panel').hidden=true;
    mount(); workspace.hidden=false; newPost(); showDrafts();
    showPublished().catch(error=>message('발행 목록을 불러오지 못했습니다. '+error.message,true));
    message('관리자 연결 완료. 초안은 이 브라우저에만 저장됩니다.');
  } catch(error) {token='';message(error.message,true);}
  finally {button.disabled=false;}
});
function mount() {
  workspace.innerHTML=`<div class="editor-toolbar"><button class="button" id="new-post">새 글</button><button class="button secondary" id="import-draft">초안 불러오기</button><input type="file" id="draft-file" accept="application/json,.json" hidden><button class="button secondary" id="disconnect">연결 종료</button></div><p class="draft-note">임시저장은 이 기기·브라우저에서만 유지됩니다. 브라우저 데이터를 지우면 삭제되므로 중요한 초안은 내보내기로 보관하세요.</p><div class="editor-grid"><aside><h3>이 브라우저의 초안</h3><div id="draft-list"></div><h3>발행한 글</h3><button id="refresh-published">목록 새로고침</button><div id="published-list"></div></aside><div><form id="post-form"><label for="post-title">제목</label><input id="post-title" name="title" maxlength="120" required><div class="editor-fields"><div><label for="post-category">카테고리</label><select id="post-category" name="category" required>${CATEGORIES.map(c=>`<option value="${e(c)}">${e(c)}</option>`).join('')}<option value="__custom__">직접 입력</option></select><div id="custom-category-field" hidden><label for="post-custom-category">새 카테고리 이름</label><input id="post-custom-category" name="customCategory" maxlength="30" placeholder="예: 여행, 건강, 교육" disabled></div></div><div><label for="post-tags">태그 (쉼표로 구분, 최대 10개)</label><input id="post-tags" name="tags" maxlength="310"></div></div><label for="post-description">글 요약 / 검색 설명 (10~180자)</label><input id="post-description" name="description" maxlength="180" required><label for="post-image">대표 이미지 주소 (선택)</label><input id="post-image" name="image" placeholder="https://… 또는 /assets/…" maxlength="2000"><label for="post-image-alt">이미지 설명</label><input id="post-image-alt" name="imageAlt" maxlength="160"><p class="draft-note">직접 제작했거나 사용 권한이 있는 이미지 주소를 입력하세요.</p><label for="post-format">본문 작성 방식</label><select id="post-format" name="format"><option value="markdown">기본 글쓰기</option><option value="html">HTML + CSS</option></select><p id="format-help" class="draft-note"></p><label for="post-body">본문</label><textarea id="post-body" name="body" maxlength="100000" placeholder="# 소제목&#10;&#10;내용을 작성하세요.&#10;&#10;- 목록&#10;**굵은 글씨**&#10;[링크 이름](https://example.com)"></textarea><div id="css-field" hidden><label for="post-css">추가 CSS (선택)</label><textarea id="post-css" name="css" maxlength="30000" spellcheck="false" placeholder=".card { padding: 24px; background: #edf5ed; border-radius: 12px; }"></textarea><p class="draft-note">HTML 안에 &lt;style&gt;로 넣어도 됩니다. 이미지 주소는 &lt;img src=&quot;https://…&quot; alt=&quot;이미지 설명&quot;&gt; 형식으로 본문에 넣으세요.</p></div><div class="editor-actions"><button class="button secondary" type="button" id="save-draft">임시저장</button><button class="button secondary" type="button" id="preview">미리보기</button><button class="button secondary" type="button" id="export-draft">초안 내보내기</button><button class="button" type="submit" id="publish">발행 검토</button></div></form><div id="preview-panel" hidden><div class="preview-head"><h2>미리보기 · 미발행</h2><button id="close-preview" class="button secondary">닫기</button></div><iframe title="글 미리보기" sandbox="" referrerpolicy="no-referrer"></iframe></div><p id="publish-result" aria-live="polite"></p></div></div><dialog class="publish-dialog" id="publish-dialog"><h2>이 글을 공개할까요?</h2><strong id="review-title"></strong><p id="review-description"></p><p>발행하면 본문과 이미지 주소가 공개 저장소에 기록됩니다. 배포 완료 후 읽을거리와 메인에 자동으로 표시됩니다.</p><button id="confirm-publish" class="button">공개 발행</button><button id="cancel-publish" class="button secondary">계속 수정</button></dialog>`;
  const on=(id,fn)=>document.getElementById(id).addEventListener('click',fn);
  on('new-post',()=>{saveDraft(false);newPost();}); on('save-draft',()=>saveDraft(true)); on('preview',()=>preview().catch(error=>message(error.message,true)));
  on('close-preview',()=>document.querySelector('#preview-panel').hidden=true);
  on('export-draft',exportDraft); on('import-draft',()=>document.querySelector('#draft-file').click());
  on('refresh-published',()=>showPublished().catch(err=>message(err.message,true)));
  on('disconnect',()=>{saveDraft(false);token='';accountId=null;clearTimeout(timer);workspace.innerHTML='';workspace.hidden=true;document.querySelector('#login-panel').hidden=false;message('연결을 종료했습니다.');});
  document.querySelector('#post-category').addEventListener('change',updateCategoryUI);
  document.querySelector('#post-format').addEventListener('change',updateFormatUI);
  document.querySelector('#draft-file').addEventListener('change',importDraft);
  document.querySelector('#post-form').addEventListener('input',()=>{dirty=true;clearTimeout(timer);timer=setTimeout(()=>saveDraft(false),1200);});
  document.querySelector('#post-form').addEventListener('submit',event=>{event.preventDefault();try {validatePost(fields());document.querySelector('#review-title').textContent=fields().title;document.querySelector('#review-description').textContent=fields().description;document.querySelector('#publish-dialog').showModal();}catch(error){message(error.message,true);}});
  on('cancel-publish',()=>document.querySelector('#publish-dialog').close());
  on('confirm-publish',publish);
}
function fields() {
  const form=document.querySelector('#post-form'); const data=Object.fromEntries(new FormData(form));
  const {customCategory, ...post}=data;
  return {...post,category:post.category==='__custom__' ? (customCategory || '').trim() : post.category,tags:post.tags.split(',').map(t=>t.trim()).filter(Boolean)};
}
function fill(post) {
  const form=document.querySelector('#post-form');
  for(const key of ['title','description','image','imageAlt','body','css']) form.elements[key].value=post[key]||'';
  const category=post.category || CATEGORIES[0], preset=CATEGORIES.includes(category);
  form.elements.category.value=preset ? category : '__custom__';
  form.elements.customCategory.value=preset ? '' : category;updateCategoryUI();
  form.elements.tags.value=(post.tags||[]).join(', ');
  form.elements.format.value=post.format || 'markdown';updateFormatUI();
  document.querySelector('#preview-panel').hidden=true;
  document.querySelector('#publish-result').textContent='';dirty=false;
}
function updateCategoryUI() {
  const custom=document.querySelector('#post-category').value==='__custom__';
  document.querySelector('#custom-category-field').hidden=!custom;
  const input=document.querySelector('#post-custom-category');
  input.disabled=!custom;input.required=custom;
}
function updateFormatUI() {
  const html=document.querySelector('#post-format').value==='html';
  document.querySelector('#css-field').hidden=!html;
  document.querySelector('#format-help').textContent=html
    ? 'HTML 본문이나 HTML 문서 전체를 붙여 넣으세요. 이미지·표·카드·색상·반응형 배치를 지원하며 스타일은 글 안에만 적용됩니다. 실행 코드와 외부 임베드·외부 스타일 파일은 제외됩니다.'
    : '일반 글을 입력하세요. 소제목(#), 목록(- 또는 1.), 굵게(**), 코드와 HTTPS 링크를 지원합니다.';
  document.querySelector('#post-body').spellcheck=!html;
  document.querySelector('#post-body').placeholder=html ? '<section class="card">\n  <h2>소제목</h2>\n  <p>글 내용을 입력하세요.</p>\n  <img src="https://…" alt="이미지 설명">\n</section>' : '# 소제목\n\n내용을 작성하세요.\n\n- 목록\n**굵은 글씨**';
}
function newPost() {clearTimeout(timer);current=crypto.randomUUID();sha=null;fill({category:'생활'});message('새 글을 작성합니다.');}
function saveDraft(notify) {
  if (!current || !accountId || busy) return;
  try {
    const post=fields(); if (!post.title && !post.body) return;
    const saved=drafts();saved[current]={id:current,post,sha,savedAt:new Date().toISOString()};
    localStorage.setItem(draftKey(),JSON.stringify(saved));dirty=false;showDrafts();
    if(notify) message('이 브라우저에 임시저장했습니다.');
  } catch(error) {message('초안을 저장하지 못했습니다. 내보내기로 보관하세요. '+error.message,true);}
}
function showDrafts() {
  const saved=drafts(), list=document.querySelector('#draft-list');list.replaceChildren();
  for(const draft of Object.values(saved).sort((a,b)=>b.savedAt.localeCompare(a.savedAt))) {
    const button=document.createElement('button');button.type='button';button.textContent=draft.post.title || '제목 없는 초안';
    button.addEventListener('click',()=>{saveDraft(false);clearTimeout(timer);current=draft.id;sha=draft.sha;fill(draft.post);message('저장된 초안을 불러왔습니다.');});list.append(button);
  }
  if(!list.children.length) list.textContent='아직 초안이 없습니다.';
}
async function showPublished() {
  const {posts}=await api('list'); const list=document.querySelector('#published-list');list.replaceChildren();
  for(const item of posts) {
    const button=document.createElement('button');button.type='button';button.textContent=item.id;
    button.addEventListener('click',async()=>{try{saveDraft(false);const result=await api('load',{id:item.id});clearTimeout(timer);current=item.id;sha=result.sha;fill(result.post);message('발행한 글을 불러왔습니다. 수정 후 다시 발행할 수 있습니다.');}catch(error){message(error.message,true);}});list.append(button);
    api('load',{id:item.id}).then(result=>{button.textContent=result.post.title;}).catch(()=>{});
  }
  if(!posts.length) list.textContent='아직 발행한 글이 없습니다.';
}
let previewCss;
async function preview() {
  const post=fields();
  if(!previewCss) {
    const response=await fetch('/assets/site.css',{cache:'no-cache'});
    if(!response.ok)throw new Error('미리보기 스타일을 불러오지 못했습니다. 다시 시도해 주세요.');
    previewCss=(await response.text()).replace(/^@import[^;]+;/gm,'');
  }
  const frame=document.querySelector('iframe');
  frame.srcdoc=`<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src https: ${location.origin}; base-uri 'none'; form-action 'none'"><style>${previewCss}</style></head><body class="editorial-site"><main class="site-main"><article class="article"><header class="article-heading"><span class="eyebrow">${e(post.category)} · 미발행 미리보기</span><h1>${e(post.title||'제목 없는 글')}</h1><p>${e(post.description)}</p></header>${articleBody(post)}</article></main></body></html>`;
  document.querySelector('#preview-panel').hidden=false;frame.scrollIntoView({behavior:'smooth',block:'start'});
}
function exportDraft() {
  const value={version:1,id:current,post:fields(),sha};
  const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download=`modu-draft-${current}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message('초안 파일을 내보냈습니다. 파일은 공개하지 말고 보관하세요.');
}
async function importDraft(event) {
  const file=event.target.files[0];if(!file)return;
  try {
    if(file.size>450000) throw new Error('초안 파일이 너무 큽니다.');
    const data=JSON.parse(await file.text());
    if(data.version!==1 || !data.post || typeof data.post.title!=='string' || typeof data.post.body!=='string' || !Array.isArray(data.post.tags)) throw new Error('지원하지 않는 초안 형식입니다.');
    saveDraft(false);newPost();fill(data.post);saveDraft(true);message('초안을 새 글로 불러왔습니다. 기존 발행 글을 수정하려면 발행 목록에서 열어 주세요.');
  } catch(error) {message(error.message,true);} finally {event.target.value='';}
}
async function publish() {
  if(busy)return;
  const post=fields();saveDraft(false);busy=true;clearTimeout(timer);
  document.querySelector('#publish-dialog').close();
  const controls=[...workspace.querySelectorAll('button,input,textarea,select')];controls.forEach(c=>c.disabled=true);
  message('글을 발행하고 있습니다.');
  try {
    const result=await api('publish',{id:current,sha,post});sha=result.sha;dirty=false;
    try {const saved=drafts();delete saved[current];localStorage.setItem(draftKey(),JSON.stringify(saved));showDrafts();} catch { /* Publication already succeeded; local cleanup must not turn it into a failure. */ }
    message('저장소에 발행했습니다. 사이트 배포를 기다리는 중입니다.');
    const box=document.querySelector('#publish-result');box.replaceChildren();const a=document.createElement('a');a.href=result.url;a.target='_blank';a.rel='noopener';a.textContent='발행 페이지 열기 ↗';box.append(a);
    const expected=result.post.updatedAt;
    for(let attempt=0;attempt<24;attempt++) {
      await new Promise(resolve=>setTimeout(resolve,5000));
      try {
        const response=await fetch(`${result.url}?published=${encodeURIComponent(expected)}`,{cache:'no-store',signal:AbortSignal.timeout(10000)});
        if(response.ok && (await response.text()).includes(`content="${expected}"`)) {message('배포가 완료되어 글이 공개되었습니다.');return;}
      } catch { /* Transient deployment fetch failure does not undo a published commit. */ }
    }
    message('발행 저장은 완료됐지만 배포 완료를 아직 확인하지 못했습니다. 잠시 후 발행 페이지를 확인해 주세요.');
  } catch(error) {message(error.message,true);}
  finally {busy=false;controls.forEach(c=>c.disabled=false);showPublished().catch(()=>{});}
}
window.addEventListener('beforeunload',event=>{if(dirty||busy){event.preventDefault();event.returnValue='';}});
