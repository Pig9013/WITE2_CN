# v1.9.20 —— 地面分队名「1/56th」重算 940 条 · 党卫军串味清理

**发布日期：2026-11-18** · 适用于 War in the East 2 1.0.5.02 · [更新日志](https://github.com/Pig9013/WITE2_CN/blob/main/CHANGELOG.md) · [下载](https://github.com/Pig9013/WITE2_CN/releases/latest)

## 一句话

指挥官报告和单位面板里「第1/第56 步兵师」这类**两个「第」叠在一起**的写法全部重算：940 个分队名按该键在全部剧本里实际配过的编制类型，分别写成「第56师第1团」或「第1/8」；同时清掉 7 条把英军坦克旅、德军空军高炮营定成「第33党卫军（法国）第1营」的陈旧条目，并新增第 21 道构建守卫。

## 为什么只能译成「片段」

引擎把单位名拼成 **译(Units.csv 的 Name) + 空格 + 译(OBs.csv 的 Suffix)**：

- 师徽文件名 `//Sym//GE//1st 装甲师.tga` 是硬证据（name 段未译、suffix 段已译），`mod/build_crest_map.py` 也按 `dictionary.get(name) + " " + dictionary.get(suffix)` 生成映射；
- 所以 Name 只能译成片段，兵种词由后缀补。旧翻译把 `1/56th` 逐字拼成「第1/第56」，游戏里就显示成「第1/第56 步兵师」。

## 新规则

| 情形 | 判定 | 例子 |
|:--|:--|:--|
| 分队号 1–3，且全部后缀都含 Division | 师属团 | `1/56th` → 第56师第1团（显示「第56师第1团 步兵师」） |
| 同一键跨师/旅/团/营/连（`1/8th` 配过 6 种后缀） | 只写编号，不揣测级别 | `1/8th` → 第1/8 |
| 带附属词 | 附属词译出后接在编号后 | `I/3rd Lehr` → 第1/3 教导；`I/999th Afrika` → 第1/999 非洲；`(158th Res)` → 第1/16（158预备） |
| 党卫军各师、空军番号、装备名 | 整条跳过，保持原译 | `1/13th SS` → 第13党卫军第1营；`2/15 IAP` → 第15歼击航空团第2大队 |

附属词表：伞兵、教导、近卫（Guards/Gds）、非洲（Afrika/African）、摩托化、国民、东方、特设（zbV）、要塞、阵地、山地、海军、空军（LW）、预备、突击、摩洛哥土著（Tabor Goums）、塞内加尔、库内奥、科塞里亚、蓝色（'Blue'）；`KH`、`FR` 语义未定，按原文保留。

## 改动范围

- 新脚本 `integration/fix_unit_slash.py`（`--check` 有待改返回 2），覆盖 **940 键**：师级 321、编号 619。
- 改 `data/scenario_csv/translations/unit.zh.jsonl` 与 `unit.zh.qa.jsonl`，以及 13 个 `build/scenario_csv_zh/*/Units.zh.csv`（按英文源表同一行同一列定位，写后往返核对）。
- 清掉 `glossary/unit_name_canon.csv` 里 7 条 csv-majority 误判（`1/33rd`、`2/33rd`、`3/33rd`、`I/13th`、`I/20th`、`I/33rd`、`II/33rd` 被定成「第N党卫军…营」），真正的党卫军师（`1/13th SS` 等）是独立键，不受影响。
- 删除 `glossary/reference_overrides.json` 的 terms 组 5 条陈旧斜杠覆盖（`CCXIV/44th`、`CCXXX/21st`、`CCXXXII/12th`、`CLXII/6th`、`CLXII/44th`，值还写着「第114/第44」「162/6师」）。
- `mod/finalize.py` 新增第 21 道守卫 **Unit-slice name guard**：分队名再被逐字译回「第N/第M」就拒绝发布。

## 构建与验证

- master overrides 6,140；词典 **74,473 条 / 9,580,150 B**（条数不变，值改动）；字体 2,448 字形；四语言包各 74,473 条、缺字 0。
- finalize EXIT 0：**21 道守卫**全通过、MapText 69,481 条四包全中、百科四表与游戏原版逐字节一致、Integrity 125 files；publish 目标版本 1.9.20、校验通过。
- 安装包抽验：`1/56th`→第56师第1团、`I/13th`→第1/13、`1/8th`→第1/8、`I/3rd Lehr`→第1/3 教导、`1/16th (158th Res)`→第1/16（158预备）、`1/182nd Reserve`→第182预备师第1团、`II/3rd Sturm (II/22nd)`→第2/3 突击（2/22）、`CCXXXII/12th`→第232/12。
- 保留项与回归：`1/13th SS`→第13党卫军第1营、`2/15 IAP`→第15歼击航空团第2大队；`Mar`→3月、`GENM`→少将、`DIS`→解散、`CITY`→CITY、`Load`→载重、`Pen`→穿甲。
- 不改游戏 EXE、`.scn`、原 CSV、贴图或存档；删除 mod 文件夹即回到英文。

## 已知限制（如实说明）

- 跨级别键（`1/8th` 同时配师/旅/团/营/连）只显示编号，级别由后缀补——这是「引擎按名查表 + 单键多义」的固有限制，硬套「师第团」会在 252 个跨级别键上出错。
- `14/20th KH` 的 `KH`、`I/41st FR` 的 `FR` 语义未定，按原文保留。
- 「可用航空作战群」列表为空仍未定性（v1.9.18 的 trace 诊断开关可用）。
- 百科正文、事件正文在游戏内仍英文：前者受引擎单字节渲染限制，后者在加密容器里。
