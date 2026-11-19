# AOG 名字必须原样交回：指针与副本的差别（v1.10.1）

## 一、问题

「空中指令设置」面板下方的「可用航空作战群」列表自 v1.9.15 起为空。v1.9.21 把 13 个剧本的 612 个 AOG 名字做成恒等钉死（键与值都是英文原名），玩家复测**仍然为空**。

## 二、两组日志的对照

同一份 `native.log`：失败段（v1.9.21 钉死版）从第 71,848 行的 `addr overrides: 8` 起算，成功段（前缀放行诊断态）从第 47,717 行起算。

| 观察点 | 失败段（钉死） | 成功段（前缀放行） |
|:--|:--|:--|
| 载入阶段的名字 | `exact en "Luftflotte 1..5"`（已返回英文） | 同左，另有 `guard en ...` |
| 面板标题 | `heap none zh "GND ATTACK : ??? ?????"`（中文） | `heap none en "GND ATTACK : Luftflotte 4"` |
| 行文本请求 | `available air operational groups` 之后 **0 条**，直接跳 `Show Air Groups` | `%d %s`、`169 `、`(E)`、`224 (E)`、`(-)`、`353 (-)`、`12 Bf 109E-7`、`++`、`Assign AOG to air directive`… |

结论：行循环在执行取文字之前就结束了，所以问题在**行是否被接受**，不在绘制、字体或数据缺失。

## 三、机制

`translate()` 有两种「返回英文」的方式：

1. **恒等钉死**：查表命中，返回 `Entry.value` —— 一份存在词典池里的英文副本。文本相同，指针不同。
2. **名称守卫**：不查表，`return source` —— 调用方传进来那个缓冲区本身。

引擎在这一处把航空队名与 AOG 名当**对象**用（缓存、比较、作为键），副本与原件被视为两个不同的名字；交回原件时两边是同一个字符串，匹配成立。指针层面的细节没有反汇编逐条确证，但「钉死失败 / 守卫成功」在同一份存档、同一份词典上稳定复现。

## 四、实现

`mod/src/text_hook.c`：

- `name_guard(const WCHAR *s)`（配 `w_prefix()` / `w_has()`）：前缀 `Luftflotte` / `Luftwaffe` / `Flieger` 命中即放行。
- 例外表 `Lw_skip[]`：Field、Flak、Jaeger、Fallschirm、Battalion、Regiment、Division、Company、Battery、Abteilung —— 带这些词的是部队名（`Luftwaffe Field Division`），照常翻译。
- `translate()` 开头：`if(name_guard(source)) { trace_lookup(source,source,"guard"); return source; }`，位于 passthru 之后、`@@SKIP` 之前。
- 自测（`-DW2CN_TEST`）新增返回码 120–123。

## 五、验证

玩家复测日志（1,291,493 B / 23,976 行）：

- `guard` 命中 6 条：`Luftflotte 1/2/3/4/5`、`Flieger Fuehrer Ostsee`。
- 第 23,508 行标题恢复英文；23,542 起逐行请求行文本，列表出现（`104 `、`108 (E)`、`8 Blenheim I Rcn (RU)`、`40 IAR 38`、`4th Rum. Army Recon Gro` …）。
- 玩家确认恢复。

## 六、限制

- 守卫是**前缀级**的：凡以这三个词开头的串都不再翻译。`LW Kdo Center`（词典值「中央总部司令部」）不在此列，仍显示译文。
- v1.9.21 的 612 条恒等钉死层保留作第二道保险。
- 若将来出现别族「被引擎当标识符」的名字，沿用同一判据：日志里看该串是否在载入阶段被译、随后在判定处对不上；修法优先「返回源指针」，而不是「译文写成原文」。
