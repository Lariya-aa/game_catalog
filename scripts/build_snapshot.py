#!/usr/bin/env python3
"""Read local and NAS PKG attributes and metadata; write a new catalog snapshot."""
import argparse
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TITLE = re.compile(r"PCS[A-Z]\d{5}")
NPWR = re.compile(r"NPWR\d{5}_\d{2}")
CONTENT = re.compile(r"[A-Z]{2}\d{4}-PCS[A-Z]\d{5}_\d{2}-[A-Z0-9]{16}")
VERSION_PATTERN = re.compile(r"(.+)_(PCS[A-Z]\d{5})")
QUEUES = (
    "matched_games.json", "daburo_batch_games.json", "vn_batch_games.json",
    "galgame_batch_28.json", "final_psnine_download_queue.json",
)


def names_from_queues(roots):
    names = defaultdict(list)
    for root in roots:
        cache_dir = root / "pkg/.cache"
        if not cache_dir.is_dir():
            continue
        # 1. 传统队列文件
        for filename in QUEUES:
            path = cache_dir / filename
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            groups = data.values() if isinstance(data, dict) else [data]
            for group in groups:
                items = group if isinstance(group, list) else [group]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    tid = item.get("title_id", "")
                    if not isinstance(tid, str) or not TITLE.fullmatch(tid):
                        continue
                    # 显式白名单：不复制 url、zrif 或许可证密钥
                    for key in ("chinese_name", "name", "orig_name"):
                        value = item.get(key)
                        if isinstance(value, str) and value.strip():
                            names[tid].append({
                                "name": value.strip(),
                                "field": key,
                                "source": f"{path.name}:{key}",
                            })

        # 2. NAS 全量下载队列 (783 个去重多版本游戏元数据)
        nas_q = cache_dir / "nas_download_queue_1108_pkgs.json"
        if nas_q.is_file():
            try:
                data = json.loads(nas_q.read_text(encoding="utf-8"))
            except Exception:
                data = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                tid = item.get("title_id", "")
                if not isinstance(tid, str) or not TITLE.fullmatch(tid):
                    continue
                zh = item.get("game_zh")
                if isinstance(zh, str) and zh.strip():
                    names[tid].append({
                        "name": zh.strip(),
                        "field": "chinese_name",
                        "source": "nas_download_queue:game_zh",
                    })
                name_val = item.get("name")
                if isinstance(name_val, str) and name_val.strip():
                    names[tid].append({
                        "name": name_val.strip(),
                        "field": "name",
                        "source": "nas_download_queue:name",
                    })
                gt = item.get("game_title")
                if isinstance(gt, str) and gt.strip():
                    names[tid].append({
                        "name": gt.strip(),
                        "field": "game_title",
                        "source": "nas_download_queue:game_title",
                    })
    return names


def historical_mapping(local_root):
    result = defaultdict(list)
    path = local_root / "docs/reference/TitleID_NPWR对照.md"
    if not path.is_file():
        return result
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) != 6:
            continue
        tid = cells[0].strip("`")
        npwr = cells[2].strip("`")
        if TITLE.fullmatch(tid) and NPWR.fullmatch(npwr):
            result[tid].append({
                "npwr": npwr,
                "name": cells[1],
                "source": f"{path.relative_to(local_root)}:{number}",
                "evidence_level": "historical_document",
            })
    return result


def collect_source(root, label, is_categorized):
    """扫描指定 PSV 根目录下的 pkg 子目录，自适应支持两层与三层结构。"""
    pkg_base = root / "pkg"
    if not pkg_base.is_dir():
        return []
    records = []
    # 使用 os.walk 避免通配符中方括号等特殊字符引起的 glob 误判
    for dirpath, dirs, files in os.walk(pkg_base):
        base_name = os.path.basename(dirpath)
        m = VERSION_PATTERN.fullmatch(base_name)
        if not m:
            continue
        region, tid = m.groups()
        version_dir = Path(dirpath)
        game_dir = version_dir.parent
        category = game_dir.parent.name if is_categorized else None
        folder_name = game_dir.name

        for f in sorted(files):
            if f.endswith(".pkg") and not f.startswith("."):
                pkg_path = version_dir / f
                try:
                    size = pkg_path.stat().st_size
                except Exception:
                    size = 0

                if label == "local":
                    asset_path = str(pkg_path.relative_to(root))
                else:
                    asset_path = f"nas:{pkg_path.relative_to(root)}"

                records.append({
                    "storage_location": label,
                    "category": category,
                    "folder_name": folder_name,
                    "region": region,
                    "title_id": tid,
                    "filename": f,
                    "asset_path": asset_path,
                    "size_bytes": size,
                    "content_id": pkg_path.stem if CONTENT.fullmatch(pkg_path.stem) else None,
                })
    return records


def collect(local_root, nas_root=None):
    roots_for_queues = [local_root]
    sources = [("local", local_root, False)]
    if nas_root and nas_root.is_dir():
        roots_for_queues.append(nas_root)
        sources.append(("nas", nas_root, True))

    names = names_from_queues(roots_for_queues)
    mapping = historical_mapping(local_root)
    observed = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")

    raw_items = []
    for label, root, is_cat in sources:
        raw_items.extend(collect_source(root, label, is_cat))

    records = []
    for item in raw_items:
        tid = item["title_id"]
        candidates = mapping.get(tid, [])
        variants = {x["npwr"] for x in candidates}
        choices = names.get(tid, [])

        # 优先提取中文名称
        preferred = next((x for x in choices if x["field"] == "chinese_name"), None)
        if preferred is None and candidates:
            preferred = {"name": candidates[0]["name"], "source": candidates[0]["source"]}
        if preferred is None and choices:
            preferred = choices[0]

        record = {
            "name": preferred["name"] if preferred else item["folder_name"].replace("_", " "),
            "name_source": preferred["source"] if preferred else "folder_name",
            "folder_name": item["folder_name"],
            "region": item["region"],
            "title_id": tid,
            "content_id": item["content_id"],
            "app_version": None,
            "trophy_variant": None,
            "trophy_revision": None,
            "npwr": None,
            "npwr_candidates": candidates,
            "npwr_status": "conflict" if len(variants) > 1 else
                           "historical_candidate" if variants else "unknown",
            "asset_path": item["asset_path"],
            "size_bytes": item["size_bytes"],
            "storage_location": item["storage_location"],
            "category": item["category"],
            "file_status": "present_not_integrity_checked" if item["size_bytes"] else "empty_file",
            "observed_at": observed,
        }
        records.append(record)

    # 稳定排序：按名称、区域、Title ID、资产路径
    records.sort(key=lambda r: (r["name"], r["region"], r["title_id"], r["asset_path"]))

    return {
        "schema_version": 1,
        "observed_at": observed,
        "scope": "local:pkg/<game>/<region_TitleID>/*.pkg + nas:pkg/<category>/<game>/<region_TitleID>/*.pkg",
        "package_count": len(records),
        "local_package_count": sum(1 for r in records if r["storage_location"] == "local"),
        "nas_package_count": sum(1 for r in records if r["storage_location"] == "nas"),
        "unique_title_ids": len({r["title_id"] for r in records}),
        "records": records,
    }


def render(snapshot):
    records = snapshot["records"]
    local_count = snapshot.get("local_package_count", 0)
    nas_count = snapshot.get("nas_package_count", 0)
    unique_tids = snapshot.get("unique_title_ids", len({r["title_id"] for r in records}))

    lines = [
        "# 已下载游戏目录",
        "",
        f"本地观察时间：{snapshot['observed_at']}。",
        f"共 **{len(records)}** 个 PKG 资产路径、**{unique_tids}** 个独立 Title ID。",
        f"- **本地存储**：{local_count} 个 PKG 包",
        f"- **群晖 NAS**：{nas_count} 个 PKG 包（涵盖四大白金品类全量多版本）",
        "",
        "文件存在与大小已观察；完整性、游戏更新版本、奖杯分套和配置版本待核验。",
        "NPWR 列列出历史候选，尚未填入已核验编号；冲突保留所有候选。",
        "",
        "| 游戏名称 | 存储位置 | 区域版本 | Title ID | 游戏更新版本 | 奖杯分套 / 修订版本 | NPWR 候选 | 编号状态 | 资产路径 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    labels = {"conflict": "冲突", "historical_candidate": "历史待核验", "unknown": "未知"}
    for row in records:
        candidates = ", ".join(sorted({x["npwr"] for x in row["npwr_candidates"]})) or "待核验"
        loc_label = "群晖 NAS" if row["storage_location"] == "nas" else "本地"
        cells = [
            row["name"],
            loc_label,
            row["region"],
            row["title_id"],
            "待核验",
            "待核验",
            candidates,
            labels[row["npwr_status"]],
            row["asset_path"],
        ]
        lines.append("| " + " | ".join(x.replace("|", "\\|").replace("\n", " ") for x in cells) + " |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--psv-root", type=Path, default=Path(".."), help="Path to local PSV root (default: ..)")
    parser.add_argument("--nas-root", type=Path, default=None, help="Path to Synology NAS PSV root")
    parser.add_argument("--output", type=Path, required=True, help="Directory for the new snapshot")
    args = parser.parse_args()

    local_root = args.psv_root.resolve()
    nas_root = args.nas_root.resolve() if args.nas_root else None
    if nas_root is None:
        default_nas = Path("/mnt/nas_flies/Games/PSV")
        if default_nas.is_dir():
            nas_root = default_nas

    if args.output.exists():
        parser.error(f"output already exists: {args.output}; choose a new snapshot directory")

    snapshot = collect(local_root, nas_root)
    markdown = render(snapshot)

    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "catalog.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output / "CATALOG.md").write_text(markdown, encoding="utf-8")
    print(
        f"Recorded {snapshot['package_count']} PKG paths ({snapshot['local_package_count']} local, "
        f"{snapshot['nas_package_count']} NAS, {snapshot['unique_title_ids']} unique Title IDs) in {args.output}"
    )


if __name__ == "__main__":
    main()

