import {htmlArticle, htmlText} from './html-content.mjs';

import {escape, safeUrl, validatePost as validatePostFields} from './post-schema.mjs';
export {CATEGORIES, SITE, ID, escape, safeUrl} from './post-schema.mjs';
export {MAX_IMAGE_BYTES, validateImageFile} from './image-policy.mjs';

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
    else if (/^!\[[^\]\n]*\]\(https:\/\/[^\s)]+\)$/.test(line)) {
      flush();
      const [,alt,source] = /^!\[([^\]\n]*)\]\(([^)]+)\)$/.exec(line);
      const url = safeUrl(source, true);
      output.push(url ? `<img src="${escape(url)}" alt="${escape(alt)}" loading="lazy" decoding="async">` : `<p>${escape(line)}</p>`);
    }
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
  const post = validatePostFields(input);
  if (post.format === 'html' && htmlText(htmlArticle(post.body, post.css)).length < 40)
    throw new Error('HTML 태그를 제외한 글 내용을 40자 이상 작성해 주세요.');
  return post;
}
export function articleBody(post) {
  return `${post.image ? `<img class="article-cover" src="${escape(safeUrl(post.image))}" alt="${escape(post.imageAlt)}" referrerpolicy="no-referrer">` : ''}<div class="prose">${post.format === 'html' ? htmlArticle(post.body, post.css || '') : markdown(post.body)}</div>`;
}
