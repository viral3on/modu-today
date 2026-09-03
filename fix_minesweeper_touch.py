from pathlib import Path

p = Path('games/minesweeper/index.html')
s = p.read_text(encoding='utf-8')

old = '''btn.addEventListener("click",e=>{e.preventDefault();if(performance.now()<suppressClickUntil||longPressTriggered){longPressTriggered=false;return}handlePrimary(cell)});btn.addEventListener("contextmenu",e=>{e.preventDefault();toggleFlag(cell)});btn.addEventListener("pointerdown",e=>{if(e.pointerType==="mouse")return;e.preventDefault();longPressTriggered=false;longPressPointerId=e.pointerId;clearTimeout(longPressTimer);try{btn.setPointerCapture(e.pointerId)}catch(_e){}longPressTimer=setTimeout(()=>{longPressTriggered=true;suppressClickUntil=performance.now()+900;toggleFlag(cell);if(navigator.vibrate)navigator.vibrate(35)},460)});const cancel=e=>{clearTimeout(longPressTimer);if(e&&longPressPointerId===e.pointerId){try{btn.releasePointerCapture(e.pointerId)}catch(_e){}longPressPointerId=null}};btn.addEventListener("pointerup",cancel);btn.addEventListener("pointercancel",cancel);'''

new = '''let touchTimer=null,touchLong=false,touchStartX=0,touchStartY=0,touchMoved=false;
btn.addEventListener("click",e=>{e.preventDefault();if(performance.now()<suppressClickUntil)return;handlePrimary(cell)});
btn.addEventListener("contextmenu",e=>{e.preventDefault();toggleFlag(cell)});
btn.addEventListener("touchstart",e=>{if(e.touches.length!==1)return;e.preventDefault();clearTimeout(touchTimer);touchLong=false;touchMoved=false;const t=e.touches[0];touchStartX=t.clientX;touchStartY=t.clientY;touchTimer=setTimeout(()=>{if(touchMoved)return;touchLong=true;suppressClickUntil=performance.now()+1000;toggleFlag(cell);if(navigator.vibrate)navigator.vibrate(45)},420)},{passive:false});
btn.addEventListener("touchmove",e=>{if(e.touches.length!==1)return;e.preventDefault();const t=e.touches[0];if(Math.abs(t.clientX-touchStartX)>12||Math.abs(t.clientY-touchStartY)>12){touchMoved=true;clearTimeout(touchTimer)}},{passive:false});
btn.addEventListener("touchend",e=>{e.preventDefault();clearTimeout(touchTimer);suppressClickUntil=performance.now()+700;if(!touchLong&&!touchMoved)handlePrimary(cell);touchLong=false;touchMoved=false},{passive:false});
btn.addEventListener("touchcancel",e=>{e.preventDefault();clearTimeout(touchTimer);touchLong=false;touchMoved=false},{passive:false});'''

if old not in s:
    raise SystemExit('Expected old mobile handler not found; refusing to modify file')

s = s.replace(old, new, 1)
s = s.replace('길게 누르기</b>하면 깃발을 꽂습니다.', '약 0.4초 길게 누르기</b>하면 깃발을 꽂습니다.', 1)
p.write_text(s, encoding='utf-8')
print('Updated minesweeper mobile touch handling.')
