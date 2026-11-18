# v1.9.19 —— 航空部队番号补译 1,914 条 · 苏军两级番号截断修复

**发布日期：2026-11-18** · 适用于 War in the East 2 1.0.5.02 · [更新日志](https://github.com/Pig9013/WITE2_CN/blob/main/CHANGELOG.md) · [下载](https://github.com/Pig9013/WITE2_CN/releases/latest)

## 一句话

用我们自己的规则引擎，把指挥官报告/航空队列表里仍然英文的 **1,682 个航空队番号**、**232 个航空作战群（AOG）番号**全部译出并抽验；同时修好场景表里 242 格把 `2/15 IAP` 截成「第2/第15」的旧缺陷，并加了一道构建守卫防止复发。全部译名由游戏自带 `Dat/CSV` 的英文名 + 本仓库规则生成，**没有使用任何第三方汉化资源**。

## 这次补了什么

- **AirGroups 1,682 条**：皇家空军 284、南非空军 195、意大利空军 243、匈牙利 84、罗马尼亚 51、芬兰 32、加拿大 41、澳大利亚 16、新西兰 6、美国陆军航空队约 150、德国空军 266（JG/KG/SG/Aufklärer/NAGr 等），其余为苏军各航空团与零散单位。
- **AOGs 232 条**：`Air Command` / `Recon Group` / `Transport Group` / `Fliegerfuehrer` / `N PVO IAD` / `N GShAK` / 各国航空旅与支队等。

规则写在 `glossary/air_designations.py`（入口 `translate_airgroup(name)` / `translate_aog(name)`）：

- 先按国家分派（德 / 苏 / 英联邦 / 美 / 意 / 罗 / 匈 / 芬 / 斯洛伐克 / 保 / 法 / 巴西 / 盟军意大利），**缩写先还原全称**再拼中文，不按字母硬译。
- 罗马数字统一成阿拉伯数字；苏军近卫固定写「近卫第N」；两级番号输出「第M……第N大队」。
- 体例与既有 1,431 条人工译文一致：`II./JG 1`→第1战斗机联队第2大队、`Stab/FAGr 1`→第1远程侦察大队指挥部、`No.1 RAF FB Sqn`→皇家空军第1战斗轰炸机中队、`1 GBAP`→近卫第1轰炸航空团。

写入 `data/scenario_csv/translations/airgroup.zh.jsonl`（1,431→3,113 行）与 `aog.zh.jsonl`（261→493 行），每条都带 `"source": "glossary/air_designations.py"`，可逐条复核、可再生成。

## 修好的旧缺陷

- `build/scenario_csv_zh/*/AirGroups.zh.csv` 里 12 个文件共 **242 格**把 `2/15 IAP` 这类两级番号写成「第2/第15」，兵种词整段丢失；jsonl 里没有这些键，所以以前每次重建都修不回来。新增 `integration/fix_airgroup_slash.py`：只认「英文源单元格是 `数字/数字 字母`、中文是纯 `第N/第M`、两侧数字一致」的格子，按规则重算，保留 BOM 与行尾，写后核对行数。
- `mod/finalize.py` 新增**两级番号守卫**：每次构建调用上面的脚本 `--check`，再有截断就直接拒绝发布。
- `integration/fix_cell_dirt.py` 撤掉两条旧的英文恒等映射（`2/13 IAP-KBF`、`2/20 IAP`）——那是「IAP 一律保留英文」时代的遗留，会把新译名顶回英文。
- 国籍守卫识别 `RHAF`（匈牙利皇家空军），`2nd RHAF Brigade`→匈牙利皇家空军第2旅 不再被误判成「共用后缀带国籍」。

## 这次变了什么

- 版本 1.9.19；词典 **72,566 → 74,473 条**（+1,907，新增 1,914 条中 7 条与既有键合并）；字体 2,448 字形，四套语言包各 74,473 条、缺字 0。
- 构建链 **20 道守卫**全通过；MapText 69,481 条四包全中；checksums 125 条；百科四表仍与游戏原版逐字节一致。
- 不改游戏 EXE、`.scn`、原 CSV、贴图或存档；删除 mod 文件夹即回到英文。

## 已知限制（如实说明）

- 新增番号里有 14 条保留拉丁专名（`Sonderkommando Goetz`、`Gruppe Buschmann`、`'Buscaglia-Faggioni'`、`Kdo Nowotny` 等），这些是人名/绰号，不作音译。
- `1/56th` 这类单位名（英文本身只有「营/团」两个数字）仍按字面译作「第1/第56」，全库约 1,121 条，需按编制类型另批处理。
- 「可用航空作战群」列表为空仍未定性（v1.9.18 的 trace 诊断开关可用）。
- 百科正文、事件正文在游戏内仍英文：前者受引擎单字节渲染限制，后者在加密容器里，均不是补词条能解决的。
