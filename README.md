# War in the East 2 简体中文 Mod 工程

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
- 游戏通过 settings.json → 环境变量 WITE2_GAME → Steam 注册表/库目录自动解析。
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

## 验证

静态验证包括：

- translations.bin 的 W2CNMAP1 头、条目数；
- 字体 cmap 覆盖（缺字 0）；
- checksums 25 个文件通过；
- 场景 CSV 行数/字段数/表头/BOM/非文本列与原始导出对比；
- settings.json 为 {}，启动器可自动找到 Steam 游戏。

实机验证由用户执行；工程侧不启动游戏。
