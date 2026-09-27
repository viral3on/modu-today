import sanitizeHtml from 'sanitize-html';
import {parseDocument} from 'htmlparser2';
import render from 'dom-serializer';
import {parse, generate, walk} from 'css-tree';

const scope = '.modu-html-content';
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const id = value => `modu-post-${value.replace(/[^a-zA-Z0-9_-]/g,'-')}`;
const properties = new Set(`color background background-color background-image background-position background-size background-repeat background-clip background-origin opacity border border-top border-right border-bottom border-left border-color border-width border-style border-radius border-collapse border-spacing box-shadow box-sizing outline outline-color outline-width outline-style outline-offset font font-family font-size font-weight font-style font-variant line-height letter-spacing word-spacing text-align text-decoration text-decoration-color text-decoration-thickness text-underline-offset text-transform text-indent text-shadow white-space word-break overflow-wrap vertical-align list-style list-style-type list-style-position display visibility width min-width max-width height min-height max-height margin margin-top margin-right margin-bottom margin-left margin-inline margin-block padding padding-top padding-right padding-bottom padding-left padding-inline padding-block gap row-gap column-gap grid grid-template grid-template-columns grid-template-rows grid-template-areas grid-column grid-row grid-area grid-auto-flow grid-auto-columns grid-auto-rows flex flex-direction flex-wrap flex-flow flex-grow flex-shrink flex-basis align-items align-self align-content justify-content justify-items justify-self order position top right bottom left inset z-index overflow overflow-x overflow-y object-fit object-position aspect-ratio float clear content columns column-count column-width column-rule break-inside caption-side table-layout border-inline border-block border-inline-start border-inline-end border-block-start border-block-end`.split(' '));
const functions = new Set('rgb rgba hsl hsla hwb lab lch oklab oklch color color-mix calc min max clamp var linear-gradient radial-gradient conic-gradient repeating-linear-gradient repeating-radial-gradient repeating-conic-gradient repeat minmax fit-content'.split(' '));
const pseudos = new Set('root hover focus focus-visible focus-within active visited link any-link first-child last-child only-child nth-child nth-last-child first-of-type last-of-type only-of-type nth-of-type nth-last-of-type empty not is where'.split(' '));

function safeValue(node) {
  let safe = true;
  walk(node, item => {
    if (['Raw','Url','Atrule'].includes(item.type) || item.type === 'Function' && !functions.has(item.name.toLowerCase())) safe = false;
  });
  return safe;
}
function declarations(block) {
  const output = [];
  block.children.forEach(node => {
    if (node.type !== 'Declaration') return;
    const property = node.property.toLowerCase();
    if (!properties.has(property) && !/^--[a-z][a-z0-9-]*$/i.test(property)) return;
    if (!safeValue(node.value)) return;
    const value = generate(node.value);
    if (property === 'position' && !['static','relative','absolute','sticky'].includes(value)) return;
    // Source is inserted into an HTML style element, never let CSS strings close it.
    output.push(`${property}:${value}${node.important?'!important':''}`);
  });
  return output.join(';').replace(/</g,'\\3c ').replace(/>/g,'\\3e ');
}
export function sanitizeInlineStyle(source = '') {
  if (source.includes('\\')) return '';
  try {return declarations(parse(source,{context:'declarationList',parseCustomProperty:true}));} catch {return '';}
}
function selectors(list) {
  if (list?.type !== 'SelectorList') return '';
  const output = [];
  list.children.forEach(selector => {
    let safe = true;
    walk(selector, node => {
      if (node.type === 'Raw' || node.type === 'NestingSelector') safe = false;
      if (node.type === 'TypeSelector') {
        if (!/^(?:[a-zA-Z][\w-]*|\*)$/.test(node.name)) safe = false;
        if (node.name.toLowerCase() === 'html' || node.name.toLowerCase() === 'body') {
          const name = node.name.toLowerCase();node.type = 'ClassSelector';node.name = `modu-html-${name}`;
        }
      }
      if (node.type === 'IdSelector') node.name = id(node.name);
      if (node.type === 'PseudoClassSelector') {
        if (!pseudos.has(node.name.toLowerCase())) safe = false;
        if (node.name.toLowerCase() === 'root') {node.type='ClassSelector';node.name='modu-html-html';delete node.children;}
      }
      if (node.type === 'PseudoElementSelector' && !['before','after','marker','first-letter','first-line','selection'].includes(node.name.toLowerCase())) safe=false;
    });
    if (safe) output.push(`${scope} ${generate(selector)}`);
  });
  return output.join(',');
}
export function sanitizeStylesheet(source = '') {
  // Escaped CSS identifiers complicate URL/function validation; ordinary Unicode remains supported.
  if (source.includes('\\')) return '';
  let ast;
  try {ast=parse(source,{parseCustomProperty:true});} catch {return '';}
  function rules(children, depth=0) {
    if (depth>4) return '';
    const output=[];
    children.forEach(node => {
      if (node.type==='Rule') {
        const selector=selectors(node.prelude), body=declarations(node.block);
        if (selector && body) output.push(`${selector}{${body}}`);
      } else if (node.type==='Atrule' && node.name.toLowerCase()==='media' && node.prelude && node.block && safeValue(node.prelude)) {
        const body=rules(node.block.children,depth+1);
        if (body) output.push(`@media ${generate(node.prelude)}{${body}}`);
      }
    });
    return output.join('');
  }
  return rules(ast.children).replace(/</g,'\\3c ');
}
function contentUrl(value, anchor=false) {
  if (!value || /[\u0000-\u0020\\]/.test(value)) return '';
  if (anchor && /^#[\w-]+$/.test(value)) return '#'+id(value.slice(1));
  if (/^\/(?!\/)/.test(value)) return value;
  try {const url=new URL(value);if(url.protocol==='https:' && !url.username && !url.password)return url.href;}catch{}
  return '';
}
const options = {
  allowedTags: ['div','section','article','header','footer','main','aside','p','br','hr','h1','h2','h3','h4','h5','h6','span','strong','b','em','i','u','s','del','ins','mark','small','sub','sup','abbr','time','blockquote','q','cite','pre','code','kbd','samp','ul','ol','li','dl','dt','dd','figure','figcaption','img','a','table','caption','colgroup','col','thead','tbody','tfoot','tr','th','td','details','summary'],
  allowedAttributes: {'*':['class','id','style','title','lang','dir'],a:['href','target','rel'],img:['src','alt','width','height','loading','decoding','referrerpolicy'],th:['colspan','rowspan','scope'],td:['colspan','rowspan'],col:['span'],ol:['start','reversed'],li:['value'],time:['datetime'],details:['open']},
  allowedSchemes:['https'], allowProtocolRelative:false, parseStyleAttributes:false,
  nonTextTags:['style','script','textarea','option','xmp','noscript','head','iframe','object','embed','svg','math','template','form'],
  transformTags: {'*':(tagName, attrs) => {
    const attribs={...attrs};
    if(attribs.style)attribs.style=sanitizeInlineStyle(attribs.style);
    if(attribs.id)attribs.id=id(attribs.id);
    if(tagName==='a') {
      attribs.href=contentUrl(attribs.href,true);attribs.target='_blank';attribs.rel='noopener noreferrer';
      if(attribs.href.startsWith('#'))delete attribs.target;
    }
    if(tagName==='img') {
      attribs.src=contentUrl(attribs.src);attribs.alt=attribs.alt||'';attribs.loading='lazy';attribs.decoding='async';attribs.referrerpolicy='no-referrer';
    }
    return {tagName,attribs};
  }},
  exclusiveFilter: frame => frame.tag==='img' && !frame.attribs.src
};

// Same parser and policy run during server builds, API validation and browser preview.
export function htmlArticle(source, css='') {
  const doc=parseDocument(source), styles=[];
  function collect(nodes) {
    for(const node of nodes) {
      if(node.name==='style')styles.push((node.children||[]).map(n=>n.data||'').join(''));
      else if(node.children && !['script','iframe','object','svg','math','template','noscript'].includes(node.name))collect(node.children);
    }
  }
  collect(doc.children);
  const html=doc.children.find(n=>n.name==='html');
  const body=(html?.children||doc.children).find(n=>n.name==='body');
  const nodes=body?.children||html?.children||doc.children;
  const wrapper=(tag,attrs,content)=>`<div${Object.entries(attrs||{}).filter(([key])=>['class','id','style','lang','dir'].includes(key)).map(([key,value])=>` ${key}="${escape(value)}"`).join('')}><div class="modu-html-${tag}">${content}</div></div>`;
  const clean=sanitizeHtml(wrapper('html',html?.attribs,wrapper('body',body?.attribs,render(nodes))),options);
  const stylesheet=sanitizeStylesheet([...styles,css].join('\n'));
  return `${stylesheet?`<style>${stylesheet}</style>`:''}<div class="modu-html-boundary" style="contain:layout paint style;isolation:isolate;position:relative;min-width:0;overflow:hidden"><div class="modu-html-content">${clean}</div></div>`;
}
export function htmlText(source) {return sanitizeHtml(source,{allowedTags:[],allowedAttributes:{},nonTextTags:options.nonTextTags}).trim();}
