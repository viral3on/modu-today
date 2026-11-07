import {escape as e} from './content.mjs';

// Replace the legacy generated explanation at build time, after scheduled source
// refreshes. A missing anchor is a build error, never a silently dropped guide.
export function applyToolGuide(html, file, guides) {
  const guide = guides[file];
  if (!guide) return html;
  if (!guide.title || !guide.body || /<script|<iframe|\son\w+\s*=/i.test(guide.body)) throw new Error(`Invalid tool guide: ${file}`);
  const anchor = /<section class="detail-seo" data-static-seo="1">[\s\S]*?<\/section>/g;
  if ([...html.matchAll(anchor)].length !== 1) throw new Error(`Expected one tool guide anchor: ${file}`);
  html = html.replace(/<section class="modu-seo">[\s\S]*?<\/section>/g, '');
  return html.replace(anchor, `<section class="modu-tool-guide" id="tool-guide" aria-labelledby="tool-guide-title"><h2 id="tool-guide-title">${e(guide.title)}</h2>${guide.body}<p class="modu-guide-note">설명과 예제 확인: 2026.11.07 · <a href="/contact/">오류 제보</a></p></section>`);
}
