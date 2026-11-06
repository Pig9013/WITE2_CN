**中文** · [English](README.en.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [Русский](README.ru.md)

# War in the East 2 中文 Mod 工程（简体 + 繁体）

**当前版本 v1.9.9（2026-11-06）** · [更新日志](CHANGELOG.md) · [下载最新版](https://github.com/Pig9013/WITE2_CN/releases/latest) · [项目百科（Wiki）](https://github.com/Pig9013/WITE2_CN/wiki)

## 当前交付

唯一入口是：

    mod\WitE2CN.exe

它从游戏目录创建私有 mod\runtime 副本，加载 mod\payload 里的字体/overlay/翻译词典，并在该副本上注入 WitE2CN_Text.dll。原游戏 EXE、.scn、原 CSV 不被修改。

**四套语言包**：简体中文（中国大陆）、繁體中文（台灣）、繁體中文（香港）、繁體中文（澳門）。首次启动时选一次，记住到 settings.local.json；也可以带参数 `WitE2CN.exe --variant zh-TW`（别名 cn/tw/hk/mo）。切换语言只换词典与字体，不重装。繁体由简体按地区标准转换生成，词汇层差异见 [繁体版说明](docs/繁体版说明.md)。

运行说明见 mod\README.md。实际操作只由用户本人执行；工程侧只做文件构建与静态审计，不启动游戏或 Steam。

**已知限制**：`.scn` 未重建，战役脚本里的单位悬停、事件、回合摘要仍为英文；百科正文在游戏内单字节引擎下仍以英文显示（UTF-8/GBK 两种代码页方案实机均失败），中文正文见 [百科中文版](docs/百科中文版_v1.6.0.md)。其余界面/表格/单位名/番号/地名/百科标题与链接已中文化。

**当前规模**：四套语言包各 72,228 条（简体 + 台湾 + 香港 + 澳门）；字体 2,270～2,431 字形、四套缺字均为 0；188 个场景 CSV / 398,480 行结构与原始导出逐一比对通过（0 失败）；payload 92 个文件 checksums 全通过。

**百科中文版（游戏外阅读）**：正文已导出为 [docs/百科中文版_v1.6.0.md](docs/百科中文版_v1.6.0.md)（**1,178 条**，同目录有 DOCX，Releases 附件亦可下载）。

游戏打补丁后**不再拒绝启动**：未登记构建照常尝试接入，接不上就以英文运行，补丁与存档不受影响。判定看 logs/native.log，详见 [CHANGELOG](CHANGELOG.md) 与 mod/README.md 的「游戏更新」一节。

**配套手册（不属于 Mod 本体）**：《钢铁炼狱》官方手册中文版 v1.0 · 110 页 · 文本可选中复制 —— 见 [Releases](https://github.com/Pig9013/WITE2_CN/releases) 附件。

## 最近更新（2026-11-06，v1.9.9）

- **用维基校准译名（v1.9.9）**：以中文维基《[火炮列表](https://zh.wikipedia.org/wiki/火炮列表)》697 条记录为参照，严格匹配 21 组，炮种词与口径 21/21 一致；实修 120 条——`de`/`da` 被当国别与实词（比利时 155 炮曾译成「德制」）、飞机编制表 10 条分组表头（Slovakia 被译成捷克斯洛伐克、`WA` 被音译成「威亚」）、荷兰 `Van` 族 8 条、日制 `Type NN` 13 条、自行高射炮族 17 条（`M15 MGMC` 曾译「坦克歼击车」、`Flak 38` 的型号被当成 38 毫米口径）、匈牙利 `Turan`/`Zrinyi` 4 条、坦克与装甲车辆族 54 条（`Staghound` 被拆成「野猪猎人」、`White Scout Car` 译成「白色侦察车」、`M5A1 Stuart` 译成「武士坦克」、`Chaffee` 音译「夏菲」）。判据与覆盖率的实话见 [wiki 校准报告](docs/wiki校准_v1.9.9.md)。
- **分组表头星号清零（v1.9.9）**：编制表/地名的分组行 `****** 步兵 ******` 曾被机翻吃掉星号，14 个剧本合计 585 格；已按原文星号形状重建，并把守卫从「告警」改为「构建失败」。
- **小河回来了（v1.9.7）**：地图上的小河图块由引擎按 `//Tiles//RIVER//%sR%d_%3.3d.tga` 拼路径，其中 `%s` 取值是 `MINOR//`；该串曾被译成「次要」，路径变成 `//Tiles//RIVER//次要R0_001.tga`，文件不存在时引擎静默跳过——于是只剩河名标签、河床空白。已把 10 个美术路径/目录名键移出词典（`MINOR//`、`//units//`、CUSTOM、FERRY、HVY_URBAN、IMPASSABLE、SAND、AVERAGE、GOOD、POOR），并新增美术路径守卫（构建时拒绝自名型图块目录名与路径令牌）与「丢弃层永远最后执行」的顺序修正。审计见 [美术汉化审计](docs/美术汉化审计_v1.9.7.md)。
- **枪炮译名（v1.9.8）**：544 条火炮条目全部带炮种词（此前 116 条只有一个「炮」字）；判定以引擎自身的分类为准（`Ground.csv` 单元名 + `Devices.csv` Type 码），德式按 KwK/Pak/Flak/Haubitze 等原语分流；13 条口径量级错误订正（如 18.1in 曾被写成「18.1 厘米」，实为 460mm）；英寸口径不强行换算毫米。
- **覆盖层不再压掉设备表**：`master_overrides.json` 最后套用，曾把 12 条旧译名压回新定名之上；已从源头 `reference_overrides.json` 修正并重生成，新增守卫拒绝「已丢弃的键又出现在覆盖层」。规则、勘误表与判据来源见 [枪炮译名比对](docs/枪炮译名比对_v1.9.8.md)。
- 完整条目见 [CHANGELOG](CHANGELOG.md)。

## 这次校准的局限（如实写明）

- **维基覆盖率只有百分之二**：908 条炮类条目里，能同时对上「型号记号 + 口径」的只有 21 条（2.3%）；英文维基按条目名查中文链接命中 29/1,078（2.7%）。没查到不是没查——中文维基没有对应条目，英文条目名又与游戏内部名不同，所以**无出处就不改名**。
- **国籍看数据表，不看名字**：本轮两起事实性错误（比利时装备变「德制」、Slovakia 变「捷克斯洛伐克」）都源于按名字猜国别。判据是 `Nations.csv` 的国别码与剧本 CSV 的 `Nation` 列。
- **维基不等于军事史**：校准只能证明「与维基一致/不一致」，不能证明符合史实；维基自身的分类也有混用，故只用来验证炮种与口径。
- **只修可判定的错**：国别、年份、型号消失、星号/换行破坏有据可查；「重型→重」这类语义压缩与文风偏好没有自动判据，不动。
- **未进游戏核对**：工程侧按铁律不启动游戏（离线 `--selftest` 只校验包完整性），需玩家目视地图小河与编制表分组行。
- 尚余：英军 `Mk II AA` 型号归属未定，保留原译待考；覆盖层里另有 12 条设备名旧值待随推进逐步改；`T-35`、`KV-85`、`LT-38`、`L3/35` 等代号在源表里就是 `qa_status=kept`，属主动保留英文、尚未补译。意大利/法国型号词头（`Carro Armato`、`Char` 等）已全库搜索确认为 0 条，不存在待办。

## 上一批更新（2026-11-03，v1.9.0）

- **繁体语言包**：新增 繁體中文（台灣 / 香港 / 澳門）三套，与简体并列；台湾 s2tw、港/澳 s2hk（HKVariants 地区用字：衞/羣/裏/着/麪/説），台港之间有 4,084 条不同。
- **修正层 149 条**：OpenCC 短语表把音译地名换错的地方（佈雷達→布雷達 73、併成為→並成為 52、參與瞭→參與了 22、幾周→幾週 18、占領→佔領 1），带白名单，只做高置信度替换。
- **启动器选语言**：首次启动弹选择框，标题带语言名；新增 `--selftest` 离线自检四套语言包，不启动游戏。
- **载荷结构**：`payload/variants/<code>/` 四套词典与 overlay；活动槽 `payload/translations.bin` 由启动器物化，checksums 从 26 个文件增加到 92 个。
- 详见 [繁体版说明](docs/繁体版说明.md) 与 [CHANGELOG](CHANGELOG.md)。

## 上一次更新（2026-11-03，v1.8.0）

- **术语裁决**：Panzerjagd＝坦克猎歼；Panzer-Zerstörer＝反坦克；Jagdpanzer＝坦克歼击车；Panzerschreck＝反坦克火箭筒；Panzerfaust＝铁拳反坦克榴弹。考据见 [术语裁决报告](docs/术语裁决_Panzerjaeger_Panzerjagd.md)。
- **人名清理 88 条**：Model＝莫德尔、Student＝施图登特、Son＝松（旧「儿子」）、Major＝马约尔、Bull＝布尔、Hunter＝亨特、Price＝普赖斯、Old＝奥尔德、Down＝唐、Geloso＝杰洛索。
- **装备命名 960 条**：德军坦克「N号X型坦克」、苏军「型号+年型」、飞机「德国拉丁/苏联中文/西方主力中文」；俘获装备核对表 35 条；火炮按型号前缀定炮种。规则见 [装备命名规范](docs/装备命名规范_德国苏联与飞机.md)、[俘获装备核对表](docs/俘获装备核对表.md)。
- **结构修复**：事件 CSV 的 168 格非文本列（脚本参数）曾被翻译并双重编码，已全部恢复源值；场景 CSV 审计 0 失败。
- **构建守卫**：UI 标签优先于场景 CSV，军衔 Major 不再被同名人名覆盖。

## 参考资料与致谢

本项目的术语、句式和译名不是凭空来的，主要参考了以下中文资料。原文与字段语义则以游戏自带数据（Dat/CSV、Dat/Info）和官方英文手册为准。

### 中文手册与译本

- **《东线战争2》规则手册分章中文译本（16 章 PDF，T1 层）**——术语与规则表述的第一依据。各章译者：
  - 第 1 章 新手入门：**leninlyender**
  - 第 8、9、10、11、14 章：**Fulda**
  - 第 15 章 将领：**Mizore**
  - 第 27 章 增援与撤离：**兔空**
  - 第 13、20、29、34、38、39、40、41 章：**克里斯蒂安-cristianwj**
  - 全书订正：**克里斯蒂安-cristianwj**
- **《东线战争2规则手册》中文全本（809 页，T1B）**——长段正文、书目与术语的对照本，译者：**张萧临**。
- **《钢铁炼狱》（Steel Inferno）手册**——英文原版与中文版，英文原作者 **James Wirth**。
- **新手教程中文版（T3）**——界面与流程用语参考。

对应文件（供核对，均只读引用、不随本仓库分发）：「1 新手入门.pdf」…「41 附录L-编辑器.pdf」（WITE2translation 分章）、「东线战争2规则手册_中文全本.pdf」、「WITE2_Steel_Inferno_Manual_EBOOK.pdf」及其中文版、「WITETutorialManual中文.pdf」。

### 社区文本与讨论

- **kkuy678**、**zisongzi**、**魔法训练营**——提供了本项目参考的中文文本与讨论；若干术语取舍与机制解释来自这些材料。
- 以及兵棋 / TOAW 社区里分享 WitE2 资料、答疑与勘误的各位。

### 工具书

- 《世界人名翻译大辞典》，新华社译名室编，2007 年 4 月，ISBN 7500107994/Z21；维基百科「外语译音表/英语」——人名、地名译写的依据。

### 部队番号与缩写（术语依据）

番号不是英文，是英文转写的俄文/德文缩写（иак / ПВО / РВГК / AOK / PAOK / FBD / OT …）。
它们的译名只能回到原语才靠得住，所以单独立了两份文档：

- [番号与缩写术语表](docs/番号与缩写术语表.md)——规则 + 原语对照 + 易混表；表格由 `glossary/designations.py` 生成，与代码同步。
- [文献参考目录](docs/文献参考目录.md)——编制/OOB 参考书目，GB/T 7714-2015 著录，能公开下载的注明本地路径，不能下载的给链接。

主要依据（详见上述目录）：美陆军 TM 30-430《苏联军事力量手册》（1946）、TM-E 30-451《德国军事力量手册》（1945）、
TM 30-506《德英军事词典》（1944）、FM 100-2-3《苏军：部队、编制与装备》（1991），
以及 Charles C. Sharp、David Glantz、Georg Tessin、Niehorster 等人的编制研究。

### 本机语料与交叉核对

除了下载的参考书，本项目还会把本机书库（战史、兵棋规则书、WitE 中文手册）转成可检索文本：
文字版直接抽取，扫描版用本机 Tesseract OCR（中英），页内已有文字层的不重复 OCR。
统计与交叉核对脚本见 `integration/corpus/`，产物：

- [全量问题清查](docs/全量问题清查.md)——28 类缺陷、判定方法、当前命中、根因、状态；附「为什么以前会反复改同一个词」的结构说明
- [术语与番号总表](docs/术语与番号总表.md)（另有 XLSX）——俄/德/英/中四语对照，224 条，每条带编号、来源、语料验证次数
- [权威对照表](docs/权威对照表.md)（另有 XLSX）——出版译本附录 + 语料用法统计 + 已改动条目（R-xxx）
- [仆从国番号对照表](docs/仆从国番号对照表.md)——罗/匈/意/芬/斯洛伐克/克罗地亚/西班牙七国语言建制词与师名
- [文献参考目录](docs/文献参考目录.md)——GB/T 7714 著录与下载状态
- [术语裁决：Panzerjäger / Panzerjagd](docs/术语裁决_Panzerjaeger_Panzerjagd.md)——文献考据、装备指向、同义/近义术语清点与人名修复记录
- [装备命名规范：德国装甲、苏联装备与飞机](docs/装备命名规范_德国苏联与飞机.md)——文献依据、命名规则、805 条修订与审计口径
- [俘获装备核对表](docs/俘获装备核对表.md)——德军编号、原厂型号、逐条核对结果
- [项目 skill](skills/wite2-cn-mod/SKILL.md)——整体梳理：工作流、铁律、禁止项、28 类缺陷判据、已统一体例、存疑清单；可作为后续接手的作业手册

凡是依据文献改动词条，都要先写进 `glossary/reference_overrides.json`（带出处），
再由 `integration/apply_reference_overrides.py` 写回数据源。

词典由多层数据叠加而成（jsonl → 词表 CSV → translation.csv → 场景 CSV），后层覆盖前层。
为避免"改了一层被下一层盖回去"，构建时最后会套用 `glossary/master_overrides.json`
（`integration/build_master_overrides.py` 汇总生成）与 `glossary/master_drops.json`（技术性字符串丢弃层），
**一处改动、全层生效**。

### 特别致谢

**cristianwj、leninlyender、Fulda、Mizore、kkuy678、zisongzi、魔法训练营、兔空、张萧临**

这个项目的术语、句式和译名，很大一部分是从你们的中文文本里学来的。没有这些底本，本 Mod 不可能做成现在这样。**居功至伟。**

另感谢《钢铁炼狱》原作者 **James Wirth**，以及游戏本体与官方手册的开发者/发行方 **2by3 Games、Matrix Games、Slitherine**。

如有遗漏或作者标注有误，请开 issue 指正，我们立刻改。


## 目录

    mod/
      WitE2CN.exe                启动器
      WitE2CN_Text.dll           原生文本钩子
      payload/                   运行时词典、字体、checksums、package
      payload/variants/          四套语言包（zh-CN / zh-TW / zh-HK / zh-MO）
      runtime/                   私有游戏副本与存档（不属于可分发代码）
      assets/                    构建源：GuiFonts.json、translation.csv
      build_maps.py              组装词典/字体/overlay/checksums
      complete_font.py           补齐字体缺字
      (integration/build_variants.py)  生成繁体语言包（词典 + 字体 + overlay）
      finalize.py                生成 checksums 与可移植 settings
      src/                       启动器与文本钩子源码
      README.md                  使用说明

    glossary/                    术语表与 UI 额外词表
    pipeline/                    本地 Qwen 提取/翻译/QA/术语保护
    data/                        翻译源与中间数据
    build/                       字体源、基础 translation.csv、战役简报、场景 CSV 译文
    integration/                 文本提取/生成/审计脚本

## 可移植性

- 代码不写死本机 D:\ 或 Steam 库路径。
- 游戏按 `--game` → settings.json → settings.local.json（自动记忆）→ WITE2_GAME → Steam 注册表/全部库目录/盘符扫描 → 手动选择 的顺序解析；都找不到时弹窗选目录。
- `WitE2CN.exe --where` 把解析结果写进 logs\launcher.log，排查"找不到游戏"时先看这个。
- settings.json 默认为空对象 {}；需要非 Steam 安装时才手写 game_path。
- runtime\WitE2CN.runtime.json 的 source 只是来源记录；移动 Mod 后只校验 game_sha256。
- 构建脚本使用 MOD/PROJECT 相对路径；不再依赖已删除的 mod_full。

## 构建（不启动游戏）

    python mod\build_maps.py
    python mod\complete_font.py
    python integration\build_variants.py
    python mod\finalize.py
    python mod\publish.py

build_maps.py 读取已有译文，不调用模型。翻译本身由 pipeline 本地 Qwen 完成。

## 快捷键文本

游戏 EXE 的 UI 键可能是：

    Show Turn Summary {ctrl-s}
    Toggle Ground Support on/off {x}
    Move mode {F1}
    Zoom map in {+}

构建时会扫描 EXE 中所有含 {...} 的字符串，生成完整模板；不能只处理一种占位符。

## 清理原则

已删除：旧 mod_full/mod_additive/install 目录、旧覆盖安装、旧 CSV swap、diagnostics 会话日志、旧截图/预览/zip、旧 docs、测试 exe/pdb/lib、审计快照。

保留：当前 Mod、runtime（含存档）、翻译源、场景 CSV 译文、字体源、构建/审计脚本、术语表。

## 常见问题

**启动器提示「汉化包文件缺失或损坏：payload\...」**

2026-10-25 之前的仓库版本受 Git 换行转换影响：payload 下的 txt/csv/json 在提交时被转成 LF，下载后与 payload\checksums.json 里的 SHA-256 对不上（文件其实在，只是字节变了）。已在 .gitattributes 中对 mod/payload/** 设 -text 修复。遇到该提示请删除旧文件夹，重新下载最新版本，不要新旧目录混用。

## 验证

静态验证包括：

- translations.bin 的 W2CNMAP1 头、条目数；
- 字体 cmap 覆盖（四套语言包，缺字均 0）；
- 四套语言包的键集合与简体逐条一致，骨架/长度/括号/占位符守卫 0 失败；
- checksums 92 个文件通过（含四套语言包）；
- 场景 CSV 行数/字段数/表头/BOM/非文本列与原始导出对比；
- settings.json 为 {}，启动器可自动找到 Steam 游戏。

实机验证由用户执行；工程侧不启动游戏。
