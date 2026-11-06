# 发布流程（维护者用）

每次发版都按这个顺序走，版本号与说明就不会乱。

## 1. 改代码 / 改译文

- 启动器与钩子源码在 mod/src/；改完启动器用 mod/build_launcher.cmd 编译。
- 改完 payload 里任何文件，必须在 mod/ 目录跑一次 python finalize.py 刷新 payload/checksums.json，否则用户侧会报「汉化包文件缺失或损坏」。
- 改了简体译文后，繁体三套必须重生成，顺序固定：`python mod\build_maps.py` → **`python mod\complete_font.py`** → `python integration\build_variants.py` → `python mod\finalize.py` → `python mod\publish.py`。
  - `complete_font.py` 不能省：`build_maps.py` 会用 `build/WitE2CN.ttf`（旧子集字体）覆盖 payload 字体，不补字则 `build_variants.py` 报「字体仍缺字」直接失败（v1.9.7 实测缺 74 字）。它从系统字体补缺并落回 payload，缺字 0 才继续。
  - 改了 `glossary/reference_overrides.json` 或 `manual_translations.json` 时，先跑 `python integration\build_master_overrides.py` 重生成覆盖层：`master_overrides.json` 是生成物，手改会在下次生成时丢失；生成器会与 `master_drops.json` 交叉核对，发现「已丢弃的键又回到覆盖层」直接失败。
- 改了 `Dat\Art` 目录结构时先跑 `python mod\scan_art_tokens.py`：`finalize.py` 的美术路径守卫读它产出的 `glossary/art_tokens.json`，不一致会直接拒绝构建。跳过 build_variants.py 会让 payload 里的繁体语言包停在旧译文（finalize.py 会因条目数/键集合不符直接报错，不会静默通过）。
- `payload/translations.bin` 是活动槽，由启动器按语言选择生成，不进 Git、不进 checksums；不要手工提交。
- 钩子源码改动后用 zig cc -target x86-windows-gnu 重新编译 WitE2CN_Text.dll（详见 CHANGELOG v1.1.0 的构建记录）。

## 2. 升版本号（三处必须一致）

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

## 6. 双更新纪律（2026-11-01 起）

**每次更新必须同时完成两件事，缺一不可：**

1. **本机**：`python mod\finalize.py` → `python mod\publish.py`，让实际运行的安装目录与仓库一致；
2. **GitHub**：`git commit` → `git tag` → `git push origin main` → `git push origin <tag>`，并同步 Wiki。

只做其中一件，就等于没更新：
- 只推 GitHub 不发布 → 玩家启动的安装目录还是旧 payload（v1.6.1 的教训）；
- 只发布不推 GitHub → 别人下载不到，问题无法复现。

### 收尾自检（四条全绿才算完）

- [ ] 启动器标题版本 = `VERSION` = `payload/package.json` = git tag
- [ ] 安装目录 `payload/translations.bin` 的 SHA-256 = 仓库同名文件
- [ ] `git status` 干净，`origin/main` 与本地 HEAD 一致
- [ ] Wiki 对应页面（首页版本、年表、当前版本）已同步
