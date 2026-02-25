# -*- coding: utf-8 -*-
"""
砦攻略システム側のCSVから fort_status.json を生成する。
CSV は npc_name と strategy_status 列を含むこと（カンマ区切り）。
例: id,npc_name,strategy_status,level,base1_x,base1_y,...
    2,許昌,攻略済,8,1100,1100,...
出力: fort_status.json … { "許昌": "攻略済", "北西砦1442": "失", ... }
マップHTMLと同じフォルダに置くと、攻略済・失の砦が薄く表示される。
"""
import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
# 砦攻略システムのCSV（Supabaseエクスポート等）を指定。無ければ遠征システム内のCSVを探す
CSV_CANDIDATES = [
    BASE_DIR.parent / "_砦攻略システム" / "pwa" / "npc_strategy_export.csv",
    BASE_DIR / "npc_strategy_em6_rows.csv",
    BASE_DIR / "npc_strategy_export.csv",
]
OUT_PATH = BASE_DIR / "fort_status.json"


def find_csv():
    for p in CSV_CANDIDATES:
        if p.exists():
            return p
    return None


def main():
    csv_path = find_csv()
    if not csv_path:
        print("砦攻略CSVが見つかりません。以下のいずれかを配置してください:")
        for p in CSV_CANDIDATES:
            print("  -", p)
        print("CSV には npc_name と strategy_status の列が必要です。")
        return
    status_map = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            print("CSV にヘッダーがありません")
            return
        name_col = "npc_name" if "npc_name" in r.fieldnames else None
        status_col = "strategy_status" if "strategy_status" in r.fieldnames else None
        if not name_col:
            for c in r.fieldnames:
                if "name" in c.lower() or c == "NPC名":
                    name_col = c
                    break
        if not status_col:
            for c in r.fieldnames:
                if "status" in c.lower() or "攻略" in c:
                    status_col = c
                    break
        if not name_col or not status_col:
            print("npc_name または strategy_status に相当する列が見つかりません。", r.fieldnames)
            return
        for row in r:
            name = (row.get(name_col) or "").strip()
            status = (row.get(status_col) or "").strip()
            if name and status:
                status_map[name] = status
    OUT_PATH.write_text(json.dumps(status_map, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"Generated: {OUT_PATH} ({len(status_map)} entries from {csv_path.name})")


if __name__ == "__main__":
    main()
