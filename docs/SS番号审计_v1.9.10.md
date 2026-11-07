# SS 番号整族审计（v1.9.10 批次四）

日期：2026-11-07　范围：词典 72,253 条中含 `SS` 的键（短键 441 个）、四张场景表（Units / UnitRenames / OBs / AirGroups）与三张词表。
铁律：全程离线静态审计，未启动游戏；`WitE2CN.exe --selftest` 允许且已通过。

## 0. 结论

| # | 结论 | 置信度 |
|---|---|---|
| 1 | SS 番号此前**没有统一口径**：同一支部队在词典、jsonl 语料层、场景表里最多出现四种写法（`I 党卫军` / `第1党卫军` / `第一党卫军` / `第四党卫军装甲师`） | 高（三层实测） |
| 2 | 最硬的缺陷是**斜杠分队名**：`1/13th SS` 译「第1/第13」，`SS` 与分队语义整段丢失，玩家只看到两个数字 | 高（词典 + CSV 双证） |
| 3 | 次硬的是**国籍缩写被当地名音译**：`第28党卫军师墙单位`（Wall.→墙）、`第34党卫军师（净选）`、`第25党卫军「匈」师`、`党卫军兰斯多姆荷兰队` | 高 |
| 4 | jsonl 层对裸番号**擅自补「师」**（`13th SS`→第13党卫军装甲师，实为山地师；`101st SS`→第101党卫军师），属过度补全，已回退为不补兵种 | 高 |
| 5 | 编制层级**无法从数据反推**：`Units.zh.csv` 的 `Men` 列全为 0，多数剧本 CSV 无 `ID` 列，`Type` 是编制模板号且无对照表，`Dat\Scen\*.scn` 是压缩二进制 → 只能依赖英文原文自带的 Corps/Mountain/Division/Brigade 等词 | 高（三条取证路均失败，见 §5） |
| 6 | 本轮落地：词典 60 条、jsonl 240 格 / 4 文件、场景表 527 格 / 46 文件、词表 8 格 / 2 文件；`--check` 残留 0 | 高 |

## 1. 口径（写死在这 5 条上，后续批次沿用）

1. 数字一律阿拉伯数字；罗马数字只用于判读英文原文，不进译文（`I SS`→第1党卫军，不写「第一党卫军」）。
2. `SS` 一律译「党卫军」，`Waffen SS` 译「武装党卫军」。
3. 语序：**番号在前、兵种在后**——`第N党卫军（国籍）<兵种><编制>`，如 `第20党卫军（爱沙尼亚）第1营`。
4. **兵种与编制只在英文原文写明时才补**。裸番号（`13th SS`、`XX SS`）一律不补「师/军/旅」——补了就是编造。
5. 军级避开叠字：`V SS Mountain` 写「党卫军第5山地军」，不写「第5党卫军山地军」；分队名 `N/M` 读作「第M党卫军第N营」；名号型（Nord / Wiking / Nederland / Landstorm）写「<名>党卫军」。

## 2. 五类缺陷与处置

| 类 | 典型旧值 | 现译 | 说明 |
|---|---|---|---|
| 斜杠分队名丢 SS | `1/13th SS`→`第1/第13`、`1/33rd SS Fr.`→`第1/第33` | 第13党卫军第1营 / 第33党卫军（法国）第1营 | 13 个键，含 `1/Nord SS`→`1北党卫军`、`3/Wiking SS`→`3／维京党卫军` |
| 国籍缩写乱序 | `第15拉脱维亚运兵党卫军步兵师`、`爱沙尼亚党卫军第20` | 第15党卫军（拉脱维亚）、第20党卫军（爱沙尼亚） | 缩写表：Ukr.=乌克兰、Latv.=拉脱维亚、Est.=爱沙尼亚、Hun.=匈牙利、Wall.=瓦隆、Ital.=意大利、Russ.=俄罗斯、Croat.=克罗地亚、Neth.=荷兰、Flan.=佛兰德、Fr.=法国、Lett.=拉脱维亚 |
| 脏值（音译/直译/元话语） | `第28党卫军师墙单位`、`第34党卫军师（净选）`、`党卫军兰斯多姆荷兰队`、`荷兰陆战师党卫军`、`第八法国突击师（党卫军）` | 第28党卫军（瓦隆）、第34党卫军（荷兰）、荷兰国土风暴党卫军、第8党卫军（法国）突击旅 | `Wall.`=瓦隆被读成 wall「墙」；`Landstorm` 被拆成「兰斯多姆」；`Neth.` 被读成「陆战」 |
| 数字体例混用 | `I 党卫军`、`X 党卫军`、`第四党卫军装甲师`、`第十一党卫军`、`第二装甲师（党卫军）` | 第1/第10/第4/第11/第2党卫军 | 罗马数字与中文数字各 20 键，统一为阿拉伯 |
| 裸番号被补编制 | `第13党卫军装甲师`、`第101党卫军师`、`第600装甲师（党卫军）` | 第13党卫军、第101党卫军、第600党卫军 | 只改 jsonl（不进 CSV），消除「同一番号两种编制」 |

英文写明编制的照原文补：`18th SS Mountain`→第18党卫军山地师、`V SS Mountain`→党卫军第5山地军、`XV SS Cossack`→党卫军第15哥萨克骑兵军、`35th SS und Polizei`→第35党卫军与警察部队、`23rd SS Vlntr Pzrgrn 'Nederland'`→第23党卫军志愿装甲掷弹兵师（荷兰）。

## 3. 血案：只改 jsonl 与场景表不起作用

第一次重建（`build_maps.py`）产出 72,253 条，**条数没变、字节数也没变**，抽验四键仍是旧值：`23rd SS Vlntr Pzrgrn 'Nederland'`、`IV SS Panzer Corps`、`VII SS Panzer Corps`、`XI SS Panzer Corps`。

- 根因：`mod/build_maps.py` 第 97–99 行还读三张**词表**——`build/translation.csv`、`data/translations/unit_names_en_zh.csv`、`mod/assets/translation.csv`，它们的值在词典里压过 jsonl 与场景 CSV。`audit/provenance.json` 早已写明 provenance 是 `mod/assets/translation.csv`。
- 修法：给 `integration/fix_ss_names.py` 加第三层 `fix_vocab()`，同时改这三张表（列位不同：translation.csv 的键在第 2 列、译文在末列；unit_names_en_zh.csv 是 `en,zh,source,id,note`）。
- 教训：**先查 `audit/provenance.json` 再动手**。同一个键可能同时存在于 jsonl、场景 CSV、词表、覆盖层四层，改错层就是白改一轮（v1.9.8 的 Min River 也是同样的坑）。

覆盖层另有 3 键（`VI SS Latv.`、`2nd SS Latvian`、`19th SS Latvian`）在 `glossary/reference_overrides.json` 里是旧值，已从**源头**改正并重跑 `integration/build_master_overrides.py`（5,649 条），而不是改生成物。

## 4. 落地统计

| 层 | 文件 | 格数 |
|---|---|---:|
| jsonl 语料 | `data/scenario_csv/translations/unit.zh.jsonl` 及 `.qa`、`data/extracted/all.jsonl`、`info.jsonl` | 240 |
| 场景表 | `build/scenario_csv_zh/*/Units.zh.csv` 等 46 个文件（188 个中命中） | 527 |
| 词表 | `mod/assets/translation.csv`、`build/translation.csv` | 8 |
| 覆盖层 | `glossary/reference_overrides.json` → 重生成 `master_overrides.json` | 3 |
| 词典 | `mod/payload/translations.json`（72,253 条，条数不变，仅改值） | 60 |

复跑 `fix_ss_names.py --check` = 0 格；词典内短 SS 键 441 个，按正则扫「罗马数字残留 / 师墙 / 运兵 / 净选 / 兰斯多姆 / 陆战 / 土地风暴 / N/第M」= **0 条**。

## 5. 取证失败的三条路（为什么编制只能靠英文原文）

1. `Units.zh.csv` 的 `Men` 列全为 0 —— 拿不到兵员数；
2. 多数剧本 CSV **没有 `ID` 列**，且 `HigherHQ` 指向的父单位在部分剧本里 subs=0 —— 拿不到上下级关系；
3. 游戏 `Dat\CSV` 只有 14 个按剧本命名的 `.dat`（4–12 KB），`Dat\Scen\*.scn` 是压缩二进制 —— 没有 `Type`→编制名对照表。

因此 `X SS`、`XX SS` 这类只有番号的键，保持「第N党卫军」，**不加任何编制词**。

## 6. 守卫

- 新增 `mod/finalize.py` 的 **SS-name guard**：构建时执行 `integration/fix_ss_names.py --check`，jsonl / 场景 CSV / 词表任一层残留旧写法即 `refuse: SS 番号写法未统一`。构建日志出现 `SS-name guard: OK`。
- `integration/fix_ss_names.py` 自身：`--check` 只报不写、有残留 exit 2；写盘前做「读入 → 序列化 → 重新读入 → 逐行比对」，不一致即 `SystemExit`；CSV 保留 BOM 与行尾（`build/scenario_csv_zh` 多为 CRLF）。
- 与既有守卫的关系：`Name-artifact guard` 管元话语与残片，`Staffel guard` 管 `N./` 中队计数，本条管 SS 番号族，三者判据互不重叠。

## 7. 复现与残留

```
python integration\fix_ss_names.py --check      # 0 格才算干净
python integration\fix_ss_names.py              # 三层同时写
python mod\build_maps.py && python mod\complete_font.py && python integration\build_variants.py
python mod\finalize.py && python mod\publish.py
```

残留（未在本轮处理，留待 semantic 单例批次）：

- 仍只写「第N党卫军」的裸番号 166 个（英文本身无编制词，按第 4 条口径属正确写法）；
- `Units` 同名碰撞 281 组中与 SS 无关的部分（师/团层级差异）未动；
- `939th Rhodos`=「939罗得 部队」等其他脏值属别的族，见 `docs/译名脏值审计_v1.9.10.md`。
