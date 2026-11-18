# v1.9.18 —— 航空作战群窗口词条订正 · 按需诊断 trace

**发布日期：2026-11-18** · 适用于 War in the East 2 1.0.5.02 · [更新日志](https://github.com/Pig9013/WITE2_CN/blob/main/CHANGELOG.md) · [下载](https://github.com/Pig9013/WITE2_CN/releases/latest)

## 一句话

玩家反馈自动 AI 空军分配窗口里「可用航空作战群」标题在、下面一行都没有。这一版先修掉同窗口里能确认的 8 条错译，并给文本钩子加了一个**默认关闭**的诊断开关：打开后能看清引擎到底有没有请求过那些行，从而把「数据为空」与「画不出来」分开。

## 这次修好了什么

- `rdy` / `Rdy` / `Rdy:` → 「就绪」/「就绪：」（原来多出百分号，键里根本没有 `%`，百分号属于另一条 `Rdy %`）。
- `Req` / `REQ` → 「需求」（同上，原来带 %）。
- `damaged` → 「受损」（原来多一个冒号）。
- `AOG:` → 「航空作战群：」（原来吞掉了键尾冒号）。
- `Set formation counter color` → 「设置部队棋子颜色」。`formation counter` 指的是地图上那枚部队棋子，不是队形计数器。

## 这次加了什么（诊断用，默认关闭）

`mod/src/text_hook.c` 新增 `trace_enabled()` / `trace_lookup()`：

- **不建标记文件就不开**：只有 `mod\logs\trace.on` 存在时才启用，普通玩家完全不写额外日志。
- 开启后对**去重后的**每次查表往 `mod\logs\native.log` 追加一行：`TRACE rva=12A5E8 exact zh "available air operational groups"`。
- `rva=` 是源串在主模块镜像内的相对虚拟地址（能直接对回 EXE 里的字面量）；运行期堆上的串记 `heap`。
- 命中方式：`exact`（精确键）/ `norm`（忽略大小写第二索引）/ `addr`（地址特化）/ `none`（未命中）。
- 上限 20,000 条，约 1 MB，超过即停，不会失控。

判读规则：打开空中指令窗口后，如果日志里出现 `Luftflotte 1` 这类 AOG 名的 `TRACE` 行，说明行文本确实被请求了，问题在绘制层；如果只见标题类串、没有任何 AOG 名，说明列表数据本身是空的，与汉化无关。

## 这次变了什么

- 版本 1.9.18；词典 **72,566 条**（与 v1.9.17 同量，8 条改值）；字体 2,447 字形，四套语言包缺字 0；构建链 19 道守卫；checksums 125 条全通过。
- `WitE2CN_Text.dll` **重编**：99,840 → **100,864 字节**，sha256 `B5FC1995FCB46D33036E23508CE0DCAF4DEB49D8928761E3614ED1310BF22F02`，导出 `Wite2CN_Initialize@4` 不变，`-DW2CN_TEST` 自测 PASS。启动器随包更新，不需要手动替换。
- 不改游戏 EXE、`.scn`、原 CSV、贴图或存档；删除 mod 文件夹即回到英文。

## 关于「可用航空作战群 列表为空」的当前结论

玩家给的两张截图不是同一状态：中文版 `Auto ( mission 193 / escort 0 )`，英文版 `Auto ( mission 263 / escort 64 )`，空中指令序号也不同，不能直接对比。但同一窗口**上方**的空中指令列表在中文版里显示正常（「地面支援 (10)」「地面攻击 (15) 171, 138 ( 半径 5 )」），说明这个窗口画中文行没有问题；而按手册 37.16.6，自动分配时「all the available AOGs that could contribute are shown」，潜在最大 193 架却一行都没有，逻辑上是矛盾的。

要定性还差一步，两条路任选：同存档、同一条空中指令的中英截图各一张；或按上面的方法开 trace 复现一次，把 `mod\logs\native.log` 发来。

## 怎么看某个游戏版本行不行

看 `mod\logs\native.log`：

- `READY: hooked 2 call site(s); lookup at text+0x...` —— 钩子已接上；`FAILED` 表示该构建接不上，游戏以英文运行，存档不受影响。
- `ADDR override: ...` —— 地址特化生效（`CITY` / `DIS` / `TR` 等按窗口分译）。
- `NORM blocked: ...` —— 第二索引按预期拦下非界面串。
- `TRACE ...` —— 仅在 `mod\logs\trace.on` 存在时出现。

## 已知限制（如实说明）

- 「可用航空作战群」列表为空**尚未定性**，本版只提供了诊断手段，没有动资格判定的任何逻辑。
- `DIS` 仍作「解散」（单位状态义），战斗表里的「紊乱」由地址特化按 RVA 单独处理；`TR` / `FF` / `F` 等与任务设置短码冲突的仍留英文。
- `plt` / `trvl` / `FHQ` / ` (escort)` / `Add another assignment of AOG to air directive.` 未译：语义未定（可能是值而非标签），待确认后再补。
- 小城镇名仍是英文；`.scn` 未重建；百科正文在游戏内仍英文（引擎单字节限制）。