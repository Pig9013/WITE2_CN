# War in the East 2 简体中文 Mod 工程

> **当前版本 v1.2.2（2026-10-28）** · [更新日志](CHANGELOG.md) · [下载最新版](https://github.com/Pig9013/WITE2_CN/releases/latest)

**已知限制**：百科正文仍为英文（引擎按单字节渲染，UTF-8/GBK 两种代码页方案实机均失败）；`.scn` 未重建，单位悬停、事件、回合摘要仍为英文。其余界面/表格/单位名/百科标题与链接已中文化。

**百科中文版（游戏外阅读）**：正文已导出为 [docs/百科中文版_v1.0.md](docs/百科中文版_v1.0.md)（1,171 条，同目录有 DOCX）。

游戏打补丁后**不再拒绝启动**：未登记构建照常尝试接入，接不上就以英文运行，补丁与存档不受影响。判定看 logs/native.log，详见 [CHANGELOG](CHANGELOG.md) 与 mod/README.md 的「游戏更新」一节。

**配套手册（不属于 Mod 本体）**：《钢铁炼狱》官方手册中文版 v1.0 · 110 页 · 文本可选中复制 —— 见 [Releases](https://github.com/Pig9013/WITE2_CN/releases) 附件。

## 参考资料与致谢

本项目的术语、句式和译名不是凭空来的，主要参考了以下中文资料。原文与字段语义则以游戏自带数据（Dat/CSV、Dat/Info）和官方英文手册为准。

### 中文手册与译本

- **《东线战争2》规则手册分章中文译本（16 章 PDF，T1 层）**——术语与规则表述的第一依据。各章译者：
  - 第 1 章 新手入门：**leninlyender**
  - 第 8、9、10、11、14 章：**Fulda**
  - 第 15 章 将领：**Mizore**
  - 第 27 章 增援与撤离：**兔空**
  - 第 13、20、29、34、38、39、40、41 章：**克里斯蒂安-cristianwj**
  - 全书订正：**克里斯蒂安-cristianwj**
- **《东线战争2规则手册》中文全本（809 页，T1B）**——长段正文、书目与术语的对照本，译者：**张萧临**。
- **《钢铁炼狱》（Steel Inferno）手册**——英文原版与中文版，英文原作者 **James Wirth**。
- **新手教程中文版（T3）**——界面与流程用语参考。

对应文件（供核对，均只读引用、不随本仓库分发）：「1 新手入门.pdf」…「41 附录L-编辑器.pdf」（WITE2translation 分章）、「东线战争2规则手册_中文全本.pdf」、「WITE2_Steel_Inferno_Manual_EBOOK.pdf」及其中文版、「WITETutorialManual中文.pdf」。

### 社区文本与讨论

- **kkuy678**、**zisongzi**、**魔法训练营**——提供了本项目参考的中文文本与讨论；若干术语取舍与机制解释来自这些材料。
- 以及兵棋 / TOAW 社区里分享 WitE2 资料、答疑与勘误的各位。

### 工具书

- 《世界人名翻译大辞典》，新华社译名室编，2007 年 4 月，ISBN 7500107994/Z21；维基百科「外语译音表/英语」——人名、地名译写的依据。

### 特别致谢

**cristianwj、leninlyender、Fulda、Mizore、kkuy678、zisongzi、魔法训练营、兔空、张萧临**

这个项目的术语、句式和译名，很大一部分是从你们的中文文本里学来的。没有这些底本，本 Mod 不可能做成现在这样。**居功至伟。**

如有遗漏或作者标注有误，请开 issue 指正，我们立刻改。

## 当前交付

唯一入口是：

    mod\WitE2CN.exe

它从游戏目录创建私有 mod\runtime 副本，加载 mod\payload 里的字体/overlay/翻译词典，并在该副本上注入 WitE2CN_Text.dll。原游戏 EXE、.scn、原 CSV 不被修改。

运行说明见 mod\README.md。实际操作只由用户本人执行；工程侧只做文件构建与静态审计，不启动游戏或 Steam。

## 目录

    mod/
      WitE2CN.exe                启动器
      WitE2CN_Text.dll           原生文本钩子
      payload/                   运行时词典、字体、checksums、package
      runtime/                   私有游戏副本与存档（不属于可分发代码）
      assets/                    构建源：GuiFonts.json、translation.csv
      build_maps.py              组装词典/字体/overlay/checksums
      complete_font.py           补齐字体缺字
      finalize.py                生成 checksums 与可移植 settings
      src/                       启动器与文本钩子源码
      README.md                  使用说明

    glossary/                    术语表与 UI 额外词表
    pipeline/                    本地 Qwen 提取/翻译/QA/术语保护
    data/                        翻译源与中间数据
    build/                       字体源、基础 translation.csv、战役简报、场景 CSV 译文
    integration/                 文本提取/生成/审计脚本

## 可移植性

- 代码不写死本机 D:\ 或 Steam 库路径。
- 游戏按 `--game` → settings.json → settings.local.json（自动记忆）→ WITE2_GAME → Steam 注册表/全部库目录/盘符扫描 → 手动选择 的顺序解析；都找不到时弹窗选目录。
- `WitE2CN.exe --where` 把解析结果写进 logs\launcher.log，排查"找不到游戏"时先看这个。
- settings.json 默认为空对象 {}；需要非 Steam 安装时才手写 game_path。
- runtime\WitE2CN.runtime.json 的 source 只是来源记录；移动 Mod 后只校验 game_sha256。
- 构建脚本使用 MOD/PROJECT 相对路径；不再依赖已删除的 mod_full。

## 构建（不启动游戏）

    python mod\build_maps.py
    python mod\complete_font.py
    python mod\finalize.py

build_maps.py 读取已有译文，不调用模型。翻译本身由 pipeline 本地 Qwen 完成。

## 快捷键文本

游戏 EXE 的 UI 键可能是：

    Show Turn Summary {ctrl-s}
    Toggle Ground Support on/off {x}
    Move mode {F1}
    Zoom map in {+}

构建时会扫描 EXE 中所有含 {...} 的字符串，生成完整模板；不能只处理一种占位符。

## 清理原则

已删除：旧 mod_full/mod_additive/install 目录、旧覆盖安装、旧 CSV swap、diagnostics 会话日志、旧截图/预览/zip、旧 docs、测试 exe/pdb/lib、审计快照。

保留：当前 Mod、runtime（含存档）、翻译源、场景 CSV 译文、字体源、构建/审计脚本、术语表。

## 常见问题

**启动器提示「汉化包文件缺失或损坏：payload\...」**

2026-10-25 之前的仓库版本受 Git 换行转换影响：payload 下的 txt/csv/json 在提交时被转成 LF，下载后与 payload\checksums.json 里的 SHA-256 对不上（文件其实在，只是字节变了）。已在 .gitattributes 中对 mod/payload/** 设 -text 修复。遇到该提示请删除旧文件夹，重新下载最新版本，不要新旧目录混用。

## 验证

静态验证包括：

- translations.bin 的 W2CNMAP1 头、条目数；
- 字体 cmap 覆盖（缺字 0）；
- checksums 25 个文件通过；
- 场景 CSV 行数/字段数/表头/BOM/非文本列与原始导出对比；
- settings.json 为 {}，启动器可自动找到 Steam 游戏。

实机验证由用户执行；工程侧不启动游戏。
