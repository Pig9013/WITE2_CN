# Release v1.9.21（2026-11-19）

## 这次修好了什么

**「可用航空作战群」列表为空——修好了。** 空中指挥部 →「空中指令设置」面板下方那一栏，从 1.9.15 起一直一行都没有；英文原版有。

根因不在数据、不在字体、也不在绘制：引擎载入剧本时会把航空作战群（AOG）的名字交给本地化并**缓存进对象**，而面板筛选时比对的是航空队（Unit）的**原始英文名**——引擎按字符串比，名字一译成「第4航空队」，就永远等不上「Luftflotte 4」，每一行在取文字之前就被滤掉了。

修法：把 13 个剧本 `AOGs.csv` 里的 **612 个 AOG 名字钉死为原文**（恒等条目），并新增第 22 道构建守卫——谁再把这些名字译出来就拒绝发布。

顺带修好的：

- 「已分配空中指令 11 (8) / 上限 32」「自动（任务 193 / 护航 0）」这类引擎现场拼接、带数字的行终于能译了。
- GUI 旗标与边框图不再丢：`-red` / `-white` / `-green` / `red` / `white` 会被拼进图片文件名，翻译后变成中文路径、引擎静默丢图；现按源串地址原样返回。
- 文本钩子的诊断日志：计数改为按「不同源串」去重（上限 10 万，以前被地图标签每帧刷爆）、修正 rva 偏移、`native.log` 到 8 MB 自动轮转。

## 这次变了什么

- 词典 **74,478 条**（键数不变）：与上一版逐键比对，只有这 612 个 AOG 名字的值变化，无新增、无删除、无其它改动。
- **已知代价**：AOG 名字与航空队/航空军 HQ 的单位名是同一个词典键，每个剧本约 **24 个** HQ 名（`Luftflotte 1/2/4`、`I Fliegerkorps`、`1st Royal HAF Field Bde` 等）在其余界面也显示原文；分组表头（`**** 德国 ****`）仍是中文。
- 新增 `integration/gen_aog_identity.py` 与 `glossary/aog_identity.json`；`mod/build_maps.py` 增加 AOG 名字钉死层，`mod/finalize.py` 增加第 22 道守卫。
- 新增诊断开关（只用于排查，不随包发布）：`mod\logs\passthru.on`（全界面回退英文做 A/B）、`mod\logs\bypass.txt`（按前缀逐族放行）、`mod\logs\trace.on`（记录每次查表）。
- 构建：词典 74,478 条 / 9,583,406 B；字体 2,448 字形；四语言包各 74,478 条、缺字 0；finalize EXIT 0（22 道守卫、MapText 69,481 四包全中、百科四表与游戏原版逐字节一致、Integrity 125 files）；publish 校验通过。

## 怎么看某个游戏版本行不行

- 启动器标题显示 `1.9.21` 即为本版；启动后看 `mod\logs\native.log`：应出现 `addr overrides: 8`、`addr skips: 5`、`AOG identity pins: 612/612`。
- 游戏打补丁后仍不拒绝启动：接入失败就以英文运行，存档与补丁不受影响。
- 装新 DLC 后如果某个剧本的「可用航空作战群」又空了，重跑 `python integration\gen_aog_identity.py` 再构建（DLC 剧本的 `AOGs.csv` 在加密 `.scn` 里，扫描不到）。

## 附件

- `terms-and-designations.xlsx`：术语与番号总表
- `reference-table.xlsx`：权威对照表
- `encyclopedia-v1.6.0.docx`：百科中文版（游戏外阅读，1,178 条）
- `aog-list-empty-audit-v1.9.21.md`：可用航空作战群列表为空的完整排查记录（根因、证据链、修复与限制）
- `aog-window-audit-v1.9.18.md`、`addr-overrides-audit-v1.9.17.md`：此前两次同类排查的存档

---

版本：1.9.21 · 词典 74,478 条 · 四语言包缺字 0 · 22 道构建守卫 · 游戏版本 1.0.5.02
