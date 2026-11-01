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
- ③ 构建：build_maps.py → complete_font.py → finalize.py。
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
      → glossary/master_drops.json（丢弃层）
      → glossary/master_overrides.json（最高优先级）

**教训**：只改 jsonl，场景 CSV 里的旧值照样覆盖回来，同一个词要改三四次，表现为「反复改同一个词」。

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

## 七、必须人工核验的（机器判不准）

1. **译名取舍**：一地多名（哈尔科夫/哈尔基夫、萨拉热窝/塞拉耶佛），无对错，人定。
2. **句子流畅度**：语义无误但读着别扭，机器判不出。
3. **否定/全体/限定语义**：not / all / only 是否在译文中消失，需逐条读原文。
4. **史实性**：原文自身矛盾（如「1945 年组建、1945 年 2 月改称」），照译不算错。
5. **番号一致性**：同一号不同部队、师/步兵师简称混用属合法，不能机械统一。
6. **长句润色**：百科正文仍是机翻底子，只保证不截断、不缺译、术语地名统一。

## 八、高频错误清单（28 类，含检测规则）

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
| 单位未汉化 | 8.8cm / 4.5in / 107mm | 一律换算为毫米 |
| 大小写变体不一致 | 同英文不同写法译法不同 | 统一 |
| 句内整句重复 | 同一句出现两次 | 删重 |
| 未翻译 | 整条纯拉丁 | 补译；语言代码类直接丢弃 |

### 术语类（需规则表）

| 类型 | 典型 | 规则 |
|---|---|---|
| 专名直译 | 「3 Gennaio」→1月3日 | 番号保留原文 |
| 缩写误读 | Sep.→九月、Rec→回收、ART→艺术 | 查原文全称 |
| 国名缩写误译 | Bul.→布良斯克 | 缩写表 |
| 地名常用词化 | Vecht→战斗、Ouse→使用 | 地名不按字面义译 |
| 名称与编制矛盾 | 名字写「师」、编制是营 | 去类型词，交给编制显示 |
| 同名异物 | Moss→藓类植物门 | 维基按词条+坐标校验 |

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

## 十一、存疑与未解决

- 百科正文（1,178 条）仍是机翻底子，只保证不截断/不缺译/术语统一。
- 战役脚本 .scn 未重建，单位悬停、事件、回合摘要仍为英文。
- 百科正文在游戏内单字节引擎下仍显示英文（UTF-8/GBK 两方案实机均失败）。
- 罗马尼亚语文献缺（rft.forter.ro 502、biblioteca-digitala.ro 403）。
- 乌斯塔沙部队建制名未逐条核对。
- 120 条否定/全体/限定语义待人工复核。

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
- payload/translations.json / .bin：词典；钩子用 .bin。
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