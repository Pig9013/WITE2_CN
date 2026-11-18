# 「可用航空作战群」列表为空：排查记录（1.9.18）

玩家反馈：自动 AI 空军分配窗口里，英文版 `available air operational groups` 标题下会列出 `Luftflotte 4   263 64 (E) 497 (-)`、`12 Bf 109E-7` 这样的行；中文版标题「可用航空作战群」在，标题下整块空白，连行底色都没有。

本文记录已排除的可能、已确认的事实，以及下一步的取证开关。结论：**尚未定性**，但已经把范围压到「列表数据为空」与「请求了但没画」二者之一。

## 一、截图给到的信息

- 中文版：`已分配  Auto ( mission 193 / escort 0 )`；标题「可用航空作战群」以暗灰正常绘出；下方无行；再下方是「显示航空队 / 不兼容类型」「隐藏非活动项」复选框。
- 英文版：`Assigned  Auto ( mission 263 / escort 64 )`；一行 `Luftflotte 4   263 64 (E) 497 (-)`、一行 `12 Bf 109E-7`；AD 是 GND ATTACK (35)，目标 Hex 180,165。
- **两张图不是同一状态**（193/0 对 263/64，AD 序号也不同），不能据此直接定罪。

## 二、已排除的可能

| 假设 | 结论 | 依据 |
|:--|:--|:--|
| CSV 被翻译导致读不到 AOG | 排除 | 覆盖层只有 `Dat\Fonts`、`Dat\Info`、`Dat\Scen`、`GuiFonts.json`，没有 `Dat\CSV`；runtime 里也没有 `*.zh.csv`。翻译只发生在绘制时。 |
| 字体缺字 | 排除 | 四语言包缺字 0；2,447 字形；AOG 名里无怪字符。 |
| 字体行高/度量差异挤掉整块 | 排除 | 本字体 upm 2048 / hhea 2229,-536 → 1.350 em；Segoe UI 1.330 em，差 1.5%；OS/2 均不使用 typo 度量。 |
| `GuiFonts.json` 条目缺失或被改坏 | 排除 | 游戏与覆盖层各 48 项、键集相同，逐字段比对除 `name`/`file` 外 0 差异；`FONT_AOG`（id 57，size 10）保留。 |
| 译文破坏了 `sprintf` 格式串 | 排除 | 72,566 条逐条比对 printf 说明符序列，0 处不一致。 |
| 静态代码 xref 追到判定逻辑 | 死路 | 全 `.text` 线扫 214 万条指令，落在 UI 字符串区的非跳转立即数去重仅 23 个且全是垃圾；字符串按索引/运行期装配访问。 |
| 窗口布局数据可查 | 无此数据 | `Dat` 下只有 credits / FontConfig / GuiColors / GuiFonts / scriptRec / splashTime / SoundFXConfig / wfgamedata / wrfind。 |

## 三、支持「列表数据为空」的证据

1. **同一窗口的上半部分画得很好**：中文版里空中指令列表显示「地面支援 (10)」「地面攻击 (15) 171, 138 ( 半径 5 )」，说明窗口的行绘制与中文字体都正常。
2. **手册 37.16.6**：自动分配时「all the available AOGs that could contribute are shown but the 'assigned' box is empty apart from indicating the potential maximum number of mission and escort planes」。中文版已显示出潜在最大值 193/0，却没有一行，逻辑上自相矛盾。
3. 手册还写明底部复选框用于「过滤不合格飞机或说明为何某些航空队不可用」——如果资格判定把所有单位都判为不合格，就会出现这种「有最大值、无行」的样子。

## 四、本版加入的取证开关（默认关闭）

`mod/src/text_hook.c` 的 `trace_enabled()` 在首次查表时探测 `mod\logs\trace.on`：

```
（建一个空文件即可开启）
mod\logs\trace.on
```

开启后 `native.log` 会多出形如下面的行（去重、上限 20,000 条）：

```
TRACE rva=12A5E8 exact zh "available air operational groups"
TRACE rva=12B4C0 none en "Luftflotte 1"
TRACE heap none en "12 Bf 109E-7"
```

- `rva=` 表示源串在游戏主模块镜像内，可直接对回 EXE 字面量；堆上的串记 `heap`。
- 第二段是命中方式：`exact` / `norm` / `addr` / `none`。
- 第三段 `zh` / `en` 表示返回串是否含中文。
- 用完把 `trace.on` 删掉即恢复静默。

## 五、判读规则

打开那条空中指令窗口，然后看 `native.log`：

- 出现 `TRACE ... "Luftflotte 1"`、`"12 Bf 109E-7"` 这类 AOG 行 → **行文本被请求了**，问题在绘制层（颜色/裁剪/字体度量），继续查绘制。
- 只有标题类串（`available air operational groups`、`Show Air Groups` 等），没有任何 AOG 名 → **列表数据为空**，与汉化无关，属引擎资格判定或存档状态。

## 六、待补的词条（语义未定，本版未动）

`plt`、`trvl`、`FHQ`、` (escort)`、`Add another assignment of AOG to air directive.`（带尾空格）。这几个可能是值而不是标签，需要看到实际出现的位置再定。