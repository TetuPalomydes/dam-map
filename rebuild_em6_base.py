# -*- coding: utf-8 -*-
"""
em6DATA.txt を「座標修正」してから「基本データ」で作り直す。
・座標: 1180基準 → 1100基準に統一（鄴・下邳・長沙・天水とその周辺砦）
・並び: 先頭に 洛陽→★8→★7大砦→★6宮砦 を固定し、それ以外は地域・Y降順・X昇順。
"""
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
REGIONS_PATH = BASE_DIR / "座標区分けリスト.txt"
EM6_PATH = BASE_DIR / "em6DATA.txt"

# 1180基準 → 1100基準（東西南北★8と周辺砦の座標を統一）
CONV_X = {
    1180: 1100, 1288: 1208, 1072: 992,
    -1180: -1100, -1288: -1208, -1072: -992,
}
CONV_Y = {
    1180: 1100, 1288: 1208, 1072: 992,
    -1180: -1100, -1288: -1208, -1072: -992,
}


def convert_coord(v: int, conv: dict) -> int:
    return conv.get(v, v)


# 先頭に出す基本データの並び（NPC名の完全一致）
BASE_ORDER = [
    "洛陽",
    "許昌", "建業", "成都", "長安", "鄴", "下邳", "長沙", "天水",
    "玄武大砦", "青龍大砦", "朱雀大砦", "白虎大砦",
    "霊亀大砦", "応龍大砦", "麒麟大砦", "鳳凰大砦",
    "坎宮砦", "一白砦", "艮宮砦", "八白砦", "震宮砦", "三碧砦",
    "巽宮砦", "四緑砦", "離宮砦", "九紫砦", "坤宮砦", "二黒砦",
    "兌宮砦", "七赤砦", "乾宮砦", "六白砦",
]


def load_regions(path: Path) -> list:
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


def main():
    regions = load_regions(REGIONS_PATH)
    lines = EM6_PATH.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        print("em6DATA.txt が空です")
        return
    header = lines[0]
    # 全行を (name, x, y, star) にパースし、座標を 1180→1100 に修正
    by_name = {}
    others = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        name = parts[0].strip()
        try:
            x, y = int(parts[1].strip()), int(parts[2].strip())
        except ValueError:
            continue
        x = convert_coord(x, CONV_X)
        y = convert_coord(y, CONV_Y)
        star = parts[3].strip()
        if name in BASE_ORDER and name not in by_name:
            by_name[name] = (x, y, star)
        else:
            others.append((name, x, y, star))
    # 基本データを定義順に並べる（見つかったものだけ）
    base_rows = []
    for name in BASE_ORDER:
        if name in by_name:
            x, y, star = by_name[name]
            base_rows.append((name, x, y, star))
    # その他を地域・Y降順・X昇順でソート
    def other_key(t):
        name, x, y, star = t
        region = get_region(x, y, regions)
        return (region_sort_key(region), -y, x)
    others.sort(key=other_key)
    # 出力
    out = [header]
    for name, x, y, star in base_rows:
        out.append(f"{name}\t{x}\t{y}\t{star}")
    for name, x, y, star in others:
        out.append(f"{name}\t{x}\t{y}\t{star}")
    EM6_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Rebuilt: {EM6_PATH} (base={len(base_rows)}, others={len(others)}, total={len(base_rows)+len(others)})")


if __name__ == "__main__":
    main()
