# -*- coding: utf-8 -*-
"""CSV から 遠征計画_座標マップ.html を生成（Canvas 描画で軽量）。"""
import csv
import json
import re
from pathlib import Path

BASE = Path(__file__).parent
CSV_PATH = BASE / "遠征計画_座標別一覧.csv"
OUT_PATH = BASE / "遠征計画_座標マップ.html"

# 完全自動連動: 砦攻略のAPIを指定するとマップが常に最新の攻略状況を取得する（未設定時は同梱の fort_status.json を使用）
FORT_STATUS_URL = ""  # 例: "https://npc-strategy-sheet.vercel.app/api/fort_status"


def star_level(s):
    m = re.search(r"★?(\d+)", s or "")
    return int(m.group(1)) if m else 1


def main():
    points = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for row in r:
            x, y = int(row["X"]), int(row["Y"])
            kind = row["種別"]
            list_id = "cw" if "cw2" in kind else "em"
            auto_url = (row.get("自動出兵SC") or "").strip()
            map_url = (row.get("MAP") or "").strip()
            points.append({
                "x": x, "y": y, "n": row["名称"], "s": row["★"],
                "st": star_level(row["★"]), "l": list_id, "u": auto_url, "m": map_url
            })

    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    pad = 80
    x_min -= pad
    x_max += pad
    y_min -= pad
    y_max += pad
    w, h = x_max - x_min, y_max - y_min
    if w < 800:
        w = 800
        x_min = (x_min + x_max) / 2 - 400
        x_max = x_min + 800
    if h < 800:
        h = 800
        y_min = (y_min + y_max) / 2 - 400
        y_max = y_min + 800

    grid_step = 400 if (w > 2000 or h > 2000) else 200

    # JSON: </ を \u003c/ にして script タグを閉じないようにする
    fort_json = json.dumps(points, ensure_ascii=False).replace("</", "\\u003c/")
    view_json = json.dumps({"xMin": x_min, "yMax": y_max, "w": w, "h": h, "gridStep": grid_step})
    fort_status_url_js = json.dumps(FORT_STATUS_URL)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>遠征計画 座標マップ（シート状配置）</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: "Meiryo","Yu Gothic",sans-serif; margin: 12px; background: #1a1a2e; color: #eee; }}
h1 {{ font-size: 1.1rem; margin-bottom: 6px; color: #e0e0e0; }}
.toggle {{ display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }}
.toggle label {{ display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 4px 10px; border-radius: 4px; border: 1px solid #555; font-size: 13px; }}
.toggle label:hover {{ background: #252540; }}
.toggle .opt-cw {{ color: #b8d4ee; }}
.toggle .opt-em {{ color: #d4eeb8; }}
.toggle .opt-cw:has(input:checked) {{ background: #2d4a6e; border-color: #6e9ecc; }}
.toggle .opt-em:has(input:checked) {{ background: #4a6e2d; border-color: #8ecc6e; }}
.map-toolbar {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }}
.map-toolbar .zoom-btn {{ width: 32px; height: 28px; border: 1px solid #555; border-radius: 4px; background: #2a2a3e; color: #ccc; font-size: 18px; cursor: pointer; line-height: 1; }}
.map-toolbar .zoom-btn:hover {{ background: #353550; color: #fff; }}
.map-toolbar .zoom-label {{ font-size: 12px; color: #888; min-width: 4em; }}
.map-wrap {{ background: #3d2914; border: 1px solid #5c4a2a; border-radius: 8px; padding: 12px; overflow: hidden; width: 100%; aspect-ratio: {w} / {h}; box-sizing: border-box; position: relative; cursor: grab; touch-action: none; }}
.map-wrap:active {{ cursor: grabbing; }}
.map-wrap canvas {{ display: block; background: #4a3520; }}
.tip {{ position: fixed; background: #252530; border: 1px solid #444; padding: 6px 10px; border-radius: 4px; font-size: 12px; max-width: 280px; z-index: 10; pointer-events: none; display: none; }}
.tip .auto-link-hint {{ color: #8ecc6e; font-size: 11px; margin-top: 4px; }}
.note {{ margin-top: 8px; font-size: 11px; color: #888; }}
.nav-links {{ margin-bottom: 6px; font-size: 13px; }}
.nav-links a {{ color: #6eb5ff; }}
</style>
</head>
<body>
<h1>遠征計画 座標マップ（シート状・位置ひと目で確認）</h1>
<p class="nav-links"><a href="遠征計画_座標別一覧.html">座標別一覧</a></p>
<p>座標別に砦を配置。★で等級表示。リスト切り替え・ドラッグ・ホイール拡大縮小。砦は左クリック：自動出兵　右クリック：MAP表示。</p>
<div class="toggle" role="group" aria-label="リスト切り替え">
  <label class="opt-em"><input type="radio" name="listSwitch" value="em" checked> <span>w</span></label>
  <label class="opt-cw"><input type="radio" name="listSwitch" value="cw"> <span>E1</span></label>
</div>
<div class="map-toolbar">
  <button type="button" class="zoom-btn" id="zoomOut" title="縮小">−</button>
  <span class="zoom-label" id="zoomLabel">100%</span>
  <button type="button" class="zoom-btn" id="zoomIn" title="拡大">＋</button>
</div>
<div class="map-wrap" id="mapWrap">
  <canvas id="can"></canvas>
</div>
<div id="tip" class="tip"></div>
<div class="note">※ PC: 左クリックで自動出兵・右クリックでMAP表示。ドラッグで移動・ホイールで拡大縮小。スマホ: ドラッグで移動・ピンチで拡大縮小・タップで自動出兵を開く。＋/−ボタンでも拡大縮小可。Y軸は北が上。</div>
<script id="fortData" type="application/json">{fort_json}</script>
<script id="viewData" type="application/json">{view_json}</script>
<script>
(function(){{
  var FORT_DATA = JSON.parse(document.getElementById('fortData').textContent);
  var VIEW = JSON.parse(document.getElementById('viewData').textContent);
  var xMin = VIEW.xMin, yMax = VIEW.yMax, w = VIEW.w, h = VIEW.h, gridStep = VIEW.gridStep;

  var el = document.getElementById('can');
  var wrap = document.getElementById('mapWrap');
  var tip = document.getElementById('tip');
  var zoomLabel = document.getElementById('zoomLabel');
  var ctx = el.getContext('2d');

  var scale = 1, panX = 0, panY = 0;
  var drag = {{ on: false, startX: 0, startY: 0, startPanX: 0, startPanY: 0 }};
  var pinch = {{ on: false, startDist: 0, startScale: 0, startPanX: 0, startPanY: 0, centerMapX: 0, centerMapY: 0 }};
  var listFilter = 'em';
  var hoverPt = null;
  var statusMap = {{}};
  var fortStatusUrl = {fort_status_url_js};
  fetch(fortStatusUrl || 'fort_status.json').then(function(r) {{ return r.ok ? r.json() : Promise.reject(); }}).then(function(o) {{
    statusMap = o || {{}};
    draw();
  }}).catch(function() {{}});

  function toScreen(mx, my) {{
    var totalScale = baseScale * scale;
    return {{
      x: (mx - xMin) * totalScale + panX,
      y: (yMax - my) * totalScale + panY
    }};
  }}
  function toMap(sx, sy) {{
    var totalScale = baseScale * scale;
    return {{
      x: (sx - panX) / totalScale + xMin,
      y: yMax - (sy - panY) / totalScale
    }};
  }}

  var baseScale = 1;
  function resize() {{
    var r = wrap.getBoundingClientRect();
    var cw = r.width, ch = r.height;
    if (el.width !== cw || el.height !== ch) {{
      el.width = cw;
      el.height = ch;
      baseScale = Math.min(cw / w, ch / h);
      zoomLabel.textContent = Math.round(scale * 100) + '%';
      draw();
    }}
  }}

  function draw() {{
    var cw = el.width, ch = el.height;
    if (cw === 0 || ch === 0) return;
    var totalScale = baseScale * scale;
    var visX1 = xMin - panX / totalScale;
    var visX2 = xMin + (cw - panX) / totalScale;
    var visY1 = yMax + (panY - ch) / totalScale;
    var visY2 = yMax + panY / totalScale;

    ctx.fillStyle = '#4a3520';
    ctx.fillRect(0, 0, cw, ch);

    ctx.strokeStyle = '#6b5344';
    ctx.lineWidth = 0.5;
    var gs = gridStep;
    for (var xi = Math.floor(visX1 / gs) * gs; xi <= visX2 + gs; xi += gs) {{
      if (xi < xMin || xi > xMin + w) continue;
      var s = toScreen(xi, 0);
      ctx.beginPath();
      ctx.moveTo(s.x, 0);
      ctx.lineTo(s.x, ch);
      ctx.stroke();
    }}
    for (var yi = Math.floor(visY1 / gs) * gs; yi <= visY2 + gs; yi += gs) {{
      if (yi < yMax - h || yi > yMax) continue;
      var s = toScreen(0, yi);
      ctx.beginPath();
      ctx.moveTo(0, s.y);
      ctx.lineTo(cw, s.y);
      ctx.stroke();
    }}

    var drawStar = totalScale > 0.3;
    for (var i = 0; i < FORT_DATA.length; i++) {{
      var p = FORT_DATA[i];
      if (p.l !== listFilter) continue;
      if (p.x < visX1 - 50 || p.x > visX2 + 50 || p.y < visY1 - 50 || p.y > visY2 + 50) continue;
      var s = toScreen(p.x, p.y);
      var r = 3 + Math.min(p.st || 1, 9);
      var rad = r * totalScale;
      if (rad < 0.5) continue;
      var st = statusMap[p.n];
      if (st === '攻略済' || st === '失') ctx.globalAlpha = 0.4;
      else ctx.globalAlpha = 1;
      ctx.fillStyle = p.l === 'cw' ? '#2d4a6e' : '#2d5a2d';
      ctx.strokeStyle = p.l === 'cw' ? '#5a8acc' : '#5acc5a';
      ctx.lineWidth = hoverPt === p ? 2 : 1;
      ctx.beginPath();
      ctx.arc(s.x, s.y, Math.max(2, rad), 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      if (drawStar && rad >= 6) {{
        ctx.fillStyle = '#fff';
        ctx.font = 'bold ' + Math.max(8, Math.min(12, rad)) + 'px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(p.s || '', s.x, s.y);
      }}
      ctx.globalAlpha = 1;
    }}
  }}

  function hitTest(sx, sy) {{
    var m = toMap(sx, sy);
    var totalScale = baseScale * scale;
    var best = null, bestD = 999999;
    for (var i = 0; i < FORT_DATA.length; i++) {{
      var p = FORT_DATA[i];
      if (p.l !== listFilter) continue;
      var r = 3 + Math.min(p.st || 1, 9);
      var thresh = (r + 4) * totalScale;
      var dx = p.x - m.x, dy = p.y - m.y;
      var d = dx * dx + dy * dy;
      if (d < thresh * thresh && d < bestD) {{ bestD = d; best = p; }}
    }}
    return best;
  }}

  function zoom(delta, centerX, centerY) {{
    var rect = wrap.getBoundingClientRect();
    var oldScale = scale;
    scale = Math.max(0.1, Math.min(8, scale * (delta > 0 ? 1.2 : 1/1.2)));
    if (centerX != null && centerY != null) {{
      var mx = (centerX - rect.left - panX) / (baseScale * oldScale) + xMin;
      var my = yMax - (centerY - rect.top - panY) / (baseScale * oldScale);
      var s = toScreen(mx, my);
      panX = centerX - rect.left - (mx - xMin) * baseScale * scale;
      panY = centerY - rect.top - (yMax - my) * baseScale * scale;
    }}
    zoomLabel.textContent = Math.round(scale * 100) + '%';
    draw();
  }}

  function dist(a, b) {{ return Math.sqrt((a.clientX - b.clientX) * (a.clientX - b.clientX) + (a.clientY - b.clientY) * (a.clientY - b.clientY)); }}
  function touchCenter(touches) {{ return {{ x: (touches[0].clientX + touches[1].clientX) / 2, y: (touches[0].clientY + touches[1].clientY) / 2 }}; }}

  wrap.addEventListener('wheel', function(e) {{ e.preventDefault(); zoom(-e.deltaY, e.clientX, e.clientY); }}, {{ passive: false }});
  document.getElementById('zoomIn').addEventListener('click', function() {{ zoom(1); }});
  document.getElementById('zoomOut').addEventListener('click', function() {{ zoom(-1); }});
  document.getElementById('zoomIn').addEventListener('touchend', function(e) {{ e.preventDefault(); zoom(1); }});
  document.getElementById('zoomOut').addEventListener('touchend', function(e) {{ e.preventDefault(); zoom(-1); }});

  wrap.addEventListener('mousedown', function(e) {{
    if (e.button !== 0) return;
    drag.on = true;
    drag.startX = e.clientX;
    drag.startY = e.clientY;
    drag.startPanX = panX;
    drag.startPanY = panY;
  }});
  wrap.addEventListener('touchstart', function(e) {{
    if (e.touches.length === 2) {{
      var rect = wrap.getBoundingClientRect();
      var c = touchCenter(e.touches);
      var sx = c.x - rect.left, sy = c.y - rect.top;
      var m = toMap(sx, sy);
      pinch.on = true;
      pinch.startDist = dist(e.touches[0], e.touches[1]);
      pinch.startScale = scale;
      pinch.startPanX = panX;
      pinch.startPanY = panY;
      pinch.centerMapX = m.x;
      pinch.centerMapY = m.y;
    }} else if (e.touches.length === 1) {{
      drag.on = true;
      drag.startX = e.touches[0].clientX;
      drag.startY = e.touches[0].clientY;
      drag.startPanX = panX;
      drag.startPanY = panY;
    }}
  }}, {{ passive: true }});
  wrap.addEventListener('touchmove', function(e) {{
    if (e.touches.length === 2 && pinch.on) {{
      e.preventDefault();
      var rect = wrap.getBoundingClientRect();
      var d = dist(e.touches[0], e.touches[1]);
      var c = touchCenter(e.touches);
      var sx = c.x - rect.left, sy = c.y - rect.top;
      scale = Math.max(0.1, Math.min(8, pinch.startScale * (d / pinch.startDist)));
      var s = toScreen(pinch.centerMapX, pinch.centerMapY);
      panX = sx - s.x;
      panY = sy - s.y;
      zoomLabel.textContent = Math.round(scale * 100) + '%';
      draw();
    }} else if (e.touches.length === 1 && drag.on) {{
      e.preventDefault();
      panX = drag.startPanX + (e.touches[0].clientX - drag.startX);
      panY = drag.startPanY + (e.touches[0].clientY - drag.startY);
      draw();
    }}
  }}, {{ passive: false }});
  wrap.addEventListener('touchend', function(e) {{
    if (e.touches.length === 0) {{
      if (pinch.on) {{ pinch.on = false; }}
      if (drag.on) {{
        if (e.changedTouches && e.changedTouches[0]) {{
          var dx = e.changedTouches[0].clientX - drag.startX;
          var dy = e.changedTouches[0].clientY - drag.startY;
          if (dx * dx + dy * dy < 100) {{
            var rect = wrap.getBoundingClientRect();
            var pt = hitTest(e.changedTouches[0].clientX - rect.left, e.changedTouches[0].clientY - rect.top);
            if (pt && pt.u) window.open(pt.u, '_blank');
          }}
        }}
        drag.on = false;
      }}
    }} else if (e.touches.length === 1) {{ pinch.on = false; }}
  }}, {{ passive: true }});

  document.addEventListener('mousemove', function(e) {{
    var rect = wrap.getBoundingClientRect();
    var sx = e.clientX - rect.left, sy = e.clientY - rect.top;
    if (drag.on) {{
      panX = drag.startPanX + (e.clientX - drag.startX);
      panY = drag.startPanY + (e.clientY - drag.startY);
      draw();
      return;
    }}
    var pt = hitTest(sx, sy);
    if (pt !== hoverPt) {{
      hoverPt = pt;
      draw();
      if (pt) {{
        var txt = pt.n + ' (' + pt.x + ',' + pt.y + ') ' + (pt.s || '');
        if (statusMap[pt.n]) txt += ' [' + statusMap[pt.n] + ']';
        if (pt.u || pt.m) tip.innerHTML = txt + '<div class="auto-link-hint">左クリック: 自動出兵　右クリック: MAP</div>';
        else tip.textContent = txt;
        tip.style.display = 'block';
      }} else tip.style.display = 'none';
    }}
    if (tip.style.display === 'block') {{ tip.style.left = (e.clientX + 12) + 'px'; tip.style.top = (e.clientY + 8) + 'px'; }}
  }});
  document.addEventListener('mouseup', function() {{ drag.on = false; }});

  wrap.addEventListener('click', function(e) {{
    if (e.pointerType === 'touch') return;
    if (e.button !== 0) return;
    if (drag.startX !== e.clientX || drag.startY !== e.clientY) return;
    var rect = wrap.getBoundingClientRect();
    var pt = hitTest(e.clientX - rect.left, e.clientY - rect.top);
    if (pt && pt.u) window.open(pt.u, '_blank');
  }});
  wrap.addEventListener('contextmenu', function(e) {{
    var rect = wrap.getBoundingClientRect();
    var pt = hitTest(e.clientX - rect.left, e.clientY - rect.top);
    if (pt && pt.m) {{ e.preventDefault(); window.open(pt.m, '_blank'); }}
  }});

  document.querySelectorAll('input[name="listSwitch"]').forEach(function(r) {{
    r.addEventListener('change', function() {{
      listFilter = document.querySelector('input[name="listSwitch"]:checked').value;
      hoverPt = null;
      tip.style.display = 'none';
      draw();
    }});
  }});

  window.addEventListener('resize', resize);
  resize();
}})();
</script>
</body>
</html>
"""
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Generated: {OUT_PATH} ({len(points)} points, Canvas)")


if __name__ == "__main__":
    main()
