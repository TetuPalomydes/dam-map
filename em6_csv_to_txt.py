# -*- coding: utf-8 -*-
"""
em6DATA.csv（最新）を読み、build_expedition_sheet が使う em6DATA.txt（TSV）を生成する。
CSV: npc_name, base1_x, base1_y, level, event_id
TXT: NPC名\tX座標\tY座標\t★
"""
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "em6DATA.csv"
TXT_PATH = BASE_DIR / "em6DATA.txt"


def main():
    rows = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for row in r:
            name = (row.get("npc_name") or "").strip()
            try:
                x = int(row.get("base1_x", 0))
                y = int(row.get("base1_y", 0))
                level = int(row.get("level", 1))
            except (ValueError, TypeError):
                continue
            star = f"★{level}" if level >= 1 else "★1"
            rows.append((name, x, y, star))
    out = ["NPC名\tX座標\tY座標\t★"]
    for name, x, y, star in rows:
        out.append(f"{name}\t{x}\t{y}\t{star}")
    TXT_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Generated: {TXT_PATH} ({len(rows)} rows from {CSV_PATH})")


if __name__ == "__main__":
    main()
