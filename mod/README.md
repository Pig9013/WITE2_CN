# WitE2 独立汉化 Mod

> **v1.1.0（2026-10-25）** · 完整更新历史见仓库根目录 [CHANGELOG.md](../CHANGELOG.md)

## 使用

正常登录 Steam 后，双击本目录的 WitE2CN.exe。

第一次会从本机游戏复制资源到本目录的 runtime，约占 2 GB；以后直接启动。它不会启动或重启 Steam，也不会修改原游戏 EXE、.scn 或原 CSV。

## 路径

本 Mod 不写死本机路径。启动器按下面的顺序找游戏，第一个命中就用：

1. 命令行参数 `--game "游戏文件夹"`；
2. `settings.json` 里的 `game_path`（手动指定，优先级最高，写错的会被跳过）；
3. `settings.local.json` 里的 `game_path`（启动器自动记住上次找到的位置，可随时删掉）；
4. 环境变量 `WITE2_GAME`；
5. 自动查找：
   - Steam 注册表：HKCU/HKLM、32 位/64 位三个位置（SteamPath / InstallPath / SteamExe）；
   - 每个 Steam 的所有库目录：`libraryfolders.vdf`（新格式 "path" 与旧格式数字键）、`config\config.vdf` 的 `BaseInstallFolder_N`；
   - 每个库里先按 `appmanifest_1775550.acf` 的 `installdir` 定位（改装到自定义文件夹名也能找到），再退回默认目录名；
   - 各盘符常见位置（Steam / SteamLibrary / Games\Steam / Program Files (x86)\Steam）；
   - 最后做一次有上限的浅层全盘扫描（找 steamapps 目录，深度 3，跳过系统目录）；
6. 仍然没找到时弹窗让你手动选择游戏文件夹（选 `steamapps\common\Gary Grigsby's War in the East 2`），选一次就写进 `settings.local.json`，以后直接秒开。

想确认它到底找到了哪个目录：

    WitE2CN.exe --where

结果写在 `logs\launcher.log`，形如 `GAME D:\Steam\steamapps\common\Gary Grigsby's War in the East 2`。找错了就往 `settings.json` 里写死 `game_path` 覆盖。

`settings.local.json` 只是本机缓存，已在 .gitignore 里；搬动或删除 Mod 目录后它会自动失效并重新查找。

如果 runtime 已存在，只校验游戏版本哈希，不要求原来的 source 路径；因此整个 Mod 目录可以搬到别的电脑或别的盘。

## 目录

- WitE2CN.exe：启动器；
- WitE2CN_Text.dll：原生文本钩子，读取 payload/translations.bin；
- payload/translations.json / .bin：精确词典，包含 UI、快捷键、事件、单位、地名、百科；
- payload/overlay/Dat/Fonts：字体与 GuiFonts；
- payload/checksums.json / package.json：完整性/版本；
- runtime：私有游戏副本与存档；
- assets：构建源（GuiFonts、translation.csv），不是运行时依赖；
- build_maps.py / complete_font.py / finalize.py：离线构建脚本；
- src：启动器与文本钩子源码。

## 快捷键/占位符

游戏 UI 不只是 name 或 name (Ctrl+X)，还会显示：

    Show Turn Summary {ctrl-s}
    Toggle Ground Support on/off {x}
    Move mode {F1}
    Zoom map in {+}

构建时会扫描 EXE 中所有含 {...} 的原始字符串，生成完整键；文本钩子精确匹配后替换为中文并显示可读的按键。

## 卸载

1. 先备份 runtime\Dat\Save；
2. 删除整个 Mod 文件夹；
3. 原游戏目录不受本 Mod 影响。

旧 mod_full 入口已删除；不要再使用旧启动器或旧 CSV 替换脚本。

## 校验

WitE2CN.exe --verify：只检查汉化包完整性，不启动游戏。

WitE2CN.exe --prepare：只更新私有 runtime，不启动游戏。

日志：logs\launcher.log、logs\native.log、runtime\engine.log。


## 游戏更新

游戏打补丁后**不再拒绝启动**：

- 已登记构建（`payload/compat.json`）：正常启动。
- 未登记构建：照常启动并尝试接入；接入失败则**以英文运行**，游戏补丁与存档不受影响，只弹一次提示。
- 检测到版本变化时，私有 runtime 会增量同步到新版本（只复制变化的文件，`Dat\Save` 原样保留），不需要重建。

文本钩子不再写死内存地址：它按函数特征码在游戏的 `.text` 里定位本地化查表函数，再反查所有 `E8` 调用点。只要官方没有重写这段函数，小版本补丁通常**无需任何更新**即可继续用中文。

判定结果看 `logs\native.log`：

- `READY: hooked N call site(s); lookup at text+0x...` —— 本次构建可用，把新构建登记进 compat.json 即可；
- `FAILED: localization lookup not found in .text (build changed)` —— 该构建改了代码结构，需要适配；此时游戏仍以英文正常运行。

登记新构建：把 `WarInTheEast2.exe` 的 SHA-256 与版本号追加到 `payload/compat.json` 的 `builds` 数组，然后在该目录运行一次 `python finalize.py` 刷新 `payload/checksums.json`。

> 注意：该 EXE 的 `.text` 在磁盘上是 SteamStub 加密的，**无法离线静态判断**新版本能否挂钩；只能以运行时的 `native.log` 为准。换版本后请先跑一次并查看这条日志。
