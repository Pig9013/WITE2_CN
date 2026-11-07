---
name: wite2-cn-mod
description: Use when localizing Gary Grigsby's War in the East 2 (WitE2) into Chinese with a self-contained, removable mod, or when auditing/repairing an existing WitE2 Chinese mod. Covers the data-layer pipeline (jsonl → vocabulary CSV → scenario CSV → master override), native text-hook DLL and translation dictionary, place/designation/equipment terminology governance, the 28-class defect taxonomy with detection rules, publish-to-install discipline, and strict no-game-launch rules.
version: 2.0.0
---

# WitE2 独立汉化 Mod

## 一、目标与铁律

目标：在不修改原游戏 EXE、不覆盖原 .scn、不依赖本机绝对路径的前提下，把界面、快捷键提示、单位/事件/地图/百科文本汉化，并保持可整体删除。

铁律：

1. **绝不启动、附加、重启或结束游戏/Steam。** 只读文件、只改文件；实机测试一律由用户执行。
2. **不修改原游戏 EXE、.scn、原 CSV。** 运行资源放在独立 mod/runtime 私有副本中。
3. **翻译只用本机模型**；不调用云端。
4. **任何看起来像 UI 的字符串，必须先从 EXE 原始 UTF-16 字符串与真实占位符取证**，不能凭猜测批量塞词典。
5. **先静态审计再改；改后重新审计 + checksums。** 不要一催一动。
6. **改了不等于交付了。** 每次重建后必须发布到实际运行的安装目录并校验（见 §四）。这是本项目最容易翻车的一条。

## 二、工作流全景

六个阶段，缺一不可：

    ① 语料取证 → ② 数据层修改 → ③ 构建 → ④ 发布 → ⑤ 静态审计 → ⑥ 用户实机验证

- ① 语料取证：本机书库（战史/兵棋规则书/WitE 手册）转可检索文本；文字版直接抽取，扫描版 OCR；已有文字层的不重复 OCR。
- ② 数据层修改：改动只写进 glossary 的定译表，不散落在各处 CSV。
- ③ 构建：integration/fix_equipment_names.py（装备修订表）→ integration/unify_layers.py（分层统一）→ build_maps.py（简体）→ complete_font.py → build_variants.py（繁体三套：s2tw / s2hk / s2hk）→ finalize.py（四套语言包守卫 + checksums）→ publish.py。
  改了简体译文必须重跑 build_variants.py，否则繁体三套停在旧译文（finalize.py 会因键集合/条目数不符报错）。
- ④ 发布：mod/publish.py 同步到安装目录并校验 checksums。
- ⑤ 静态审计：跑验证清单（§九）。
- ⑥ 用户实机：用户自己启动 mod\WitE2CN.exe。

## 三、数据分层与优先级（反复踩坑的根源）

词典是**多层叠加**构建的，后读的层覆盖先读的层：

    data/**/*.jsonl
      → data/translations/unit_names_en_zh.csv
      → build/translation.csv
      → mod/assets/translation.csv
      → build/scenario_csv_zh/*.zh.csv
      → glossary/master_overrides.json（覆盖层：定译/地名/术语，优先级最高）
      → glossary/master_drops.json（丢弃层，永远最后执行）
      → glossary/pending_sources.json（搁置层，永远最后执行）

执行顺序在 mod/build_maps.py:140-163：覆盖层先写入，丢弃层与搁置层最后 pop。**顺序不能反**——v1.6.5 的 82 条地形枚举词、2026-11-06 的小河 `MINOR//` 都是「drop 在前、override 在后」漏回来的。

两层丢弃的分工：`master_drops.json` = 永不翻译（技术串、美术路径令牌）；`pending_sources.json` = 缺权威出处、暂缓翻译（保留英文原文，查到出处把键移出清单重跑即回中文）。

**教训**：只改 jsonl，场景 CSV 里的旧值照样覆盖回来，同一个词要改三四次，表现为「反复改同一个词」。

**三层词表压语料（v1.9.10 批次四实测）**：`data/translations/unit_names_en_zh.csv`、`build/translation.csv`、`mod/assets/translation.csv` 的读取顺序在 jsonl **之后**，所以它们的值会盖掉 jsonl。判断某键来自哪层直接看 `audit/provenance.json`：若 provenance 是 `mod/assets/translation.csv`，那改 jsonl 与场景 CSV 都不会生效。

**分层统一（2026-11-06 起强制）**：一个装备名同时存在于四个层——`data/scenario_csv/translations/*.zh.jsonl`（含 `.qa`）、`build/scenario_csv_zh/*/*.zh.csv`（与游戏原 CSV 逐格对照，同名装备在 14 个剧本里重复 585 次）、`glossary/reference_overrides.json`（覆盖层源头）、以及由它生成的 `master_overrides.json`。**只改一层 = 没改。**

- 改装备名：写 `glossary/equipment_name_fixes.json`（`{source, old, new, note}`，可选 `"add": true` 补词条）→ 跑 `integration/fix_equipment_names.py`。它按**英文原文**匹配全部 jsonl 与三类 CSV（`Ground/Aircraft/Devices.csv`）的 Name 列；原文同名两值冲突直接 `SystemExit`。
- 改界面词/裁决冲突：写 `glossary/layer_unify.json`（`entries` 四动作 `set/revert/drop_override/adopt_override`，`patterns` 正则批量）→ 跑 `integration/unify_layers.py`。它一条规则同时写 jsonl（含 .qa）、场景 CSV、覆盖层与 manual；**只有 jsonl 里也没有的键**才允许补进覆盖层，否则等于把语料再抄一份进覆盖层。`--check` 只统计不改文件，有漂移 exit 2。
- 守卫：`mod/finalize.py` 的 **Layer guard** 会调 `integration/audit_layers.py --check`，`override-vs-lower` 不为 0 即拒绝构建；`lower-multi`（同词多译）只报告。

**纪律**：任何定译只写进 glossary/reference_overrides.json（分 places / ui / terms 三组）与 glossary/manual_translations.json；
由 integration/build_master_overrides.py 汇总为 master_overrides.json，build_maps.py 在写词典前最后套用。

同一键同时出现在多组时，优先级 **terms（自动批量）< places < ui（人工逐条）**。

技术性字符串（语言代码 en-GB、编码名 UTF-8、内部占位符）进 master_drops.json，**不进词典**——否则会被模型翻成废话，界面显示一整段「请提供需要翻译的原文内容」。

## 四、发布（本项目的最大事故）

**本机可能同时存在两份 mod**：仓库（修改源）与安装目录（实际运行）。payload 停留在旧日期时，仓库里的一切修改都不会进游戏。

发布动作：

    python mod\publish.py            # 读 settings.local.json 的 install_path
    python mod\publish.py <目标目录>  # 或显式指定

发布后必须核对三项：package.json 的 mod_version、translations.bin 的 sha256、checksums 全通过。

版本戳链路：VERSION 文件 → build_maps.py 写入 package.json 的 mod_version → 启动器窗口标题。**用户看标题就知道跑的是哪一版。**

### GitHub 上传纪律（2026-11-06 / 2026-11-07 用户指示）

**一、不发碎版本（2026-11-07）。** 版本号是「发布次数」，不是「对话次数」。一批改动做完 → 重建 → publish 到安装目录 → 本地 `git commit` 即止，**不动版本号、不打 tag、不 push**。版本号在一次发布周期里只认一个：

- 周期开始时定下「下一个版本号」（如 v1.9.10），之后所有批次都在这一个号下积累，**中途不再加号**；
- 用户说「发布」时，才把 v1.9.10 定稿并打出唯一的 tag；
- 一次发布只发一个版本，正文覆盖**上次发布至今的全部改动**（不是只写最后一批）。分三天做的三批，仍是一个 v1.9.10、一篇 Release。

反例（已犯）：v1.9.1～v1.9.9 八天九个 tag，一个对话一个版本；玩家看到的「最新版」永远落后，Release 说明只覆盖最后一次改动，主页版本行也跟着碎。

**二、只有用户明确说「上传 / 发布」才 push。** 那次要把五件事一起做完：VERSION 与 package.json、CHANGELOG（把周期内各批合并成**一节**，不是每批一节）、README 第 5 行版本 / 第 21 行规模 / 「最近更新」小节（四个语言版同步版本行）、Release 标题与面向玩家的正文、tag + Wiki。

**三、CHANGELOG 的写法随之上移**：周期内可以按批提交 commit，但 CHANGELOG 只保留「上一个已发布版本 → 下一个版本」的一节，发布时一次写全；不要把每批都写成独立版本节再在发布时拼接。

## 五、已认可的做法

- 独立私有 runtime：启动器把游戏复制到 mod 自己的 runtime，只在该副本上加载字体、overlay、文本钩子；删除 mod 不影响原游戏。
- 文本钩子：WitE2CN_Text.dll 在游戏原生本地化查询处替换字符串；不改游戏数据对象、不扫描改写内存。
- 精确词典 + 大小写变体：对 UI 来源生成 lower/upper 变体；场景散文不展开。
- 原始占位符优先：UI 键常带 {ctrl-s} / {x} / {F1} / {+}；必须按 EXE 原始字符串生成完整键，译文里换成可读的 (...) 。
- 编辑器 CSV 导入：编辑器只从固定的 Dat\CSV\<剧本>\ 读固定文件名。必须备份原 CSV → 放入 .zh.csv → Import Selected → Save As 新 .scn → 恢复原 CSV。
- CSV 完整保真：按行/列原样复制，保留额外字段、BOM、编码；只改允许的文本列。GameEvents.csv 常无 BOM，MapText.csv 常有 BOM。
- 字体子集：从译文/overlay 收集字符，用系统 CJK 字体子集化；**补字源必须与底字体 unitsPerEm 一致**（本项目用 DengXian Deng.ttf，2048；SimHei 是 256，merge 会崩）。
- 可移植：路径相对 mod 根目录；游戏路径从 settings.json → WITE2_GAME → Steam 注册表自动解析。

## 六、已否决的做法

| 做法 | 否决原因 |
|---|---|
| 直接改 WarInTheEast2.exe | Steam DRM 校验，改动导致退出码 51/53 |
| 只往 Dat 放 translation.csv / 字体 | 引擎忽略，实测无效 |
| 旧式内存扫描替换启动器 | 与文本钩子冲突，曾导致卡死 |
| 用 DictReader/DictWriter 处理剧本 CSV | 丢弃事件行表头之外的脚本字段，点事件即崩 |
| Batch Import 一次导入所有表 | 不同表/剧本 ID 引用混在一起，validation error、闪退 |
| 把快捷键提示机械写成 (Ctrl+X) | 占位符可能是单字母/F 键/+/-/全角括号 |
| 代码里写死 D:\Tool\... 绝对路径 | 换机即失效 |
| 反复启动游戏做验证 | 用户明确禁止 |
| **只改仓库不发布** | 用户启动的是安装目录，改了个寂寞 |
| **专名按字面义直译** | Sep.=September、「3 Gennaio」=1月3日、Bul.=布良斯克、ART=艺术、Max=马克斯 |
| **按英文词条名去维基匹配中文** | Moss→藓类植物门、Fish→鱼群、Saki→作家、Yerevan→叶里温 |
| **把 ABBR 一律当人名音译** | Rec=Received、Dif=Difference、Num=Number |
| **位置无关的短语查找** | 「Radom」→拉多姆会把 Rzeszow-Radom 的铁路线也改掉 |
| **翻译地形/天气/美术枚举名** | CLEAR/FOREST/SWAMP/WATER/URBAN/ART/TILE/HEX/TERRAIN 被引擎当作图块贴图查表键，译成中文后查不到贴图，**地图大面积 hex 变黑**（2026-11-01 事故） |
| **把 EXE 全量字符串当界面词一股脑翻译** | 同一张字符串表里既有显示文本也有数据枚举，必须先分类再译 |

## 七、必须人工核验的（机器判不准）

1. **译名取舍**：一地多名（哈尔科夫/哈尔基夫、萨拉热窝/塞拉耶佛），无对错，人定。
2. **句子流畅度**：语义无误但读着别扭，机器判不出。
3. **否定/全体/限定语义**：not / all / only 是否在译文中消失，需逐条读原文。
4. **史实性**：原文自身矛盾（如「1945 年组建、1945 年 2 月改称」），照译不算错。
5. **番号一致性**：同一号不同部队、师/步兵师简称混用属合法，不能机械统一。
6. **长句润色**：百科正文仍是机翻底子，只保证不截断、不缺译、术语地名统一。

## 七之二、EXE 字符串：先分类，再翻译

游戏 EXE 里约 9,900 条 UTF-16 字符串，**同一个池子里混着三类东西**：

| 类别 | 例子 | 处理 |
|---|---|---|
| 显示文本 | `Disband`、`Freight`、`Leader: %d`、`Turn: %d` | 翻译 |
| 数据枚举 / 查表键 | `CLEAR`、`FOREST`、`SWAMP`、`WATER`、`URBAN`、`DESERT`、`TUNDRA`、`BOCAGE`、`ART`、`TILE`、`HEX`、`TERRAIN`、`BORDER ART IDX` | **不译**，保持英文 |
| 内部标识 / 格式骨架 | `Ws0_Qty%d`、`AmmoN`、`ENA`…`ENZ`、`sqd[%d]`、语言代码 `en-GB` | 不译或直接丢弃 |

判定口诀：**全大写、无空格、含义是地形/天气/美术/渲染/图块 → 一律不译**。
这类词一旦翻译，引擎按名字查贴图会失败，表现为地图黑格、图标消失。

技术实现：不译的词写进 `glossary/master_drops.json`（构建期从词典剔除），
并从 `glossary/reference_overrides.json` 删除，防止下次重建被加回。

### 美术路径键（v1.9.7 血案，务必读完）

引擎用字符串拼图块路径。**凡是出现在路径里的字符串进了词典，那张图就永远画不出来**，而引擎不报错、不写日志——只能靠人眼发现「某个地形不见了」。

| 模板（EXE 字符串池） | 参与拼接的字符串 | 危险键 |
|---|---|---|
| `//Tiles//RIVER//%sR%d_%3.3d.tga` | `MINOR//`(0x56200c) `MAJOR//M`(0x56201c) `IMPASS//I`(0x562030) | 都是路径令牌 |
| `//Tiles//%s//%s_%3.3d.tga` | 目录名 + 文件名前缀（同一个串） | **自名型目录名**，见下 |
| `//Tiles//ROAD//%s//%s_%3.3d.tga` | AVERAGE / GOOD / POOR | 同上 |
| `//Tiles//FACTORY//%s.tga` | FAC_* | 低 |
| `//Sym//%s//%s.tga` `//AirSym//%s//%s.tga` | 国籍码 / 单位英文名 | 观察项 |
| `//Gui//frame%s.tga` | green / red / white / highlight | 观察项 |

- **自名型目录**：目录内存在 `<DIR>_<idx>.tga`（例 `CLEAR\CLEAR_001.tga`）→ 目录名会同时当文件名前缀用，译了它整目录全黑。非自名型（COAST/BORDER/RAIL/DRAIL/WEATHER/PORT/FACTORY）模板把前缀写死，目录名可译。
- 名单不要手抄：跑 `python mod\scan_art_tokens.py` 生成 `glossary/art_tokens.json`（20 个自名目录、4 个路径令牌），`finalize.py` 会拒绝任何等于自名目录名或路径令牌的键，并拒绝「纯 ASCII 且含 `//`」的键。
- 历史教训：v1.6.5 只清理了 82 个全大写地形词，`MINOR//`（带斜杠）、`SAND`、`IMPASSABLE`、`HVY_URBAN` 这些「不像枚举」的漏了 → v1.9.7 小河全部消失。
- **改 key 前先查 `audit/provenance.json`**：`Min River` 的值来自 `data/translations/ui_14b.zh.jsonl`，改 `assets/translation.csv` 无效（实测白改一轮）。
- 构建顺序：`build_maps.py` 里**丢弃层必须在覆盖层之后执行**，否则 drops 里的键会被 overrides 复活（v1.9.6 及以前一直如此，连带复活了 Art/City/UTF-8 等 6 键）。

### 覆盖层压设备表（v1.9.8 血案）

设备表的译名不是最终值：`glossary/master_overrides.json` 在 `build_maps.py` 里最后套用，**同名键会静默压掉设备表的新译名**。

- 实测：`equipment.zh.jsonl` 已改成「15.5厘米/60倍径三年式高射炮」，重建后字典里仍是「152毫米M1937火炮」——因为覆盖层也有一条同名键。与 `Devices.csv` 同名的 17 条里 12 条是旧值。
- **改法顺序**：`glossary/reference_overrides.json`（源头）→ `python integration\build_master_overrides.py`（生成物）→ 重建链路。只改 `master_overrides.json` 会在下次重跑生成器时被覆盖回去。
- `reference_overrides.json` 的结构是 `{_meta, places, ui, terms}`，值是 `[译文, 出处注记]`；批量注记（如「口径单位统一为毫米」）往往就是整批错误的指纹，见到先怀疑。
- `integration/build_master_overrides.py` 已加守卫：`master_drops.json` 里的键若又出现在覆盖层，直接 `SystemExit` 并列出键名。
- **丢弃层不是永久黑名单**：`Art`（炮兵）、`City`（城市）在 2026-11-04 被有意恢复，但仍留在 `master_drops.json` 里；v1.9.7 改成「drop 优先」后这两条被静默吞掉。恢复一条译名时，必须同时把它从丢弃层撤下。

### 外语介词被当实词（v1.9.9 血案）

法/比/意装备名里的介词不是实义词：`Canon de 155 C`、`Semovente da 90` 里的 `de`/`da` 只是「……的」。机翻会把它们当国别或动词，产出**事实性错误**：

- `155mm de 155 C Howitzer` → 「155毫米**德制**155C榴弹炮」——实际是**比利时**装备（`Vistula to Berlin Campaign/Ground.csv` 里 `Nation=9`，`Nations.csv` 中 `9=Belgium`；同族的 `76mm de FRC` 的 FRC 就是比利时皇家铸炮厂）。
- `75mm de TR Field Gun` → 「75毫米**拖曳式**野战炮」——`TR` = tir rapide（速射），不是拖曳。
- `75mm de GP III Field Gun` → 「75毫米**穿甲弹三级**野战炮」——`GP` = Grande Puissance（大威力），不是 AP。
- `Semovente M41M da 90` → 「**圣切奇利亚**M41型…」、`Semovente L40 da 47` → 「**自行研发的** L40 轮式突击炮」——Semovente 就是「自行火炮」。
- 还有编年份的：`152mm de 152 Howitzer` → 「M1937」、`220mm de 220 TR Howitzer` → 「M1931牵引」。

**规则**：不猜国别、不补年份。型号段保留拉丁原文，只译口径与炮种 → `155毫米de 155 C榴弹炮`、`M41M 90毫米自行火炮`。修订表落在 `glossary/equipment_name_fixes.json`（`{source, old, new, note}`，source 是 CSV 文件名，如 `Ground.csv`），改完跑 `integration/fix_equipment_names.py` 才会落到 jsonl 与 `build/scenario_csv_zh`。
检测：键或译名含 `\b(de|da|di|des|du)\b`，而译名含「德式/德制/德产/牵引/轮式/穿甲弹」。

### 型号记号被当成可译词（v1.9.9 血案之二·荷兰 Van 族 / 日制 Type）

与 de/da 同源：机翻不认识型号前缀，就把它当实词处理，产物有四类病——大写、删除、改写、编造。

- **大写**：`81mm Van 8 Mortar` → 「81毫米**VAN** 8迫击炮」、`20mm Van TL 1 AA Gun` → 「20毫米**VAN** TL 1高射炮」。
- **改写**：`40mm Van TL 4 AA Gun` → 「40毫米**四联**高射炮」（`TL 4` 是型号，被当成「四联」）；`47mm Van 4.7 AT Gun` → 「47毫米反坦克炮 Van 4.7」（语序错乱）。
- **删除**：`75mm Van TL 1 AA Gun` → 「75毫米**防空炮**」，型号整段消失。
- **编造**：`120mm Van 12 Howitzer` → 「120毫米**M12牵引**榴弹炮」、`150mm Van 15 Howitzer` → 「150毫米**M1935**榴弹炮」、`152mm Van 15 Howitzer` → 「152毫米**M1937**榴弹炮」——M12/M1935/M1937 都不在原文里。

同一病根在日制装备上表现为**写法失控**：同一批 13 件装备在词典里有 9 种写法（`Type97` / `Type 95` / `型2` / `九一型` / `92式21英寸` / `24英寸九三式` / `88式地雷` …）。

**规则**：

1. 型号段保留拉丁原文，只译口径与类别：`81毫米Van 8迫击炮`、`40毫米Van TL 4高射炮`。
2. 日制 `Type NN` → 口径 + 汉字数字 + 式 + 类别：`21英寸九五式鱼雷`、`九一式深水炸弹`、`二式深水炸弹`、`八八式水雷`。
3. 英制雷达 `Type NNN` 保留拉丁（`Type 271 雷达`）；日制雷达 `Type 13/21/22` 暂保留拉丁——旧日本海军电探编号用「一三号」不用「式」，没把握不硬套。
4. 类别以 `Devices.csv` 的 Type 码为准（20 雷达、24 鱼雷、26 深水炸弹、27 水雷）——`Type 88` 曾被写成「地雷」，而 Type=27 是**水雷**。
5. 人名/厂商名可以音译（`van Duren` → 范杜伦），型号记号不行。

检测：源串含 `\b(Van|van)\b` 或 `^\d*mm? ?Type ?\d+` 而译文里该 token 消失/被大写/被换成汉字数量词。

### 族内不成对与型号当口径（v1.9.9 血案之三·自行高射炮族）

前三轮按「名字里的外语词」找族，会漏掉一类问题：**同一族里只有个别条目被译坏**，名字上看不出族。改法是把 `Ground.csv` 的 `Type` 列当分族依据（22 = 自行高射炮、23 = 半履带），整族拉出来横向比：

- **型号当口径**：`SdKfz-7/1 Flak38` → 「38毫米防空炮车」。`Flak 38` 是 20mm 炮的**型号**，不是 38 毫米；同理 `Flak 43`、`Type 97`、`Mk II`。
- **炮种事实错误**：`SdKfz-7/2 Flak43` → 「迫击炮车」（实为防空车）、`M15 MGMC` → 「坦克歼击车」（37mm+双联 12.7mm 组合炮座，Type 22）。
- **缩写丢职能**：`MGMC`（Multiple Gun Motor Carriage）→「机枪载具车」、`AAMG`（anti-aircraft MG）→「自动机枪车」——防空语义全丢。
- **不成对**：`Wirbelwind` 译「旋风式」而 `Ostwind` 译「东风」；`M13/M14/M16/M17 MGMC` 四条四种写法。同族必须同构，单看一条看不出来。
- **错音译**：`Möbelwagen` → 「梅花车」（原意家具搬运车）、`Turan` → 「土尔干」（应为图兰）。
- **罗马数字当日制年式**：`Zrinyi II` → 「兹里尼二式」；「二式/三式」只给日制年式。
- **译文截断**：`SdKfz-8 Flak18` → 「SdKfz-8 8.8 厘米 F」，在字母处断掉。

**规则**：分族看 `Type` 不看名字；型号段保留原文；编制缩写必须译出职能（含「防空」）；同族横向比对，宁可整族一起改，不要只改被点名的那一条。

检测：按 `Type` 分组后，把译名去掉数字与型号段，比较同族词尾是否一致；译名里出现 `Flak ?\d+\s*毫米`、`\d+式` 修饰非日制装备、或长度不足源串 40% 的，都是嫌疑。

**意大利/法国词头在本库不存在**：13 个 jsonl 全量搜 `Carro Armato`、`Autoblindo`、`Chi-Ha`、`Char`、`Chenillette` 均 0 命中（`Semovente` 仅 5 条）。不要为「补齐族」去造条目。

### 拆词直译、厂商名当实词（v1.9.9 血案之四·坦克与装甲车辆族）

按 `Type` 拉坦克族（12 轻/13 中/14 重/15 巡洋支援）与装甲车、突击炮、坦克歼击车、自行火炮族，54 条里能分出四种病灶：

- **一个词被拆开直译**：`Staghound`（T17 猎鹿犬）被拆成 Stag + Hound →「野猪猎人」，同族三条各不相同（`野猪猎人I型` / `野猪III型` / `斯塔霍恩T17E3`）。凡译文出现「野猪猎人」式组合词，先查是不是专名。
- **厂商名当实词**：`White Scout Car`（White Motor Company）→「白色侦察车」；`Humber` →「胡默尔」（应为亨伯）；`Möbelwagen` →「梅花车」（家具搬运车）。车名前缀先判是厂牌、地名还是形容词。
- **机翻残渣**：`Sherman` 竟出现「詹姆斯顿」「詹姆斯」「莫尔斯顿」三种；`Mk VIB` 只剩「马克」；`M5A1 Stuart` →「武士坦克」（Stuart 是人名/型号，不是武士）。译名里混进人名、只剩车种一个词、或同族出现明显无意义词，都是机翻残渣。
- **编制缩写丢职能**：`M10/M18/M3/M36 GMC`（Gun Motor Carriage）→「自行火炮」，数据表里它们是 Type 60/67 坦克歼击车；`TACAM T-60`（罗马尼亚坦克歼击车）→「自行火炮 T-60轻型坦克」。
- **覆盖层里的占位残渣**：`Panzer IVg` 的值是「装甲IVg型」，注记自承占位；5 条 `Jagdpanzer` 系的语序也是覆盖层写的（「坦克歼击车38」）。改这类值必须改 `glossary/reference_overrides.json` 的 terms 组再重跑 `build_master_overrides.py`，改 jsonl/CSV 会被压掉。
- **型号后缀整段丢失**：`Sherman IIA` / `IIIAY` / `IVB 105` 三条都只剩「谢尔曼」，界面上看是同一辆车。

**规则**：专名不拆、厂牌不译意、缩写必须译出职能、同族必须补回型号后缀与车种（坦克/装甲车/坦克歼击车/自行火炮）。

检测：同族译文去掉数字与型号段后比较词尾；译文长度 < 源串 40%、或含「式/型」却无车种词（坦克/装甲车/歼击车/火炮/榴弹炮）、或同族出现两种以上人名音译（詹姆斯/莫尔斯），都是嫌疑。
### 分组表头行被机翻改坏（v1.9.9 血案之三）

飞机、装备列表里的国籍分组行是**数据字符串**，`***` 是分隔装饰：`*** GERMANY (1) ***`、`*** SLOVAKIA (6)***`、`*** WA ITALY (24)***`。这类行有三个特殊风险：

1. **译文里塞换行** → 分组标题在界面上断成三行（`*** France (27)***` 就是这样，原文带 `\n`）。
2. **星号被吃掉** → `*** BELGIUM (9)***` 变成「比 利 时 (9)」，标题失去视觉层级，还多了字间空格。
3. **国家/缩写误读** → `SLOVAKIA` 译「捷克斯洛伐克」（`Nations.csv` 里 6=Slovakia、8=Czech 是两个国家）、`WA ITALY` 译「威亚意大利」（`WA` = Western Allies，应为盟军）、`UK/CW` 译「协约国」（`CW` = Commonwealth，应为英联邦）。

**规则**：表头行只译国家名与括号里的数字，`***`、空格、半角括号格式原样保留 → `*** 名称 (n) ***`；`WA`/`CW` 这类缩写查 `Nations.csv` 的国名再落笔。

**判据（v1.9.9 第三轮定稿）**：与**键本身的装饰形状**对齐，不看固定格式——键以 N 个星号开头则译文开头 ≥3 个；键以星号结尾则译文结尾 ≥3 个；只有前缀的报错串（`*** DrawText VB Lock FAILED…`）只要求前缀；`***Off Map Soviet` 这种原文本来没有尾部星号的，不许自作主张加。数量不必精确相等（引擎只当文本显示），但一个都没有就失败。`mod/finalize.py` 的 **Section-header guard** 现在是**硬失败**（含换行、缺星号都拒绝构建）。

**修复工具 `integration/fix_section_headers.py`**：按原文星号形状重建 `build/scenario_csv_zh/*/*.zh.csv` 的文本列，顺带清掉重复片段（`轻步兵师团   ****** 轻步兵师团 *****`）与尾随注记（`… ******  【注】`），并同步 `data/scenario_csv/translations/*.jsonl`（含 `.qa`）。**必须三处一起改**：词典按英文原串去重，但同一个分组行在 14 个剧本里重复出现——34 个键对应 **585 个单元格**，只改字典下次重建又回来。

### 只改一层＝没改（v1.9.9 血案之五·分层）

同一个英文串在五个地方各有一份值：`equipment.zh.jsonl`（+ `.qa`）、`build/scenario_csv_zh/*/*.zh.csv`、`glossary/reference_overrides.json`、`glossary/master_overrides.json`、`glossary/manual_translations.json`。构建顺序决定谁赢，**改了输的那一层，游戏里就是没变**。

两个真实机制 bug：

1. `integration/fix_equipment_names.py` 旧版按 `(source, old)` 精确匹配——同一门炮既在 `Devices.csv` 又在 `Ground.csv`，修订表只写了 `Ground.csv`，于是 `Devices.csv` 那行不动，`Jagdpanzer` 整族「改了却看不到」。现改为**只按英文原文**建索引，并支持补词条。
2. 覆盖层与下层不一致时，静态地看谁都不会报错：覆盖层自认是最终裁决表。`integration/audit_layers.py` 专查这种冲突，输出 `audit/layer-conflicts.json`；首跑抓到 11 条（`F-6B Mustang` 被覆盖层改名成 P-51、`Mustang I (PR)` 型号被换、`SS` 与 `SS Only` 混用、`Hedgehog` 长文被 jsonl 截断等）。

**判据**：覆盖层不是「更新的值」，只是「最后套用的值」。下层（jsonl/CSV，来自语料与逐条核对）与覆盖层冲突时，先查 `audit/provenance.json` 与原文语境，多数情况是**下层对、覆盖层错**（覆盖层里混着占位残渣与机翻）。裁决结果写进 `layer_unify.json`，不要两处手改。

**检测**：`python integration\audit_layers.py --check`（`override-vs-lower` 必须为 0）；`python integration\unify_layers.py --check`（必须无漂移）。

### 型号被吃掉（v1.9.9 血案之六·飞机族）

模型遇到 `I-153BS`/`Yak-9U`/`Mosquito NF.30` 这类「机名 + 型号后缀」时，会把后缀当噪声丢掉，只剩「伊」「雅克」「蚊式」——同一族十几架飞机在界面上完全同名。飞机 798 名里已有 23 条这样，另 7 条丢了后缀；全局扫描（译文不含键里的数字、且长度 < 键 75%）命中 88 条，还包括 `Somua S-35`→「索马瓦」、`Hedgehog Mk 10/11`→「豪猪」。

**规则**：型号段（字母+数字+点+斜杠，如 `B.XVI`、`NF.XIX`、`9DD`、`-2M3`）保留拉丁原文，只译机名与炮种。`Airframe` 统一「…机体」（`Bf 109 Airframe`→`Bf 109机体`，机名未译就整段留拉丁）；`*** AIRFRAMES ***`→`*** 机体 ***`。**498 个纯型号名（`Bf 109G-6`）保留英文是有意为之**，不算未汉化。

### 一个键只能有一个权威来源（v1.9.9 血案之七·装备族）

- **多义缩写按单词直译**：`Drop/Auxiliary/Ferry/Drum Tank` 里的 Tank 不是坦克，是油箱（译成「支援坦克」「油桶坦克」共 80 条）；`BMG/CMG/TMG` 是车体/同轴/炮塔机枪，机翻把 10 组三种位置全译成同一个「维克斯机枪」，等于把三种武器抹成一种。定语境靠 `Devices.csv` 的 Type 码，不靠词义。
- **同族同译碰撞的检测**：同族内两个不同英文键映射到同一译文，且差异只在缩写（BMG/CMG/TMG、WBD/WBF/WBG、RMA/RMD、Sound Detector (A)/(J)）——这是漏译，不是同义词。
- **两处权威互相覆盖**：`glossary/equipment_name_fixes.json` 与 `glossary/layer_unify.json` 都能写同一个键，而构建时 fix 先跑、unify 后跑，下一轮 fix 又会把 unify 的裁决改回旧值（Jagdpanzer 38 Hetzer / Jagdpanzer IV/70(V) 就是这样来回打架，导致 `Layer guard: FAIL`）。**同一个键只能在一个表里定值**：装备名归 fixes，界面词归 unify，覆盖层只做源头修正。
- **改了覆盖层必须重生成**：改 `glossary/reference_overrides.json` 后不跑 `integration/build_master_overrides.py`，等于没改（`900 L Auxiliary Tank`、`.50in M2 Quad AAMG` 两条就是这样让重建失败了两次）。

### 同族同译与编制层级（v1.9.9 血案之八·Ground 单位名）

- **症状**：同一个 Type 里不同英文名译成同一个中文——四个型号都叫「丘吉尔」（`Churchill I/AVRE/V-CS/VIII-CS`）、四种步兵都叫「步兵班」（`Infantry Squad/Rifle Squad/Infantry Section/Rifle Section`）。编制表里看到同名单位，玩家无法分辨。
- **检测**：按 Type 分组，把「译文 → 英文名集合」聚合，集合大小 >1 即碰撞；总碰撞数 = Σ(组内条目数−1)。第八轮实测 Ground 13 组 → 0，Devices 4 组 → 6（剩余全是同义与大小写）。
- **修法**：`Squad=小队`、`Section=分队`（不要都译「班」，层级会消失）；`Pioneer=工兵`、`Combat Engineer=战斗工兵`、`Sapper=爆破工兵`、`Assault=突击`；型号段（罗马数字、`CS`、`AVRE`）保留拉丁。
- **缩写当单词**：`CV-33` 曾译「战斗值33」（CV 当 combat value）、`A13 Mk II` 曾译「玛蒂尔达II型坦克」（A13 是巡洋坦克）。缩写要看 `GroundTypes.csv` 的族上下文，不能按字面拆。
- **允许的同译**：同一装备两种写法（`Drop Tank`/`Auxiliary Tank`）、源表大小写变体（`DShK`/`DShk`）——译文相同是正确行为，不要为「不重复」硬拆。

### Staffel/Gruppe 与场景表失同步（v1.9.10 血案）

- **症状**：中文化后 `1./JG 51` 与 `I./JG 51` 都显示「第51战斗机联队第1大队」，两条不同建制的部队在列表里同名。
- **判据**：Luftwaffe 番号 `N./JG 51` 是 **Staffel（中队）**，`I./JG 51` 是 **Gruppe（大队）**；`II./`、`III./` 同理。数字与罗马数字在这一位不是写法差异，而是编制层级差异。
- **根因**：语料层 `data/scenario_csv/translations/airgroup.zh.jsonl` 是**对的**（`1./NJG 100`＝第100夜间战斗机联队第1中队、`I./JG 51`＝第I大队），但场景表 `build/scenario_csv_zh/*/AirGroups.zh.csv` 由已失传的生成器写出，把阿拉伯数字 Staffel 也写成「大队」，共 **299 格 / 21 文件**（AirGroups 264 + AirGroupRenames 35，跨 12 个剧本）。旧生成器 `integration/apply_scenario_translations.py` 依赖不存在的 `name_rules` 模块，**不能重生成，只能就地改成品**。
- **修法**：`python integration\fix_airgroup_staffel.py`（`--check` 出口 2）。规则只命中「源单元格 `^(\d+)\./` + 译单元格以同数字的『第N大队』结尾」，其余行字节级 round-trip 不变。
- **守卫**：`integration/audit_layers.py` 内嵌调用该脚本 `--check`，`finalize.py` 转成硬失败，输出 `Staffel guard: OK` / `FAIL`。
- **改这类 zh CSV 的铁律**：先探测字节形态再写。`AirGroups.zh.csv` 是 **CRLF + 双 BOM**（UTF-8 BOM 之后正文还以字符 `ï»¿` 开头），`AirGroupRenames.zh.csv` 是 **LF + 单 BOM**；写前必须用同一序列化器还原原字节做基线比对，不一致就 `SystemExit`，写后校验行数。

### SS 番号族与第三层词表（v1.9.10 批次四血案）

- **症状**：同一支党卫军部队在词典、jsonl、场景表里最多四种写法（`I 党卫军` / `第1党卫军` / `第一党卫军` / `第四党卫军装甲师`）；`1/13th SS` 显示成「第1/第13」，SS 与分队语义整段消失。
- **口径 5 条**：① 数字一律阿拉伯，罗马数字只用于判读原文；② `SS`=党卫军、`Waffen SS`=武装党卫军；③ 语序「第N党卫军（国籍）<兵种><编制>」；④ **兵种只在英文写明时才补**，裸番号（`13th SS`、`XX SS`）不许补师/军/旅；⑤ 军级写「党卫军第N山地军」，避开「第N党卫军军」叠字；分队 `N/M` 读作「第M党卫军第N营」。
- **缩写表**：Ukr.=乌克兰、Latv./Lett.=拉脱维亚、Est.=爱沙尼亚、Hun.=匈牙利、Wall.=瓦隆（**不是 wall「墙」**）、Ital.=意大利、Russ.=俄罗斯、Croat.=克罗地亚、Neth.=荷兰（**不是「陆战」**）、Flan.=佛兰德、Fr.=法国；Landstorm=国土风暴（**不是音译「兰斯多姆」**）。
- **血案（最重要）**：只改 jsonl + 场景 CSV，重建后**条数与字节数都没变**，四键仍是旧值。原因：`mod/build_maps.py` 第 97–99 行还读三张词表——`build/translation.csv`、`data/translations/unit_names_en_zh.csv`、`mod/assets/translation.csv`，**词表的值压过 jsonl 与场景 CSV**。修法是三层同时写（`integration/fix_ss_names.py` 的 `fix_vocab()`）。
- **编制层级不可反推**：`Units.zh.csv` 的 `Men` 列全 0、多数剧本 CSV 无 `ID` 列、`Type` 是编制模板号且无对照表、`Dat\Scen\*.scn` 是压缩二进制。别想着用兵员数或下属数判师/军，**只能读英文原文里的 Corps/Division/Brigade/Battalion**。
- **守卫**：`finalize.py` 的 `SS-name guard`（内部调 `fix_ss_names.py --check`，三层任一残留即构建失败）。
- **通用教训**：动手前先 `grep` `audit/provenance.json` 该键的来源文件；同一键可能同时活在 jsonl、场景 CSV、词表、覆盖层**四层**里，改错层＝白改一轮（与 v1.9.8 的 Min River 同型）。

### semantic 同词多译：不要按词典值统一（v1.9.10 批次五血案）

- **症状**：`audit/layer-conflicts.json` 里 399 条 semantic——同一英文在 jsonl 与场景表是两个**真不同的译名**，不是空格/数字/片段差异。典型：`Rosiorii`（罗马尼亚地名）译成「摩托化步兵」、`Transcaucasus` 丢「外」、`Fliegerkorps` 降级成「航空队」、`I/…Heimat` 五种写法且夹拉丁前缀。
- **铁律**：分层冲突只说明「两层不一致」，**不说明哪层对**。想批量收敛到词典值之前，先抽 20 条验证词典本身——本轮抽到 7 类错误，按词典统一会把错误固化成「全域统一」。
- **可判定的才改**：只处理英文原文足以定案的键（军语层级、缩写、语序、地名/兵种混淆）。纯音译分歧（Leeming 利明/莱明格）与人名习惯译法，没有权威表就不动。
- **写法**：`integration/fix_semantic_names.py`（`--check` 出口 2）。jsonl 按 `text` 精确匹配；场景表**按英文源表同一行列**定位（`<game>/Dat/CSV/<scenario>/<name>`），不按中文值猜——同一中文值可能对应多个键。
- **血案（最容易踩）**：`GameEvents.zh.csv` 是 **500+ 列的宽参数表**，列里同名的英文格是**事件脚本参数**，不是可译文本。按全表匹配会把脚本改坏（第一版 40 格）。必须按文件名白名单（Units/Locations/Leaders/AOGs/MapText）+ 列名（Name/newName/mtText）双重限定。
- **剩下的别丢**：未裁决条目导出成 `audit/semantic-unresolved.csv`（key,family,dict_value,variants），按 place/unit/prose 分族排期；prose 类多是事件正文 `<cr>` 截断，不值得修。

### 译名混入翻译过程的残渣（v1.9.10 批次三血案）

- **症状**：玩家在编成表、地图标签里看到「德宾dden（地名保留英文，避免不准确的音译）」「哈罗贝尔回答问题时，请注意提供的信息表明没有现成的」这类值——译文本身就是解释与残片。
- **三类**：① LLM 元话语（自我说明、免责、追问）；② 原文残片与转义符（Debden = 德宾 + 原文剩余 dden、Lyzha = 利扎 + hya 说明、Harrowbeer 里把回车符读成了文字）；③ 缩写当单词（Fin.=芬兰被当 finish →「结束」、Hun.=匈牙利被当 Horn →「霍恩」）。
- **判据**：值里含「保留英文 / 避免不准确 / 请注意 / 回答问题时 / 回车符 / 换行符 / 最终译文」话术；或以中文句读（。，、）开头；或汉字后紧跟 2 个以上小写拉丁字母（粘连残片）。**半角句点开头必须放行**——「点 50 英寸防空机枪」是口径标准写法，v1.9.10 首版守卫把 40 条口径打成脏值、finalize 直接 exit 1。
- **修法**：`integration/fix_name_artifacts.py`（精确值表 DICT_FIX + CELL_FIX，同时写 jsonl 与场景 CSV，`--check` 出口 2）。本类缺陷**不能用规则重译**，只能按已确认的键/单元格逐条钉正译。
- **守卫**：`finalize.py` 的 Name-artifact guard（词典层）+ 内嵌 `fix_name_artifacts.py --check`（jsonl 与 CSV 两层）。
- **找它的最快办法**：按「译文长度 ÷ 原文长度 > 3 且含中文」排序人工过一遍，元话语条目几乎都在这儿。
- **连带教训**：缩写前缀要看同族证据，`Fin. Air Base` 旁边就摆着 `Fin. Infantry Division`＝芬兰步兵师，一眼能证伪「结束」。

### 单位概念词以 token 表为唯一判据（v1.9.10 批次二）

- `glossary/unit_tokens_en_zh.csv`（199 行，en,zh,type）是**裁决表**：coastal=滨海、fallschirm=伞兵、feldherrnhalle=统帅堂、grossdeutschland=大德意志、light=轻装、north=北方、replacement=补充、russian=俄罗斯、gds/guards=近卫、fortress=要塞、mot.=摩托化、ss=党卫军。
- 场景 CSV 原本就按 token 表译，**jsonl 语料层才是漂移方**；因此改 jsonl 不一定改显示（build_maps 先读 jsonl、后读 CSV 覆盖）。批次二实测改了 430 格 jsonl，只有 **9 条**真正上屏——那些键不出现在任何剧本 CSV 里。
- `fix_unit_terms.py` 必须过滤 `is_name()`（长度 ≤48、不含句读空格模式、空格 ≤6），否则会把战史正文里的 North Caucasus 改成「北北方高加索」「第341俄罗斯师」。
- 结论：**判断某个单位名会不会上屏，先 grep 场景 CSV，再看 jsonl。**


### 代号不意译（v1.9.9 血案之九·电子设备）

雷达告警/干扰/导航设备的代号都是**绰号**，不是普通名词，直译必错：

| 原文 | 机翻 | 为什么错 |
|------|------|----------|
| `Boozer` | 醉鬼 | 当普通名词 |
| `Spanner` | 扳手 | 同上 |
| `Oboe`（双簧管导航） | 奥博乐队 | 乐器→乐队 |
| `Perfectos` | 完美多斯 | 拆词音译 |
| `Serrate IV` | 锯齿 | 当普通名词 |
| `Postklystron` | 后克利斯特隆 | Post + klystron 拆开 |
| `Mandrel` | 芯轴 | 当普通名词 |
| `Gee` | 吉 | 单音节音译，零信息 |
| `X-Geraet` / `Y-Geraet` | X装置 / Y-格尔设备 | Geraet=德文「装置」，半译 |

规则：
1. **没有通行中文名的代号，保留拉丁原文**（Boozer/Spanner/Oboe/Perfectos/Serrate IV/Postklystron/Mandrel/Gee/X-Geraet/Y-Geraet）。
2. **已有通行音译且语义无误的保留**：莫妮卡（Monica）、弗伦斯堡（Flensburg）、海因里希（Heinrich）、海王星（Neptun）、柏林（Berlin）、霍滕维勒（Hohentwiel）。
3. **设备类别不能丢**：`FuG 200/218/240`、`AI Mk VII/VIII/X`、`ASV Mk II/III/VI`、`Mk IV Radar` 统一补「雷达」；`Mk.` 的句点去掉，写成 `Mk IV`。
4. **`译文 == 原文` 的键会被 `mod/build_maps.py` 丢弃**（避免恒等映射占体积）：想「保留英文」就是把译文写成原文，字典条目数会减少，这是预期行为，不是丢词；统计口径（README/CHANGELOG 的「N 条」）要跟着改。
5. 检测法：按 Type 分组打印 `ID\t英文\t=> 译文` 逐条读，机翻残留一眼可见；再用「空格丢失检测器」`([A-Za-z]{1,6})\s+(\d)` 查「字母+数字」连写。

### 维基百科能校准什么、不能校准什么（v1.9.9 实测）

- **能**：中文维基《[火炮列表](https://zh.wikipedia.org/wiki/火炮列表)》是一张「口径 + 中文名 + 分类」大表，697 条，可批量对照炮种与口径。用它核对 908 条炮类词条：严格匹配（型号记号 + 口径同时吻合）21 组，**炮种与口径 21/21 一致**——说明 v1.9.8 的炮种体系是对的。
- **不能**：英文维基按精确标题查中文链接（`prop=langlinks&lllang=zh`）命中率只有 29/1,078（2.7%），因为游戏装备名是内部写法（`88mm KwK36 L/56`），不是条目名。别再走这条路。
- **限流**：`list=search` 并发 4 线程必触发 `HTTP 429`，冷却约 75 秒；串行、间隔 ≥2 秒稳定。批量 `prop=langlinks` 40 条/请求、间隔 1.2 秒未见 429。
- **覆盖率是硬约束**：908 条里只有 21 条能与中文维基对上（2.3%），其余多为德军型号。没条目就不改名——没有出处时改译名等于主观臆断。

## 八、高频错误清单（含检测规则）

### 结构类（可全自动清零）

| 类型 | 检测 | 处理 |
|---|---|---|
| 空译文 | 值为空/纯空白 | 补译或丢弃 |
| 模型自述残留 | 含「注意：/应该是/请提供/无法确定」 | 取模型最终答案，否则截断到标记前完整中文 |
| 内部占位符 | 含 @ / @@PHn@@ / @col...@@ | 全删 |
| 假名/西里尔/希腊/乱码 | 非中文字符区 | 重译 |
| 叠字 | 军军/师师/的的 | 合并 |
| 数字残渣 | 60% c% | 删残字 |
| 标点堆积 | 。，：连续 | 修 |
| 括号失衡 | （）计数不等 | 修 |
| 单位未汉化 | 8.8cm / 4.5in / 107mm | 统一到毫米，但 **`in` 必须按 1in=25.4mm 换算，不得把数字原样搬成厘米/毫米**（v1.9.8：`18.1in` 被写成「18.1厘米」、`15in` 被写成「150毫米」共 13 条） |
| 大小写变体不一致 | 同英文不同写法译法不同 | 统一 |
| 句内整句重复 | 同一句出现两次 | 删重 |
| 未翻译 | 整条纯拉丁 | 补译；语言代码类直接丢弃 |
| **美术路径键被译** | key 等于图块目录名、路径令牌（`MINOR//`/`MAJOR//M`/`IMPASS//I`/`//units//`），或纯 ASCII 且含 `//` | `scan_art_tokens.py` → 进 `master_drops.json`；`finalize.py` 已硬拦截 |
| **覆盖层压掉设备表** | 键同时出现在 `Devices.csv` 与 `master_overrides.json`，且两值不同 | 改 `reference_overrides.json` 源头 → 重跑 `build_master_overrides.py`；不要只改生成物 |
| **semantic 同词多译** | 同键在 jsonl 与场景表值不同，且差异不属于空格/星号/数字体例/片段补全 | 先验证词典值本身；只改英文原文可判定者，写 `integration/fix_semantic_names.py`；未裁决的进 `audit/semantic-unresolved.csv` |
| **表头行被破坏** | 键以 `***` 开头，而译文含换行或丢失首尾 `***` | `finalize.py` 的 Section-header guard 硬拦（含换行、缺星号）；修复用 `integration/fix_section_headers.py`（v1.9.9 修 10 条 + 585 格） |
| **型号记号被当实词** | 源串型号 token（`Van`/`TL 4`/`Type 97`）在译文里被大写、删除、改写或凭空补上 `M1935` | 型号段保留拉丁原文；日制 `Type NN` → 汉字数字+式（v1.9.9 修 21 条） |
| **型号后缀被吃掉** | 键尾含数字/型号而译文不含该数字，且译文长度 < 键 75%（`I-153BS`→「伊」、`Yak-9U`→「雅克」、`Mosquito NF.30` 与 `B.XVI` 同名「蚊式」） | 型号段保留拉丁原文（v1.9.9 修飞机 23+7 条、他族 10 条） |
| **分层不一致** | 同一键在 jsonl / 场景 CSV / 覆盖层里译文不同 | `integration/audit_layers.py --check` 硬失败；裁决写 `glossary/layer_unify.json`，跑 `unify_layers.py`（v1.9.9 修 11 条） |
| **Staffel 译成大队** | 场景表源单元格匹配 `^(\d+)\./`，译单元格却是「第N大队」 | 空军中队＝Staffel、大队＝Gruppe；跑 `integration/fix_airgroup_staffel.py`，`audit_layers.py` 已内嵌守卫 |
| **同族同译碰撞** | 同族内不同英文键映射到同一译文，差异只在缩写（BMG/CMG/TMG 全叫「维克斯机枪」、RMA/RMD 都叫「遥控水雷」） | 按缩写拆译：BMG=车体、CMG=同轴、TMG=炮塔、AAMG=高射机枪（v1.9.9 第七轮修 60 条） |
| **译名混入元话语/残片** | 值含「保留英文/避免不准确/请注意/回答问题时/回车符/最终译文」，或以中文句读开头，或汉字后跟小写拉丁字母 | `integration/fix_name_artifacts.py` 钉正译；`finalize.py` 的 Name-artifact guard 硬拦（v1.9.10 修 7 键 / 150 格） |
| **SS 番号写法不统一** | 值匹配 `[IVX]{1,5}党卫军`、`^第N/第M$`、含「师墙/运兵/净选/兰斯多姆/陆战/土地风暴」，或裸番号被补「师」 | 口径见「SS 番号族」小节；`integration/fix_ss_names.py`（三层同时写）；`finalize.py` 的 SS-name guard 硬拦（v1.9.10 修 60 键 / 775 格） |

### 术语类（需规则表）

| 类型 | 典型 | 规则 |
|---|---|---|
| 专名直译 | 「3 Gennaio」→1月3日 | 番号保留原文 |
| 缩写误读 | Sep.→九月、Rec→回收、ART→艺术 | 查原文全称 |
| 国名缩写误译 | Bul.→布良斯克 | 缩写表 |
| 地名常用词化 | Vecht→战斗、Ouse→使用 | 地名不按字面义译 |
| 名称与编制矛盾 | 名字写「师」、编制是营 | 去类型词，交给编制显示 |
| 同名异物 | Moss→藓类植物门 | 维基按词条+坐标校验 |
| 外语介词当实词 | de→德式、da→牵引、TR→拖曳式、GP→穿甲弹 | 介词不译；型号段保留原文，只译口径与炮种（v1.9.9 修 13 条） |
| 型号被当口径 | `Flak 38`→「38毫米」、`Flak 43`→「43毫米」 | 型号不是口径；同族按 `Type` 列横向比（v1.9.9 修 1 条） |
| 编制缩写丢职能 | `MGMC`→机枪载具车、`AAMG`→自动机枪车 | MGMC/AAMG/SPAA 必须译出「防空」（v1.9.9 修 6 条） |
| 同族不同名同一译名 | 四个 `Churchill` 都叫「丘吉尔」、`Infantry Squad`/`Rifle Squad`/`Section` 全叫「步兵班」 | 型号段保留拉丁；Squad=小队、Section=分队（v1.9.9 第八轮修 13 组） |
| 罗马数字当日制年式 | `Zrinyi II`→兹里尼二式 | 「二式/三式」只给日制年式（v1.9.9 修 1 条） |
| 多义词按字面直译 | `Drop Tank`→支援坦克、`Ferry Tank`→渡运坦克 | 先看 `Devices.csv` 的 Type 码定语境（15=副油箱），再看词（v1.9.9 修 80 条） |

### 内容类（最危险）

| 类型 | 检测 | 说明 |
|---|---|---|
| **正文丢失/被截断** | 原文数字覆盖率 <35% 且译文 <50% 长度 | 模型只译了末段致谢或最后一句 |

## 九、验证清单

- 词典：条目数、magic W2CNMAP1、抽样 20 条核心译名命中
- 字体：cmap 覆盖数 ≥ 译文所需字符数，缺字 = 0
- CSV：188 个场景文件与原始导出行数/字段数/BOM 一致
- checksums：26 个文件全通过
- 片段键守卫：纯数字/序数/罗马数字不得进词典（会污染表格数字列）
- 美术路径守卫：`finalize.py` 必须打印 `Art-path guard: OK (20 self-named dirs, 4 path tokens)`；改了 `Dat\Art` 目录结构先跑 `scan_art_tokens.py`
- 分层守卫：`finalize.py` 必须打印 `Layer audit: override-vs-lower 0` 与 `Layer guard: OK`；改装备名后先跑 `integration/fix_equipment_names.py`，改界面词先写 `glossary/layer_unify.json` 再跑 `integration/unify_layers.py`；`unify_layers.py --check` 必须无漂移
- Staffel 守卫：`finalize.py` 的 Layer audit 段必须打印 `Staffel guard: OK`；改过 `AirGroups.zh.csv` / `AirGroupRenames.zh.csv` 先跑 `integration\fix_airgroup_staffel.py --check`
- Name-artifact 守卫：`finalize.py` 必须打印 `Name-artifact guard: OK` 与 `fix_name_artifacts: jsonl 0 cells / 0 files; csv 0 cells / 0 files`；改过单位/地名/战斗序列名先跑 `integration\fix_name_artifacts.py --check`
- semantic 定点：`integration\fix_semantic_names.py --check` 必须 0 格；只改 Units/Locations/Leaders/AOGs/MapText 的 Name/newName/mtText 列，**绝不能全表匹配** `GameEvents.zh.csv`
- SS-name 守卫：`finalize.py` 必须打印 `SS-name guard: OK`；改过 `Units.zh.csv` / `UnitRenames.zh.csv` / `unit.zh.jsonl` / 三张词表先跑 `integration\fix_ss_names.py --check`（它同时检查 jsonl、场景 CSV、词表三层）
- 表头守卫：`finalize.py` 必须打印 `Section-header guard: OK`（v1.9.9 第三轮起缺星号也是硬失败，不再有 `WARN`）
- 族核对：按 `Type` 码拉族后，同族译名必须同构，且每条都要有车种/炮种词（v1.9.9 第四轮自行高射炮族 17 条、匈牙利族 4 条；第五轮坦克与装甲车辆族 54 条）
- 同族碰撞计数：按 Type 聚合「译文 → 英文名集合」，集合大小 >1 即缺陷；`Drop Tank`/`Auxiliary Tank` 与 `DShK`/`DShk` 两类可保留（v1.9.9 第八轮 Ground 清零）
- 「保留英文」核验：译文写成原文的键必须**不在**字典里（build_maps 丢弃恒等键，条目数会减少）；`Devices.csv` 未译键应当恰好等于这批代号，不能多出别的
- 空格丢失：`([A-Za-z]{1,6})\s+(\d)` 命中的原文，译文若出现「字母+数字」连写且无空格版本即缺陷（v1.9.9 第九轮清零）
- 权威唯一：同一个键不得同时出现在 `equipment_name_fixes.json` 与 `layer_unify.json`（值不同必有一方每轮被覆盖）；改过 `reference_overrides.json` 就要重跑 `build_master_overrides.py`
- 字体补缺：`complete_font.py` 必须在 `build_maps.py` 之后跑（build_maps 会覆盖成旧子集字体），缺字 0 才继续
- 发布：安装目录 package.json 版本与 translations.bin 哈希与仓库一致

## 十、已统一的体例（被认可的翻译、番号、方法）

### 番号

- 修饰语在「第 N」之前：近卫第 N、防空第 N、第 N 近卫步兵师（出版物 3:1，可切 guards_first）。
- 国名前置：罗马尼亚第 3 集团军，不写「第 3 罗马尼亚集团军」。
- 航空兵：航空军/航空师/航空团（与官方中译一致）。
- 无类型词的名字只保留编号（第 410），类型由编制列显示，避免「第 410 军」而实际是炮兵营。
- 双编号/罗马数字：II/40th → 第 2/第 40；CCXIV/44th → 第 114/第 44。

### 地名

- 有文献用文献，无文献用维基 langlinks（OpenCC 转简体），**不信任 GeoNames 中文名**（慕尼黑被记成「邱家垭」）。
- 地名不按字面义译（Vecht 费赫特河、Ouse 乌斯河、Imperia 因佩里亚）。
- 地图标签用通名不用正式长名（法兰克福，不写美因河畔法兰克福）。

### 装备

- 口径一律「毫米」；型号保留原文；类型词按原语：Haubitze 榴弹炮、Kanone 加农炮、Geschütz 步兵炮、Pak 反坦克炮、Flak 高射炮。

### 仆从国

- 本国语言建制词：divizie/hadosztály/divisione/divisioona/divízia。
- 意大利黑衫军按纪念日命名的师保留原文（3 Gennaio、23 Marzo），不译成日期。

### 界面

- 机制词以官方中文手册为准：战区框、编制表、战斗序列、铁路端点、整补、被孤立。

## 十之二、署名与正版校验

启动器窗口固定显示三行：

    中文汉化 Mod 制作人：Pig9013 · DeepSeek-V4.1-Flash1017
    仅供交流，严禁商用
    不含游戏本体，仅支持正版游戏

正版校验放在 `Prepare()`：主程序哈希命中 compat.json 直接放行；未命中时要求
①游戏目录附近存在 `steamapps\appmanifest_1775550.acf`，②Steam 客户端在运行。
缺一即拒绝启动。

**必须对用户说清**：这是门槛不是 DRM。启动器开源，改几行就能绕过；
Steam 模拟器也能伪造清单。它挡的是「拿破解版直接用」，不是「铁了心要破解的人」。
对外表述不要承诺「绝对无法盗用」。

## 十一、存疑与未解决

- 百科正文（1,178 条）仍是机翻底子，只保证不截断/不缺译/术语统一。
- 战役脚本 .scn 未重建，单位悬停、事件、回合摘要仍为英文。
- 百科正文在游戏内单字节引擎下仍显示英文（UTF-8/GBK 两方案实机均失败）。
- 罗马尼亚语文献缺（rft.forter.ro 502、biblioteca-digitala.ro 403）。
- 乌斯塔沙部队建制名未逐条核对。
- 120 条否定/全体/限定语义待人工复核。
- 2026-11-01 事故：翻译地形枚举导致地图黑格，已回滚 82 条；此类词永久禁止翻译。
- EXE 字符串仍有约 1,166 条未覆盖（内部标识为主，判定为不需要翻译）。

## 十二、技术难点

1. **多层覆盖**：见 §三。解法是统一覆盖层，不是逐层改。
2. **片段键污染**：引擎会把表格数字也查表，纯数字键会把整列改成「第第41」。
3. **字体 merge 崩溃**：unitsPerEm 不一致（2048 vs 256）；必须选同 upem 的补字源。
4. **维基匹配噪声**：按标题匹配会撞同名异物，需坐标/国家辅助校验。
5. **CSV 保真**：事件行字段数远超表头，DictReader 会截断。
6. **发布断层**：仓库 ≠ 安装目录，见 §四。

## 十三、关键文件角色

- WitE2CN.exe：启动器；发现游戏、准备私有 runtime、注入 DLL。
- WitE2CN_Text.dll：原生文本钩子；读 payload/translations.bin。
- payload/translations.json：简体底本；payload/variants/<code>/translations.bin：四套语言包；
  payload/translations.bin 是活动槽，由启动器按选择物化，不进 Git、不进 checksums。
- integration/build_variants.py：多语言包构建（OpenCC s2tw/s2hk + 修正层 + 字体子集）。
- glossary/variants_overrides.json：繁体人工覆盖层（键=简体整条译文，值=该语言整条译文）。
- payload/overlay/Dat/Fonts/WitE2CN.ttf、Dat/GuiFonts.json：字体与配置。
- payload/checksums.json、package.json：完整性与版本（含 mod_version）。
- glossary/reference_overrides.json：定译主表（places/ui/terms）。
- glossary/manual_translations.json：整段人工重译。
- glossary/master_overrides.json、master_drops.json：构建期最后套用。
- integration/*.py：各类清洗与审计脚本。
- mod/publish.py：发布到安装目录并校验。
- VERSION：版本号来源。

## 十四、汇报纪律

- 只说已验证的事实；未实机验证的内容明确标注。
- 区分「机器判定为 0」与「人工判断正常」，不要混为一谈。
- 报数字要给口径（多少条、多少格、命中判据）。
- 推送 GitHub 不是汇报动作：没有用户明说「上传」，一轮工作只到本地 commit；说了才按 §四「GitHub 上传纪律」五件事一次做齐。