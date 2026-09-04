from pathlib import Path
import re

p = Path('games/minesweeper/index.html')
s = p.read_text(encoding='utf-8')

new = '''btn.addEventListener("touchstart",e=>{if(e.touches.length!==1)return;clearTimeout(touchTimer);touchLong=false;touchMoved=false;const t=e.touches[0];touchStartX=t.clientX;touchStartY=t.clientY;touchTimer=setTimeout(()=>{if(touchMoved)return;touchLong=true;suppressClickUntil=performance.now()+900;toggleFlag(cell);if(navigator.vibrate)navigator.vibrate(45)},430)},{passive:true});
btn.addEventListener("touchmove",e=>{if(e.touches.length!==1)return;const t=e.touches[0];if(Math.abs(t.clientX-touchStartX)>10||Math.abs(t.clientY-touchStartY)>10){touchMoved=true;clearTimeout(touchTimer)}},{passive:true});
btn.addEventListener("touchend",()=>{clearTimeout(touchTimer);touchLong=false;touchMoved=false},{passive:true});
btn.addEventListener("touchcancel",()=>{clearTimeout(touchTimer);touchLong=false;touchMoved=false},{passive:true});'''

pattern = r'btn\.addEventListener\("touchstart".*?btn\.addEventListener\("touchcancel".*?\}\);'
patched, n = re.subn(pattern, new, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f'Expected exactly one touch handler block, found {n}')

p.write_text(patched, encoding='utf-8')
print('Updated minesweeper: tap=click/open, long press=flag, drag=scroll.')
