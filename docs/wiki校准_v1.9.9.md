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
| 7 | 飞机编制表 10 条分组表头被机翻改坏：`SLOVAKIA`→「捷克斯洛伐克」、`WA Italy`→「威亚意大利」、`France` 译文被塞进换行 | 高 |
| 8 | 荷兰 `Van` 族 8 条、日制 `Type NN` 13 条写法混乱（编造 M1935/M1937、`TL 4`→四联、`型2`），已统一为「型号保留拉丁／日制汉字式」 | 高 |

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

## 5. 边界与残留（第一轮）

1. **覆盖率有限**：908 条炮类条目里只有 21 条能与中文维基严格对上（2.3%）。不是没查，而是中文维基没有对应条目——大部分游戏装备（尤其德军型号）只有英文维基条目，而英文条目名与游戏内部名对不上（§1.2）。
2. **本轮改的是「明显错」而非「更好」**：13 条都属于「外语介词当实词」的事实性错误（国别错、年份编造、乱码音译），改动有据可查；其余条目保持 v1.9.8 的译法不动。
3. **未进游戏核对**：按铁律不启动游戏。译文在文件层面已生效，玩家侧需进游戏看装备详情/单位编制表确认。
4. **待办**：其他装备族（飞机、车辆）可照同样方法做「de/da/type」介词专项扫描；`Semovente` 之外还有 `Carro Armato`、`Autoblindo` 等意大利语词头，尚未逐个核对。

## 6. 同日第二轮：飞机 / 车辆族与 `Type` 系列

第一轮把「de / da 介词」清干净后，按同一思路把扫描面扩到飞机与车辆：不再只看介词，而是抽取源串里的**拉丁字母/数字 token**（型号记号、口径、罗马数字），逐个检查是否在译文中原样保留；再单独检查飞机列表的**分组表头行**。

### 6.1 表头行 `*** NAME (n) ***`（10 条）

飞机编制表的国籍分组行是数据里的字符串，`***` 是分隔装饰。机翻把其中 10 条改坏了，其中 2 条是事实性错误：

| 键 | 旧译 | 新译 | 问题 |
|---|---|---|---|
| `*** SLOVAKIA (6)***` | `*** 捷克斯洛伐克（6）***` | `*** 斯洛伐克 (6) ***` | **Slovakia ≠ Czechoslovakia**（后者是 Nation 8 Czech） |
| `*** WA ITALY (24)***` | `*** 威亚意大利 (24)***` | `*** 盟军意大利 (24) ***` | `WA` = Western Allies，被音译成「威亚」 |
| `*** France (27)***` | 译文被塞进两个换行，断成三行 | `*** 法国 (27) ***` | **换行破坏分组标题** |
| `*** BELGIUM (9)***` | `比 利 时 (9)` | `*** 比利时 (9) ***` | 星号全丢 + 字间插空格 |
| `*** UK/CW (15/26) ***` | `*** 英国/协约国 (15/26) ***` | `*** 英国/英联邦 (15/26) ***` | `CW` = Commonwealth，不是「协约国」（一战概念） |
| `*** BULGARIA (7)***` | `***保加利亚(7)***` | `*** 保加利亚 (7) ***` | 星号后缺空格 |
| `*** NETHERLANDS (10)***` | `*** 荷兰（10）***` | `*** 荷兰 (10) ***` | 全角括号 |
| `*** POLAND (11)***` | `*** 波兰（11）***` | `*** 波兰 (11) ***` | 全角括号 |
| `*** USA/America (13/38)***` | `*** 美国 (13/38)***` | `*** 美国 (13/38) ***` | 尾部缺空格 |
| `*** GERMANY Extension ***` | `*** 德国 扩展 ***` | `*** 德国（扩展） ***` | 多余空格 |

`France` 那条最能说明问题：机翻在译文里插入了换行，而这一行是**列表分组标题**，换行会让表头断成三行——这不是风格问题，是排版破坏。

### 6.2 荷兰「Van」族（8 条）

`Ground.csv` 里有一整族荷兰装备（Nation 10 = Netherlands），型号段以 `Van` 开头。机翻把它当成实词，产出四类错误：

| 键 | 旧译 | 新译 | 问题 |
|---|---|---|---|
| `81mm Van 8 Mortar` | 81毫米**VAN** 8迫击炮 | 81毫米Van 8迫击炮 | 型号段被整体大写 |
| `20mm Van TL 1 AA Gun` | 20毫米**VAN** TL 1高射炮 | 20毫米Van TL 1高射炮 | 同上 |
| `40mm Van TL 4 AA Gun` | 40毫米**四联**高射炮 | 40毫米Van TL 4高射炮 | `TL 4` 被当成「四联」，型号消失 |
| `75mm Van TL 1 AA Gun` | 75毫米**防空炮** | 75毫米Van TL 1高射炮 | 型号被整个删掉 |
| `47mm Van 4.7 AT Gun` | 47毫米反坦克炮 **Van 4.7** | 47毫米Van 4.7反坦克炮 | 语序错乱，型号跑到句尾 |
| `120mm Van 12 Howitzer` | 120毫米**M12牵引**榴弹炮 | 120毫米Van 12榴弹炮 | 编造型号与「牵引」 |
| `150mm Van 15 Howitzer` | 150毫米**M1935**榴弹炮 | 150毫米Van 15榴弹炮 | 编造年份 |
| `152mm Van 15 Howitzer` | 152毫米**M1937**榴弹炮 | 152毫米Van 15榴弹炮 | 编造年份 |

与 `de` 族是同一个病根：**把不认识的型号记号当成可翻译的词**。规则统一为「型号段保留拉丁原文，只译口径与类别」。`70mm van Duren Mortar` → `70毫米范杜伦迫击炮` 是唯一保留音译的，因为 `Van Duren` 是厂商/人名，不是型号记号。

### 6.3 日制 `Type NN` 系列（13 条）

同一批日制装备在词典里有 **9 种写法**，玩家在装备表里会看到自相矛盾的一套名字：

| 键 | 旧译 | 写法 |
|---|---|---|
| `20mm Type 97 AT-Rifle` | 20毫米Type97反坦克枪 | 拉丁、无空格 |
| `25mm Type 96 AA Gun` | 25毫米Type96高射炮 | 拉丁、无空格 |
| `21in Type 95 Torpedo` | 21英寸Type 95鱼雷 | 拉丁、有空格 |
| `Type 2 Depth Charge` | **型2**深水炸弹 | **残缺**（「式」被吃掉） |
| `Type 91 Depth Charge` | 九一**型**深水炸弹 | 汉字 + 型 |
| `21in Type 92 Torpedo` | **92式21英寸**鱼雷 | 阿拉伯数字 + 口径后置 |
| `24in Type 93 Torpedo` | 24英寸九三式鱼雷 | 汉字 + 口径前置 |
| `Type 88 Mine` | 88式**地雷** | 阿拉伯数字 + 类别错（Devices Type=27 是水雷） |
| `Type 271 Radar` | **TYPE 271 雷达设备** | 全大写 + 加词 |

统一规则（与 v1.9.8 的 `3YT → 三年式`、`Type 88 → 八八式` 一脉相承）：

- **日制**：口径 + 汉字数字 + 式 + 类别，如 `21英寸九五式鱼雷`、`九一式深水炸弹`、`八八式水雷`。
- **英制雷达**：保留拉丁（`Type 271 雷达`、`Type 279 雷达`）——RN 的 `Type NNN` 是型号编号，不适用「式」。
- **日制雷达**（`Type 13/21/22`）：暂保留拉丁。旧日本海军电探编号是「一三号／二一号」而非「式」，没有把握前不硬套格式。

### 6.4 新增守卫：表头行

`mod/finalize.py` 增加 **Section-header guard**：

- 任何以 `***` 开头的键，其译文含换行 → **构建失败**（`refuse: N section-header row(s) contain a line break`）；
- 星号标记丢失／不闭合 → 首版只告警并计数（首次启用时 34 条），**第三轮已改为硬失败**，见 §7。
- 告警里点名的 3 条例外是真正的坏值：`****** Light Infantry Regiments ******` 的译文重复成 `轻步兵师团   ****** 轻步兵师团 *****`、`****** Border/Security ******` 尾部带 `【注】`、`*** D3DUtil_…` 是 Direct3D 报错串（不是表头，只保留前缀 3 个星号即合规）。

### 6.5 重建与验证

```
python integration/fix_equipment_names.py   # jsonl cells: 62; csv cells: 390; fixes: 1235
python mod/build_maps.py                    # Shelved 0/0; Packaged 72227; 9435642 bytes
python mod/complete_font.py                 # 2429 字形
python integration/build_variants.py        # 四套 72227，缺字 0；zh-TW/HK/MO 改动 64803/64789/64789
python mod/finalize.py                      # Section-header guard: WARN 34
python mod/publish.py                       # 校验通过
```

活动槽 sha256 `A7A2798C32B4134000F18AA81876B3EBB836987370A86BCA38275AB6F13D61EA`；`--selftest` exit 0、`SELFTEST PASS`。安装目录逐条复核：10 条表头、8 条 Van、13 条 Type 全部为新值。

### 6.6 残留

1. 34 条表头丢了星号标记（信息未丢，仅装饰缺失）——**已由第三轮清零，见 §7**。
2. 意大利语词头 `Carro Armato`、`Autoblindo` 等尚未逐族核对。
3. 本轮仍是文件层验证：按铁律未启动游戏。


## 7. 同日第三轮：34 条表头告警清零（实为 585 格）

### 7.1 为什么告警只有 34 条，坏格却有 585 个

词典是**按英文原串去重**的，而分组行在 14 个剧本里逐个复制：同一个 `****** Infantry ******` 在每个剧本的 `OBs.csv` 里各占一格。所以「34 个键」在数据层是 **585 个单元格**（26 个 CSV 文件）——只改字典不改 CSV，下次 `build_maps.py` 又会按 CSV 重建出坏值；只改 CSV 不改 jsonl，下次 `apply_scenario_translations.py` 又会写回旧值。三处必须一起动。

### 7.2 判据：镜像原文的星号形状，而不是「有没有星号」

原判据「译文必须以 *** 开头且以 *** 结尾」把两类正常串误判了：

- `*** D3DUtil_SetDeviceCursor LockRect FAILED` 这类**报错前缀**，原文本来就只有开头星号，没有结尾星号；
- `***Off Map Soviet`（Locations.csv 的分组行）原文也只有前缀。

新判据与**键本身的装饰形状**对齐：

| 原文形状 | 译文要求 |
|---|---|
| 开头 N≥3 个星号 | 开头 ≥3 个星号 |
| 结尾 M≥3 个星号 | 结尾 ≥3 个星号 |
| 只有前缀（报错串） | 只要求前缀 |
| 无星号 | 不管 |

数量不必与原文完全相等（引擎只当文本显示，多一个少一个星号不影响布局），但**一个都没有**就等于丢掉了分组视觉分隔，构建直接失败。

### 7.3 新工具 `integration/fix_section_headers.py`

对 `build/scenario_csv_zh/*/*.zh.csv` 的每个文本列，取游戏 `Dat/CSV` 原单元格的星号形状，把译文重建为 `星号 + 空格 + 正文 + 空格 + 星号`；同时清掉三类脏值，并同步 `data/scenario_csv/translations/*.jsonl`（含 `.qa` 副本，按 `(source, text)` 对齐）：

| 脏值类型 | 实例 | 处置 |
|---|---|---|
| 星号全丢 | `****** Infantry ******` → `步兵` | `****** 步兵 ******` |
| 只丢一侧 | `**** Mot. Inf/Panzergren Brigades ****` → `摩托化步兵/装甲掷弹兵旅群 ****` | 补齐前缀 |
| 重复片段 | `****** Light Infantry Regiments ******` → `轻步兵师团   ****** 轻步兵师团 *****` | `****** 轻步兵师团 ******` |
| 尾随注记 | `****** Border/Security ******` → `****** 边境/治安 ******  【注】` | 去注记 |

首轮统计：**585 格 / 26 个 CSV / 36 条 jsonl**。另外 `***** Scenario Check *****` 不在 CSV 里（覆盖层 UI 串），按同一规则在 `glossary/reference_overrides.json` 里恢复为 `***** 剧本检查 *****`，重生成覆盖层。

### 7.4 验证

```
python integration/fix_section_headers.py    # stats: {'cell': 585, 'file': 26, 'jsonl': 36}
python integration/build_master_overrides.py # master overrides: 5650
python mod/build_maps.py                     # Shelved 0/0; Packaged 72227; 9436108 bytes
python mod/complete_font.py                  # 2429 字形
python integration/build_variants.py         # 四套 72227，缺字 0
python mod/finalize.py                       # Section-header guard: OK
python mod/publish.py                        # 校验通过
```

字典里以星号开头的键共 **236** 个，全部通过镜像校验；活动槽 sha256 `CE54D4408469DF0B6892CF1FC8184A7627B62225CB9E58A6D937FA4D680D5C37`；`--selftest` exit 0、`SELFTEST PASS`（四语言包各 9 MB OK）。

## 8. 局限（对外口径，写进 README / Release）

这一节是给玩家的说法，也是本轮的自我限定——**不夸大覆盖范围**：

1. **维基覆盖率低是硬约束，不是偷懒**：908 条炮类条目里只有 21 条能与中文维基《火炮列表》严格对上（2.3%）；英文维基按条目名查中文链接的命中率是 29/1,078（2.7%）。大部分德军型号只有英文条目，而英文条目名与游戏内部名对不上，所以**宁可不动，也不做「无源改名」**。
2. **国籍靠数据表，不靠名字**：本轮实锤的两起事实性错误——「比利时 155 炮被译成德制」（`de` 被当成德国）、「Slovakia 被译成捷克斯洛伐克」——都说明看名字猜国别一定会错。判据是 `Nations.csv` 的国别码与剧本 CSV 的 `Nation` 列。
3. **维基不等于军事史**：校准只能证明「与维基一致/不一致」，不能证明「符合史实」；维基的分类与年代本身也有混用（例如把舰炮与岸防炮混列）。21 组匹配只用于**验证炮种词与口径**，不用来改写型号。
4. **只修「可判定的错」**：国别错、年份编造、型号消失、星号/换行破坏——这些有据可查；「重型→重」这类语义压缩、文风偏好，没有自动判据，本轮不动。
5. **未进游戏核对**：按铁律不启动游戏（离线 `--selftest` 只校验包完整性），全部为文件层验证。玩家侧需要目视两处：地图小河、编制表分组行。
6. **尚余**：日制雷达 `Type 13/21/22` 暂留拉丁；英军 `Mk II AA` 型号归属待考；覆盖层里仍有 12 条设备名旧值（职责划分未动，随推进逐步改）。意大利/法国词头已确认本库无条目（见 §9.3）。

## 9. 同日第四轮：按 `Type` 分族核对（自行高射炮 / 匈牙利）

前三轮都是「按名字里的词」找族（`Van`、`de`、`da`、`Type`）。这一轮换判据：**先看数据表的 `Type` 列，再看名字**。理由很直接——名字是机翻的产物，`Type` 是数据表里的硬分类，不会骗人。

`Ground.csv` 里 Type 22 = 自行高射炮 / 自行防空（24 条），Type 23 = 半履带载具（6 条）。

### 9.1 自行高射炮族（Type 22）17 条

| # | 键 | 旧译 | 新译 | 问题 |
|---:|---|---|---|---|
| 1 | `M13 MGMC` | M13机枪载具车 | M13 多管自行高射机枪 | `MGMC`=Multiple Gun Motor Carriage，原译丢掉防空职能 |
| 2 | `M14 MGMC` | M14机枪载具 | M14 多管自行高射机枪 | 同上，且与 M13 不成对 |
| 3 | `M15 MGMC` | M15 坦克歼击车 | M15 组合式自行高射炮 | **事实错误**：Type 22，37mm+双联 12.7mm 组合炮座 |
| 4 | `M16 MGMC` | M16机枪载具 | M16 多管自行高射机枪 | 四联 12.7mm |
| 5 | `M17 MGMC` | M17 带机枪的装甲车 | M17 多管自行高射机枪 | 与 M16 同型，原译与 M16 完全不同构 |
| 6 | `M19 GMC` | M19自行火炮 | M19 双联装自行高射炮 | 双联 40mm，Type 22，原译不表防空 |
| 7 | `Moebelwagen` | 梅花车 | 家具车式防空坦克 | `Möbelwagen`=家具搬运车；zh.wikipedia 条目「家具車式防空坦克」 |
| 8 | `Wirbelwind` | 旋风式 | 旋风式防空坦克 | 缺车种；wiki「旋風式防空坦克」 |
| 9 | `Ostwind` | 东风 | 东风式防空坦克 | 缺车种，且与「旋风式」不成对 |
| 10 | `SdKfz-10/4 Flak30` | SdKfz-10/4 高射炮30 | SdKfz-10/4 Flak 30高射炮 | 型号与炮种倒置 |
| 11 | `SdKfz-6/2 Flak36` | SdKfz-6/2 弗拉克36 | SdKfz-6/2 Flak 36高射炮 | 音译「弗拉克」 |
| 12 | `SdKfz-7/1 Flak38` | SdKfz-7/1 38毫米防空炮车 | SdKfz-7/1 Flak 38高射炮 | **Flak 38 是型号（20mm 炮），被当成 38mm 口径** |
| 13 | `SdKfz-7/2 Flak36` | SdKfz-7/2 弗拉克36 | SdKfz-7/2 Flak 36高射炮 | 音译 |
| 14 | `SdKfz-7/2 Flak43` | SdKfz-7/2 迫击炮车 | SdKfz-7/2 Flak 43高射炮 | **事实错误**：Type 22 是防空车，不是迫击炮 |
| 15 | `SdKfz-10/5 Flak38` | SdKfz-10/5 弗拉克38 | SdKfz-10/5 Flak 38高射炮 | 音译 |
| 16 | `SdKfz-9 Flak18` | （无译文） | SdKfz-9 Flak 18高射炮 | 词典里根本没有这个键 |
| 17 | `SdKfz-251/21 AAMG` | SdKfz-251/21 自动机枪车 | SdKfz-251/21 高射机枪车 | `AAMG`=anti-aircraft MG，原译丢掉防空 |

同族的 `Flakpanzer 38`（38(t)自行高射炮）、`Nimrod`（尼姆罗德）、`Crusader III Mk 1/2 AA`、`Morris C9/B SPAA` 经核对无误，未动。

### 9.2 匈牙利族 4 条与一处截断

| 键 | 旧译 | 新译 | 依据 / 问题 |
|---|---|---|---|
| `Turan I` | 土尔干I型 | 图兰I型 | zh.wikipedia「图兰坦克」（40M 图兰）；「土尔干」是错音译 |
| `Turan II` | 土尔干II | 图兰II型 | 同上，且原译缺「型」 |
| `Turan Chassis` | 土尔干底盘 | 图兰底盘 | 同上 |
| `Zrinyi II` | 兹里尼二式 | 兹里尼II型 | zh.wikipedia「43M兹里尼II型突击炮」；罗马数字 II 被当成日制年式「二式」 |
| `SdKfz-8 Flak18` | SdKfz-8 8.8 厘米 F | SdKfz-8 8.8厘米Flak 18自行火炮 | 原译文在「F」处被**截断**，型号丢失 |

`Toldi` 四条（托尔迪I型 / II型 / IIa型 / 底盘）经核对无误，未动。

### 9.3 「意大利语族」待办关闭（不是漏做，是不存在）

把 13 个 `data/scenario_csv/translations/*.jsonl` 全量搜了一遍：`Carro Armato`、`Autoblindo`、`Chi-Ha`、`Ha-Go`、`Ka-Mi`、`Ho-Ni`、`Ho-Ro`、`Char`、`Chenillette`、`Automitrailleuse` **全部 0 命中**；`Semovente` 只有 5 条（第一轮已处理）。日制战车在本库里统一以 `Type NN` 形式出现（第二轮已处理），法、意两国的型号词头在本库里没有条目。

### 9.4 规则沉淀

1. **分族用 `Type` 码，不用名字**：名字是翻译对象，拿它当分类依据会把「同族不同译」当成「不同族」。
2. **型号 ≠ 口径**：`Flak 38` / `Flak 43` 是炮的型号（20mm / 37mm 炮），不是 38 / 43 毫米；`Type 97`、`Mk II` 同理。
3. **编制缩写必须译出职能**：`MGMC`（Multiple Gun Motor Carriage）、`AAMG`（anti-aircraft MG）、`SPAA` 都含防空语义，不能只留「机枪车 / 装甲车」。
4. **同族要「成对」检查**：Wirbelwind / Ostwind、M13 / M14 / M16 / M17 应同构；单看一条看不出「这条少了个车种」。
5. **「二式 / 三式」是日制年式专用**，不能拿来译罗马数字 `II` / `III`。

### 9.5 重建与验证

```
python integration/fix_equipment_names.py   # 首轮 jsonl 34 / csv 234；二轮 jsonl 10 / csv 65；fixes 1257
python mod/build_maps.py                    # Shelved 0/0; Packaged 72228; 9436328 bytes
python mod/complete_font.py                 # 2429 字形
python integration/build_variants.py        # 四套 72228，缺字 0；修改 0 / 64802 / 64788 / 64788
python mod/finalize.py                      # 五道守卫全 OK，92 files
python mod/publish.py                       # 复制 10 文件，1.9.9，校验通过
```

安装目录逐条复核：22 条全部为新值，字典 72,228 条；活动槽 sha256 `B828704ED042DF670F403DA15334D1D6CB500AA9BBE3AB87789ACD5555ABAE83`（= `variants/zh-CN`）；`WitE2CN.exe --selftest` exit 0、`SELFTEST PASS`（四语言包各 9 MB OK）。

### 9.6 残留

1. `Mk II AA`（英军，Type 22）保留原译「二号高射炮系统」未动：`Mk II` 可能指 Crusader AA Mk II，也可能是博福斯炮座，缺少可判定依据——按「没出处不动」处理，仅登记。
2. MGMC 五条用「多管」概括，未在译文里写死联装数（M13/M14 双联、M16/M17 四联）：数值来自型号常识而非本轮抓到的出处，留给玩家反馈再定。
3. Type 23 的 `SdKfz-251/10、/17、/22`、`SdKfz-250/10、/11` 五条只译到「半履带车」，未标车上武器——属信息缺失而非错误，本轮不动。

## 10. 同日第五轮：坦克族与装甲车辆族（54 条）

第四轮按 `Type` 分族验证了这条路可行（名字是翻译产物，`Type` 是数据表里的硬分类）。这一轮把同一判据推到坦克与装甲车辆：`Type` 12 轻型坦克（46 条）、13 中型坦克（74 条）、14 重型坦克（19 条）、15 巡洋/支援坦克（14 条），再连带 11 装甲车、18/66 突击炮、60/61/67 坦克歼击车、21/90 自行火炮、30 高射机枪。

### 10.1 覆盖层里的 5 条（必须先改源头）

这 5 条在词典里的值来自 `glossary/master_overrides.json`，改 jsonl 或场景 CSV 都不会生效（v1.9.8 血案）——必须改 `glossary/reference_overrides.json` 的 `terms` 组，再重跑 `integration/build_master_overrides.py`：

| 键 | 旧值 | 新值 | 依据 |
|---|---|---|---|
| `Panzer IVg` | 装甲IVg型 | 四号G型坦克 | 旧值注记自承「占位符残渣」 |
| `Jagdpanzer 38` | 坦克歼击车38 | 38式坦克歼击车 | 语序（型号在前） |
| `Jagdpanzer 38 Hetzer` | 坦克歼击车38 追猎者 | 追猎者式坦克歼击车 | zh.wikipedia「追獵者式坦克殲擊車」 |
| `Jagdpanzer IV` | 坦克歼击车 IV型 | 四号坦克歼击车 | zh.wikipedia「四號驅逐戰車」 |
| `Jagdpanzer IV/70(V)` | 坦克歼击车 IV/70(V) | 四号坦克歼击车 IV/70(V) | 同车族 |

### 10.2 事实类错误（不是风格问题）

| 键 | 旧值 | 新值 | 错在哪 |
|---|---|---|---|
| `White Scout Car` | 白色侦察车 | 怀特侦察车 | White 是 White Motor Company，不是颜色 |
| `Staghound I Armored Car` | 野猪猎人I型装甲车 | 猎鹿犬I型装甲车 | Staghound 是一个词（猎鹿犬）；旧译把 Stag+Hound 拆开直译 |
| `Staghound III Armored Car` | 野猪III型装甲车 | 猎鹿犬III型装甲车 | 同上，且丢了「装甲车」 |
| `Staghound T17E3 Armored Car` | 斯塔霍恩T17E3装甲车 | 猎鹿犬T17E3装甲车 | 同族音译与意译并存 |
| `TACAM T-60` | 自行火炮 T-60轻型坦克 | TACAM T-60坦克歼击车 | TACAM＝罗马尼亚「T-60 坦克歼击车」，不是自行火炮 + 另一辆坦克 |
| `Chaffee` | 夏菲 | 霞飞 | zh.wikipedia「M24霞飛坦克」；同族的 `M24 Chaffee` 本来就叫「霞飞」 |
| `M26 Pershing` | M26 派许 | M26潘兴 | zh.wikipedia「M26潘興坦克」 |
| `Humber Mk III/IV Armored Car` | 胡默尔Mk III/IV装甲车 | 亨伯Mk III/IV装甲车 | Humber＝亨伯 |
| `Sturmmoerser` | 突击迫击炮 | 突击臼炮 | Mörser＝臼炮（与既有「突击虎自行臼炮」一致）；迫击炮是 Granatwerfer |
| `StuH42` | 三号42型突击榴弹炮 | 三号突击榴弹炮42型 | StuH 42＝Sturmhaubitze 42，年份在车种后 |
| `Sturmpanzer IV` | 四号突击坦克 | 灰熊式突击炮 | zh.wikipedia「灰熊式突擊砲」；Type 66 是重型突击炮 |
| `ISU-152` | ISU-152自行火炮 | ISU-152重型突击炮 | zh.wikipedia「ISU-152式重型突擊炮」 |
| `M10/M18/M3/M36 ... GMC` | …自行火炮 | …坦克歼击车 | GMC＝Gun Motor Carriage，这四种在数据表里就是 Type 60/67 坦克歼击车 |
| `7.62mm Quad Maxim AAMG` | 7.62毫米四联马克沁重机枪高射机枪 | 7.62毫米四联马克沁高射机枪 | 「机枪」叠词 |

### 10.3 机翻残渣与截断

| 键 | 旧值 | 新值 |
|---|---|---|
| `Mk VIB` | 马克 | Mk VIB轻型坦克 |
| `M5A1 Stuart` | M5A1 武士坦克 | M5A1斯图亚特轻型坦克 |
| `M4A3(75)W Sherman` | M4A3(75)W 詹姆斯顿 | M4A3(75)W谢尔曼 |
| `M4A3(76)W Sherman` | M4A3(76)W 詹姆斯顿 | M4A3(76)W谢尔曼 |
| `M4(105) Sherman` | M4(105) 詹姆斯 | M4(105)谢尔曼 |
| `M4A3(105) Sherman` | M4A3(105) 莫尔斯顿 | M4A3(105)谢尔曼 |
| `Sherman IIA/IIIAY/IVB 105` | 谢尔曼 | 谢尔曼IIA / 谢尔曼IIIAY / 谢尔曼IVB 105 |

「詹姆斯顿」「莫尔斯顿」「詹姆斯」都不是型号，是 `Sherman` 被逐字母机翻后的产物；`Sherman IIA` 这一族则相反——型号后缀整段被吃掉，显示成同一辆车。

### 10.4 族内一致（不改事实，只改写法）

- Stuart 一族：`斯图尔特` → `斯图亚特`（zh.wikipedia「M3/M5斯圖亞特坦克」），并统一补车种：`斯图亚特I型坦克`、`M3斯图亚特轻型坦克`、`M3A1/M3A3斯图亚特轻型坦克`、`斯图亚特侦察车`。
- Sherman 一族：`雪曼` 与 `谢尔曼` 并存 → 统一 `谢尔曼`（简体区习惯，且族内多数已是谢尔曼）。
- Lee 一族：`M3“李”`、`M3A3李式坦克` → `M3李坦克`、`M3A3李坦克`，`(late model)` 由「晚期型号」改「后期型」。
- 英制巡洋坦克：`“玛蒂尔达”II`、`“瓦伦丁”III`、`“丘吉尔”IV` → 去引号 + 补车种 `玛蒂尔达II型坦克`、`瓦伦丁III型坦克`、`丘吉尔IV型坦克`；`Grant` → `格兰特坦克`。
- 自行火炮三兄弟：`主教`→`主教式自行火炮`、`牧师`→`牧师式自行火炮`、`赛克森`→`司事式自行火炮`（zh.wikipedia 题名「塞克斯頓式自行火炮」，正文作「司事式」；Sexton 本义即教堂司事）。

### 10.5 有意保留原文的（未动）

`data/scenario_csv/translations/equipment.zh.jsonl` 里 `qa_status` 为 `kept`/`blocked` 的条目是**主动**保留英文的：`T-35`、`KV-85`、`LT vz.35`、`LT-38`、`L3/35`、`L6/40`、`M-11/39`、`M-13/40`、`M-15/42`、`P-26/40`、`R-2`、`R-35`、`T-38`、`T-3(n)`、`T-4(g)`、`T-4(h)`、`TACAM R-2`、`T.13 B`、`SU-76M`、`SU-85M`、`SU-57`、`Archer`、`Wolverine`、`BT-42`、`SU-122`、`SU-152`、`ISU-122`、`StuIG33B` 等。这一轮只修「已经译错」的，不给这些补译——补译需要逐条出处，属于下一批。

### 10.6 重建与验证

```
python integration\fix_equipment_names.py      # jsonl cells: 92; csv cells: 715; fixes: 1298
python integration\build_master_overrides.py   # master overrides: 5650
python mod\build_maps.py                       # Shelved 0/0; Packaged 72228; 9436434 bytes
python mod\complete_font.py                    # Completed glyph coverage: 2431
python integration\build_variants.py           # 四套 72228，缺字 0；zh-TW 改动 64812
python mod\finalize.py                         # 五道守卫 OK，92 files
python mod\publish.py                          # 11 文件，1.9.9，72228，校验通过
```

- 词典 72,228 条，键集未变（新增 0、删除 0），**改值 54 条**。
- zh-TW/HK/MO 三套按简体底本重新生成；字体 2,431 字形（新增「臼」等）。
- 活动槽 `payload/translations.bin` 已物化为 zh-CN，sha256 `78746DCBD167ED65…`；`WitE2CN.exe --selftest` exit 0、`SELFTEST PASS`（四套 9 MB OK）。

### 10.7 残留

- 英文保留的代号仍未译（见 §10.5），需要逐条出处再动。
- `Mk II AA`（英军）型号归属未定，继续保留。
- 覆盖层里另有 12 条设备名旧值（§9.6），仍按「随推进逐步改」处理。

## 11. 同日第七轮：整族推进（副油箱 / 炸弹 / 鱼雷 / 机枪）

### 11.1 「还剩多少族没清」的口径

| 数据面 | 族数 | 唯一名称 | 完全干净 | 剩余 |
|:--|--:|--:|--:|--:|
| `Devices.csv`（Type 0–30） | 28 | 1,066 | 14 | 14 |
| `Ground.csv`（GroundTypes 116 类） | 116 | 935 | 69 | 47 |
| `Aircraft.csv`（Type 0–13） | 11 | 798 | 11 | 0 |

四条判据：①未译（无词条，或译文与原文相同）；②族内同译碰撞（两个不同原名译成同一个中文）；③型号 token 丢失（先把 `mm/in/kg/lb/L` 归一化再比，避免把单位换算误判成丢型号）；④类型词不符（`AAMG` 必须出现「高射」等）。纯型号保留英文（`T-28`、`D2`、`KV-85`）不计缺陷，但同族写法必须一致。

### 11.2 副油箱族 80 条（重灾区）

`Drop Tank / Auxiliary Tank / Ferry Tank / Drum Tank` 里的 `Tank` 被机翻成「坦克」，全族 80 条无一正确：

| 原文 | 旧译 | 新译 |
|:--|:--|:--|
| `100 IG Drop Tank` | 100 IG 支援坦克 | 100英制加仑副油箱 |
| `1052 IG Auxiliary Tank` | 1052 支援坦克工程队 | 1052英制加仑副油箱 |
| `108/110 USG Drop Tank` | 第108/第110 | 108/110美制加仑副油箱 |
| `250 USG Auxiliary Tank` | 加仑辅助油罐车 | 250美制加仑副油箱 |
| `300 L Drum Tank` | 300升油桶坦克 | 300升桶形副油箱 |
| `170 IG Ferry Tank` | 170 IG 渡运坦克 | 170英制加仑转场副油箱 |

规则：`IG`=英制加仑、`USG`=美制加仑、`L`=升、`Ferry`=转场副油箱、`Drum`=桶形副油箱、`(Jet)`=（喷气式）；数量与单位之间不留空格，中文与型号之间保留一个空格。80 条全部由正则生成，无未匹配项。

### 11.3 炸弹 12 条、鱼雷 4 条、零散 3 条

- 炸弹：`GPHE`→通用高爆（5 条）、`MC`→中容量（3 条）、`HC`→高容量（2 条）、`12000lb DP Bomb`「深水炸弹」→「12000磅深侵彻炸弹」（DP=deep penetration，不是 depth charge）、`Hs 293` 补「滑翔炸弹」。
- 鱼雷：`450mm 45-36AV-A Torpedo` 旧译「水雷」→鱼雷、`533mm W 250 Torpedo` 旧译「W型250千克鱼雷」→「533毫米W 250鱼雷」、`550mm 24V/M` 旧译「24型鱼雷」→「24V/M」、`456mm Torpedo` 补「鱼雷」；另清掉「毫米」与「鱼雷」之间的多余空格。
- 零散：`Rifle-Grenade` 旧译「步骑」→「枪榴弹」；`7.62mm Maxim AAMG` 补全为「7.62毫米马克沁高射机枪」；`FuG 202 / FuG 212 / FuG 220 SN-2` 补「雷达」。

### 11.4 机枪族 60 条（BMG / CMG / TMG 必须分开）

`BMG/CMG/TMG` 分别是车体、同轴、炮塔机枪，旧译全部塌成同一个「维克斯机枪」，10 组同译碰撞：

| 原文 | 旧译 | 新译 |
|:--|:--|:--|
| `.303in Vickers BMG` | .303英寸维克斯机枪 | .303英寸维克斯车体机枪 |
| `.303in Vickers CMG` | .303英寸维克斯机枪 | .303英寸维克斯同轴机枪 |
| `.303in Vickers TMG` | .303英寸维克斯机枪 | .303英寸维克斯炮塔机枪 |
| `7.92mm MG42 TMG-RC` | 7.92毫米MG 42通用机枪遥控装置 | 7.92毫米MG 42遥控炮塔机枪 |

另有 4 条机翻硬伤借机修正：`7.5mm MAC 31 BMG`「机枪弹」、`7.92mm vz.26 BMG`「子弹制造机」（machine gun→machine tool）、`7.92mm vz.26 TMG`「持续火力机枪」、`7.92mm vz.37 BMG`「子弹机枪」。

高射机枪族 10 条统一写法：`AAMG` 一律「高射机枪」（原混用「防空机枪/高炮/同轴机枪」）、英寸口径一律 `.50英寸`（原 `0.5in`／`12.7毫米` 混用）、`1.1in`/`3in` 保留英寸不换算。零散 6 条：`2 Pounder Mk IX`（原「九型」）、`40mm 40/41M` 空格、三条 `Mle 1931/1936/1937` 空格、`160mm Stielgranate 41`（原「手榴弹筒41」）。

### 11.5 分层：两处必须同改的地方（本轮踩的坑）

1. **改了下层没改覆盖层**：`900 L Auxiliary Tank`（places 组）与 `.50in M2 Quad AAMG`（terms 组）在 `glossary/reference_overrides.json` 里仍是旧值，`Layer guard` 当场拦下（`override-vs-lower 3`→`1`→`0`）。改覆盖层后必须重跑 `integration/build_master_overrides.py`，否则 `master_overrides.json` 还是旧值。
2. **同一个键有两处权威**：`equipment_name_fixes.json` 里 v1.9.8 写的 `Jagdpanzer 38 Hetzer`=`38(t)“追猎者”坦克歼击车`、`Jagdpanzer IV/70(V)`=`四号坦克歼击车/70(V)`，每轮 `fix_equipment_names.py` 都会把第六轮 `unify_layers.py` 的裁决（`追猎者式坦克歼击车`／`四号坦克歼击车 IV/70(V)`）覆盖回去。处置：把 fix 表两条改成与 `reference_overrides.json` 一致。**教训：一个键只能有一个权威来源；fix 表与 unify 表各写一份，就会互相打架，且只有 `Layer guard` 能发现。**

### 11.6 重建与验证

`fix_equipment_names.py`（修订表 1,440→1,493）→ `unify_layers.py` → `build_master_overrides.py` → `build_maps.py`（**72,263 条** / 9,439,904 字节）→ `complete_font.py`（**2,432** 字形）→ `build_variants.py`（四套各 72,263、缺字 0、改动 0 / 64,864 / 64,850 / 64,850）→ `finalize.py`（Fragment / Art-path / Pending-source / Layer / Section-header / Nationality / Language / Integrity 全 OK）→ `publish.py`（11 文件、1.9.9、校验通过）→ 手工物化 zh-CN 活动槽（sha256 `EA914CC3816CAE9E…`）→ `WitE2CN.exe --selftest` exit 0、`SELFTEST PASS`。

### 11.7 剩余清单（下一轮起点）

**Devices 剩余 14 族**（括号内为启发式告警数，多数是日制「九三式/九六式」与昵称音译，属可接受写法，不算错）：

`Mine` 70（型号 14、碰撞 1）、`DepthCharge` 26（碰撞 3、型号 8）、`SurfaceRadar` 25（型号 8，`FuMO` 音译成「富莫」）、`DropTank` 80（碰撞 5：`Auxiliary/Drop` 同容量同译，属同义词，可保留）、`NavalAA` 43、`AAMG` 106、`Torpedo` 57、`HMG/Mortar` 44、`LMG/ATR` 39、`VehicleMG` 102、`SmallArms` 38、`DirectGun` 72、`Artillery` 136、`NavalGun` 97（以上各 1–5 条）。

真错集中在：`RMA/RMD Mine` 都译「遥控水雷」、`Sound Detector (A)/(J)` 都译「声探测器」、`WBD/WBF/WBG Depth Charge` 都译「深水炸弹发射器」——需要按字母后缀区分型号。

**Ground 剩余 47 类**，真错集中在单位名碰撞（都来自场景 CSV 底层的旧机翻，不是本轮引入）：

| 碰撞 | 涉及原名 |
|:--|:--|
| 丘吉尔 | `Churchill AVRE`、`Churchill I`、`Churchill V-CS`、`Churchill VIII-CS` |
| 克伦威尔 | `Cromwell I`、`Cromwell VI-CS`、`Cromwell VIII-CS` |
| 十字军 | `Crusader I-CS`、`Crusader III`；`Crusader II`、`Crusader II-CS` 均「十字军战士」 |
| 轻型坦克 | `LT vz.33`、`Tetrarch I` |
| 步兵班 | `Infantry Section`、`Infantry Squad`、`Rifle Section`、`Rifle Squad` |
| 工兵小队 | `Combat Engineer Squad`、`Engineer Squad`、`Sapper Squad` |

另有事实错误 `CV-33`→「战斗值33」（把 CV 当 combat value）、`A13 Mk II`→「马蒂尔达II型坦克」（A13 是巡洋坦克 Mk III/IV，不是玛蒂尔达）；以及 60 余个纯型号未译（`D2`、`T-28`、`KV-85`、`SU-85M`、`H-35`…），需按「型号保留拉丁 + 中文类别词」统一后再补。
