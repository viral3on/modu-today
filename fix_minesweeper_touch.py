from pathlib import Path

p = Path('games/minesweeper/index.html')
s = p.read_text(encoding='utf-8')

start = s.find('btn.addEventListener("pointerdown"')
end_marker = 'btn.addEventListener("lostpointercapture",()=>{clearTimeout(pressTimer)});'
end = s.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit(f'pointer block not found start={start} end={end}')
end += len(end_marker)

new = '''btn.addEventListener("pointerdown",e=>{if(e.pointerType!=="touch"&&e.pointerType!=="pen")return;if(activePointer!==null)return;activePointer=e.pointerId;pressLong=false;pressMoved=false;startX=e.clientX;startY=e.clientY;clearTimeout(pressTimer);pressTimer=setTimeout(()=>{if(pressMoved||activePointer!==e.pointerId)return;pressLong=true;suppressClickUntil=performance.now()+1000;toggleFlag(cell);if(navigator.vibrate)navigator.vibrate(45)},430)});
btn.addEventListener("pointermove",e=>{if(e.pointerId!==activePointer)return;if(Math.abs(e.clientX-startX)>10||Math.abs(e.clientY-startY)>10){pressMoved=true;clearTimeout(pressTimer)}});
btn.addEventListener("pointerup",e=>{if(e.pointerId!==activePointer)return;clearTimeout(pressTimer);if(pressLong)suppressClickUntil=performance.now()+900;activePointer=null;pressLong=false;pressMoved=false});
btn.addEventListener("pointercancel",e=>{if(e.pointerId!==activePointer)return;clearTimeout(pressTimer);activePointer=null;pressLong=false;pressMoved=false});
btn.addEventListener("lostpointercapture",()=>{clearTimeout(pressTimer)});'''

s = s[:start] + new + s[end:]
p.write_text(s, encoding='utf-8')
print('Patched minesweeper: native click opens cells; long press only toggles flags; drag remains scrollable.')
