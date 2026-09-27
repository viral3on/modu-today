export const CATEGORIES = ['생활', 'IT', '자동차', '부동산', '경제', '주식', '취미'];
export const SITE = 'https://modu.today';
export const ID = /^[a-z0-9][a-z0-9-]{7,79}$/;
export const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
export function safeUrl(value, image = false) {
  if (!value) return '';
  if (/^\/(?!\/)[^\s<>\\]*$/.test(value)) return value;
  try {
    const url = new URL(value);
    if (url.protocol === 'https:' && !url.username && !url.password) return url.href;
  } catch {}
  return '';
}
function inline(text) {
  const parts = String(text).split(/(\[[^\]\n]+\]\([^\s)]+\))/g);
  return parts.map(part => {
    const link = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(part);
    if (link) {
      const url = safeUrl(link[2]);
      return url ? `<a href="${escape(url)}" rel="noopener noreferrer">${escape(link[1])}</a>` : escape(link[1]);
    }
    return escape(part).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/`([^`]+)`/g, '<code>$1</code>');
  }).join('');
}
// Deliberately small Markdown vocabulary; raw HTML, embeds and scripts stay text.
// Shared by the server build and isolated editor preview to avoid renderer drift.
export function markdown(source) {
  const lines = String(source).replace(/\r/g, '').split('\n');
  const output = [];
  let paragraph = [], list = [], listType = '', code = null;
  function flush() {
    if (paragraph.length) output.push(`<p>${inline(paragraph.join('\n')).replace(/\n/g, '<br>')}</p>`);
    if (list.length) output.push(`<${listType}>${list.map(s=>`<li>${inline(s)}</li>`).join('')}</${listType}>`);
    paragraph = []; list = []; listType = '';
  }
  for (const line of lines) {
    if (line.startsWith('```')) {
      flush();
      if (code !== null) { output.push(`<pre><code>${escape(code.join('\n'))}</code></pre>`); code = null; }
      else code = [];
    } else if (code !== null) code.push(line);
    else if (!line.trim()) flush();
    else if (/^#{1,3} /.test(line)) {
      flush(); const [, hashes, text] = /^(#{1,3}) (.*)$/.exec(line);
      const level = Math.min(hashes.length + 1, 4);
      output.push(`<h${level}>${inline(text)}</h${level}>`);
    } else if (/^([-*]|\d+\.) /.test(line)) {
      const type = /^\d/.test(line) ? 'ol' : 'ul';
      if (paragraph.length || listType && listType !== type) flush();
      listType = type; list.push(line.replace(/^([-*]|\d+\.) /, ''));
    } else { if (list.length) flush(); paragraph.push(line); }
  }
  flush(); if (code !== null) output.push(`<pre><code>${escape(code.join('\n'))}</code></pre>`);
  return output.join('\n');
}
export function validatePost(input) {
  if (!input || typeof input !== 'object') throw new Error('글 내용을 확인해 주세요.');
  const text = (key, min, max) => {
    if (typeof input[key] !== 'string' || input[key].trim().length < min || input[key].length > max)
      throw new Error(`${key}: ${min}~${max}자로 입력해 주세요.`);
    return input[key].trim();
  };
  const title = text('title', 2, 120), category = text('category', 1, 30);
  const description = text('description', 10, 180), body = text('body', 40, 100000);
  const image = text('image', 0, 2000), imageAlt = text('imageAlt', 0, 160);
  if (image && !safeUrl(image, true)) throw new Error('대표 이미지는 HTTPS 주소 또는 사이트 내부 경로를 사용해 주세요.');
  if (image && !imageAlt) throw new Error('대표 이미지 설명을 입력해 주세요.');
  if (!Array.isArray(input.tags) || input.tags.length > 10 || input.tags.some(t=>typeof t !== 'string' || t.length > 30))
    throw new Error('태그는 30자 이내로 최대 10개까지 입력해 주세요.');
  return {title, category, description, body, image, imageAlt, tags:[...new Set(input.tags.map(t=>t.trim()).filter(Boolean))]};
}
export function articleBody(post) {
  return `${post.image ? `<img class="article-cover" src="${escape(safeUrl(post.image))}" alt="${escape(post.imageAlt)}" referrerpolicy="no-referrer">` : ''}<div class="prose">${markdown(post.body)}</div>`;
}
