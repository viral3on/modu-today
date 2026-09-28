import {escape as escapeHtml, safeUrl, validateImageFile} from '/assets/content.mjs';

const ACCEPT = '.jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp';
export const coverImageFields = `<div class="image-drop-zone" id="cover-drop" aria-describedby="image-help">
  <button class="button secondary" id="choose-cover" type="button">대표 이미지 업로드</button>
  <input class="image-file" id="cover-file" type="file" accept="${ACCEPT}" aria-label="대표 이미지 파일" hidden>
  <p id="image-help" class="draft-note">파일을 선택하거나 여기에 끌어다 놓으세요. JPG · PNG · WebP, 파일당 최대 3MB.</p>
  <p id="cover-upload-status" class="upload-status" role="status" aria-live="polite"></p>
  <img id="cover-preview" class="cover-preview" alt="대표 이미지 미리보기" referrerpolicy="no-referrer" hidden>
  <p id="cover-preview-error" class="upload-status error" hidden>이미지를 표시하지 못했습니다. 이미지 주소나 연결 상태를 확인하세요.</p>
</div>`;
export const bodyImageFields = `<div class="body-image-tools">
  <button class="button secondary" id="choose-body-images" type="button">본문 이미지 추가</button>
  <input class="image-file" id="body-image-files" type="file" accept="${ACCEPT}" multiple aria-label="본문 이미지 파일" hidden>
  <p id="body-image-help" class="draft-note">본문에 이미지를 끌어다 놓거나 Ctrl+V로 붙여넣으세요. 현재 커서 위치에 삽입합니다. JPG · PNG · WebP, 파일당 최대 3MB, 한 번에 최대 10개.</p>
  <p id="body-upload-status" class="upload-status" role="status" aria-live="polite"></p>
</div>`;

function readBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1]);
    reader.onerror = () => reject(new Error('파일을 읽지 못했습니다. 파일을 다시 선택해 주세요.'));
    reader.onabort = () => reject(new Error('파일 읽기가 취소되었습니다.'));
    reader.readAsDataURL(file);
  });
}

export function mountImages({workspace, upload, canStart, onStart, onFinish}) {
  const find = selector => workspace.querySelector(selector);
  const body = find('#post-body'), cover = find('#post-image'), preview = find('#cover-preview');
  let active = false;
  const say = (target, text, error=false) => {
    const element = find(`#${target}-upload-status`);
    element.textContent = text; element.classList.toggle('error', error);
  };
  function refresh() {
    const url = safeUrl(cover.value.trim(), true);
    find('#cover-preview-error').hidden = true;
    preview.hidden = !url;
    preview.alt = find('#post-image-alt').value || '대표 이미지 미리보기';
    if (url) preview.src = url;
    else preview.removeAttribute('src');
  }
  preview.addEventListener('error', () => {
    if (!preview.hasAttribute('src')) return;
    preview.hidden = true; find('#cover-preview-error').hidden = false;
  });
  preview.addEventListener('load', () => {preview.hidden=false;find('#cover-preview-error').hidden=true;});
  cover.addEventListener('input', refresh);
  find('#post-image-alt').addEventListener('input', refresh);

  async function add(files, target) {
    if (!files.length) return;
    if (active || !canStart()) {say(target, '진행 중인 작업이 끝난 뒤 다시 선택해 주세요.', true);return;}
    const selected = [...files];
    let controls = [], changed = false, started = false;
    try {
      if (target === 'cover' && selected.length !== 1) throw new Error('대표 이미지는 한 개만 선택해 주세요.');
      if (selected.length > 10) throw new Error('이미지는 한 번에 최대 10개까지 선택해 주세요.');
      selected.forEach(validateImageFile);
      if (target === 'body' && body.value.length + selected.length * 2400 > body.maxLength)
        throw new Error('본문이 너무 깁니다. 이미지 주소를 넣을 공간을 확보해 주세요.');
      // Freeze the document/selection during asynchronous uploads, preserving disabled fields.
      onStart(); active = true; started = true;
      let start = body.selectionStart, end = body.selectionEnd;
      const closingBody = body.value.search(/<\/body\s*>/i);
      if (find('#post-format').value === 'html' && closingBody >= 0 && start > closingBody) start = end = closingBody;
      let insertionPoint = start, first = true;
      controls = [...workspace.querySelectorAll('button,input,textarea,select')].map(control => [control, control.disabled]);
      controls.forEach(([control]) => {control.disabled = true;});
      find(target === 'cover' ? '#cover-drop' : '.body-image-tools').setAttribute('aria-busy', 'true');
      for (let i=0; i<selected.length; i++) {
        const file = selected[i];
        say(target, `이미지 업로드 중… ${i+1}/${selected.length} · ${file.name}`);
        const result = await upload({name:file.name, type:file.type, data:await readBase64(file)});
        const url = safeUrl(result.url, true);
        if (!url || !url.startsWith('https://')) throw new Error('이미지 주소를 확인하지 못했습니다. 다시 시도해 주세요.');
        const alt = file.name.replace(/\.[^.]+$/, '').slice(0, 160);
        if (target === 'cover') {
          cover.value = url;
          if (!find('#post-image-alt').value.trim()) find('#post-image-alt').value = alt;
          refresh();
        } else {
          const image = find('#post-format').value === 'html'
            ? `<img src="${escapeHtml(url)}" alt="${escapeHtml(alt)}" loading="lazy" decoding="async">`
            : `![${alt.replace(/[\[\]\r\n]/g, ' ')}](${url.replace(/\)/g, '%29')})`;
          const text = `\n\n${image}\n\n`;
          // Assign explicitly so disabled textarea behavior is consistent across browsers.
          body.value = body.value.slice(0, insertionPoint) + text + body.value.slice(first ? end : insertionPoint);
          insertionPoint += text.length; first = false;
          body.setSelectionRange(insertionPoint, insertionPoint);
        }
        changed = true;
      }
      say(target, target === 'cover' ? '업로드 완료. 이미지 주소와 미리보기를 반영했습니다.' : `${selected.length}개 이미지 삽입 완료. 미리보기에서 확인하세요.`);
    } catch (error) {
      say(target, `${changed ? '완료된 이미지는 반영했습니다. 나머지 파일을 다시 선택해 주세요. ' : ''}${error.message}`, true);
    } finally {
      if (started) {
        controls.forEach(([control, disabled]) => {control.disabled = disabled;});
        active = false;
        find(target === 'cover' ? '#cover-drop' : '.body-image-tools').removeAttribute('aria-busy');
        onFinish(changed);
        if (target === 'body') body.focus();
      }
    }
  }
  for (const [button, input, target] of [['#choose-cover','#cover-file','cover'], ['#choose-body-images','#body-image-files','body']]) {
    find(button).addEventListener('click', () => find(input).click());
    find(input).addEventListener('change', event => {
      const files = [...event.target.files];event.target.value = '';void add(files, target);
    });
  }
  function bindDrop(element, target) {
    element.addEventListener('dragover', event => {
      if (!event.dataTransfer.types.includes('Files')) return;
      event.preventDefault();event.dataTransfer.dropEffect=active?'none':'copy';element.classList.add('drag-over');
    });
    element.addEventListener('dragleave', () => element.classList.remove('drag-over'));
    element.addEventListener('drop', event => {
      element.classList.remove('drag-over');
      if (!event.dataTransfer.types.includes('Files')) return;
      event.preventDefault();event.stopPropagation();void add([...event.dataTransfer.files], target);
    });
  }
  bindDrop(find('#cover-drop'), 'cover');bindDrop(body, 'body');
  body.addEventListener('paste', event => {
    const files = [...(event.clipboardData?.items || [])].filter(item => item.kind === 'file').map(item => item.getAsFile()).filter(Boolean);
    if (!files.length) return; // Normal text/HTML paste keeps the editor's existing behavior.
    event.preventDefault();void add(files, 'body');
  });
  return {isBusy:() => active, refresh, reset:() => {refresh();say('cover','');say('body','');}};
}
