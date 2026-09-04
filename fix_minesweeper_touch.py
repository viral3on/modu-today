from pathlib import Path

p = Path('games/minesweeper/index.html')
s = p.read_text(encoding='utf-8')

old = '''btn.addEventListener("touchstart",e=>{if(e.touches.length!==1)return;clearTimeout(touchTimer);touchLong=false;touchMoved=false;const t=e.touches[0];touchStartX=t.clientX;touchStartY=t.clientY;touchTimer=setTimeout(()=>{if(touchMoved)return;touchLong=true;suppressClickUntil=performance.now()+1000;toggleFlag(cell);if(navigator.vibrate)navigator.vibrate(45)},420)},{passive:false});
btn.addEventListener("touchmove",e=>{if(e.touches.length!==1)return;const t=e.touches[0];if(Math.abs(t.clientX-touchStartX)>12||Math.abs(t.clientY-touchStartY)>12){touchMoved=true;clearTimeout(touchTimer)}},{passive:false});
btn.addEventListener("touchend",e=>{clearTimeout(touchTimer);suppressClickUntil=performance.now()+700;if(!touchLong&&!touchMoved)handlePrimary(cell);touchLong=false;touchMoved=false},{passive:false});
btn.addEventListener("touchcancel",e=>{clearTimeout(touchTimer);touchLong=false;touchMoved=false},{passive:false});'''

new = '''btn.addEventListener("touchstart",e=>{if(e.touches.length!==1)return;clearTimeout(touchTimer);touchLong=false;touchMoved=false;const t=e.touches[0];touchStartX=t.clientX;touchStartY=t.clientY;touchTimer=setTimeout(()=>{if(touchMoved)return;touchLong=true;suppressClickUntil=performance.now()+900;toggleFlag(cell);if(navigator.vibrate)navigator.vibrate(45)},430)},{passive:true});
btn.addEventListener("touchmove",e=>{if(e.touches.length!==1)return;const t=e.touches[0];if(Math.abs(t.clientX-touchStartX)>10||Math.abs(t.clientY-touchStartY)>10){touchMoved=true;clearTimeout(touchTimer)}},{passive:true});
btn.addEventListener("touchend",()=>{clearTimeout(touchTimer);touchLong=false;touchMoved=false},{passive:true});
btn.addEventListener("touchcancel",()=>{clearTimeout(touchTimer);touchLong=false;touchMoved=false},{passive:true});'''

if old not in s:
    raise SystemExit('Expected current touch handler not found; refusing to modify file')

s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('Updated minesweeper: normal tap uses click; long press toggles flag; drag scrolls board.')
