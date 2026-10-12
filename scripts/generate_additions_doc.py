#!/usr/bin/env python3
"""Generate NEW_ADDITIONS.md comparison and detail report between snapshots."""
import json
from collections import Counter, defaultdict
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    s1_path = root / "data/snapshots/2026-10-11/catalog.json"
    s2_path = root / "data/snapshots/2026-10-12/catalog.json"
    out_path = root / "data/snapshots/2026-10-12/NEW_ADDITIONS.md"

    s1 = json.loads(s1_path.read_text(encoding="utf-8"))
    s2 = json.loads(s2_path.read_text(encoding="utf-8"))

    tids1 = {r["title_id"] for r in s1["records"]}
    nas_records = [r for r in s2["records"] if r.get("storage_location") == "nas"]

    cat_meta = {
        "fast_plat": ("极速白金神作 / 叙事小品", "高解锁率、耗时极短或纯剧情速通的白金佳作"),
        "visual_novel": ("视觉小说 / 纯爱与乙女 Galgame", "文字冒险、恋爱养成、剧情向视觉小说"),
        "contested_bulk": ("批量刷杯候选", "多版本/全区奖杯套叠、批量收割候选游戏"),
        "casual_easy": ("轻度休闲白金", "休闲益智、低难度全奖杯通关游戏"),
    }

    nas_bytes = sum(r["size_bytes"] for r in nas_records)
    local_bytes = sum(r["size_bytes"] for r in s2["records"] if r.get("storage_location") == "local")
    total_bytes = nas_bytes + local_bytes

    lines = [
        "# 2026-10-12 快照新增资产收录报告 (群晖 NAS 全量入库)",
        "",
        "本报告记录从群晖 NAS（`nas:pkg/`）补充收录到 `game_catalog` 的 **780 个 PKG 资产** 详细清单及对比统计。",
        "",
        "## 1. 核心增量统计",
        "",
        "| 统计维度 | 2026-10-11 初版快照 | 2026-10-12 最新快照 | 增量变动 |",
        "| --- | --- | --- | --- |",
        f"| **PKG 资产包总数** | {len(s1['records'])} 个 | {len(s2['records'])} 个 | **+780 个** (+234.2%) |",
        f"| **独立 Title ID 数** | {len(tids1)} 个 | {s2['unique_title_ids']} 个 | **+589 个** (+180.7%) |",
        f"| **覆盖存储空间** | {local_bytes / (1024**3):.2f} GB (本地) | {total_bytes / (1024**3):.2f} GB (本地+NAS) | **+{nas_bytes / (1024**3):.2f} GB** |",
        "| **存储源分布** | 本地 333 包 | 本地 333 包 + 群晖 NAS 780 包 | 新增群晖 NAS 分类源 |",
        "",
        "## 2. NAS 四大品类资产分布",
        "",
        "| 分类标识 | 分类中文说明 | PKG 包数 | 独立 Title ID | 磁盘占用 | 区域分布 (JP / US / EU / ASIA) |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for cat_key in ["fast_plat", "visual_novel", "contested_bulk", "casual_easy"]:
        c_records = [r for r in nas_records if r["category"] == cat_key]
        c_tids = {r["title_id"] for r in c_records}
        c_sz = sum(r["size_bytes"] for r in c_records) / (1024**3)
        reg_c = Counter(r["region"] for r in c_records)
        reg_str = f"{reg_c['JP']} / {reg_c['US']} / {reg_c['EU']} / {reg_c['ASIA']}"
        name_zh, desc = cat_meta[cat_key]
        lines.append(f"| `{cat_key}` | {name_zh} | {len(c_records)} | {len(c_tids)} | {c_sz:.2f} GB | {reg_str} |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. 各品类新增资产详细清单",
        "",
    ])

    for idx, cat_key in enumerate(["fast_plat", "visual_novel", "contested_bulk", "casual_easy"], 1):
        c_records = [r for r in nas_records if r["category"] == cat_key]
        name_zh, desc = cat_meta[cat_key]
        lines.extend([
            f"### 3.{idx} {name_zh} (`{cat_key}` - 共 {len(c_records)} 包)",
            "",
            f"> 说明：{desc}",
            "",
            "| 游戏名称 | 区域 | Title ID | Content ID | 包大小 | 资产路径 |",
            "| --- | --- | --- | --- | --- | --- |",
        ])
        for r in sorted(c_records, key=lambda x: (x["name"], x["region"], x["title_id"])):
            cid = r["content_id"] or "未提取"
            sz_mb = r["size_bytes"] / (1024**2)
            sz_str = f"{sz_mb / 1024:.2f} GB" if sz_mb >= 1024 else f"{sz_mb:.1f} MB"
            row_cells = [
                r["name"],
                r["region"],
                r["title_id"],
                cid,
                sz_str,
                r["asset_path"],
            ]
            escaped = [c.replace("|", "\\|") for c in row_cells]
            lines.append("| " + " | ".join(escaped) + " |")
        lines.append("")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated {out_path} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
