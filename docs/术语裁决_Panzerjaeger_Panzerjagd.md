# Panzerjäger / Panzerjagd 术语裁决与项目内近义术语清点

- 项目：WITE2 中文汉化（WitE2_CN_repo）
- 日期：2026-11-03
- 结论状态：**已定裁决并落库**（2026-11-03 用户确认：Panzerjagd=坦克猎歼；Panzer-Zerstörer=反坦克）
- 证据等级：同时代条令/词典 > 战后编制史专著 > 游戏数据 > 网络文章（本次知乎文章 403，未采信）

---

## 0. 一句话结论

**Panzerjäger 与 Panzerjagd 不是同义词，但也不是「差异很大」到互不相干。**

- **Panzerjäger**＝「坦克猎人」：德国的**反坦克兵种／编制／装备类别**。指人（反坦克部队成员）、指单位（Panzerjäger-Abteilung，反坦克营）、指车（Panzerjäger I、Marder、Nashorn 这类自行反坦克炮）。
- **Panzerjagd**＝「猎坦克」：**任务／行动概念**，1945 年才大量用作**临时编组名**（Panzerjagd-Brigade 104、Panzerjagd-Abteilung、Panzerjagd-Kommando）。其部队或配 Jagdpanzer，或只拿 Panzerfaust 的猎坦克小队。

两者同属反坦克语义场，但**指称对象、词性、历史时段、装备指向都不同**，不能互译，更不能在词典里合并成同一个中文词。项目现状恰恰是合并了：两个不同的 OB 都译成「坦克歼击营」。

### 0.1 最终裁决（2026-11-03 用户确认）

| 英文 | 定译 | 说明 |
|---|---|---|
| Panzerjaeger | 坦克歼击 | 兵种/编制通名，不变 |
| Panzerjagd | **坦克猎歼** | 1945 年猎坦克编组，与上者分层 |
| Panzer Destroyer / Panzer-Zerstörer | **反坦克** | 属步兵、装备 Panzerschreck，不是装甲兵 |
| HJ Panzer Destroyer | **希特勒青年团反坦克** | HJ-Panzerschreckabteilung |
| Jagdpanzer | 坦克歼击车 | 统一定型 |
| Panzerschreck | 反坦克火箭筒 | 与铁拳区分 |
| Panzerfaust | 铁拳反坦克榴弹 | 非火箭筒 |

落库位置：glossary/reference_overrides.json（terms 18 条）、glossary/designations.py:171/258、
data/scenario_csv/translations/{unit,equipment,leader}.zh.jsonl、build/scenario_csv_zh/*/*.zh.csv。


---

## 1. 构词与语义

| 词 | 构词 | 词性 | 字面 | 军事义 |
|---|---|---|---|---|
| Panzerjäger | Panzer + Jäger（猎人，施事名词） | 名词（人／单位／装备名） | 坦克猎人 | 反坦克兵种；反坦克营；自行反坦克炮 |
| Panzerjagd | Panzer + Jagd（狩猎，动作／事件名词） | 名词（事／行动） | 猎坦克 | 反坦克作战；1945 年猎坦克编组 |

德语构词对立很干净：**-jäger 是「谁来做」，-jagd 是「做这件事」**。这跟 Jäger（猎兵）／Jagd（狩猎）的对立同源。

> 注意：WitE2 的英文串用 ASCII 转写 Panzerjaeger，不是另一个词；ae 就是 ä。

---

## 2. 文献证据

### 2.1 TM 30-506《German Military Dictionary》（美国陆军部，1944）

这是同时代最直接的官方对译，词条把 Panzerjäger 的语义钉死在「反坦克」上：

- **Panzerjäger** m — *member of antitank unit.*（反坦克部队成员）
- **Panzerjägerabteilung** f — *antitank battalion.*（反坦克营）
- **Panzerjägergeschütz** n — *antitank gun.*（反坦克炮）
- **Panzerjägerkanone** f — *See Panzerjägergeschütz.*（即反坦克炮）
- **Panzerjägerkompanie** f — *antitank company.*
- **Panzerjägerregiment** n — *antitank regiment.*
- **Panzerjägerzug** m — *antitank platoon.*
- **Panzerabwehr** — *antitank defense, antimechanized defense (in compounds, **now superseded by Panzerjäger-**).*（Panzerabwehr- 复合词已被 Panzerjäger- 取代）
- **Panzerabwehrkanone** — *antitank gun (**now called Panzerjagerkanone**).*
- **tank destroyer gun** — *Panzerjägergeschütz.*
- **Tank Destroyer School** — *Panzerjägerschule.*

同一词典里：

- **Panzer** m — *armor; tank.*（装甲；坦克——一词二义，这解释了后面「装甲Ib型」的错误）
- **Sturmgeschütz** n — *assault gun (self-propelled).*（突击炮，不是歼击车）
- **Panzergrenadier** m — *armored infantry rifleman...*
- **Panzergrenadier-Division** — *motorized division.*

**关键负证据**：该词典**没有 Panzerjagd 词条**，也没有 Panzerzerstörer、Jagdpanzer 词条。1944 年的官方词典尚未把「猎坦克」当作标准军语收录，这与 Panzerjagd 作为 1945 年新编组名的历史时间线一致（见 2.2）。

> 出处：TM 30-506, War Department, 1944（本机文本版 文献库/02_德军编制/TM 30-506 ... .txt，按词条检索；无页码，引用词条名）。

### 2.2 Tessin《Verbände und Truppen der deutschen Wehrmacht und Waffen-SS 1939–1945》

Tessin 把三者放在**同一章（III. Panzerjäger）的不同节**里，这本身就是最清楚的分类证据：

- **§4 Umbenennung in Panzerjäger-Abteilungen**（S.178）
  Panzerabwehr-Abteilung → Panzerjäger-Abteilung 的改名。说明 Panzerjäger 是**原有反坦克兵的正式续名**，不是新兵种。
- **§6 Panzerjäger als Heerestruppen**（S.179）
  独立重型反坦克营（Nashorn、Ferdinand/Elefant、Jagdpanther、Jagdtiger）。
- **§7 Panzerjagdverbände und -einheiten; Panzer-Zerstörer-Bataillone**（S.179–180）
  这是全章唯一把 **Panzerjagd** 单列的节：

  > "Die **Panzerjagd-Brigade 104** mit 6 **Panzerjagd-Abteilungen** (jede Abt. mit 2 **Panzerjagd-Kompanien** zu 14 **Jagdpanzern** und einer Pz.Aufklärungs-Kompanie) wurde am 24. 1. 1945 aufgestellt. Die später aufgestellten **Panzerjagd-Verbände** bestanden aus selbständigen **Panzerjagd-Kommandos** unter Führung eines jungen Offiziers mit wenigen Mannschaften, die mit **Panzer-Nahkampfmitteln** ausgerüstet waren."

  译文：第 104 猎坦克旅下辖 6 个猎坦克营（每营 2 个猎坦克连，每连 14 辆歼击坦克，另 1 个装甲侦察连），1945 年 1 月 24 日组建。后来组建的猎坦克部队由独立猎坦克指挥部组成，由一名年轻军官带少量士兵，装备**近战反坦克器材**（即 Panzerfaust 一类）。

  > 紧接一句："Die **Panzerzerstörer-Bataillone** gehörten **nicht zur Panzerwaffe, sondern zur Infanterie**..."（坦克破坏营**不属于装甲兵，而属于步兵**），并且自 1943 年秋起由解散步兵师的反坦克单位编成。

**这段文献同时解决三个问题**：
1. Panzerjagd 是 1945 年才成建制的**新编组名**，与 1940 年就存在的 Panzerjäger 不同层。
2. Panzerjagd 部队的装备跨度很大：既有 14 辆 Jagdpanzer 的正规连，也有只拿 Panzerfaust 的突击小队。
3. **Panzer-Zerstörer 是步兵**，不是装甲兵——把它译成「装甲歼击营」在兵种上就错了。

### 2.3 TM-E 30-451《Handbook on German Military Forces》（1945-03-15）

- **"i. TANK DESTRUCTION BATTALION (Panzerzerstörer Bataillon). This battalion is equipped with bazookas and other infantry antitank weapons."**（PDF p.139；OCR 原文作 Panzerverstürer，按 Tessin 正字）
  → 美军官方把 Panzer-Zerstörer 译作 **Tank Destruction Battalion**，不是 Tank Destroyer Battalion；装备是巴祖卡一类步兵反坦克武器。
- **"Bazooka battalions (Panzerschreckabteilungen) have recently been formed from HJ personnel."**（PDF p.210）
  → 希特勒青年团的 "Panzer Destroyer" 部队实际是 **Panzerschreckabteilung**（反坦克火箭筒营），与装甲无关。
- **"a generous allotment of bazookas and rocket antitank pistols"**（PDF p.154）
  → 同时代美军文件明确区分 **bazooka（Panzerschreck，火箭筒）** 与 **rocket antitank pistol（Panzerfaust，反坦克手枪/铁拳）**，两者不是一种东西。

### 2.4《Order of Battle of the German Army》（1944）

- **"Panzerzerstorer Kompanie (antitank rifle company). — Equipped with 36 antitank rifles (Panzerbüchsen)."**（printed p.71）
  → 1943–44 年的 Panzerzerstörer-Kompanie 是**反坦克枪连**，连「反坦克炮」都不是。这说明该词在不同年份指向不同编制，按字面「坦克破坏者」直译会误导。
- **"Panzerjagerabteilung (antitank battalion)"**（printed p.72–73）
  → 同一本书把 Panzerjäger 稳定对译为 antitank battalion。

### 2.5 Niehorster《German WWII Organizational Series》vol. 3/5（2010）

装备分类的英文对译非常清楚：

- **Panzerjäger 38(t), Ausf. H für 7,5cm Pak — "self-propelled antitank gun on Pz-38(t) chassis « Marder III »"**（PDF p.81）
- **Jagdpanzer 38 — "light tank destroyer on Pz-38(t) basis « Hetzer »"**（PDF p.82）
- **Jagdpanzer IV — "self-propelled heavy antitank gun on Pz-IV basis « Jagdpanzer IV »"**（PDF p.82）
- **Jagdpanzer V — "tank destroyer on Panther basis « Jagdpanther »"**（PDF p.83）
- **Panzerjäger Tiger (P) für 8,8cm Pak 43 (Ferdinand) — "self-propelled, heavy antitank gun on prototype Pz-VI chassis"**（PDF p.83）

→ **Panzerjäger 车族＝自行反坦克炮（多为敞篷、临时底盘）；Jagdpanzer 车族＝封闭战斗室的歼击坦克。** 英文都叫 tank destroyer，德文是两类。

---

## 3. WitE2 内的装备指向（实测数据）

数据源：mod/runtime/Dat/CSV/1941 Campaign/OBs.csv、Ground.csv。

### 3.1 Panzerjaeger 系（OB 177–230）

| OB ID | Suffix | 年代 | 主要装备 |
|---|---|---|---|
| 177/179/183 | SP Panzerjaeger Battalion（41a/41b/41c PzJ-I） | 1941 | 27× Panzerjaeger I（47mm 自行反坦克炮） |
| 180/181 | SP Panzerjaeger Battalion（42/43 PzJ-II） | 1942–43 | 9× Panzerjaeger II + 12–18× 50mm Pak38 |
| 184/185 | SP Panzerjaeger Battalion（42/43 38(t)） | 1942–43 | 9× Panzerjaeger 38(t) + 12–18× 75mm Pak40 |
| 199/201/202/204 | SP Panzerjaeger Battalion（Marder） | 1942–43 | 18–45× Marder II/III |
| 205 | SP Heavy Panzerjaeger Battalion（Ferdinand） | 1943 | 45× Ferdinand |
| 206 | SP Heavy Panzerjaeger Battalion（Nashorn） | 1943 | 45× Nashorn |
| 208/209 | SP Heavy Panzerjaeger Battalion（Jagdpanther） | 1944 | 45× Jagdpanther |
| 210 | SP Panzerjaeger Battalion（Hetzer） | 1944 | 45× Jagdpanzer 38 Hetzer |
| 213 | SP Heavy Panzerjaeger Battalion（Jagdtiger） | 1945 | 45× Jagdtiger |
| 193–235 | Mot. Panzerjaeger Battalion | 1941–44 | 27× 50mm Pak38、36× 88mm Pak43、75mm Pak40 等牵引/自行混编 |

**指向**：Pak 反坦克炮 + 敞篷自行反坦克炮（Marder/Nashorn/Panzerjaeger I/II/38(t)）+ 后期重型歼击坦克。与 TM 30-506 "antitank battalion"、Niehorster "self-propelled antitank gun" 完全对应。

### 3.2 Panzerjagd 系（OB 215/216，仅 1945）

| OB ID | Suffix | 年代 | 主要装备 |
|---|---|---|---|
| 215 | Mot. Panzerjagd Battalion（45a） | 1945-01 | 9× PzGren Squad 45、4× Panzer Pioneer Squad 45、8× SdKfz-251/21、**14× Jagdpanzer 38 Hetzer、31× StuG IIIg** |
| 216 | Mot. Panzerjagd Battalion（45b） | 1945-01 | 同上，但 **31× Jagdpanzer 38 Hetzer**，无 StuG |

**指向**：1945 年混编自行突击炮/歼击坦克营，配装甲掷弹兵与装甲工兵。与 Tessin §7 的 Panzerjagd-Brigade 104（Jagdpanzer 连）同型；不是牵引反坦克炮营。

### 3.3 "Panzer Destroyer" 系（OB 232/233）

| OB ID | Suffix | 年代 | 主要装备 |
|---|---|---|---|
| 232 | Panzer Destroyer Battalion | 1943-10 | **54× Panzerschreck Team**，15× Support；无任何车辆 |
| 233 | HJ Panzer Destroyer Battalion | 1945-01 | 18× Sturm Squad 45、**54× Panzerschreck Team**，17× Support；无任何车辆 |

**指向**：纯步兵反坦克部队，装备是 Panzerschreck（火箭筒），与 Tessin §7 "Panzerzerstörer-Bataillone 属步兵"、TM-E 30-451 "bazookas and other infantry antitank weapons"、1945 手册 "Panzerschreckabteilungen from HJ personnel" 三条独立证据完全吻合。

**结论：把它译成「装甲歼击营/装甲歼灭营」是装备指向和兵种指向的双重错误。**

### 3.4 装备名（Ground.csv / equipment.zh.jsonl）

| 英文 | 现译 | 判定 |
|---|---|---|
| Panzerjaeger I | 坦克歼击车I | 基本可用 |
| Panzerjaeger II | 坦克歼击车II | 基本可用 |
| Panzerjaeger 38(t) | 坦克歼击车 38(t) | 基本可用 |
| Panzerjaeger 35R(f) | 坦克歼击车 35R(f) | 基本可用 |
| Jagdpanzer IV | 歼击坦克 IV型 | 词序与上不一致 |
| Jagdpanzer 38 Hetzer | 歼击坦克38追猎者 | 词序不一致；「追猎者」是 Hetzer 的意译，可保留 |
| Jagdpanzer IV/70(V) | 歼击坦克 IV/70(V) | 词序不一致 |
| Panzer Ib | 装甲Ib型 | **错**：型号名不应拆成「装甲」 |
| Panzer IIc | II型C型装甲车 | **错**：语序与型号体例都乱 |
| Panzerschreck | 坦克杀手火箭筒 | 与 Panzerfaust 混 |
| Panzerfaust | 铁拳反坦克火箭筒 | **错**：Panzerfaust 不是火箭 |

---

## 4. 裁决

### 4.1 差异在哪里（「差异很大」到底大不大）

| 维度 | Panzerjäger | Panzerjagd | 差异 |
|---|---|---|---|
| 构词 | -jäger（人） | -jagd（事） | 大 |
| 指称 | 兵种／编制／装备类别 | 任务／行动；1945 年编组名 | 大 |
| 出现时间 | 1940 年前后取代 Panzerabwehr- | 1945 年大量用作部队名 | 大 |
| 装备 | Pak、Marder、Nashorn、Jagdpanther… | Jagdpanzer、StuG、Panzerfaust 小队 | 部分重叠 |
| 上位概念 | 反坦克 | 反坦克 | 相同 |

**裁决：属于「同族不同类」，不是同义词；「差异很大」这个说法方向对，但程度被夸大了——两者不是无关，而是同一反坦克体系里的两个层级。**

### 4.2 建议译名

| 英文／德文 | 现译 | 建议 | 理由 |
|---|---|---|---|
| Panzerjaeger / Panzerjäger | 坦克歼击 | **坦克歼击**（不变） | 兵种／编制通名，项目已统一；现存 507 处「坦克歼击营」里混有 Panzerjagd，需按源区分 |
| Panzerjagd | 坦克歼击 | **坦克猎歼** | 与上者区分；对应「猎坦克」的任务义；1945 年编组 |
| Panzer Destroyer / Panzer-Zerstörer | 装甲歼击 | **反坦克** | 该部属步兵、装备 Panzerschreck，不是装甲兵 |
| HJ Panzer Destroyer | 装甲歼灭 | **希特勒青年团反坦克** | 同上，并统一「歼击」 |
| Jagdpanzer（装备） | 歼击坦克 | **坦克歼击车** | 统一词序，与 Panzerjaeger 装备同族 |
| Panzerschreck | 坦克杀手火箭筒 | **反坦克火箭筒** | 与 Panzerfaust 区分 |
| Panzerfaust | 铁拳反坦克火箭筒 | **铁拳反坦克榴弹** | 无后坐力抛射破甲弹，不是火箭 |
| US Tank Destroyer Battalion | 美军歼击坦克营 | **美军坦克歼击营** | 统一词序 |
| Destroyer Anti-Tank（苏军） | 反坦克歼击车旅 | **反坦克歼击旅** | 该旅无「车」 |
| FF Tank Destroyer Regiment | 快速反应歼击坦克团 | **自由法国坦克歼击团** | FF=Free French（Nations.csv ID 22） |

> 最终采用「坦克猎歼」。项目语料里的「坦克猎杀」（corpus/TTW_Exclusive_Rules_Living_zh_CN/full.txt 第 1708、1716 行）只作语义参考，不再作为定译。

---

## 5. 项目内近义／同义术语清点

### 5.1 真同义（历史改名，可互译）

| 组 | 关系 | 证据 | 处理 |
|---|---|---|---|
| Panzerabwehrkanone = Panzerjägerkanone | 同一武器改名 | TM 30-506: "now called Panzerjagerkanone" | 统一译「反坦克炮」 |
| Panzerabwehr-Abteilung = Panzerjäger-Abteilung | 同一编制改名 | Tessin §4 "Umbenennung" | 统一译「反坦克营」 |
| Panzerabwehr- 复合词 = Panzerjäger- 复合词 | 构词替换 | TM 30-506: "now superseded by Panzerjäger-" | 按 Panzerjäger 处理 |

### 5.2 近义（同族不同类，不可互译）

| 英文（WitE2） | 德文 | 现译 | 判定 | 建议 |
|---|---|---|---|---|
| Panzerjaeger | Panzerjäger | 坦克歼击 | 正确（通名） | 保留 |
| Panzerjagd | Panzerjagd | 坦克歼击 | **混同** | 坦克猎歼 |
| Panzer Destroyer | Panzer-Zerstörer | 装甲歼击 | **误译（兵种错）** | 反坦克 |
| HJ Panzer Destroyer | HJ-Panzerschreckabteilung | 装甲歼灭 | **误译（兵种+用词）** | 希特勒青年团反坦克 |
| Jagdpanzer | Jagdpanzer | 歼击坦克 | 不统一 | 坦克歼击车 |
| StuG / Stug | Sturmgeschütz | 突击炮 | 正确（不是歼击车） | 保留 |
| Pak | Panzerabwehrkanone | 反坦克炮 | 正确 | 保留 |
| Tank Destroyer（美军） | — | 歼击坦克营 | 词序不统一 | 坦克歼击营 |
| Destroyer Anti-Tank（苏军） | истребительная ПТ | 反坦克歼击车旅 | 多「车」 | 反坦克歼击旅 |
| FF Tank Destroyer | — | 快速反应歼击坦克团 | FF 误读 | 自由法国坦克歼击团 |

### 5.3 假朋友（形近义异，最容易错）

| 词 | 字面陷阱 | 实际 | 证据 |
|---|---|---|---|
| Panzer | 总被译「装甲」 | 也可指「坦克」 | TM 30-506: "armor; tank" |
| Panzer-Zerstörer | 看似「装甲歼击/坦克歼击车」 | 步兵反坦克部队（Panzerschreck/反坦克枪） | Tessin §7；TM-E 30-451 p.139；1944 OOB p.71 |
| Panzerjagd | 看似 Panzerjäger 的变体 | 任务名/1945 编组 | Tessin §7 |
| Jagdpanzer | 与 Panzerjäger 混 | 封闭战斗室歼击坦克 | Niehorster p.81–83 |
| "Destroyer"（苏军） | 看似「驱逐舰/驱逐」 | истребительная＝歼击 | 苏军 ИПТАБр 编制 |
| FF | 被读成 fast/fast reaction | Free French 自由法国 | Nations.csv ID 22 |

### 5.4 相邻但不必改的

| 组 | 现状 | 说明 |
|---|---|---|
| Panzer（编制名） | 装甲营/装甲师 | 兵种义，正确；只改装备名里的「装甲Ib型」 |
| Panzergrenadier / Mot. Infantry / Schützen | 装甲掷弹兵/摩托化步兵/步兵 | 基本一致；仅 2 处「汽车化步兵」应统一为「摩托化步兵」 |
| Sturmgeschütz / Sturmpanzer | 突击炮/突击坦克 | 正确，不与 Jagdpanzer 混 |
| Jaeger / Grenadier / Volksgrenadier | 猎兵/掷弹兵/国民掷弹兵 | 正确 |

---

## 6. 针对性文献复核结论（按家族）

1. **反坦克家族**：Panzerjäger 是 1940 年前后取代 Panzerabwehr- 的正式兵种名，Panzerjagd 是 1945 年编组名，Panzer-Zerstörer 是步兵反坦克部队——三者层级不同，不能合并。**依据：TM 30-506；Tessin §4/§7；TM-E 30-451 p.139；1944 OOB p.71。**
2. **车辆家族**：Panzerjäger 车＝自行反坦克炮，Jagdpanzer＝歼击坦克，StuG＝突击炮。英文都叫 tank destroyer，但德文是三类。**依据：Niehorster p.81–83；TM 30-506 "Sturmgeschütz: assault gun"。**
3. **武器家族**：Panzerschreck 是火箭筒，Panzerfaust 是抛射破甲弹；Pak 1944 年改名 Panzerjägerkanone。**依据：TM-E 30-451 p.154/210；TM 30-506。**
4. **装甲/步兵家族**：Panzer 一词二义（装甲/坦克）；Panzergrenadier 是装甲步兵，不是「装甲掷弹兵」以外的新兵种；Schützen 是旧称。**依据：TM 30-506 词条。**
5. **游戏数据自证**：WitE2 的 232/233 OB 没有任何车辆，只有 54 个 Panzerschreck 小组；215/216 OB 是 1945 年 Hetzer/StuG 混编。**数据与文献互相印证，不是猜测。**

---

## 7. 下一步工作

### P0（已实施，2026-11-03）

1. **Panzerjagd → 坦克猎歼**：改 glossary/designations.py:171，并在 glossary/reference_overrides.json 的 terms 增加 "Panzerjagd": "坦克猎歼"；同步 data/scenario_csv/translations/unit.zh.jsonl 的 Mot. Panzerjagd Battalion。
2. **Panzer Destroyer Battalion → 反坦克营**；**HJ Panzer Destroyer Battalion → 希特勒青年团反坦克营**。
3. 重新生成 build/scenario_csv_zh/*/OBs.zh.csv，确认：
   - 「摩托化坦克猎歼营」出现次数＝Panzerjagd 实际行数（当前 13 个场景文件，共 26 行）；
   - 「装甲歼击营」「装甲歼灭营」＝0；
   - 「摩托化坦克歼击营」中属于 Panzerjaeger 的行**保持不变**（重建前 195 行是两者混在一起；重建后「坦克猎歼营」26 行，其余「坦克歼击营」676 行归 Panzerjaeger）。

### P1（同批做，统一体例）

4. Jagdpanzer* → **坦克歼击车**（与 Panzerjaeger 装备同族；Jagdpanzer 38 Hetzer 可作「38型坦克歼击车 追猎者」）。
5. Panzerschreck → **反坦克火箭筒**；Panzerfaust → **铁拳反坦克榴弹**。
6. US Tank Destroyer Battalion → **美军坦克歼击营**；Destroyer Anti-Tank Brigade/Regiment → **反坦克歼击旅/团**；FF Tank Destroyer Regiment → **自由法国坦克歼击团**。
7. 两处「汽车化步兵」→「摩托化步兵」。

### P2（装备名系统性修复，单独一轮）

8. Panzer Ib → **I号B型坦克**；Panzer IIc → **II号C型坦克**；Panzer 38(t) 等按「号型」体例统一。根因是 designations.py 把 Panzer 一律映射成「装甲」，而装备名需要「〔罗马数字〕号〔字母〕型坦克」的独立规则；glossary/ww2_military_en_zh.csv 只有 Panzer IV/III/II 精确条目，覆盖不到 Ib/IIc 等变体。

### 实施路径（按 skill 纪律）

    改 glossary/designations.py + reference_overrides.json(terms) + equipment.zh.jsonl/unit.zh.jsonl
      → python integration/build_master_overrides.py
      → python build_maps.py（或项目现有构建入口）
      → python mod/publish.py
      → 静态审计：grep 上述字符串 + checksums + 字体覆盖
      → 用户实机验证（不由我启动游戏）

### 验收判据

- grep -c "摩托化坦克猎歼营" = 26（13 个场景 × 2 个 OB）；
- grep "装甲歼击营\|装甲歼灭营" = 0；
- grep "歼击坦克" = 0（若采纳 P1 统一）；
- grep "装甲Ib型" = 0（若采纳 P2）；
- Panzerjaeger 的 676 处「坦克歼击营」不得误伤；
- package.json mod_version 递增，translations.bin 哈希与安装目录一致。

---

## 8. 实施记录（2026-11-03）

| 项 | 结果 |
|---|---|
| 术语覆盖 | reference_overrides terms 新增 18 条；designations.py 两处 token |
| 词典 | 72,642 条（重建后） |
| 字体 | 覆盖 2,416 字，缺字 0 |
| checksums | 26 个文件 |
| 「摩托化坦克猎歼营」 | 26 行（13 场景 × 2 OB） |
| 「装甲歼击营」「装甲歼灭」 | 0 |
| 「坦克歼击营」 | 676 行（Panzerjaeger 保留） |
| 「歼击坦克」 | 0（统一为坦克歼击车） |
| 人名修复 | 88 条：常用词误译 10、未译 41、von 残留 22、片段/过短 15 |

人名修复的典型项：Model=莫德尔、Student=施图登特、Son=松（旧「儿子」）、Major=马约尔、Bull=布尔、Hunter=亨特、Price=普赖斯、Old=奥尔德、Down=唐、Geloso=杰洛索。

构建守卫：UI 标签优先于场景 CSV。军衔 Major 仍为「少校」，人名 Major 在 Leaders.csv 为「马约尔」，两者不再互相覆盖。

已知未做：P2 装备名（装甲Ib型/II型C型装甲车）尚未系统修复；GameEvents.csv 有 10 条 extra 列审计告警，待复核（非本次改动引入）。

## 附录 A：文献清单（本机路径）

| 文献 | 本机路径 | 用途 |
|---|---|---|
| TM 30-506 German Military Dictionary (1944) | 文献库/02_德军编制/TM 30-506 ... .txt | 词条对译；Panzerjäger/Panzerabwehr/Sturmgeschütz |
| Tessin, Verbände und Truppen... | 文献库/02_德军编制/Tessin G. ... .txt | §4/§6/§7 编制史；Panzerjagd/Panzer-Zerstörer |
| TM-E 30-451 Handbook on German Military Forces (1945) | 文献库/02_德军编制/USWarDept_1945_HandbookGermanMilitaryForces.pdf | p.139/154/210 |
| Order of Battle of the German Army (1944) | 文献库/02_德军编制/USWarDept_1944_OrderOfBattleGermanArmy.pdf | p.71–73 |
| Niehorster, German WWII Organizational Series vol.3/5 (2010) | 文献库/02_德军编制/Niehorster_2010_...pdf | p.81–83 车辆分类 |
| WitE2 数据 | mod/runtime/Dat/CSV/1941 Campaign/OBs.csv、Ground.csv、Nations.csv | 装备指向 |

## 附录 B：核查方法（可复现）

- OBs：python 读 OBs.csv，按 Suffix 过滤 Panzerjagd|Panzerjaeger|Destroyer，展开 Slot1–32/Qty1–32，用 Ground.csv 的 ID→Name 还原装备名。
- 装备：Ground.csv 过滤 Panzer|Jagd|StuG|Pak|Marder|Hetzer，对照 data/scenario_csv/translations/equipment.zh.jsonl。
- 文献：TM 30-506 按词条正则；Tessin 按 Panzerjagd|Panzerzerst 行号；PDF 用 PyMuPDF 逐页 get_text() 检索并记录 PDF 页码。
- 未使用：知乎文章（https://zhuanlan.zhihu.com/p/1934939686419305857）返回 403，未能读取；其无文献引用，按用户要求不作为裁决依据。如需要，可把正文贴给我，我再做一次对照。

## 附录 C：本次未能核实的事项

- Panzerabwehr- → Panzerjäger- 的**具体命令日期**：TM 30-506 与 Tessin §4 只证明「改名」事实，未给出统一日期；本报告只写「1940 年前后」，不写具体日。
- 1945 年 Panzerjagd-Bataillon 的**标准 KStN 编号**：Tessin 只给编组描述，未给 KStN；游戏 OB 的 31 辆 StuG/31 辆 Hetzer 属游戏抽象，未逐条对 KStN。
- 知乎文章的具体论点：未能读取，未评论。