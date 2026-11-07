(function () {
  'use strict';

  var COLS = 17, ROWS = 10, TIME = 120;   // 세로 화면에서는 10x17로 자동 전환
  var TARGETS = [10, 20];           // 이 합이면 사라진다

  var board = document.getElementById('board');
  var scoreEl = document.getElementById('score');
  var bestEl = document.getElementById('best');
  var timeEl = document.getElementById('time');
  var fill = document.getElementById('timerfill');
  var bar = document.getElementById('timerbar');
  var overlay = document.getElementById('overlay');
  var live = document.getElementById('live');

  var vals = [], cells = [], score = 0, left = 0, timer = null, running = false;
  var start = null, cur = null, best = 0;

  try { best = parseInt(localStorage.getItem('apple1020-best') || '0', 10) || 0; } catch (e) {}
  bestEl.textContent = best;

  // 화면 방향에 맞춰 격자를 17x10(가로) 또는 10x17(세로)로 만든다.
  // 세로 폰에서도 사과 한 칸이 손가락으로 다룰 만한 크기가 된다.
  function buildGrid() {
    var portrait = window.innerHeight > window.innerWidth * 1.1;
    COLS = portrait ? 10 : 17;
    ROWS = portrait ? 17 : 10;
    document.documentElement.style.setProperty('--cols', COLS);
    document.documentElement.style.setProperty('--rows', ROWS);
    board.innerHTML = '';
    cells = [];
    for (var i = 0; i < COLS * ROWS; i++) {
      var c = document.createElement('div');
      c.className = 'cell';
      c.innerHTML = '<div class="apple"></div>';
      board.appendChild(c);
      cells.push(c);
    }
  }

  function newBoard() {
    if (!running) buildGrid();
    vals = [];
    var sum = 0;
    for (var i = 0; i < COLS * ROWS; i++) {
      var v = 1 + Math.floor(Math.random() * 9);
      vals.push(v);
      sum += v;
    }
    // 전체 합을 10의 배수로 맞춰 모두 지울 수 있는 가능성을 남긴다
    var r = sum % 10;
    if (r) {
      var last = vals[vals.length - 1];
      var nv = last + (10 - r);
      if (nv > 9) nv = last - r;
      if (nv < 1) nv = 1;
      vals[vals.length - 1] = nv;
    }
    cells.forEach(function (c, i) {
      c.className = 'cell';
      c.firstChild.textContent = vals[i];
    });
  }

  function rectOf(a, b) {
    return { r1: Math.min(a.r, b.r), r2: Math.max(a.r, b.r), c1: Math.min(a.c, b.c), c2: Math.max(a.c, b.c) };
  }
  function inRect(rc, fn) {
    for (var r = rc.r1; r <= rc.r2; r++) for (var c = rc.c1; c <= rc.c2; c++) fn(r * COLS + c);
  }
  function sumOf(rc) {
    var s = 0, n = 0;
    inRect(rc, function (i) { if (vals[i]) { s += vals[i]; n++; } });
    return { s: s, n: n };
  }
  function isTarget(s) { return TARGETS.indexOf(s) !== -1; }

  // 보드 좌표 → 격자 칸. 화면 크기와 무관하게 비율로 계산하므로 폰·태블릿 모두 동일하게 동작
  function pos(e) {
    var b = board.getBoundingClientRect();
    var c = Math.floor((e.clientX - b.left) / b.width * COLS);
    var r = Math.floor((e.clientY - b.top) / b.height * ROWS);
    return { r: Math.max(0, Math.min(ROWS - 1, r)), c: Math.max(0, Math.min(COLS - 1, c)) };
  }

  function clearSel() {
    cells.forEach(function (c) { c.classList.remove('sel', 'good'); });
  }
  function paint() {
    clearSel();
    if (!start || !cur) return;
    var rc = rectOf(start, cur), t = sumOf(rc), good = isTarget(t.s);
    inRect(rc, function (i) {
      cells[i].classList.add('sel');
      if (good) cells[i].classList.add('good');
    });
    live.innerHTML = '합계 <b>' + t.s + '</b> · 사과 ' + t.n + '개' + (good ? ' <span class="ok">→ 놓으면 사라져요</span>' : '');
  }

  var activePointer = null;
  board.addEventListener('pointerdown', function (e) {
    if (!running || activePointer !== null) return;   // 멀티터치는 첫 손가락만 사용
    e.preventDefault();
    activePointer = e.pointerId;
    try { board.setPointerCapture(e.pointerId); } catch (x) {}
    start = cur = pos(e);
    paint();
  });
  board.addEventListener('pointermove', function (e) {
    if (e.pointerId !== activePointer || !start) return;
    cur = pos(e);
    paint();
  });
  function end(e, commit) {
    if (e.pointerId !== activePointer) return;
    activePointer = null;
    if (commit && start) release();
    start = cur = null;
    clearSel();
  }
  board.addEventListener('pointerup', function (e) { end(e, true); });
  board.addEventListener('pointercancel', function (e) { end(e, false); });
  board.addEventListener('contextmenu', function (e) { e.preventDefault(); });

  function release() {
    var rc = rectOf(start, cur), t = sumOf(rc);
    if (isTarget(t.s)) {
      inRect(rc, function (i) {
        if (!vals[i]) return;
        vals[i] = 0;
        var c = cells[i];
        c.classList.add('pop');
        setTimeout(function () { c.classList.remove('pop'); c.classList.add('gone'); }, 340);
      });
      score += t.n;
      scoreEl.textContent = score;
      live.innerHTML = '합 <b>' + t.s + '</b> 성공! +' + t.n + '점';
      if (navigator.vibrate) { try { navigator.vibrate(15); } catch (x) {} }
    } else {
      live.innerHTML = t.n ? '합이 ' + t.s + '이에요. 10이나 20이 필요합니다.' : '&nbsp;';
    }
  }

  function tick() {
    left--;
    timeEl.textContent = left;
    fill.style.transform = 'scaleX(' + (left / TIME) + ')';
    bar.classList.toggle('low', left <= 20);
    if (left <= 0) finish();
  }

  function finish() {
    clearInterval(timer);
    running = false;
    start = cur = null;
    activePointer = null;
    clearSel();
    var newBest = score > best;
    if (newBest) {
      best = score;
      bestEl.textContent = best;
      try { localStorage.setItem('apple1020-best', String(best)); } catch (e) {}
    }
    document.getElementById('ov-title').textContent = score + '점';
    document.getElementById('ov-text').textContent = newBest ? '최고 기록을 새로 세웠어요.' : '최고 기록은 ' + best + '점입니다.';
    document.getElementById('start').textContent = '다시 하기';
    overlay.hidden = false;
  }

  document.getElementById('start').addEventListener('click', function () {
    score = 0;
    scoreEl.textContent = 0;
    left = TIME;
    timeEl.textContent = left;
    fill.style.transform = 'scaleX(1)';
    bar.classList.remove('low');
    newBoard();
    overlay.hidden = true;
    live.innerHTML = '&nbsp;';
    running = true;
    clearInterval(timer);
    timer = setInterval(tick, 1000);
  });

  // 시작 전에도 보드를 미리 보여준다. 대기 화면에서 기기를 돌리면 격자도 다시 만든다.
  newBoard();
  window.addEventListener('resize', function () { if (!running) newBoard(); });
})();
