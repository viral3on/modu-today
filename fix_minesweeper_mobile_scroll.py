from pathlib import Path

p = Path('games/minesweeper/index.html')
text = p.read_text(encoding='utf-8')
old = text

# Let mobile drag gestures reach the scroll container/page instead of being cancelled by each cell.
text = text.replace('.cell{width:32px;height:32px;touch-action:none;', '.cell{width:32px;height:32px;touch-action:pan-x pan-y;')
text = text.replace('btn.addEventListener("touchstart",e=>{if(e.touches.length!==1)return;e.preventDefault();clearTimeout(touchTimer);', 'btn.addEventListener("touchstart",e=>{if(e.touches.length!==1)return;clearTimeout(touchTimer);')
text = text.replace('btn.addEventListener("touchmove",e=>{if(e.touches.length!==1)return;e.preventDefault();const t=e.touches[0];', 'btn.addEventListener("touchmove",e=>{if(e.touches.length!==1)return;const t=e.touches[0];')
text = text.replace('btn.addEventListener("touchend",e=>{e.preventDefault();clearTimeout(touchTimer);', 'btn.addEventListener("touchend",e=>{clearTimeout(touchTimer);')
text = text.replace('btn.addEventListener("touchcancel",e=>{e.preventDefault();clearTimeout(touchTimer);', 'btn.addEventListener("touchcancel",e=>{clearTimeout(touchTimer);')

# On phones keep the board inside a dedicated horizontal scroller with visible momentum scrolling.
text = text.replace('@media(max-width:700px){.page{padding:10px}', '@media(max-width:700px){html,body{overflow-x:hidden}.page{padding:10px}')
text = text.replace('.board-wrap{justify-content:flex-start;padding:12px}', '.board-wrap{justify-content:flex-start;padding:12px;max-width:100%;overflow-x:auto;overflow-y:visible;overscroll-behavior-x:contain;touch-action:pan-x pan-y}')

if text == old:
    raise SystemExit('No matching minesweeper mobile code found; refusing empty patch')
p.write_text(text, encoding='utf-8')
print('patched minesweeper mobile scrolling')
