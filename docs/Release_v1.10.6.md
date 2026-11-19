# Release v1.10.6（2026-11-19）

## 这次修好了什么

**生产表「兵器生产」按玩家口径改「武器生产」**，并把「大小写只改半边」的一刀切遗留清了一遍，另加一道语境术语守卫。

1. **「兵器生产」不是 EXE 那条串。** EXE 里的 `Armamanents production`（`0x531470`，原文拼写有误）一直译「装备生产」；玩家看到的行其实是**装备/地面元素表**里的生产类别：`build/scenario_csv_zh/<剧本>/Ground.zh.csv` 的 `ID=1489`、`Type=107`、`Name=兵器生产`，13 个剧本各一行，进词典后就是 `Armaments Production`（`data/scenario_csv/translations/equipment.zh.jsonl` 第 610 行）。生产面板按装备类别名画这一行，所以改的是它。
2. **大小写变体的坑。** `mod/build_maps.py` 的 `add()` 对「含空格的 UI 源串」会自动补一份小写键与一份大写键；而人工覆盖层（`glossary/master_overrides.json`）在构建末尾只按**精确键**覆盖，不会回头重算变体。于是修译名常常只修到一条，另一条仍是 v1.6.3 批量复用的旧译——界面查哪条就显哪条。本次查出的错位：
   - `AP HITS`=行政点伤害、`HE HITS`=穿甲弹命中（两行串位，EXE `0x52bde8` 起同块 `GROUND ELEMENT`）
   - `AIR SUPER`=空优报警 → 空优（`0x52c01c`，同块 `NAVAL PATROL`、`AIR INTRUDER`）
   - `GROUND ATTACK NORTH/SOUTH`=地面攻击北方/南方 → 北部/南部对地攻击（`0x5c4bc8`、`0x5c4c54`）
   - `GROUND ATTACK TYPES:`=地面攻击类型 → 对地攻击类型
   - `AMPHIB SUPPORT NORTH/SOUTH`=北支援/南支援 → 北部/南部两栖支援（`0x5c4c98`、`0x5c5188`）
   - `STRATEGIC AIR DAY/NIGHT`=战略空袭日/夜 → 战略轰炸（昼间/夜间）（`0x5c4d90`、`0x5c4b84`）
   - `VVS KBF`/`VVS ChF` 底层行=苏空军高射炮部队/苏空军司令部 → 波罗的海舰队空军/黑海舰队空军（`0x572cc8`、`0x572cd8`，同块 `ShAD - ChF`、`IABR - KBF`）；显示层仍按 AOG 恒等钉死返回英文。
3. **v1.10.4 的容量/建造只改到半边。** `Capacity`、`Built` 改了，自动生成的 `CAPACITY`=容量、`BUILT`=建造、`built`=建造 没改；若界面查的是大写键，玩家看到的仍是旧译。本轮三条对齐为 产能 / 已建成 / 已建成。
4. **新守卫 `Context-term guard`。** `glossary/context_terms.json` 按用途锁定 48 条定译（天气档、胜利级别、生产表列名、生产分区标题、生产行名、空中指令名），列 7 个禁用旧译（非俄罗斯部队、行政点伤害、空优报警、北支援、南支援、战略空袭日、战略空袭夜）与 29 对已复核的大小写差异；`integration/check_context_terms.py` 逐条比对词典与 13 行剧本 CSV，已接入 `finalize.py`。下次再有人只改半边，构建直接拒。

## 这次变了什么

- `data/translations/ui_ops.zh.jsonl`(+qa)：`AP HITS` 穿甲弹命中、`HE HITS` 高爆弹命中、`AIR SUPER` 空优、`VVS KBF` 波罗的海舰队空军、`VVS ChF` 黑海舰队空军、`Armamanents production` 武器生产。
- `data/translations/ui_extra.zh.jsonl`(+qa)：`STRATEGIC AIR DAY/NIGHT` 战略轰炸（昼间/夜间）、`GROUND ATTACK NORTH/SOUTH` 北部/南部对地攻击、`GROUND ATTACK TYPES:` 对地攻击类型、`AMPHIB SUPPORT NORTH/SOUTH` 北部/南部两栖支援；`glossary/ui_extra.csv` 同步。
- `data/scenario_csv/translations/equipment.zh.jsonl`(+qa) 第 610 行 `Armaments Production` → 武器生产；13 个剧本 `Ground.zh.csv` 的 `ID=1489` 行同步。
- `glossary/reference_overrides.json`：新增 `Armaments Production`、`Armamanents production`；`CAPACITY`→产能、`BUILT`→已建成、`built`→已建成、`ground attack types:`→对地攻击类型。
- `glossary/context_terms.json` + `integration/check_context_terms.py` 新增；`mod/finalize.py` 接入第 23 道守卫。
- 词典 **74,501** 条（文本 74,489 + 12 条 `@@RVA` 地址键）；四语言包各 74,501 条、缺字 0；checksums 125 条随发布重新生成。
- **没动**：`Armaments Pool`=兵器库、`Armaments factories damage…`=兵器厂…、`Armaments Prod Mod`=兵器产量模组（「兵器」作名词的既有口径）；`POOR`/`GOOD`/`FACTORY` 三个美术令牌保持英文（改了地图黑格）、`DAMAGED`=受损: 的尾冒号是清理保留。

## 怎么看本版生效

- 启动器标题显示 `1.10.6` 即为本版（游戏主界面右下角仍是游戏自身的 1.0.5.02）。
- 生产界面：特别工业分区里那一行显示「武器生产」；表头「产能 / 受损 / 储备池 / 已建成 / 单位」。
- 空中指令面板：`穿甲弹命中`、`高爆弹命中`、`空优`、`北部/南部对地攻击`、`北部/南部两栖支援`、`战略轰炸（昼间/夜间）`。

## 复查记录

- **小剧本地图城市名仍待实机证据。** 12 个有 `MapText.csv` 的剧本 69,481 条标签四语言包精确命中 69,481、缺 0；`Generic/MapText.csv` 5,568 个唯一标签覆盖全欧，DLC 常见大城市在词典里都有值——数据层没有缺口。11 个 DLC 剧本在 `Dat/CSV` 下没有目录，`.scn` 与 `Dat/GenData/*.dat` 全部加密（头 10 字节恒为 `10 95 ff f9 e0 33 b4 f1 9e 79`），静态读不到它们的标签串。取证办法：`mod/logs/` 下新建空文件 `trace.on` → 启动 → 进该小剧本看地图 → 退出 → 回传 `mod/logs/native.log`，未命中标签会写成 `... none en "..."`。
- **构建**：`build_maps.py` 打包 74,501 条；`build_variants.py` 四语言包 74,501、缺字 0；`audit_layers.py` override-vs-lower 0、lower-multi 1,332（既有）；`finalize.py` 23 道守卫全过（`Context-term guard: 48 条术语、13 行剧本 CSV / 全部一致`）、`Integrity metadata: 125 files`；唯一 WARN 仍是游戏目录 `1941 Campaign - No Early End/MapText.csv` 被改过（中文 5,714/5,782，既存）。
- **发布**：`publish.py` 目标版本 1.10.6、条目 74,501、校验通过；安装目录 `--verify` 记 `OFFLINE VERIFY PASS`；活动槽 `payload/translations.bin` 物化为 zh-CN 变体（9,584,262 字节，sha256 `2583A3FBF8AC…`）；`WitE2CN.exe`/`WitE2CN_Text.dll` 与 v1.10.5 同哈希（`CDC4294A…`/`5BAA5833…`，本版未改启动器与 DLL）。
- 本机未启动游戏（工程纪律），语境由 EXE 字符串表同块邻串与构建守卫静态复核。

---

版本：1.10.6 · 词典 74,501 条（文本 74,489 + 12 条地址键）· 四语言包缺字 0 · 23 道构建守卫 · 游戏版本 1.0.5.02
