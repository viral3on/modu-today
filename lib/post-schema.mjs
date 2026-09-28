// Source-field validation only. Rendering and HTML sanitization stay outside the serverless API.
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
export function validatePost(input) {
  if (!input || typeof input !== 'object') throw new Error('글 내용을 확인해 주세요.');
  const text = (key, min, max) => {
    if (typeof input[key] !== 'string' || input[key].trim().length < min || input[key].length > max)
      throw new Error(`${key}: ${min}~${max}자로 입력해 주세요.`);
    return input[key].trim();
  };
  const title = text('title', 2, 120), category = text('category', 1, 30);
  const description = text('description', 10, 180), body = text('body', 40, 100000);
  const format = input.format ?? 'markdown';
  if (!['markdown','html'].includes(format)) throw new Error('본문 작성 방식을 확인해 주세요.');
  const css = input.css ?? '';
  if (typeof css !== 'string' || css.length > 30000) throw new Error('추가 CSS는 30,000자 이내로 입력해 주세요.');
  const image = text('image', 0, 2000), imageAlt = text('imageAlt', 0, 160);
  if (image && !safeUrl(image, true)) throw new Error('대표 이미지는 HTTPS 주소 또는 사이트 내부 경로를 사용해 주세요.');
  if (image && !imageAlt) throw new Error('대표 이미지 설명을 입력해 주세요.');
  if (!Array.isArray(input.tags) || input.tags.length > 10 || input.tags.some(t=>typeof t !== 'string' || t.length > 30))
    throw new Error('태그는 30자 이내로 최대 10개까지 입력해 주세요.');
  return {title, category, description, body, format, css, image, imageAlt, tags:[...new Set(input.tags.map(t=>t.trim()).filter(Boolean))]};
}
