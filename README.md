# PSV Game Catalog · 已下载游戏目录

本项目独立维护已下载游戏及其版本、奖杯身份目录，位置为 `/Volumes/mbp_share/Games/PSV/game_catalog`。拥有自己的 Git 仓库，并从上层 Games 仓库排除。游戏本体仍在原资产目录，目录项目记录路径与元数据。

快照清单：
- **最新全量快照 (2026-10-12)**：[游戏目录 (1,113 包 / 915 Title ID)](data/snapshots/2026-10-12/CATALOG.md)、[完整 JSON](data/snapshots/2026-10-12/catalog.json)、[NAS 增量收录说明](data/snapshots/2026-10-12/NEW_ADDITIONS.md)。
  - 收录本地 333 包（326 Title ID，326.43 GB）+ 群晖 NAS 780 包（4 大白金品类全量多版本，710.05 GB），总计 **1,113 个 PKG 路径、915 个独立 Title ID**，总容量 **1,036.48 GB**。
- **初版快照 (2026-10-11)**：[游戏目录 (333 包)](data/snapshots/2026-10-11/CATALOG.md)、[完整 JSON](data/snapshots/2026-10-11/catalog.json)。
  - 初版仅覆盖本地 `pkg/` 目录，共登记 **333 个 PKG 路径、326 个 Title ID**。按包记录统计，233 条有历史 NPWR 候选、99 条缺少编号、1 条存在编号冲突；已核验 NPWR 仍为 0 条。

## 登记口径

| 字段 | 含义 |
| --- | --- |
| `name` / `folder_name` | 检索名称与原始游戏目录名；名称来源单独保留 |
| `region` | 下载目录中的区域/发行版本，例如 US、EU、JP、ASIA；不是奖杯分套结论 |
| `title_id` / `content_id` | 游戏安装身份与具体包身份；Content ID 初版只从文件名提取 |
| `app_version` | 游戏自身 APP_VER/更新版本；未读实际元数据则为空 |
| `trophy_variant` | 经核验的奖杯分套标签，例如共享版本或独立区域套；未核验为空 |
| `trophy_revision` | 奖杯配置修订版本；不把 NPWR 后缀 `_00` 当作修订版本 |
| `npwr` | 经核验的奖杯通信编号；初始快照为空 |
| `npwr_candidates` / `npwr_status` | 旧对照表提供的候选及来源；分别标为历史候选、冲突或未知 |
| `asset_path` / `size_bytes` / `file_status` | 包位置、观察大小、存在状态；文件存在不等于下载完整或可运行 |
| `observed_at` | 本次本地观察时间，Asia/Shanghai |

一条快照记录对应一个 PKG 路径，保留重复资产。作品数、区域包数与独立奖杯套数分别统计；多个 Title ID 可能共用同一个 NPWR。

## 更新

使用系统 Python 3 和标准库，无安装依赖：

```sh
# 仅扫描本地目录
python3 scripts/build_snapshot.py --psv-root .. --output data/snapshots/新的快照名

# 同时收录本地与群晖 NAS（支持两层与三层分类结构）
python3 scripts/build_snapshot.py --psv-root .. --nas-root /mnt/nas_flies/Games/PSV --output data/snapshots/新的快照名
```

输出路径必须尚不存在。扫描限定到本地 `pkg/<游戏>/<区域_TitleID>/*.pkg` 以及 NAS `pkg/<分类>/<游戏>/<区域_TitleID>/*.pkg`，读取文件属性和允许的名称字段，参考既有 Title ID/NPWR 对照与下载队列元数据；不读取 PKG 内容或许可证内容。此初版范围未覆盖 `app/` 中汉化整合压缩包等其他资产格式。

人工核验记录在 [data/curated.json](data/curated.json)，按 `asset_path` 关联，保存 `name`、`app_version`、`trophy_variant`、`trophy_revision`、`npwr`、`evidence`、`verified_at` 等需要补充的字段。扫描器只产出观察快照，当前不自动合并人工记录。版本或 NPWR 的证据应指向实际包元数据/奖杯配置或明确的核验资料；不要凭地区推断。

与 [Trophy PSV](../native/trophy_psv/README.md)、[Trophy Bootstrap](../native/trophy_bootstrap/README.md)、[Trophy IO](../native/trophy_io/README.zh-CN.md) 分别维护。本项目提供资产目录；三个奖杯项目负责各自的数据库排期、目录生成和回写工作。

