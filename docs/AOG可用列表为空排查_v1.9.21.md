# 可用航空作战群列表为空：根因与修复（v1.9.21）

> 玩家现象：打开空中指挥部 →「空中指令设置」面板 → 下方「可用航空作战群」永远是空的（英文原版有行）。
> 2026-11-19 定性并修复：**航空作战群（AOG）的名字被翻译**，而引擎拿它跟航空队（Unit）的原文英文名逐一比对。

## 一、根因

引擎保存的是**字符串**，不是编号：

- 载入剧本时，引擎把 `Dat\CSV\<剧本>\AOGs.csv` 的 `Name` 列交给本地化查表函数，命中的译文被**缓存进 AOG 对象**；
- 面板做「这个 AOG 能不能编给这条空中指令」的筛选时，比对的是**航空队（Unit）的原始英文名**（`Units.csv` 的 `Name`，从不经过查表）；
- 名字一旦被译成「第4航空队」，与引擎手里的「Luftflotte 4」永不相等 → 每一行都被滤掉 → 取文字之前就已经是 0 行。

因此它既不是数据缺失、也不是字体或绘制问题：**行循环一次都没进**。

## 二、证据链

1. **A/B（决定性）**：`mod\logs\passthru.on` 存在时钩子一律返回原文（= 界面全英文），列表**出现**；删掉 passthru.on 恢复中文，列表**为空**。
2. **逐族放行**：把 `Luftflotte*`、`Luftwaffe*`、`Flieger*` 三条前缀在**进程启动时**放行（不翻译），列表恢复，玩家实机确认「这一版本就是对的」。
3. **时机**：放行必须从载入剧本那一刻就生效。面板打开时才放行的做法实测无效——日志显示载入阶段就已经 `TRACE heap exact zh "Luftflotte 1..5"`（23042–23055 行），对象里存的是中文。
4. **对照**：同一份日志里，面板拼出的行首是 `TRACE heap none en "GND ATTACK : Luftflotte 4"`——**航空队一侧始终是英文**，正好印证「一边中文、一边英文」。

## 三、修复

- `integration/gen_aog_identity.py`：扫描 `Dat\CSV\*\AOGs.csv` 的 `Name` 列（排除 `**** 德国 ****` 这类分组表头行），生成 `glossary/aog_identity.json`（当前 13 个剧本、612 个名字）。
- `mod/build_maps.py`：**AOG 名字钉死层**——把清单里的键改写成恒等条目（值 = 原文），精确查表直接返回原文，与美术令牌钉死层同一思路。
- `mod/finalize.py`：新增 **AOG identity guard**，清单里任何一个名字若在词典里仍有非恒等译文，直接拒绝发布（防止以后有人把译文加回去）。

## 四、代价（必须知道）

- AOG 名字与航空队/航空军 HQ 的单位名是**同一个词典键**，钉死后这些名字在其余界面也显示原文：
  每个剧本约 **24 个**航空队/航空军级 HQ 单位（如 `Luftflotte 1/2/4`、`I Fliegerkorps`、`1st Royal HAF Field Bde`、`Rum. Combat Air Command`）保持原文。
- 「空中指令设置」面板右侧「可用航空作战群」的行名、CR「航空队」页的 AOG 名字也保持原文。
- 分组表头行（`**** 德国 ****`）不参与比对，仍译中文；实测中文表头不会让列表变空。

## 五、复现与维护

```
python integration\gen_aog_identity.py --game "<游戏目录>"   # 重新生成清单
python mod\build_maps.py        # AOG identity pins: N/N
python mod\finalize.py          # AOG identity guard: OK
python mod\publish.py
```

- **装了新 DLC / Steam 校验后**要重跑生成器：DLC 剧本的 `AOGs.csv` 在加密 `.scn` 里，本脚本扫不到；若某个 DLC 剧本出现空列表，可从存档或用 trace 日志取出该剧本的 AOG 名字，手工补进 `glossary/aog_identity.json` 的 `names`。
- `mod\logs\trace.on`：存在时钩子记录每次查表（源串、命中方式），用于同类问题取证；**不要随包发布**。
- `mod\logs\passthru.on`：存在时全界面回退英文，用于 A/B 判定「是不是翻译引起的」。
- `mod\logs\bypass.txt`：一行一个 ASCII 键，`*` 结尾表示前缀；进程启动时读一次，用于逐族放行定位。三者都只在诊断时使用。

## 六、顺带修好的问题

- `WitE2CN_Text.dll` 的 trace 计数从「调用次数」改为「不同源串数」，上限 100,000；去重表扩到 2^18 槽。旧实现被地图标签每帧刷爆，面板期什么都不记。
- trace 的 `rva=` 之前按 `WCHAR*` 相减（元素数，为真实 RVA 的一半），已改为字节偏移。
- `native.log` 到 8 MB 自动轮转为 `native.prev.log`，日志不再无限增长。
- 组合行格式化层：`Assigned Air Directives %d (%d) / MAX %d`、`Auto ( mission %d / escort %d )` 这类带数字的现场拼接串之前永远查不到精确键，现按模板补译（「已分配空中指令 11 (8) / 上限 32」「自动（任务 193 / 护航 0）」）。
- 地址跳过层（`@@SKIP`）：`-red`/`-white`/`-green`/`red`/`white` 五个字面量被拼进 `//Gui//frame%s.tga`、`//Gui//AOG-%s flag.tga`，翻译后会变成中文文件名而静默丢图；现按源串地址原样返回。
