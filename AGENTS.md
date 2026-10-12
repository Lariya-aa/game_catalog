# PSV Game Catalog

独立游戏目录项目，默认中文。先读本文件和 [README](README.md)。

- 项目根为本目录，使用独立 Git 仓库；不将内容收进上层 Games 索引。
- 职责是登记已下载游戏名称、区域/发行版本、游戏更新版本、Title ID、奖杯版本与 NPWR，以及本地文件位置和证据。
- 只读资产，不下载、提取、拷卡、连接设备、初始化奖杯、改时间戳或同步 PSN。
- 一条资产记录对应一个具体包；同名、同 Title ID 的不同路径保留，不能把包数写成作品数或奖杯套数。
- 区域版本、游戏 APP_VER、奖杯分套/版本、NPWR 分开。未知用 null；旧文编号只作为候选，冲突保留全部来源。
- 自动快照存入新的目录，不覆盖旧快照；人工核验维护在 `data/curated.json`，不得被扫描器覆盖。
- 不读取或复制许可证内容、账号备份、密钥和私人活动记录。下载队列仅提取明确允许的目录元数据字段。
- 修改相邻项目需要明确任务授权，并先读对应指南与检查其 Git 状态。

共享背景：[PSV 指南](../AGENTS.md)、[主 README](../README.md)、[协作主题](../docs/06_奖杯文件与自动化.md#三个项目协作)。独立兄弟项目：[Trophy PSV](../native/trophy_psv/AGENTS.md)、[Trophy Bootstrap](../native/trophy_bootstrap/AGENTS.md)、[Trophy IO](../native/trophy_io/AGENTS.md)。

