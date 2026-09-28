import {test,expect} from '@playwright/test';
const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aP2kAAAAASUVORK5CYII=','base64');
const file=(name='image.png')=>({name,mimeType:'image/png',buffer:png});
async function transfer(page,selector,type,files=[file()]) {
  await page.locator(selector).evaluate((element,{type,files})=>{
    const data=new DataTransfer();
    for(const file of files)data.items.add(new File([Uint8Array.from(atob(file.base64),c=>c.charCodeAt(0))],file.name,{type:file.mimeType}));
    element.dispatchEvent(type==='paste'?new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}):new DragEvent('drop',{dataTransfer:data,bubbles:true,cancelable:true}));
  },{type,files:files.map(f=>({...f,buffer:undefined,base64:f.buffer.toString('base64')}))});
}
test.beforeEach(async({page,request})=>{
  await page.route('https://teststore.public.blob.vercel-storage.com/**',async route=>{
    const url=new URL(route.request().url());const response=await request.get('/_test/blob'+url.pathname);
    await route.fulfill({response});
  });
  await page.goto('/admin/');
  await page.getByLabel('GitHub 액세스 토큰').fill('github_pat_test_not_a_real_token_12345');
  await page.getByRole('button',{name:'관리자로 연결',exact:true}).click();
  await expect(page.locator('#post-form')).toBeVisible();
});

test('cover file chooser and drop store URLs, preview, preserve disabled fields and restore drafts',async({page})=>{
  await page.locator('#cover-file').setInputFiles(file('cover.png'));
  await expect(page.locator('#new-post')).toBeDisabled();
  await expect(page.locator('#cover-upload-status')).toContainText('업로드 완료');
  const first=await page.locator('#post-image').inputValue();
  expect(first).toMatch(/^https:\/\/teststore\.public\.blob\.vercel-storage\.com\//);
  await expect(page.locator('#cover-preview')).toBeVisible();
  expect(await page.locator('#cover-preview').evaluate(img=>img.naturalWidth)).toBe(1);
  await expect(page.locator('#post-image-alt')).toHaveValue('cover');
  await expect(page.locator('#post-custom-category')).toBeDisabled();
  await page.getByRole('button',{name:'새 글',exact:true}).click();
  await page.locator('#draft-list button').first().click();
  await expect(page.locator('#post-image')).toHaveValue(first);
  await transfer(page,'#cover-drop','drop',[file('replacement.png')]);
  await expect(page.locator('#cover-upload-status')).toContainText('업로드 완료');
  expect(await page.locator('#post-image').inputValue()).not.toBe(first);
  await page.locator('#post-image').fill('/assets/og.png');
  await expect(page.locator('#cover-preview')).toHaveAttribute('src','/assets/og.png');
  await page.locator('#post-image').fill('');await expect(page.locator('#cover-preview')).toBeHidden();
});

test('HTML drop inserts multiple images at selection in order and preserves surrounding HTML',async({page})=>{
  await page.locator('#post-format').selectOption('html');
  await page.locator('#post-body').fill('<p>before</p>REPLACE<p>after</p>');
  await page.locator('#post-body').evaluate(el=>el.setSelectionRange(13,20));
  await transfer(page,'#post-body','drop',[file('first.png'),file('second.png')]);
  await expect(page.locator('#body-upload-status')).toContainText('2개 이미지 삽입 완료');
  const body=await page.locator('#post-body').inputValue();
  expect(body).toMatch(/^<p>before<\/p>\n\n<img/);expect(body).toMatch(/<p>after<\/p>$/);
  expect(body).not.toContain('REPLACE');expect(body.indexOf('alt="first"')).toBeLessThan(body.indexOf('alt="second"'));
  expect(body).not.toContain('data:image');
});

test('Ctrl+V uploads clipboard image; ordinary text and Markdown images still render',async({page,context})=>{
  await context.grantPermissions(['clipboard-read','clipboard-write']);
  await page.locator('#post-body').fill('# Keep heading\n\nParagraph');
  await page.locator('#post-body').focus();await page.locator('#post-body').press('Control+End');
  await page.evaluate(async()=>{
    const canvas=document.createElement('canvas');canvas.width=32;canvas.height=32;
    const context=canvas.getContext('2d');context.fillStyle='#216147';context.fillRect(0,0,32,32);
    const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
    await navigator.clipboard.write([new ClipboardItem({'image/png':blob})]);
  });
  await page.locator('#post-body').press('Control+V');
  await expect(page.locator('#body-upload-status')).toContainText('이미지 삽입 완료');
  expect(await page.locator('#post-body').inputValue()).toMatch(/!\[image\]\(https:/);
  await page.evaluate(()=>navigator.clipboard.writeText('ordinary text'));
  await page.locator('#post-body').press('Control+End');await page.locator('#post-body').press('Control+V');
  expect(await page.locator('#post-body').inputValue()).toContain('ordinary text');
  await page.getByRole('button',{name:'미리보기',exact:true}).click();
  await expect(page.frameLocator('iframe').locator('.prose img')).toBeVisible();
  await expect(page.frameLocator('iframe').getByRole('heading',{name:'Keep heading'})).toBeVisible();
});

test('validation and storage failures keep existing content and allow retrying the same file',async({page,request})=>{
  await page.locator('#post-image').fill('/assets/og.png');
  await page.locator('#post-body').fill('Existing body must remain unchanged');
  for(const bad of [{name:'bad.svg',mimeType:'image/svg+xml',buffer:Buffer.from('<svg/>')},{...file(),buffer:Buffer.alloc(3*1024*1024+1)}]){
    await page.locator('#cover-file').setInputFiles(bad);await expect(page.locator('#cover-upload-status')).toHaveClass(/error/);
    await expect(page.locator('#post-image')).toHaveValue('/assets/og.png');
  }
  await page.locator('#cover-file').setInputFiles({...file(),buffer:Buffer.from('<html>renamed file</html>')});
  await expect(page.locator('#cover-upload-status')).toContainText('파일 내용');
  await request.post('/_test/fail-next');
  await transfer(page,'#post-body','paste');
  await expect(page.locator('#body-upload-status')).toContainText('업로드에 실패');
  await expect(page.locator('#post-body')).toHaveValue('Existing body must remain unchanged');
  await expect(page.locator('#publish')).toBeEnabled();
  await transfer(page,'#post-body','paste');await expect(page.locator('#body-upload-status')).toContainText('삽입 완료');
});

test('HTML document upload, draft restore, preview and publish retain the same image URLs',async({page,request})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.locator('#post-title').fill('이미지 발행 테스트');
  await page.locator('#post-description').fill('로컬에서만 수행하는 이미지 발행 테스트이며 실제 글은 공개하지 않습니다.');
  await page.locator('#post-category').selectOption('__custom__');await page.locator('#post-custom-category').fill('AI·테크');
  await page.locator('#post-format').selectOption('html');
  await page.locator('#post-body').fill('<!doctype html><html><body><p>이미지 업로드가 끝난 뒤 초안에 저장하고 다시 불러와 미리보기와 발행까지 이어지는 과정을 확인하는 테스트 글입니다.</p></body></html>');
  await page.locator('#post-body').focus();await page.locator('#post-body').press('Control+End');
  await page.locator('#body-image-files').setInputFiles(file('body.png'));
  await expect(page.locator('#body-upload-status')).toContainText('삽입 완료');
  const source=await page.locator('#post-body').inputValue();expect(source.indexOf('<img')).toBeLessThan(source.indexOf('</body>'));
  await page.locator('#cover-file').setInputFiles(file('cover.png'));await expect(page.locator('#cover-upload-status')).toContainText('업로드 완료');
  const cover=await page.locator('#post-image').inputValue();
  await page.getByRole('button',{name:'새 글',exact:true}).click();
  await page.locator('#draft-list').getByRole('button',{name:'이미지 발행 테스트',exact:true}).click();
  await expect(page.locator('#post-body')).toHaveValue(source);await expect(page.locator('#post-image')).toHaveValue(cover);
  await expect(page.locator('#post-custom-category')).toHaveValue('AI·테크');
  await page.getByRole('button',{name:'미리보기',exact:true}).click();
  await expect(page.frameLocator('iframe').locator('.prose img')).toBeVisible();
  await page.getByRole('button',{name:'발행 검토',exact:true}).click();await page.getByRole('button',{name:'공개 발행',exact:true}).click();
  await expect(page.locator('#status')).toContainText('배포가 완료',{timeout:12000});
  const id=(await page.locator('#publish-result a').getAttribute('href')).split('/')[2];
  const state=await (await request.get('/_test/state')).json();const stored=state.posts.find(p=>p.id===id);
  expect(stored.body).toBe(source);expect(stored.image).toBe(cover);expect(stored.category).toBe('AI·테크');expect(errors).toEqual([]);
});

test('mobile editor and tablet navigation fit the screen; YouTube is reachable from the header',async({page})=>{
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2)).toBeTruthy();
  await expect(page.getByRole('button',{name:'대표 이미지 업로드',exact:true})).toBeVisible();
  await page.goto('/');await page.setViewportSize({width:850,height:950});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2)).toBeTruthy();
  await page.locator('.modu-primary-nav').getByRole('link',{name:'유튜브 순위'}).click();
  await expect(page).toHaveURL(/\/youtube\/$/);
  await expect(page.locator('.modu-primary-nav a[aria-current="page"]')).toHaveText('유튜브 순위');
});
