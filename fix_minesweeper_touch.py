from pathlib import Path

p = Path('games/minesweeper/index.html')
s = p.read_text(encoding='utf-8')

start = s.find('btn.addEventListener("touchstart"')
end = s.find('boardEl.appendChild(btn)', start)
if start < 0 or end < 0:
    raise SystemExit(f'touch block not found start={start} end={end}')

new = '''btn.addEventListener("touchstart",e=>{if(e.touches.length!==1)return;clearTimeout(touchTimer);touchLong=false;touchMoved=false;const t=e.touches[0];touchStartX=t.clientX;touchStartY=t.clientY;touchTimer=setTimeout(()=>{if(touchMoved)return;touchLong=true;suppressClickUntil=performance.now()+900;toggleFlag(cell);if(navigator.vibrate)navigator.vibrate(45)},430)},{passive:true});
btn.addEventListener("touchmove",e=>{if(e.touches.length!==1)return;const t=e.touches[0];if(Math.abs(t.clientX-touchStartX)>10||Math.abs(t.clientY-touchStartY)>10){touchMoved=true;clearTimeout(touchTimer)}},{passive:true});
btn.addEventListener("touchend",()=>{clearTimeout(touchTimer);touchLong=false;touchMoved=false},{passive:true});
btn.addEventListener("touchcancel",()=>{clearTimeout(touchTimer);touchLong=false;touchMoved=false},{passive:true});'''

s = s[:start] + new + s[end:]
p.write_text(s, encoding='utf-8')
print('Updated minesweeper: short tap opens via click, long press flags, drag scrolls.')
