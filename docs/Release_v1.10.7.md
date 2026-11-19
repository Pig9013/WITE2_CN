# Release v1.10.7（2026-11-20）

## 这次修好了什么

玩家反馈（1.10.6）：同一台机器上，「可用航空作战群」在 **AG A**、**Introductory Scenario 1**、**Red God of War** 三个剧本里是空列表，只有 **1941 Campaign** 正常。这不是新回归，而是 1.10.1 的名称守卫只盖住了三族前缀，其余名字从 1.9.21 起一直带病，玩家换了剧本才集中暴露。

### 一、根因：引擎比的是名字**对象**，不是文字

引擎在**载入剧本时**就把航空队/航空军名交给本地化查表并缓存进单位对象；打开「可用航空作战群」面板时，它拿数据层（`Dat/CSV/<剧本>/AOGs.csv` 的 `AirHq` 列，指向 `Units.csv` 的单位）里的**名字对象**逐行比对，**比指针，不比文本**（v1.9.21～v1.10.2 三轮排查的结论：同一份 `native.log` 两段对照、原地改写会污染引擎共用缓冲，见 [AOG名字对象比对_v1.10.1.md](AOG名字对象比对_v1.10.1.md)、[AOG原地改写_v1.10.2.md](AOG原地改写_v1.10.2.md)）。所以载入时只要交回的不是**调用方自己的源串指针**，这个 HQ 的行就被筛掉——面板连取行文字都走不到，日志里标题之后一条数据都没有。

三类名字能活下来：原样直通（`1st`、`15th` 这类词典里没有的）、三族前缀（`Luftflotte`/`Luftwaffe`/`Flieger`，v1.10.1 的名称守卫）、以及本版新补的两条规则。其余全断：

- **英文钉死条目**交回词典池里的副本——文本相同、指针不同：`LW Kdo East`、`LW Kdo West`、`Italian Luftwaffe Command`、`1st/3rd/6th Air Army`、`IV/V/VIII Fliegerkorps` 等（`glossary/aog_identity.json` 605 条）；
- **有中文译名的**直接交回中文：`Hungarian`→匈牙利、`Rumanian`→罗马尼亚、`Finnish`→芬兰、`PVO`→防空部队、以城市/方面军命名的苏军空军司令部（`Leningrad`、`Western`、`Kiev`…）。

对照玩家报的剧本：1941 Campaign 的可用列表里主要是 `Luftflotte 1/2/4`（守卫覆盖），所以一直正常；Intro1 有 `LW Kdo East`；Red God of War 有 `1st/3rd/6th Air Army`；**AG A 是 DLC**，`Dat/CSV` 下没有目录，605 条钉死表根本覆盖不到它的航空军名。顺带解释了 v1.10.2 文档里记的遗留现象「匈牙利/罗马尼亚空军司令部的可用列表为空」——同一个根因，当时归到数据层没查透。

### 二、修法

1. **载入期名字窗口**（`mod/src/text_hook.c`）：`translate()` 查到 `w_weather.dat` 就打开窗口（上限 200 次查表），窗口内**名字形态**的串（长度 ≤72、不含 `% { } " : \ / | =` 与控制字符）一律 `return source`；遇到界面串 `5 LockIn gGameOption IN` 或查满即关闭。

   日志证据：7 份 `native.log` 共 11 次剧本载入，结构完全一致——`w_weather.dat` 的两条查表（`w_weather.dat`、`GenData\w_weather.dat`）之后紧跟 65~66 条名字查表（`Luftflotte 1` 起、`XII Troop Carrier Command` 止），下一行就是 `5 LockIn gGameOption IN`。以 `native.log` 为例：23040/23041 锚点 → 23042~23106 名字 → 23107 `LockIn`。

2. **恒等条目回源指针**：词典值与源文字节相同时 `return source`，不再返回词典池副本。显示文本一个字都不变；605 条 AOG 名、`LW Kdo East` 一类钉死条目、以及以后新加的英文钉死条目一并生效。

3. **日志截字修好**：`append_utf8()` 调 `WideCharToMultiByte` 传的是显式长度，不写结尾 NUL，旧代码紧接着回读 `tmp[bytes]` 判断 UTF-8 边界，读到的是栈上脏字节，约 1/4 概率把最后一个字节当多字节尾字节吃掉。排查时看到的 `Kharko`/`Kie`/`Bryans`/`Wester`/`Air Arm`/`15t` 全是这个 bug，不是游戏数据缺字。

### 三、为什么地图城市名不受影响

城市标签是**载入段之后**另查的，不在窗口里：1941 Campaign 那次运行里 `Warsaw`（`native.log` 第 23326 行）、`Rostov`（第 23348 行）的查表都在 `5 LockIn gGameOption IN`（第 23107 行）之后约 200 行。窗口在 `LockIn` 就关，地图标签照常翻译。（v1.10.6 记的「小剧本城市名仍待取证」是另一件事，本版未动。）

### 四、覆盖范围：23 个剧本逐一核对

玩家追问「每个剧本都有各自的空军单位和指挥部，不能只修我列的三个」。本版把本机 23 个剧本全量核对了一遍（工具 `integration/audit_air_hq.py`，`--check` 已接入 `finalize.py`）：

- 有 `Dat/CSV` 的 **12 个剧本**：按 `AOGs.csv` 的 `AirHq` 列解析出全部指挥部名，逐个判定归属——前缀守卫 42 次、恒等条目 6 次、需载入窗口 100 次（去重 28 个名字）、词典无条目 56 次，**unsafe = 0**。单剧本最多 22 个需窗口名字，窗口上限 200，最长名字 15 字符（`name_like` 上限 72）。
- **空军单位（航空作战群）名**同样逐剧本核对：12 个剧本共 4,010 条 `AOGs.csv` 引用、去重 612 名，全部是恒等条目（599 名）或前缀守卫（13 名 `Luftflotte`），需窗口 0 名、未钉死 0 名。
- 无 `Dat/CSV` 的 **11 个 DLC 剧本**（AG A I/II、AG C、Case Blue II、1943/1944 Campaign、Drama on the Danube、Road to Karelia、Western Ukraine 等）：`.scn` 是加密容器（头部 `10 95 ff f9`、熵 8.0，zlib/lzma/bz2 均失败），离线取不到单位名，标为「载入窗口兜底」。
- **窗口与剧本无关的证据**：1941 Campaign 的载入段（`native.log` 23040→23107，66 条）里含 1941 根本用不到的 `RAF Transport Command`、`8th/9th US Air Force`、`Malta Air Command`、`1st–4th Ital. Air Fleet`、`IX/XII Troop Carrier Command`，还含构词部件 `15t`/`16t`/`17t` 与 `Air Arm`——说明这是一张**全局空军指挥部名词表**，DLC 自己的 HQ 名同样进表，窗口照收。

完整矩阵与复查步骤见 [全剧本空军指挥部覆盖_v1.10.7.md](全剧本空军指挥部覆盖_v1.10.7.md)。

## 这次变了什么

- `mod/src/text_hook.c`：新增 `load_window`/`name_like()`、`translate()` 两条新规则、`append_utf8()` 的 NUL 修复；自测新增 131~136 号用例，原 103 号改为只比文本。
- `WitE2CN_Text.dll`：按 `zig cc -target x86-windows-gnu -shared -O2 -s` 重建，71,168 字节，sha256 `1D8A5B9A5615746F7E08030640C210C722E84D3663C4256EB37BB74884DC54E9`；导出名与旧版一致（`Wite2CN_Initialize@4`，启动器 `mod/src/Launcher.cs:719-721` 按此名查找，已在 32 位宿主上实测解析成功）。
- `integration/audit_air_hq.py`：23 个剧本的空军指挥部名与航空作战群名覆盖审计；`--check` 接入 `finalize.py`（第 24 道守卫）。
- `docs/全剧本空军指挥部覆盖_v1.10.7.md`：逐剧本矩阵、DLC 不可枚举的原因、载入表为全局表的日志证据。
- `payload/checksums.json`：125 条随发布重新生成（DLL 在 checksums 里，必须重跑 `finalize.py`）。
- `VERSION`、`payload/package.json` `mod_version`：1.10.7。
- **没动**：词典（74,501 条 = 文本 74,489 + 12 条地址键）、188 个剧本 CSV、覆盖层、字体。

## 怎么看本版生效

- 启动器标题显示 `1.10.7` 即为本版（游戏主界面右下角仍是游戏自身的 1.0.5.02）。
- 进 **Introductory Scenario 1**、**Red God of War**、**AG A（Part I / Part II）**，打开「可用航空作战群」：列表应逐条出现航空队与飞行团；1941 Campaign 保持正常。
- `mod/logs/native.log` 里这些名字的查表行会带 `load`（窗口内）或 `id`（恒等条目），例如 `TRACE ... load en "PVO"`。

## 复查记录

- **自测**：`zig cc -target x86-windows-gnu -O1 -DW2CN_TEST` → `PASS: decoy skipped; 2 text call sites; 10000 thiscall round-trips; crest path restored; map-label variants normalized; unrelated paths unchanged`（退出 0）。
- **构建**：`finalize.py` 24 道守卫全过（`AOG identity guard: OK (605 names, 605 pinned)`、`Context-term guard: 48 条术语、13 行剧本 CSV`、`MapText coverage guard: OK`、`Air HQ guard: 23 scenarios (12 with CSV, 11 DLC), 28 window names`、四语言包缺字 0）、`Integrity metadata: 125 files`；唯一 WARN 仍是游戏目录 `1941 Campaign - No Early End/MapText.csv` 被改过（既存）。
- **发布**：`publish.py` 目标版本 1.10.7、条目 74,501、校验通过（复制 3 个文件）；安装目录 `--verify` → `OFFLINE VERIFY PASS`；`WitE2CN_Text.dll` 仓库与安装目录同哈希 `1D8A5B9A…`。
- **本机未启动游戏**（工程纪律）。实机判据见上一节；若某个剧本仍为空，请回传该次 `mod/logs/native.log`（`mod/logs/` 下放空文件 `trace.on` 即可开 trace），看该 HQ 名字是 `load`、`id` 还是 `exact zh`。
- **已知口径**：航空队/航空军名在部分面板仍显示英文——名字对象必须保持英文才能通过身份比对，这是 v1.10.2 定下的口径，本版不改。

---

版本：1.10.7 · 词典 74,501 条（文本 74,489 + 12 条地址键）· 四语言包缺字 0 · 24 道构建守卫 · 游戏版本 1.0.5.02
