# WitE2 独立汉化 Mod

## 使用

正常登录 Steam 后，双击本目录的 WitE2CN.exe。

第一次会从本机游戏复制资源到本目录的 runtime，约占 2 GB；以后直接启动。它不会启动或重启 Steam，也不会修改原游戏 EXE、.scn 或原 CSV。

## 路径

本 Mod 不写死本机路径：

1. settings.json 为空对象时，自动从 Steam 注册表/库目录寻找游戏；
2. 也可设置环境变量 WITE2_GAME，或在 settings.json 写 game_path；
3. 如果 runtime 已存在，只校验游戏版本哈希，不要求原来的 source 路径；因此整个 Mod 目录可以搬到别的电脑或别的盘。

构建脚本 build_maps.py 同样按 settings.json → WITE2_GAME → Steam 注册表/库目录解析；代码里不再写死 D:\Tool 或 Steam 库路径。

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
