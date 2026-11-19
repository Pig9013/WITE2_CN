# Release v1.10.5（2026-11-19）

## 这次修好了什么

**生产表 `Port` 行显示英文**，玩家截图报上来的；顺带把 EXE 界面串全量复查了一遍。

1. **`Port` 为什么是英文。** 词典里根本没有独立的 `Port` 键。EXE 唯一的 `Port` 在 `0x5314a0`，同块依次是 `AFV production`（`0x5312e8`）、`Heavy Industry production`、`Manpower production`、`Fuel production`、`Oil production`、`Resource production`、`Synthetic Fuel production`、`Vehicle production`、`Armamanents production`、`Port`、`Rail`（`0x5314b8`）、`Railyard` … `Freight Lost`（`0x531618`）——生产表的行名块。同块其余行（`Railyard`=铁路场站、`Synthetic Fuel production`=合成燃料生产 等）都在词典里，只有被 `glossary/master_drops.json`（449 条「永不翻译」）剔除的几个漏成英文。这份名单是 v1.6.5 修地图黑格、v1.9.7 修小河消失之后拉起来的，把 `Port`、`Rail`、`Victory`、`Resource`、`Frozen` 等界面串一并误伤。
2. **同批补上 11 处界面英文**：`Rail`（生产行名）、`Resource` / `Resource:`、`Port:`、`Frozen`（单位状态）、`Victory`（顶栏菜单）、`Depot:` / `Snow:` / `Rail:` / `(AA:`（六角格信息短标签）、空运报错「Air base is more than 300% of it's capacity.」（原文含 `it's` 笔误）。
3. **顺手订正 17 个「Major=少校」误译。** v1.6.3 批量复用旧译时把 `Major` 接到军衔，胜利等级与河流一起中招：`AXIS MAJOR`=轴心国少校、`AXIS MINOR`=轴心小国、`ALLIED MAJOR`=盟军少校、`ALLIED MINOR`=盟军次要单位、`Soviet Major Victory`=苏联少校胜利、`Major River:`=少校河流:。胜利画面图例同块（`0x5bf35c` AXIS MAJOR、`0x5bf374` AXIS MINOR、`0x5bf390` AXIS DECISIVE、`0x5bf3ac` ALLIED MAJOR、`0x5bf3c8` ALLIED DECISIVE、`0x5bf3e8` D R A W=平局、`0x5bf3f8` ALLIED MINOR）与六角格信息（`0x5616a0` Major River:、`0x5616bc` Minor River:=小河）把语境钉死。

## 这次变了什么

- `glossary/addr_overrides.json` `entries` 新增 12 条（键是 RVA = 文件偏移 + `0x1200`）：`0x5326A0` Port→港口、`0x5326B8` Rail→铁路、`0x52E294` Resource→资源、`0x59CC70` Resource:→资源:、`0x58F3EC` Port:→港口:、`0x533788` Frozen→冻结、`0x5619B4` Victory→胜利、`0x562368` Depot:→补给站:、`0x562574` Snow:→积雪:、`0x562134` Rail:→铁路:、`0x562118` (AA:→(防空:、`0x52AD90` 空运报错→「空军基地已超过其容量的 300%。」。
- 为什么不进词典：`Port` / `Rail` 这类词同时是港口图块、铁路美术与数据键，词典级翻译会波及全游戏同名串。地址层由 `WitE2CN_Text.dll` 在查表前比对源串指针的 RVA，只改这一份字面量；未命中时行为与从前一致。字面量首尾空格按 EXE 原样保留（`  (AA:`、`Rail: `、`  Snow: ` 等），构建期 `verify_addr_sources` 逐条回读 EXE 校验。
- `glossary/reference_overrides.json` ui 组：新增 17 条 Major 相关订正（其中 `Minor River:` 三条与既有「尾部标点清理」条目重复，已并入原条目，不重复计数），`ui` 组 4,671 → 4,685 条；`master_overrides.json` 重生成 6,157 条。
- 词典 **74,501** 条（文本 74,489 + 12 条 `@@RVA` 地址键）；四语言包各 74,501 条、缺字 0；22 道守卫全过；checksums 125 条随发布重新生成。
- **没动**：单键 `Major`=少校（军衔语境）、`Draw`（`0x5d18c4` 语境未定，胜利屏用的是已译的 `D R A W`）、`1 of 1`（战斗界面页码）。

## 怎么看本版生效

- 启动器标题显示 `1.10.5` 即为本版（游戏主界面右下角版本号不变，仍是游戏自身的 1.0.5.02）。
- 生产界面：分区「特别工业（其他工业）」下的 `Port` 行显示「港口」，其下 `Rail` 行显示「铁路」；表头仍是 产能 / 受损 / 储备池 / 已建成 / 单位。
- 胜利画面图例：轴心国重大胜利 / 轴心国小胜 / 轴心国决定性胜利 / 盟军重大胜利 / 盟军决定性胜利 / 平局 / 盟军小胜。
- 六角格信息：地形行显示「大河」「小河」「无法通行」；短标签显示「(防空:」「铁路:」「补给站:」「积雪:」；城市信息行 `Resource` 显示「资源」。

## 复查记录

- `data/extracted/exe.jsonl` 6,034 条 EXE 界面串：词典命中 5,474、译文含中文 5,458、无中文 576；去掉语言代码、热键、`api-ms-*`/`oauth_*`、CSV 表头、文件名与编辑器字段码后，真正显示给玩家而仍英文的就是本次补的 12 处。
- 按既有铁律保留英文：编辑器/美术索引（`Hex Art`、`TOWN ART`、`RAIL ART`、`Terrain`、`Border`）、数据字段（`SupL`、`FuelN`、`MaxCmd`、`Hexes`、`Color`）、天气地形枚举（`Clear`、`Snow`、`Urban`、`Town`、`Factory`）、空军编制名（v1.10.2 既定）。
- 构建：`Address sources verified: 27`、`Address overrides: 27`、`Packaged 74,501`；`finalize.py` 22 道守卫全过、`Integrity metadata: 125 files`；`publish.py` 目标版本 1.10.5、条目 74,501、校验通过；安装目录 `--verify` 记 `OFFLINE VERIFY PASS`；活动槽 `payload/translations.bin` 物化为 zh-CN 变体（9,584,242 字节，sha256 `9AFA5302288C…`）。
- 本机未启动游戏（工程纪律），语境由 EXE 字符串表同块邻串与构建守卫静态复核。

---

版本：1.10.5 · 词典 74,501 条（文本 74,489 + 12 条地址键）· 四语言包缺字 0 · 22 道构建守卫 · 游戏版本 1.0.5.02
