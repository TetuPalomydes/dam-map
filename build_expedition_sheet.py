# -*- coding: utf-8 -*-
"""
遠征計画・座標別一覧ビルダー
砦リスト(cw2) と 砦リスト(em6) を別種として、座標別に並べた1枚シート用のCSV/HTMLを生成する。
"""

import re
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent
MAP_BASE = "https://w1.3gokushi.jp/map.php"
AUTO_BASE = "https://w1.3gokushi.jp/auto_send_troop/index.php"


def load_regions(path: Path) -> list:
    """座標区分けリスト.txt を読み、地域の矩形リストを返す。"""
    regions = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        m = re.match(r"(.+?)\((-?\d+),(-?\d+)\)\((-?\d+),(-?\d+)\)", line.strip())
        if not m:
            continue
        name, x1, y1, x2, y2 = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        regions.append((name.strip(), x_min, x_max, y_min, y_max))
    return regions


def get_region(x: int, y: int, regions: list) -> str:
    for name, x_min, x_max, y_min, y_max in regions:
        if x_min <= x <= x_max and y_min <= y <= y_max:
            return name
    return ""


def region_sort_key(name: str) -> tuple:
    order = ["北西", "北", "北東", "西", "中原", "東", "南西", "南", "南東"]
    try:
        return (order.index(name),)
    except ValueError:
        return (99, name)


def load_tsv_forts(path: Path, kind: str) -> list:
    """砦リストTSVを読み、(x, y, 名称, ★, 種別) のリストを返す。"""
    rows = []
    text = path.read_text(encoding="utf-8")
    lines = text.strip().splitlines()
    if not lines:
        return rows
    # ヘッダー: NPC名	X座標	Y座標	★
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        name, xs, ys, star = parts[0], parts[1], parts[2], parts[3]
        try:
            x, y = int(xs.strip()), int(ys.strip())
        except ValueError:
            continue
        rows.append((x, y, name.strip(), star.strip(), kind))
    return rows


def main():
    regions_path = BASE_DIR / "座標区分けリスト.txt"
    cw2_path = BASE_DIR / "cw2.txt"
    em6_path = BASE_DIR / "em6DATA.txt"

    regions = load_regions(regions_path)
    cw2_rows = load_tsv_forts(cw2_path, "砦(cw2)")
    em6_rows = load_tsv_forts(em6_path, "砦(em6)")

    # 統合: (地域, x, y, 種別, 名称, ★, …)
    def to_record(x, y, kind, name, star):
        region = get_region(x, y, regions)
        map_url = f"{MAP_BASE}?x={x}&y={y}"
        auto_url = f"{AUTO_BASE}?x={x}&y={y}"
        return (region, x, y, kind, name, star, map_url, auto_url)

    all_rows = []
    for (x, y, name, star, kind) in cw2_rows:
        all_rows.append(to_record(x, y, kind, name, star))
    for (x, y, name, star, kind) in em6_rows:
        all_rows.append(to_record(x, y, kind, name, star))

    # 並び: 地域順（北西→南東）、同一地域内は Y 降順・X 昇順（北から南、西から東）
    def row_key(r):
        region, x, y = r[0], r[1], r[2]
        return (region_sort_key(region), -y, x)

    all_rows.sort(key=row_key)

    # CSV 出力
    out_csv = BASE_DIR / "遠征計画_座標別一覧.csv"
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["地域", "X", "Y", "種別", "名称", "★", "MAP", "自動出兵SC", "備考"])
        for r in all_rows:
            w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], ""])

    # HTML 1枚シート出力（先頭500行＋見本で軽量に。全件はCSVで）
    out_html = BASE_DIR / "遠征計画_座標別一覧.html"
    build_html(all_rows, out_html, regions, max_rows=800)

    # 座標マップ（シート状配置）HTML 出力
    out_map = BASE_DIR / "遠征計画_座標マップ.html"
    build_map_html(all_rows, out_map)

    print(f"CSV: {out_csv} ({len(all_rows)} 行)")
    print(f"HTML: {out_html}")
    print(f"座標マップ: {out_map}")


def build_html(rows: list, path: Path, regions: list, max_rows: int = 800):
    """座標別一覧の1枚シートHTMLを生成。cw / em を切り替え表示。"""
    head = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>遠征計画 座標別一覧（w / E1 切り替え）</title>
<style>
* { box-sizing: border-box; }
body { font-family: "Meiryo", "Yu Gothic", sans-serif; margin: 12px; background: #1a1a2e; color: #eee; }
h1 { font-size: 1.2rem; margin-bottom: 8px; color: #e0e0e0; }
.toggle { display: flex; gap: 8px; margin-bottom: 12px; align-items: center; flex-wrap: wrap; }
.toggle label { display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 6px 12px; border-radius: 6px; border: 1px solid #444; font-size: 14px; }
.toggle label:hover { background: #252540; }
.toggle input { margin: 0; }
.toggle input:checked + span { font-weight: bold; }
.toggle .opt-cw { color: #b8d4ee; }
.toggle .opt-em { color: #d4eeb8; }
.toggle .opt-cw:has(input:checked) { background: #2d4a6e; border-color: #4a6e9e; }
.toggle .opt-em:has(input:checked) { background: #4a6e2d; border-color: #6e9e4a; }
.wrap { overflow-x: auto; }
table { border-collapse: collapse; font-size: 12px; min-width: 100%; }
th, td { border: 1px solid #444; padding: 4px 8px; text-align: left; }
th { background: #16213e; color: #fff; position: sticky; top: 0; z-index: 1; }
tr[data-list] { transition: opacity 0.15s; }
tr[data-list].hidden { display: none; }
tr:nth-child(even):not(.hidden) { background: #252540; }
tr:hover:not(.hidden) { background: #2d2d4a; }
tr.kind-cw { background: #1e2d3d !important; }
tr.kind-em { background: #1d2d1e !important; }
td.num { text-align: right; }
a { color: #6eb5ff; }
a:visited { color: #b58eff; }
.note { margin-top: 12px; font-size: 11px; color: #888; }
.region-toggle { display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap; align-items: center; }
.region-toggle .region-btn { padding: 4px 10px; border-radius: 4px; border: 1px solid #444; background: #252540; color: #ccc; font-size: 12px; cursor: pointer; }
.region-toggle .region-btn:hover { background: #2d2d4a; color: #fff; }
.region-toggle .region-btn.active { background: #3d4a6e; border-color: #6e9ecc; color: #fff; }
tr[data-region].region-hidden { display: none; }
</style>
</head>
<body>
<h1>遠征計画 座標別一覧（1枚シート）</h1>
<p>砦リストを <strong>w</strong> と <strong>E1</strong> で切り替えて表示。並びは地域→Y降順→X昇順。</p>
<div class="toggle" role="group" aria-label="リスト切り替え">
  <label class="opt-em"><input type="radio" name="listSwitch" value="em" checked> <span>w</span></label>
  <label class="opt-cw"><input type="radio" name="listSwitch" value="cw"> <span>E1</span></label>
</div>
<div class="region-toggle" role="group" aria-label="地域で絞り込み">
  <button type="button" class="region-btn active" data-region="">すべて</button>
  <!--REGION_BUTTONS-->
</div>
<div class="wrap">
<table>
<thead><tr>
<th>地域</th><th>X</th><th>Y</th><th>種別</th><th>名称</th><th>★</th><th>MAP</th><th>自動出兵SC</th><th>備考</th>
</tr></thead>
<tbody>
"""
    foot = """
</tbody>
</table>
</div>
<div class="note">※ 全件は 遠征計画_座標別一覧.csv をスプレッドシートに取り込んで利用してください。HTMLは最大{0}件まで表示しています。</div>
<script>
(function(){{
  var radios = document.querySelectorAll('input[name="listSwitch"]');
  var rows = document.querySelectorAll('tbody tr[data-list]');
  var regionBtns = document.querySelectorAll('.region-btn');
  var currentRegion = '';
  function update() {{
    var v = document.querySelector('input[name="listSwitch"]:checked').value;
    rows.forEach(function(tr) {{
      var listMatch = tr.getAttribute('data-list') === v;
      var regionMatch = !currentRegion || tr.getAttribute('data-region') === currentRegion;
      tr.classList.toggle('hidden', !listMatch);
      tr.classList.toggle('region-hidden', !regionMatch);
    }});
  }}
  radios.forEach(function(r){{ r.addEventListener('change', update); }});
  regionBtns.forEach(function(btn){{
    btn.addEventListener('click', function(){{
      regionBtns.forEach(function(b){{ b.classList.remove('active'); }});
      btn.classList.add('active');
      currentRegion = btn.getAttribute('data-region') || '';
      update();
    }});
  }});
  update();
}})();
</script>
</body>
</html>
""".format(max_rows)

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    # 全方位の地域ボタンを常に表示（データに無い地域を押すと0件表示）
    region_order = ["北西", "北", "北東", "西", "中原", "東", "南西", "南", "南東"]
    region_buttons_html = "\n".join(
        f'  <button type="button" class="region-btn" data-region="{esc(r)}">{esc(r)}</button>' for r in region_order
    )
    head_final = head.replace("<!--REGION_BUTTONS-->", region_buttons_html)

    body_rows = []
    for r in rows[:max_rows]:
        region, x, y, kind, name, star, map_url, auto_url = r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]
        data_list = "cw" if "cw2" in kind else "em"
        css = "kind-cw" if data_list == "cw" else "kind-em"
        region_attr = esc(region) if region else ""
        body_rows.append(
            f'<tr class="{css}" data-list="{data_list}" data-region="{region_attr}">'
            f'<td>{esc(region)}</td><td class="num">{x}</td><td class="num">{y}</td><td>{esc(kind)}</td><td>{esc(name)}</td><td>{esc(star)}</td>'
            f'<td><a href="{esc(map_url)}" target="_blank">MAP</a></td>'
            f'<td><a href="{esc(auto_url)}" target="_blank">自動出兵SC</a></td><td></td></tr>'
        )

    path.write_text(head_final + "\n".join(body_rows) + foot, encoding="utf-8")


def _star_level(star_str: str) -> int:
    """★8 -> 8, ★1 -> 1 を返す。"""
    import re
    m = re.search(r"★?(\d+)", star_str or "")
    return int(m.group(1)) if m else 1


def build_map_html(rows: list, path: Path) -> None:
    """座標をシート状に配置したマップHTMLを生成。グリッド上に砦をプロット。"""
    # マップ用ポイント列（全件）
    points = []
    for r in rows:
        region, x, y, kind, name, star = r[0], r[1], r[2], r[3], r[4], r[5]
        list_id = "cw" if "cw2" in kind else "em"
        star_num = _star_level(star)
        points.append({"x": x, "y": y, "name": name, "star": star, "starNum": star_num, "list": list_id})

    # 座標範囲（余白付き）
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    pad = 80
    x_min -= pad
    x_max += pad
    y_min -= pad
    y_max += pad
    # 正方形に近い viewBox
    w = x_max - x_min
    h = y_max - y_min
    if w < 800:
        w = 800
        x_min = (x_min + x_max) / 2 - 400
        x_max = x_min + 800
    if h < 800:
        h = 800
        y_min = (y_min + y_max) / 2 - 400
        y_max = y_min + 800

    # グリッド間隔（見やすく）
    grid_step = 200
    if w > 2000 or h > 2000:
        grid_step = 400

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("\n", " ")

    # グリッド線
    grid_lines = []
    for xi in range(int(x_min // grid_step) * grid_step, int(x_max) + 1, grid_step):
        if x_min <= xi <= x_max:
            grid_lines.append(f'<line x1="{xi}" y1="{y_min}" x2="{xi}" y2="{y_max}" class="grid-line"/>')
    for yi in range(int(y_min // grid_step) * grid_step, int(y_max) + 1, grid_step):
        if y_min <= yi <= y_max:
            grid_lines.append(f'<line x1="{x_min}" y1="{yi}" x2="{x_max}" y2="{yi}" class="grid-line"/>')

    # 砦マーカー（★の大きさで等級表現）
    markers = []
    for p in points:
        x, y = p["x"], p["y"]
        # ★1→小、★8→大: 半径 3 + starNum
        r = 3 + min(p["starNum"], 9)
        list_id = p["list"]
        name_esc = esc(p["name"])
        star_esc = esc(p["star"])
        title = f"{name_esc} ({p['x']},{p['y']}) {star_esc}"
        # 星形は circle で代用（シンプル）。クラスで cw/em 色分け
        markers.append(
            f'<g class="marker marker-{list_id}" data-list="{list_id}" data-x="{x}" data-y="{y}">'
            f'<circle cx="{x}" cy="{y}" r="{r}" class="marker-circle"/>'
            f'<text x="{x}" y="{y}" class="marker-star" text-anchor="middle" dominant-baseline="central">{p["star"]}</text>'
            f'<title>{title}</title></g>'
        )

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
.map-wrap {{ background: #3d2914; border: 1px solid #5c4a2a; border-radius: 8px; padding: 12px; overflow: auto; max-width: 100%; }}
.map-wrap svg {{ display: block; max-width: 100%; height: auto; }}
#map {{ background: #4a3520; }}
.grid-line {{ stroke: #6b5344; stroke-width: 0.5; }}
.marker {{ cursor: pointer; }}
.marker.hidden {{ visibility: hidden; pointer-events: none; }}
.marker-cw .marker-circle {{ fill: #2d4a6e; stroke: #5a8acc; stroke-width: 1; }}
.marker-em .marker-circle {{ fill: #2d5a2d; stroke: #5acc5a; stroke-width: 1; }}
.marker-star {{ font-size: 10px; fill: #fff; font-weight: bold; pointer-events: none; }}
.marker:hover .marker-circle {{ stroke-width: 2; filter: brightness(1.2); }}
.tip {{ position: fixed; background: #252530; border: 1px solid #444; padding: 6px 10px; border-radius: 4px; font-size: 12px; max-width: 280px; z-index: 10; pointer-events: none; display: none; }}
.note {{ margin-top: 8px; font-size: 11px; color: #888; }}
.nav-links {{ margin-bottom: 6px; font-size: 13px; }}
.nav-links a {{ color: #6eb5ff; }}
</style>
</head>
<body>
<h1>遠征計画 座標マップ（シート状・位置ひと目で確認）</h1>
<p class="nav-links"><a href="遠征計画_座標別一覧.html">座標別一覧</a></p>
<p>座標別に砦を配置。★で等級を表示。リストを切り替えて w / E1 を表示。</p>
<div class="toggle" role="group" aria-label="リスト切り替え">
  <label class="opt-em"><input type="radio" name="listSwitch" value="em" checked> <span>w</span></label>
  <label class="opt-cw"><input type="radio" name="listSwitch" value="cw"> <span>E1</span></label>
</div>
<div class="map-wrap">
<svg id="map" viewBox="{x_min} {-y_max} {w} {h}" xmlns="http://www.w3.org/2000/svg">
  <g transform="scale(1,-1)">
    <rect x="{x_min}" y="{y_min}" width="{w}" height="{h}" fill="#4a3520"/>
    <g class="grid">{{"".join(grid_lines)}}</g>
    <g class="markers">{"".join(markers)}</g>
  </g>
</svg>
</div>
<div id="tip" class="tip"></div>
<div class="note">※ Y軸は北が上です。ホバーで名称・座標・★を表示。python build_expedition_sheet.py で再生成。</div>
<script>
(function(){{
  var radios = document.querySelectorAll('input[name="listSwitch"]');
  var markers = document.querySelectorAll('.marker');
  var tip = document.getElementById('tip');
  function update() {{
    var v = document.querySelector('input[name="listSwitch"]:checked').value;
    markers.forEach(function(m) {{
      m.classList.toggle('hidden', m.getAttribute('data-list') !== v);
    }});
  }}
  function showTip(ev, text) {{
    tip.textContent = text;
    tip.style.display = 'block';
    tip.style.left = (ev.clientX + 12) + 'px';
    tip.style.top = (ev.clientY + 8) + 'px';
  }}
  function hideTip() {{ tip.style.display = 'none'; }}
  markers.forEach(function(m) {{
    var t = m.querySelector('title');
    if (t) m.addEventListener('mouseenter', function(e) {{ showTip(e, t.textContent); }});
    m.addEventListener('mouseleave', hideTip);
  }});
  radios.forEach(function(r) {{ r.addEventListener('change', update); }});
  update();
}})();
</script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
