import {createHash} from 'node:crypto';

// One publisher identity for generated articles and the independently maintained tools.
export const ADSENSE_CLIENT = 'ca-pub-6122968996738347';
export const ADSENSE_URL = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${ADSENSE_CLIENT}`;
export const ADS_TXT = 'google.com, pub-6122968996738347, DIRECT, f08c47fec0942fa0';

export function adsEnabled(file) {
  return file === 'index.html' || /^(?:reading|tools|apt|lotto|calculator|games|youtube)\/.*\.html$/.test(file);
}

// Static pages cannot safely reuse a nonce. Trust this exact bootstrap by its hash,
// then let strict-dynamic trust scripts loaded by it (including Google's descendants).
// URLs are literals: article content, query strings and DOM attributes cannot choose them.
export const READING_BOOTSTRAP = `(()=>{const ad=document.createElement('script');ad.async=true;ad.src=${JSON.stringify(ADSENSE_URL)};ad.crossOrigin='anonymous';document.head.appendChild(ad);const ready=()=>{if(document.getElementById('reading-query')){const search=document.createElement('script');search.type='module';search.src='/assets/reading.js';document.head.appendChild(search);}const analytics=document.createElement('script');analytics.src='/_vercel/insights/script.js';document.head.appendChild(analytics);};if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready,{once:true});else ready();})();`;
export const READING_HASH = `sha256-${createHash('sha256').update(READING_BOOTSTRAP).digest('base64')}`;
// AdSense documents unsafe-eval and unrestricted ad resource destinations. Keep
// script injection, object/embed and base-tag protections; don't maintain a brittle
// Google host allowlist or disable CSP. Admin retains its separate, tighter policy.
export const READING_CSP = `script-src '${READING_HASH}' 'strict-dynamic' 'unsafe-eval'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'self'`;

export function applyAdsense(html, file) {
  // Normalize old calculator snippets so every eligible output has exactly one loader.
  html = html.replace(/<script\b[^>]*\bsrc=["']https:\/\/pagead2\.googlesyndication\.com\/pagead\/js\/adsbygoogle\.js[^"']*["'][^>]*>\s*<\/script>/gi, '')
    .replace(/<meta\b(?=[^>]*\bname=["']google-adsense-account["'])[^>]*>/gi, '');
  if (!adsEnabled(file)) return html;
  let code = `<script async src="${ADSENSE_URL}" crossorigin="anonymous"></script>`;
  if (file.startsWith('reading/')) {
    html = html.replace(/<script\b[^>]*\bsrc=["'](?:\/assets\/reading\.js|\/_vercel\/insights\/script\.js)["'][^>]*>\s*<\/script>/gi, '')
      .replace(/<script data-modu-reading-bootstrap>[\s\S]*?<\/script>/g, '');
    code = `<script data-modu-reading-bootstrap>${READING_BOOTSTRAP}</script>`;
  }
  if (!/<\/head>/i.test(html)) throw new Error(`Missing head for AdSense: ${file}`);
  return html.replace(/<\/head>/i, `<meta name="google-adsense-account" content="${ADSENSE_CLIENT}">${code}</head>`);
}

export function validateAdsenseConfig(config, adsTxt) {
  const policy = config.headers?.find(rule=>rule.source==='/reading/(.*)')?.headers?.find(header=>header.key.toLowerCase()==='content-security-policy')?.value;
  if (policy !== READING_CSP) throw new Error('Reading CSP does not match the trusted AdSense bootstrap');
  if (!adsTxt.split(/\r?\n/).some(line=>line.trim()===ADS_TXT)) throw new Error('ads.txt publisher does not match the AdSense client');
}
