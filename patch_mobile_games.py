from pathlib import Path

# Minesweeper: make long-press flagging reliable on mobile and suppress the follow-up click.
p = Path('games/minesweeper/index.html')
text = p.read_text(encoding='utf-8')
text = text.replace('let difficulty="beginner",cfg=CONFIG[difficulty],cells=[],firstMove=true,gameOver=false,openedCount=0,flags=0,seconds=0,timerId=null,flagMode=false,soundEnabled=true,audioCtx=null,longPressTimer=null,longPressTriggered=false;', 'let difficulty="beginner",cfg=CONFIG[difficulty],cells=[],firstMove=true,gameOver=false,openedCount=0,flags=0,seconds=0,timerId=null,flagMode=false,soundEnabled=true,audioCtx=null,longPressTimer=null,longPressTriggered=false,suppressClickUntil=0,longPressPointerId=null;')
old = '''btn.addEventListener("click",e=>{e.preventDefault();if(longPressTriggered){longPressTriggered=false;return}handlePrimary(cell)});btn.addEventListener("contextmenu",e=>{e.preventDefault();toggleFlag(cell)});btn.addEventListener("pointerdown",e=>{if(e.pointerType==="mouse")return;longPressTriggered=false;clearTimeout(longPressTimer);longPressTimer=setTimeout(()=>{longPressTriggered=true;toggleFlag(cell);if(navigator.vibrate)navigator.vibrate(30)},520)});const cancel=()=>clearTimeout(longPressTimer);btn.addEventListener("pointerup",cancel);btn.addEventListener("pointercancel",cancel);btn.addEventListener("pointerleave",cancel);'''
new = '''btn.addEventListener("click",e=>{e.preventDefault();if(performance.now()<suppressClickUntil||longPressTriggered){longPressTriggered=false;return}handlePrimary(cell)});btn.addEventListener("contextmenu",e=>{e.preventDefault();toggleFlag(cell)});btn.addEventListener("pointerdown",e=>{if(e.pointerType==="mouse")return;e.preventDefault();longPressTriggered=false;longPressPointerId=e.pointerId;clearTimeout(longPressTimer);try{btn.setPointerCapture(e.pointerId)}catch(_e){}longPressTimer=setTimeout(()=>{longPressTriggered=true;suppressClickUntil=performance.now()+900;toggleFlag(cell);if(navigator.vibrate)navigator.vibrate(35)},460)});const cancel=e=>{clearTimeout(longPressTimer);if(e&&longPressPointerId===e.pointerId){try{btn.releasePointerCapture(e.pointerId)}catch(_e){}longPressPointerId=null}};btn.addEventListener("pointerup",cancel);btn.addEventListener("pointercancel",cancel);'''
if old not in text:
    raise SystemExit('minesweeper event block not found')
text = text.replace(old, new)
text = text.replace('.cell{width:32px;height:32px;', '.cell{width:32px;height:32px;touch-action:none;-webkit-touch-callout:none;')
p.write_text(text, encoding='utf-8')

# Block game: add direct touch gestures on the board and prevent browser pull-to-refresh while playing.
p = Path('games/block-game/index.html')
text = p.read_text(encoding='utf-8')
text = text.replace('''#board{\n  display:block;\n  width:100%;\n  aspect-ratio:10/20;\n  background:#090d18;\n}''', '''#board{\n  display:block;\n  width:100%;\n  aspect-ratio:10/20;\n  background:#090d18;\n  touch-action:none;\n  -webkit-touch-callout:none;\n  user-select:none;\n}\n\n.board-wrap{\n  overscroll-behavior:contain;\n  touch-action:none;\n}''')
text = text.replace('''      모바일에서는 게임 아래의 조작 버튼으로 동일하게 플레이할 수 있습니다.''', '''      모바일에서는 게임판을 직접 터치해 조작할 수도 있습니다. 짧게 탭하면 회전하고, 좌우 스와이프로 이동하며, 아래로 스와이프하면 빠르게 내립니다. 길고 빠른 아래 스와이프는 하드드롭으로 동작합니다. 아래 조작 버튼도 그대로 사용할 수 있습니다.''')
marker = '''bindButton(\n  "soundBtn",\n  () => setSoundEnabled(!soundEnabled)\n);\n'''
insert = marker + r'''

// 모바일 게임판 직접 제스처 조작
// 탭: 회전 / 좌우 스와이프: 이동 / 아래 스와이프: 소프트드롭 / 빠르고 긴 아래 스와이프: 하드드롭
let touchGesture = null;

canvas.addEventListener("pointerdown", e => {
  if(e.pointerType === "mouse") return;
  if(!running || paused) return;
  e.preventDefault();
  try{ canvas.setPointerCapture(e.pointerId); }catch(_e){}
  touchGesture = {
    id:e.pointerId,
    x:e.clientX,
    y:e.clientY,
    lastX:e.clientX,
    lastY:e.clientY,
    started:performance.now(),
    moved:false
  };
}, {passive:false});

canvas.addEventListener("pointermove", e => {
  if(!touchGesture || e.pointerId !== touchGesture.id) return;
  e.preventDefault();
  const dx = e.clientX - touchGesture.lastX;
  const dy = e.clientY - touchGesture.lastY;
  const totalX = e.clientX - touchGesture.x;
  const totalY = e.clientY - touchGesture.y;
  if(Math.abs(totalX) > 8 || Math.abs(totalY) > 8) touchGesture.moved = true;

  // 좌우 드래그 중에는 약 34px마다 한 칸씩 즉시 이동
  if(Math.abs(dx) >= 34 && Math.abs(totalX) > Math.abs(totalY)){
    move(dx > 0 ? 1 : -1);
    touchGesture.lastX = e.clientX;
  }

  // 아래로 드래그 중에는 약 38px마다 한 칸씩 빠르게 내림
  if(dy >= 38 && totalY > Math.abs(totalX)){
    softDrop();
    touchGesture.lastY = e.clientY;
  }
}, {passive:false});

function finishBoardGesture(e){
  if(!touchGesture || e.pointerId !== touchGesture.id) return;
  e.preventDefault();
  const g = touchGesture;
  touchGesture = null;
  try{ canvas.releasePointerCapture(e.pointerId); }catch(_e){}

  const dx = e.clientX - g.x;
  const dy = e.clientY - g.y;
  const duration = Math.max(1, performance.now() - g.started);
  const distance = Math.hypot(dx,dy);

  // 거의 움직이지 않은 짧은 탭은 회전
  if(distance < 18 && duration < 420){
    rotate();
    return;
  }

  // 빠르거나 충분히 긴 아래 스와이프는 즉시 하드드롭
  if(dy > 85 && dy > Math.abs(dx) * 1.15 && (duration < 520 || dy > 145)){
    hardDrop();
    return;
  }

  // 손을 뗄 때 남은 좌우 이동량도 반영
  if(Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy)){
    const steps = Math.min(4, Math.max(1, Math.round(Math.abs(dx)/55)));
    for(let i=0;i<steps;i++) move(dx > 0 ? 1 : -1);
    return;
  }

  // 짧은 아래 스와이프는 몇 칸 소프트드롭
  if(dy > 30 && dy > Math.abs(dx)){
    const steps = Math.min(5, Math.max(1, Math.round(dy/40)));
    for(let i=0;i<steps;i++) softDrop();
  }
}

canvas.addEventListener("pointerup", finishBoardGesture, {passive:false});
canvas.addEventListener("pointercancel", e => {
  if(touchGesture && e.pointerId === touchGesture.id){
    touchGesture = null;
  }
}, {passive:false});
'''
if marker not in text:
    raise SystemExit('block-game insertion marker not found')
text = text.replace(marker, insert)
p.write_text(text, encoding='utf-8')

print('patched mobile minesweeper and block-game controls')
