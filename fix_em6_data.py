# -*- coding: utf-8 -*-
"""
em6DATA.txt の座標を 1180 基準 → 1100 基準に統一し、
地域・Y降順・X昇順で並べ直して上書きする。
"""
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
REGIONS_PATH = BASE_DIR / "座標区分けリスト.txt"
EM6_PATH = BASE_DIR / "em6DATA.txt"

# 1180基準 → 1100基準（80ずらす）
DELTA = 80
CONV_X = {
    1180: 1100, 1288: 1208, 1072: 992,
    -1180: -1100, -1288: -1208, -1072: -992,
}
CONV_Y = {
    1180: 1100, 1288: 1208, 1072: 992,
    -1180: -1100, -1288: -1208, -1072: -992,
}


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


def convert_coord(v: int, conv: dict) -> int:
    return conv.get(v, v)


def main():
    regions = load_regions(REGIONS_PATH)
    lines = EM6_PATH.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        print("em6DATA.txt が空です")
        return
    header = lines[0]
    rows = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        name, xs, ys, star = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
        try:
            x, y = int(xs), int(ys)
        except ValueError:
            continue
        x = convert_coord(x, CONV_X)
        y = convert_coord(y, CONV_Y)
        region = get_region(x, y, regions)
        rows.append((region, x, y, name, star))
    rows.sort(key=lambda r: (region_sort_key(r[0]), -r[2], r[1]))
    out = [header]
    for _, x, y, name, star in rows:
        out.append(f"{name}\t{x}\t{y}\t{star}")
    EM6_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Updated: {EM6_PATH} ({len(rows)} rows, 1180→1100 unified, sorted by region / Y desc / X asc)")


if __name__ == "__main__":
    main()
