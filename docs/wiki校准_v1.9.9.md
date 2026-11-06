# 维基百科校准报告（v1.9.9）

日期：2026-11-06
范围：游戏内 908 条「炮」类词条（词典中译文以「炮 / 火箭弹」结尾且有英文键名的条目），以及比利时、意大利两个「非主流」装备族的命名。
铁律：全程未启动游戏；wiki 数据为公开页面抓取，非游戏内核对。

## 0. 结论

| # | 结论 | 置信度 |
|---|---|---|
| 1 | 中文维基《火炮列表》可提供 697 条「口径 + 中文名 + 分类」记录，是本轮唯一高价值对照源 | 高 |
| 2 | 英文维基按「精确标题 → 中文链接」批量比对，命中率仅 29/1,078（2.7%），因为游戏装备名是内部写法（如 `88mm KwK36 L/56`），不是条目名 | 高 |
| 3 | 严格匹配（型号记号 + 口径同时吻合）得到 21 组，**炮种词与口径 21/21 与 wiki 一致**，无一条需要改炮种 | 高 |
| 4 | 发现真正的缺陷不在炮种，而在「de / da」族：13 条比利时、意大利装备被机翻成「德式 / 德制 / 德产 / 德法朗夏尔 / 圣切奇利亚」，另有 1 条把 `GP III` 当「穿甲弹三级」 | 高 |
| 5 | 比利时装备（`Nations.csv` 中 Nation 9 = Belgium）在 Vistula to Berlin 剧本里有一整族，被整体误标为德国货 | 高 |
| 6 | 13 条已按「型号段保留拉丁原文、只译口径与炮种」的规则改写并重建发布 | 高 |

## 1. 数据源与方法

### 1.1 中文维基《火炮列表》（主要来源）

`https://zh.wikipedia.org/wiki/火炮列表`，wikitext 40,376 字节，解析得 697 行有效记录（另有 1 行是 noteTA 模板残留）。按章节分布：

| 章节 | 行数 | 章节 | 行数 |
|---|---:|---|---:|
| 拖曳式榴弹炮 / 野战炮 | 123 | 反坦克炮 | 44 |
| 轻迫击炮 | 77 | 舰炮 | 34 |
| 高射炮 | 65 | 反坦克火箭弹发射器 | 32 |
| 战车炮 | 56 | 自行防空系统 | 30 |
| 自行榴弹炮 | 56 | 无后坐力炮 | 24 |
| 炮兵火箭 | 56 | 驱逐战车 / 突击炮 | 17 |
| 步兵炮 / 山炮 | 52 | 重迫击炮、列车炮 | 10 / 10 |
| 自行迫击炮 | 8 | 海防炮 | 3 |

每行结构为 `口径 | 武器名稱（中文维基条目名） | 原產國 | 年代`，因此同时给出「口径」与「中文规范名」两个可核对字段。

### 1.2 英文维基 langlinks（次要来源，命中率低）

对 `Dat/CSV/1941 Campaign/Devices.csv` 的 1,064 个装备名做 `prop=langlinks&lllang=zh` 批量查询（40 条/请求，27 次请求，全部成功）：

- 1,078 个页面（含规范化与重定向）里只有 **29 个**有中文链接；
- 且多为泛词：Bazooka→巴祖卡火箭筒、Flamethrower→火焰喷射器、Grenade→手榴弹、Panzerfaust→反坦克榴弹发射器、PIAT→PIAT；
- 结论：**游戏装备名不能直接当维基标题用**，这条路线放弃。

限流记录：对 544 条枪逐个 `list=search` 并发 4 线程会触发 `HTTP 429`，冷却约 75 秒；串行、间隔 ≥2 秒时稳定。本次批量 langlinks 间隔 1.2 秒、串行，未触发 429。

## 2. 严格匹配结果（21 组）

匹配规则：从 wiki 中文名和我们的英文键名中各抽「字母前缀 + 数字」的型号记号（如 `KwK36`、`ZiS3`、`SA34`、`Mle27`），记号相同**且**口径差 ≤2.5mm 才计为一组；`L/xx`（倍径）与 `M19xx`（年份）这类泛记号排除。

| wiki 分类 | 口径 | wiki 名 | 我们的键 | 我们的译文 | 判定 |
|---|---:|---|---|---|---|
| 战车炮 | 88 | KwK 36 | `88mm KwK36 L/56 Gun` | 88毫米KwK36 L/56坦克炮 | 一致 |
| 战车炮 | 88 | KWK43 L/71 | `88mm KwK43 L/71 Gun` | 88毫米KwK43 L/71坦克炮 | 一致 |
| 战车炮 | 75 | Kwk-42 L/70戰車砲 | `75mm KwK42 L/70 Gun` | 75毫米KwK42 L/70坦克炮 | 一致 |
| 战车炮 | 37 | 37 SA 18 | `37mm SA18 L/21 Gun` | 37毫米SA18 L/21坦克炮 | 一致 |
| 战车炮 | 37 | 37 SA 38 | `37mm SA38 L/33 Gun` | 37毫米SA38 L/33坦克炮 | 一致 |
| 战车炮 | 47 | 47 SA 34 | `47mm SA34 L/30 Gun` | 47毫米SA34 L/30坦克炮 | 一致 |
| 战车炮 | 47 | 47 SA 35 | `47mm SA35 L/32 Gun` | 47毫米SA35 L/32坦克炮 | 一致 |
| 战车炮 | 75 | 75 SA 35 | `75mm SA35 L/17 Gun` | 75毫米SA35 L/17坦克炮 | 一致 |
| 战车炮 | 152.4 | ML-20S | `152mm ML-20S L/29 Gun` | 152毫米ML-20S L/29加农炮 | 一致（wiki 归战车炮，该炮确为 ISU-152 主炮） |
| 反坦克炮 | 25 | 25 SA 34 | `25mm SA-34 AT Gun` | 25毫米SA-34反坦克炮 | 一致 |
| 反坦克炮 | 47 | 47 SA 37 | `47mm SA37 L/53 Gun` | 47毫米SA37 L/53反坦克炮 | 一致 |
| 高射炮 | 88 | FlaK 18 | `88mm Flak18 AA Gun` | 88毫米Flak 18高射炮 | 一致 |
| 榴弹炮/野战炮 | 76.2 | 76毫米炮M1942 (ZiS-3) | `76.2mm ZiS-3 L/42.6 Gun` | 76.2毫米ZiS-3 L/42.6加农炮 | 一致（wiki 条目名亦作「ZiS-3加农炮」） |
| 榴弹炮/野战炮 | 152.4 | 152毫米榴彈砲model 1937 (ML-20) | `152mm ML-20 Gun-Howitzer` | 152毫米ML-20榴弹炮 | 一致 |
| 自行榴弹炮 | 105 | StuH 42 | `105mm StuH42 L/28 Gun` | 105毫米StuH42 L/28突击榴弹炮 | 一致 |
| 迫击炮 | 81 | Brandt mle 27/31 | `81mm Mle 27/31 Mortar` | 81毫米Mle 27/31迫击炮 | 一致 |
| 榴弹炮/野战炮 | 155 | Canon de 155 C mle 1917 Schneider | `155mm de 155 C Howitzer` | 155毫米德制155C榴弹炮 | **炮种对、国别错**（见 §3） |
| 榴弹炮/野战炮 | 155 | Canon de 155 GPF | `155mm de 155 L Field Gun` | 155毫米德产155 L野战炮 | **炮种对、国别错** |
| 步兵炮/山炮 | 75 | Canon de 75 modèle 1897 | `75mm de 75 TR L/30 Gun` | 75毫米德法朗夏尔75TR L/30加农炮 | **国别错 + 乱码式音译** |
| 步兵炮/山炮 | 105 | Canon Court de 105 M mle 1909 Schneider山炮 | `105mm de 105 GP Howitzer` | 105毫米de 105 GP榴弹炮 | 型号码保留，可接受 |
| 步兵炮/山炮 | 105 | Canon Court de 105 M mle 1919 Schneider山炮 | `105mm de 105 Field Gun` | 105毫米德式105野战炮 | **国别错** |

合计：炮种一致 21/21，口径一致 21/21。**没有一条需要改炮种**——v1.9.8 定的「口径/倍径 + 型号 + 中文炮种」体系与中文维基的分类用词吻合（火炮→加农炮、戰車炮→坦克炮、反戰車炮→反坦克炮、艦砲→舰炮、榴彈砲→榴弹炮、迫擊砲→迫击炮、高射炮→高射炮）。

## 3. 真正的缺陷：de / da 族被机翻成「德式」

### 3.1 证据链

1. 装备名形如 `105mm de 105 Field Gun`、`155mm de 155 C Howitzer`、`75mm de 75 TR L/30 Gun`，`de` 是法语/比利时语命名法（Canon de …）里的介词，不是「德国」。
2. `Dat/CSV/Vistula to Berlin Campaign/Ground.csv` 中这一整族（ID 3072–3080）的 `Nation` 字段全部是 **9**。
3. `Dat/CSV/1941 Campaign/Nations.csv`：`9=Belgium`（1=Germany、3=Italy、27=France）。
4. 兄弟条目 `76mm de FRC L/9.2 Gun`：FRC = 比利时皇家铸炮厂（Fonderie Royale de Canons），进一步佐证是比利时装备。
5. 意呆利族 `Semovente … da …` 同样把 `da` 当成了实义词：`Semovente M41M da 90` 被译成「圣切奇利亚M41型…」（凭空造了个地名），`Semovente L40 da 47` 被译成「自行研发的 L40 轮式突击炮 47/3」（把 Semovente 当成了「自行研发」）。

结论：这些条目不是「意译过度」，而是**把外语介词当实词硬翻**，产生了「德式 155 炮其实是比利时炮」这类事实性错误。

### 3.2 处置规则

不猜国别、不补年份，**型号段保留拉丁原文，只译口径与炮种**：

- `105mm de 105 Field Gun` → `105毫米de 105野战炮`
- `155mm de 155 C Howitzer` → `155毫米de 155 C榴弹炮`
- `75mm de 75 TR L/30 Gun` → `75毫米de 75 TR L/30加农炮`
- `Semovente M41M da 90` → `M41M 90毫米自行火炮`（与已有的 `M40 75毫米自行火炮`、`M42`、`M43` 四条对齐）

口径仍是毫米、炮种仍是固定词表，与 v1.9.8 的规则不冲突；只是把「不认识的外语词」交还给原文，而不是编一个中文。

### 3.3 修订清单（13 条，全部落在 `glossary/equipment_name_fixes.json`）

| # | 源表 | 键 | 旧译 | 新译 |
|---:|---|---|---|---|
| 1 | Ground.csv | 105mm de 105 Field Gun | 105毫米德式105野战炮 | 105毫米de 105野战炮 |
| 2 | Ground.csv | 150mm de 150 Field Gun | 150毫米德式150野战炮 | 150毫米de 150野战炮 |
| 3 | Ground.csv | 150mm de 150 Howitzer | 150毫米德式150毫米榴弹炮（「毫米」重复） | 150毫米de 150榴弹炮 |
| 4 | Ground.csv | 155mm de 155 C Howitzer | 155毫米德制155C榴弹炮 | 155毫米de 155 C榴弹炮 |
| 5 | Ground.csv | 155mm de 155 L Field Gun | 155毫米德产155 L野战炮 | 155毫米de 155 L野战炮 |
| 6 | Ground.csv | 75mm de GP III Field Gun | 75毫米穿甲弹三级野战炮（GP III 误作 AP） | 75毫米de GP III野战炮 |
| 7 | Ground.csv | 75mm de TR Field Gun | 75毫米拖曳式野战炮（TR=速射，非拖曳） | 75毫米de TR野战炮 |
| 8 | Ground.csv | 152mm de 152 Howitzer | 152毫米M1937榴弹炮（年份是编的） | 152毫米de 152榴弹炮 |
| 9 | Ground.csv | 220mm de 220 TR Howitzer | 220毫米M1931牵引榴弹炮（年份与「牵引」都是编的） | 220毫米de 220 TR榴弹炮 |
| 10 | Ground.csv | Semovente L40 da 47 | 自行研发的 L40 轮式突击炮 47/3 | L40 47毫米自行火炮 |
| 11 | Ground.csv | Semovente M41M da 90 | 圣切奇利亚M41型90毫米自行火炮 | M41M 90毫米自行火炮 |
| 12 | Devices.csv | 75mm de 75 TR L/30 Gun | 75毫米德法朗夏尔75TR L/30加农炮 | 75毫米de 75 TR L/30加农炮 |
| 13 | Devices.csv | 76mm de FRC L/9.2 Gun | 76毫米德式FRC L/9.2步兵炮 | 76毫米de FRC L/9.2步兵炮 |

其中 #12、#13 的旧值正是 v1.9.8 写进修订表的（当时就带着「德法朗夏尔」「德式」），本轮是**回头改自己的错**；另 11 条为新增。

## 4. 重建与验证

```
python integration/fix_equipment_names.py   # jsonl cells: 26; csv cells: 169; fixes: 1207
python mod/build_maps.py                    # Packaged 72227 existing translations; 9435638 bytes
python mod/complete_font.py                 # Completed glyph coverage: 2429
python integration/build_variants.py        # 四套 72,227 条，缺字 0；zh-TW/HK/MO 改动 64,804/64,790/64,790
python mod/finalize.py                      # Art-path guard OK / Pending-source guard OK / Nationality OK / 92 files
python mod/publish.py                       # 复制 10 文件，目标版本 1.9.8，校验通过
```

安装目录复核（`D:/Tool/WITE2/WITE2_CN/mod/payload/translations.json`）：13 条全部为新值；活动槽 `translations.bin` 由 `variants/zh-CN` 手工物化，sha256 `87592AAC934EA4D5022093B1B136D6C26E72580E13386720790504497990952C`；`WitE2CN.exe --selftest` exit 0、`SELFTEST PASS`（四语言包各 9 MB OK）。

## 5. 边界与残留

1. **覆盖率有限**：908 条炮类条目里只有 21 条能与中文维基严格对上（2.3%）。不是没查，而是中文维基没有对应条目——大部分游戏装备（尤其德军型号）只有英文维基条目，而英文条目名与游戏内部名对不上（§1.2）。
2. **本轮改的是「明显错」而非「更好」**：13 条都属于「外语介词当实词」的事实性错误（国别错、年份编造、乱码音译），改动有据可查；其余条目保持 v1.9.8 的译法不动。
3. **未进游戏核对**：按铁律不启动游戏。译文在文件层面已生效，玩家侧需进游戏看装备详情/单位编制表确认。
4. **待办**：其他装备族（飞机、车辆）可照同样方法做「de/da/type」介词专项扫描；`Semovente` 之外还有 `Carro Armato`、`Autoblindo` 等意大利语词头，尚未逐个核对。
