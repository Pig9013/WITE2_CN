# DLC 剧本适配审计（v1.9.11 周期）

> 触发：用户指出「受众不仅有 DLC 的人，也有没有 DLC 的人，都要适配」（2026-11-07）。
> 铁律：工程侧不启动游戏，`WitE2CN.exe --selftest` / `--prepare` 允许。

## §0 结论

| # | 结论 | 置信度 | 依据 |
|:--|:--|:--|:--|
| 1 | 游戏 `Dat\Scen\` 共 23 个剧本，其中 **11 个属 DLC**（《钢铁炼狱》等），此前一个都没汉化 | 高 | 目录实测 69 文件 = 23 .scn + 23 .txt + 23 .jpg；`build\scenario_csv_zh\` 只有 13 个目录 |
| 2 | 11 份 DLC 剧本简介（`Dat\Scen\*.txt`）**已全部译完**，23/23 覆盖 | 高 | `build\scen_zh` 现有 23 个 .txt；overlay 实测 23 个 |
| 3 | DLC 的场景**数据表无法抽取**：它们没有外部 CSV，全部编译进加密的 `.scn` | 高 | `Dat\CSV\` 仅 14 个目录（全是基础剧本）；`.scn` 首字节 `10 95 ff f9…`，全文搜 `Units.csv`/`GameEvents`/`PK\x03\x04` 全为 -1 |
| 4 | DLC 剧本内的单位/地名/事件文本**无法由本仓库翻译**，只能依赖既有字典与运行时钩子 | 高 | 同 3；数据不可读即不可写，硬改 `.scn` 会破坏存档与校验 |
| 5 | **无 DLC 玩家不受影响**：overlay 只新增 `.txt`，不新增/不修改 `.scn`；启动器按目录建目标路径、按哈希决定是否写入 | 高 | `mod/src/Launcher.cs:542-558`（`Directory.CreateDirectory` + `File.Copy(...,true)`）；剧本列表来自 `.scn` |
| 6 | 游戏自身就用「* Scenario requires … DLC」标记玩家没有的剧本，说明列表不靠 `.txt` 枚举 | 高 | EXE UTF-16 串 `0x52c5f0` `* Scenario requires 'Steel Inferno' DLC`、`0x52c640` `* Scenario requires DLC`、`0x545a00` `SCENARIO REQUIRES 'STEEL INFERNO' EXPANSION (DLC)` |

## §1 11 个 DLC 剧本清单

`1943 Campaign`；`1944 Campaign (May Start)`；`AG A - Part I - Race for the Caucasus`；`AG A - Part II - Kuban Bridgehead`；`AG C - Kutuzov to Bagration 43-44`；`Case Blue Phase II 42-43`；`Case Blue Phase II 42-43 - Alternate`；`Drama on the Danube 44 - AI`；`Drama on the Danube 44 - H2H`；`Road to Karelia`；`Western Ukraine 43-44`。

已汉化的 12 个基础剧本：`1941 Campaign`、`1941 Campaign - No Early End`、`Introductory Scenario 1 - Velikie Luki`、`Introductory Scenario 2 - Road to Minsk`、`Operation Typhoon 41`、`Red Army Resurgent 42-43`、`Red God of War`、`Road To Leningrad`、`Stalingrad to Berlin Campaign`、`Stalingrad to BerlinCampaign-NoEarlyEnd`、`The Destruction of Southwestern Front`、`Vistula to Berlin Campaign`。

## §2 为什么 DLC 数据表白不了

- `mod/build_maps.py:113-116` 的场景表来源只有两处：游戏 `Dat\CSV\<剧本>\*.csv` 与 `build/scenario_csv_zh`。DLC 剧本在这两处都没有目录。
- `.scn` 不是 zip、不是纯文本：`Road to Karelia.scn` 1,701,379 字节，首字节 `10 95 ff f9 e0 33 b4 f1`，搜索 `Units.csv`、`GameEvents`、`Units`、`PK\x03\x04`、`CSV` 全部 -1。引擎在载入时解密，磁盘上没有可编辑层。
- 结论：DLC 剧本的单位番号、地名、事件文本**只能靠词典（若键与基础游戏相同）与运行时钩子**。DLC 专属的新键无法进入词典——因为我们拿不到键。

## §3 简介的体例（与基础剧本一致）

删 `Author:` 行；`历史概述` / `战役概述` 下跟 33 个半角减号；`轴心国玩家：` / `苏联玩家：`；每条 `- ` 要点；行政点写作 `- 行政点/回合：N`；`***` 建议规则段与 `**可能的…触发提前结束` 保留星号前缀并译出。段落单行不折行，UTF-8 无 BOM、LF。

## §4 无 DLC 兼容性分析

1. **只增不改**：`payload/overlay/Dat/Scen` 下 23 个 `.txt` 全是简介，不含 `.scn`；玩家没有的 DLC 剧本不会因为这 `.txt` 出现而多出条目。
2. **不因缺文件报错**：启动器把 overlay 逐文件复制到 `mod\runtime`，目标目录用 `Directory.CreateDirectory` 现场创建，源文件全部随包提供，不读取游戏目录里的对应文件（`Launcher.cs:542-558`）。
3. **私有副本同步相反方向**：`--prepare` 是「游戏 → runtime」，无 DLC 的机器只是少拷 31 个 DLC 文件，逻辑不变（v1.9.10 主菜单黑屏的修法）。
4. **剧本列表来源**：EXE 里带 DLC 归属提示串，说明列表按 `.scn` 与内置清单生成，`.txt` 只是被选中后读的说明文本。
5. **风险残留**：若引擎对 `Dat\Scen` 做全目录枚举且对 `.txt` 也建条目（未观察到，静态无法 100% 排除），无 DLC 玩家可能看到只有说明、点不进去的幽灵行。玩家侧观察项：无 DLC 环境下进入「选择剧本」页，确认列表仍是基础剧本数量。

## §5 交付与验证

- 新增 11 份译文：`build/scen_zh/`，合计 14,538 字节（源 18 KB 左右）。
- 重建链：`build_maps.py` → `complete_font.py` → `build_variants.py` → `finalize.py` → `publish.py`，全部 exit 0。
- `complete_font.py` 因新简介补了 6 个字形：简化 2,433 → **2,439**，繁体 2,271 → **2,274 / 2,276**，四套缺字 0。
- `finalize.py` 十三道守卫全 OK，`Integrity metadata: 136 files`（92 → 136 = 每个语言包各多 11 个简介 × 4）。
- 安装目录实测：`payload/overlay/Dat/Scen` 23 个 .txt；活动槽 sha256 未变（词典没动）；`--selftest` `SELFTEST PASS`。

## §6 复现命令

```powershell
cd D:\Tool\WITE2\WITE2_CN_repo
python mod\build_maps.py
python mod\complete_font.py
python integration\build_variants.py
python mod\finalize.py
python mod\publish.py
```

## §7 边界

- 未进游戏：DLC 剧本简介的实际排版（换行、星号段）只能由玩家目视确认。
- `.scn` 内部文本不可读，本报告不对「DLC 剧本里没译到的专有名词」做任何承诺。
- 无 DLC 兼容性的第 5 条（幽灵行）属静态推断，需无 DLC 玩家确认。
