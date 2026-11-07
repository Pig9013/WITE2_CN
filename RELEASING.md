# 发布流程（维护者用）

每次发版都按这个顺序走，版本号与说明就不会乱。

## 1. 改代码 / 改译文

- 启动器与钩子源码在 mod/src/；改完启动器用 mod/build_launcher.cmd 编译。
- 改完 payload 里任何文件，必须在 mod/ 目录跑一次 python finalize.py 刷新 payload/checksums.json，否则用户侧会报「汉化包文件缺失或损坏」。
- 改了简体译文后，繁体三套必须重生成，顺序固定：`python integration\fix_equipment_names.py`（改过 `equipment_name_fixes.json` 时）→ `python integration\unify_layers.py`（改过 `layer_unify.json` 时）→ `python integration\fix_airgroup_staffel.py`（改过 AirGroups/AirGroupRenames 场景表时；`--check` 出口 2）→ `python mod\build_maps.py` → **`python mod\complete_font.py`** → `python integration\build_variants.py` → `python mod\finalize.py` → `python mod\publish.py`。
  - `complete_font.py` 不能省：`build_maps.py` 会用 `build/WitE2CN.ttf`（旧子集字体）覆盖 payload 字体，不补字则 `build_variants.py` 报「字体仍缺字」直接失败（v1.9.7 实测缺 74 字）。它从系统字体补缺并落回 payload，缺字 0 才继续。
  - 改了 `glossary/reference_overrides.json` 或 `manual_translations.json` 时，先跑 `python integration\build_master_overrides.py` 重生成覆盖层：`master_overrides.json` 是生成物，手改会在下次生成时丢失；生成器会与 `master_drops.json` 交叉核对，发现「已丢弃的键又回到覆盖层」直接失败。
- 改了分组表头（`*** 名称 (n) ***`）或 `Section-header guard` 报错时，先跑 `python integration\fix_section_headers.py`：它按原文星号形状重建 `build/scenario_csv_zh/*\*.zh.csv` 的文本列并同步 `data/scenario_csv/translations/*.jsonl`。只改字典不改 CSV，下次 `build_maps.py` 会从 CSV 重建出旧值（同一个表头在 14 个剧本里各占一格，v1.9.9 实测 34 键 = 585 格）。
- **同一个译名要改就一次改全四层**：jsonl（含 `.qa`）、场景 CSV、覆盖层、manual。装备名写 `glossary/equipment_name_fixes.json` 跑 `integration\fix_equipment_names.py`（按英文原文匹配全部 jsonl 与 Ground/Aircraft/Devices 三类 CSV，同名两值冲突直接失败）；界面词与覆盖层冲突写 `glossary/layer_unify.json` 跑 `integration\unify_layers.py`（`set/revert/drop_override/adopt_override` 四动作 + 正则批量）。只改一层的话，下次构建会从别的层重建出旧值，表现为「反复改同一个词、游戏里就是没变」（v1.9.9 实测 `Jagdpanzer` 家族因此整族没生效）。
- 分层守卫：`finalize.py` 会调 `integration\audit_layers.py --check`，`override-vs-lower` 不为 0 直接拒绝构建；出现冲突先看 `audit\layer-conflicts.json`，裁决写进 `layer_unify.json` 而不是两处手改（覆盖层未必更新，它只是最后套用）。
- 译名脏值：`finalize.py` 的 Name-artifact guard 拦词典层的元话语/句读残留，并内嵌调 `integration\fix_name_artifacts.py --check`（jsonl 与场景 CSV 两层任一残留即失败）。遇到新脏值，把「英文键→正译」加进该脚本的 DICT_FIX、「脏单元格→正译」加进 CELL_FIX——它会同时写 .qa 副本并做 CSV 字节往返校验，比在两层手改安全。
- 改了 `Dat\Art` 目录结构时先跑 `python mod\scan_art_tokens.py`：`finalize.py` 的美术路径守卫读它产出的 `glossary/art_tokens.json`，不一致会直接拒绝构建。跳过 build_variants.py 会让 payload 里的繁体语言包停在旧译文（finalize.py 会因条目数/键集合不符直接报错，不会静默通过）。
- `payload/translations.bin` 是活动槽，由启动器按语言选择生成，不进 Git、不进 checksums；不要手工提交。
- 钩子源码改动后用 zig cc -target x86-windows-gnu 重新编译 WitE2CN_Text.dll（详见 CHANGELOG v1.1.0 的构建记录）。

## 2. 升版本号（三处必须一致）

**发布节奏：一版多批（2026-11-07 定）。** 版本号按「发布」计，不按「对话 / 批次」计。

- 一个发布周期开始时定下唯一的「下一个版本号」（例如 v1.9.10），周期内做几批改动都只用这一个号；**中途不升号、不打 tag**。
- 周期内的改动照常 commit（提交信息可以写「v1.9.10 批次二」），但 VERSION / package.json / CHANGELOG 的定稿都留到发布那一刻。
- 用户说「发布」时，才把全部积累合并成一节 CHANGELOG，正文覆盖**上一个已发布版本至今的所有改动**，然后 tag 一次、Release 一次。
- **一次发布只发一个版本**；不允许「补发前几个版本」或一次推多个 tag。

下面三处（package.json / CHANGELOG / tag）在**发布时**才一起改：

1. payload/package.json 的 mod_version 与 mod_date；
2. CHANGELOG.md 顶部新增一节（版本号 + 日期 + 主题 + 新增/变更/兼容性/已知限制）；
3. 本仓库的 git tag（v主.次.修订）与 Release 标题。

版本规则：

- 主版本：不兼容的大改（例如换掉整套注入方式）；
- 次版本：新增能力或行为变化（v1.1.0 的「版本容忍」属于这一类）；
- 修订号：只修 bug、不动行为。

## 3. 提交与打标签

    git add -A
    git commit -m "v1.2.0：一句话主题"
    git tag -a v1.2.0 -m "v1.2.0（日期）：一句话主题"
    git push origin main
    git push origin v1.2.0

## 4. 建 Release（说明必须有）

Release 正文至少包含四段，缺一不可：

1. **这次修好了什么**：面向玩家，不写实现细节；
2. **这次变了什么**：行为变化与兼容性影响；
3. **怎么看某个游戏版本行不行**：logs/native.log 的 READY / FAILED 判读方式；
4. **附件**：手册、术语表等非 Mod 本体的文件。

手册与术语表走 Release 附件，**不要**提交进仓库（仓库只放 Mod 本体与译文源）。

## 5. 发完自检

- 网页上 mod/payload/checksums.json 与本地一致（Git 换行转换曾导致过整批文件校验失败）；
- 新下载的压缩包解压后能通过 mod/WitE2CN.exe --verify；
- Release 附件的 digest 与本地文件 SHA-256 一致（GitHub API 的 assets[].digest 字段）；
- CHANGELOG 的版本号、tag、Release 标题三者一致。

## 游戏更新后要不要发版

不需要。未登记构建会自动尝试接入；只有确认某个新构建可用、想把它登记进 payload/compat.json 白名单时，才需要发一个修订版（例如 v1.1.1）。

## 6. 两条纪律（2026-11-06 起拆分）

**本机发布与 GitHub 上传节奏不同，不要绑在一起。**

### 6.1 本机发布：每次重建后必做，不进 GitHub

    python integration\fix_equipment_names.py   # 改过装备修订表时
    python integration\unify_layers.py           # 改过分层规则时
    python mod\build_maps.py
    python mod\complete_font.py
    python integration\build_variants.py
    python mod\finalize.py
    python mod\publish.py

publish 只读写本机安装目录（settings.local.json 的 install_path），让玩家实际启动的那份与仓库一致。重建会移除活动槽 `payload/translations.bin`，publish 不会生成它——启动器每次启动会从 `variants/<lang>/` 物化，直接跑游戏核对则要手工复制 zh-CN 那份。

### 6.2 GitHub 上传：**只在用户明确说「上传/发布」时集中做一次**

不再每个对话结束后 commit+tag+push。攒批上传时，一次把下面五件事做完，缺一件都算没传完：

1. 版本号：`VERSION`、`payload/package.json` 的 `mod_version`；
2. `CHANGELOG.md`：版本表首行 + 本版本节（把「未发布」节转正）；
3. `README.md`：第 5 行版本与日期、第 21 行规模数字、「最近更新」小节；`README.en/fr/ja/ru.md` 同步版本行；
4. GitHub Release：标题 `vX.Y.Z`、正文面向玩家（修好了什么 / 变了什么 / 怎么判断某个游戏版本行不行）、附件（手册、术语表）；
5. `git tag -a` → `git push origin main` → `git push origin <tag>` → Wiki 首页版本与年表。

为什么改：一个对话推一次，版本号碎成 v1.9.1～v1.9.8（八天八个 tag），主页与 Release 说明永远落后一两版，玩家看到的「最新版」和实际内容对不上。

### 收尾自检（上传那一次才勾）

- [ ] 启动器标题版本 = `VERSION` = `payload/package.json` = git tag
- [ ] 安装目录 `payload/translations.bin` 的 SHA-256 = 仓库 `payload/variants/zh-CN/translations.bin`
- [ ] README 的版本行、规模数字、最近更新三处 = 本次 tag
- [ ] `git status` 干净，`origin/main` = 本地 HEAD
- [ ] Wiki 对应页面（首页版本、年表、当前版本）已同步
