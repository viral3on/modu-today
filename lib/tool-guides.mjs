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
  if (file === 'games/block-game/index.html') {
    const info = /<section class="game-info"[^>]*>[\s\S]*?<\/section>/;
    if (!info.test(html)) throw new Error('Missing block game instructions');
    // Keep one complete guide beside the game, before its footer. Scheduled SEO
    // refreshes can recreate the legacy anchor; consume it rather than append it.
    html = html.replace(anchor, '').replace(/<!-- CRAWL_LINKS_START -->[\s\S]*?<!-- CRAWL_LINKS_END -->/g, '');
    return html.replace(info, `<section class="game-info" id="tool-guide" aria-labelledby="gameInfoTitle"><h1 id="gameInfoTitle">MODU BLOCKS 블록 퍼즐 게임</h1><p>설치나 회원가입 없이 블록을 쌓고 가로줄을 지우는 게임입니다.</p><h2>조작 방법</h2><p>PC에서는 ← → 이동, ↑ 회전, ↓ 빠른 낙하, SPACE 즉시 낙하, C HOLD, P 일시정지입니다. 모바일에서는 게임판을 탭해 회전하고 좌우로 밀어 이동합니다. 아래로 짧게 밀면 빠른 낙하, 길고 빠르게 밀면 즉시 낙하합니다. 화면의 버튼으로도 조작할 수 있습니다.</p>${guide.body}<p><a href="/games/">게임 전체보기</a></p><p class="modu-guide-note">설명과 화면 확인: 2026.11.26 · <a href="/contact/">오류 제보</a></p></section>`);
  }
  return html.replace(anchor, `<section class="modu-tool-guide" id="tool-guide" aria-labelledby="tool-guide-title"><h2 id="tool-guide-title">${e(guide.title)}</h2>${guide.body}<p class="modu-guide-note">설명과 예제 확인: 2026.11.07 · <a href="/contact/">오류 제보</a></p></section>`);
}
