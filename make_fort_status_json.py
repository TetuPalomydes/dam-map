# -*- coding: utf-8 -*-
"""
砦攻略システム側のCSVから fort_status.json（w用）と fort_status_c4.json（c4用）を生成する。
CSV は npc_name と strategy_status 列を含むこと。
出力: fort_status.json … w用。fort_status_c4.json … c4用。
マップは w リストで fort_status.json、c4 リストで fort_status_c4.json を参照する。
"""
import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
# w用（em6）
CSV_CANDIDATES_EM = [
    BASE_DIR.parent / "_砦攻略システム" / "pwa" / "npc_strategy_export.csv",
    BASE_DIR / "npc_strategy_em6_rows.csv",
    BASE_DIR / "npc_strategy_export.csv",
]
OUT_PATH_EM = BASE_DIR / "fort_status.json"
# c4用（cw2）
CSV_CANDIDATES_CW = [
    BASE_DIR / "npc_strategy_cw2_rows.csv",
    BASE_DIR.parent / "_砦攻略システム" / "pwa" / "npc_strategy_cw2_export.csv",
]
OUT_PATH_CW = BASE_DIR / "fort_status_c4.json"


def find_csv(candidates):
    for p in candidates:
        if p.exists():
            return p
    return None


def build_status_map(csv_path):
    status_map = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            return None, "CSV にヘッダーがありません"
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
            return None, f"npc_name/strategy_status に相当する列が見つかりません: {r.fieldnames}"
        for row in r:
            name = (row.get(name_col) or "").strip()
            status = (row.get(status_col) or "").strip()
            if name and status:
                status_map[name] = status
    return status_map, None


def main():
    # w用
    csv_em = find_csv(CSV_CANDIDATES_EM)
    if csv_em:
        status_em, err = build_status_map(csv_em)
        if err:
            print("w用:", err)
        else:
            OUT_PATH_EM.write_text(json.dumps(status_em, ensure_ascii=False, indent=0), encoding="utf-8")
            print(f"Generated: {OUT_PATH_EM} ({len(status_em)} entries, w用 from {csv_em.name})")
    else:
        print("w用CSVが見つかりません。以下のいずれかを配置してください:")
        for p in CSV_CANDIDATES_EM:
            print("  -", p)
    # c4用
    csv_cw = find_csv(CSV_CANDIDATES_CW)
    if csv_cw:
        status_cw, err = build_status_map(csv_cw)
        if err:
            print("c4用:", err)
        else:
            OUT_PATH_CW.write_text(json.dumps(status_cw, ensure_ascii=False, indent=0), encoding="utf-8")
            print(f"Generated: {OUT_PATH_CW} ({len(status_cw)} entries, c4用 from {csv_cw.name})")
    else:
        print("c4用CSVが見つかりません（任意）。以下のいずれかを置くと fort_status_c4.json を生成:")
        for p in CSV_CANDIDATES_CW:
            print("  -", p)


if __name__ == "__main__":
    main()
