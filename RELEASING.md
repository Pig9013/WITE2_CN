# 发布流程（维护者用）

每次发版都按这个顺序走，版本号与说明就不会乱。

## 1. 改代码 / 改译文

- 启动器与钩子源码在 mod/src/；改完启动器用 mod/build_launcher.cmd 编译。
- 改完 payload 里任何文件，必须在 mod/ 目录跑一次 python finalize.py 刷新 payload/checksums.json，否则用户侧会报「汉化包文件缺失或损坏」。
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
