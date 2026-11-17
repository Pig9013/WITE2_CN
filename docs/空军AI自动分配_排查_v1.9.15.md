# 空军「关掉 AI 仍自动分配飞机」排查与术语订正（v1.9.15 批次）

**日期：2026-11-17** · 触发：玩家反馈「关掉 AI，空军还是自动分配飞机」，被判定为恶性 bug。

## 一句话结论

这不是汉化改动引入的行为变化，**汉化 mod 没有任何通道能改 AI 行为**；玩家遇到的「自动分配飞机」是引擎的 **Automate AI Air Assist**（自动运行 AI 空中辅助）在起作用——该选项在多人对局开局即锁定、且选中时会**禁用**手动触发按钮（手册 17.1.1），单机则可在「游戏选项」屏（Administration 页签或 shift-g）随时改。汉化的问题在于**这套开关的中文标签把语义讲反了或讲丢了**，玩家看不出自己开的到底是什么，本轮把这一族 1,293 个键全部重订。

## 涉及层次（先分层，再动手）

| 层 | 内容 | 本轮处理 |
|:--|:--|:--|
| 1 引擎行为 | AI 空中辅助、自动补给站管理、支援单位自动转隶 | 不可由 mod 改（见证据链），只能如实解释 |
| 2 词典层 | 上述开关的标签、tooltip、状态串、进度标签 | **本轮修正主体：45 组 → 1,293 键** |
| 3 显示层 | 工具栏 tooltip 宽度、状态前缀 ON - / OFF - | 状态前置、删重复命令名，长度贴近原文 |
| 4 玩家路径 | 开局选项屏 / 局内游戏选项屏 / 工具栏按钮 | 在回复与本文中给出可执行步骤 |

## 证据链：mod 为什么改不了 AI

1. **覆盖层只有文本类资源**：mod/payload/overlay/Dat 下 32 个文件——GuiFonts.json、Fonts/WitE2CN.ttf、Info/*.csv（百科正文）、Scen/*.txt（24 份剧本简介，纯文本介绍）。**没有任何 Dat/CSV/Generic 数据表、没有 .scn、没有 AI 脚本**。
2. **文本钩子只翻译查表返回值**：mod/src/text_hook.c:279 的 return translate(original_lookup(self,source,flag)); 全镜像只挂 2 个调用点（native.log：READY: hooked 2 call site(s); lookup at text+0x4546288），另一个是师徽钩子。它不参与任何逻辑判断。
3. **启动器只是私有副本 + 注入 DLL**：mod/src/Launcher.cs:717 一处 ProcessStartInfo，不传任何参数；Launcher.cs:532 首次复制显式跳过 wirgame.dat / wirpref.dat，SyncRuntime 跳过整个 Dat/Save/。玩家原有存档与偏好不会被动过。
4. **选项不是以文本存储**：wirpref.dat（249 B，音量/窗口）、wirgame.dat（808 B，头 W2GO + 全零）都是二进制；存档 .sav 压缩加密，ASCII 搜 Assist / AI Air / Computer / Off 全 0 命中。
5. **词典里没有任何开关状态串可被译反**：On / Off / ON / OFF 在 72,519 条里**一条都没有**（Yes→是 有、No 故意不译，见下），所以不存在「勾选状态显示反了」的可能。

## 引擎机制（Living Manual，权威）

- **4.6.1 / 16.1.1**：AI assist 选中后，AI 会**生成空中指令**并**按优先级把航空大队分配给航空作战群（AOG）**，HQ 移动时还会自动转移驻地——这就是玩家说的「自动分配飞机」。两个变体：开局选项选中 → 每次按 F12（结束空中阶段、结束地面阶段）各执行一次，**多人局开局定死不能改**；不选开局选项 → 可在回合内任意时刻手动点按钮。
- **17.1.1**：This cannot be changed in a MP/PBEM game and the choice will apply to both sides. Once this choice is made, the manual option to trigger the effects of AI Assistance will be disabled. → 选了自动，**连手动按钮都会被禁用**，玩家按不到「关」的地方。
- **17.2.5**：没选自动也可以手动点按钮，但**再点会清空你手动做的部署与指令**（the AI clears the slate）。
- **36.18**：Automate AI Air Assist「选中后将失去手动设置空中指令与重新部署空军的能力；MP 局对双方生效且开局后不可改」。同页明确：**对电脑（单机）时这些值可随时改**，PBEM 局定死。入口是 **Administration 页签或 shift-g** 的「游戏选项」屏。
- 另外两条**不是** AI 的自动行为，容易混：Auto Upgrades（航空大队自动换装，逐队设置）与 AI Manage Depots（补给站自动布置，25.7.3）。

## 玩家可执行路径（回复口径）

1. 新开对局：在**游戏选项**屏（setup 时的选项页 / 局内 shift-g）**取消勾选「自动运行 AI 空中辅助」**，再开局；MP 局一旦开局无法改。
2. 单机进行中：shift-g → 游戏选项 → 取消勾选，下一阶段生效。
3. 局内**不要**再点工具栏的「运行 AI 空中辅助」按钮，也不要再按 F12 触发辅助（会覆盖手动设置）。
4. 屏幕上出现「正在自动运行 AI 空中辅助」状态串，即说明该选项仍是开的。

## 本轮词典修正（45 组 → 1,293 键）

写入 glossary/layer_unify.json（action=set，同时落 jsonl/qa、reference_overrides、manual），并同步两个生成的旁支层 data/translations/hotkey_names.json、glossary/ui_extra.csv（后两者在打包顺序里**晚于** jsonl，会盖掉 jsonl 的新值——这是本轮唯一一次「改了没生效」的坑）。

覆盖的缺陷类型：

1. **状态前缀被抹平/串行污染**（最误导）：8 条空中指令开关，旧值形如「关闭 - 关闭战略空军日的空中指令」「关闭北欧战术空军指令 ON - 关闭北欧式空战指令」。
2. **术语错**：Assist 译「支援」（兵棋中支援=兵力/火力支援）→「辅助」；AOG 译「机械化部队」/「机场群」→「航空作战群」；air orders 译「空中命令」→「空中指令」。
3. **机翻/脏值**：AI LINE FORMING XY: →「AI行形成XY:」；clear off map depots? →「移除地图上的补给站？」（off map=地图外）；bad assignment. clear aog assignment →「分配错误。晴朗航空作战群分配错误」（clear 当晴天）。
4. **中英混排与语序**：Fog of War →「迷雾-of-战争」；Prevent automatic movement of HQ support units →「禁止自动移动支援司令部单位」；When checked →「检查时」。

关键裁决（节选）：

| 英文 | 旧译 | 新译 |
|:--|:--|:--|
| AI Air Assist | AI空中辅助 / AI空中支援 | **AI 空中辅助** |
| Activate AI Air Assist | 启用AI空中支援 | **运行 AI 空中辅助**（一次性动作，非开关） |
| Automate AI Air Assist | 自动AI空中支援 | **自动运行 AI 空中辅助** |
| Using Automated AI Air System | 使用自动AI空中系统 / 使用自动AI空军系统 | **正在自动运行 AI 空中辅助** |
| ON - turn off air orders for STRATEGIC AIR DAY | 关闭 - 关闭战略空军日的空中指令 | **已开启：点击关闭战略空军（昼间）的空中指令** |
| Enhanced Player TB Control | 增强玩家投弹手控制 | **增强玩家战区盒控制**（TB=Theatre Box） |
| Lock HQ Support | 锁定司令部支援 | **锁定司令部支援等级** |
| SETTING FRONT LINE DEPOTS | 设置方面军补给线 | **设置前线补给站**（front line≠Front 方面军） |
| move aogs | 移动机械化部队 | **调动航空作战群** |

## 另发现（未修，待定）

Dat/Info 覆盖层存在**正文串行**：deviceInfo.csv 4 行只有 1 种中文（全是 Kar98k 那段）、groundInfo.csv 2 行 1 种（KV-1）、leaderInfo.csv 2 行 1 种（沙波什尼科夫）。原版这几张表的 id 列全为 0，按 id 映射会折叠到同一行，与 v1.9.11「unitInfo 整表同一句」同源。unitInfo.csv 已用 restore_unit_info.py 兜住（守卫 OK），其余三张无守卫。

## 待确认

- 玩家在哪一层关的 AI：开局选项屏 / 局内游戏选项屏 / 主菜单 Computer Controlled？是否 MP/PBEM？是否旧档？
- 若能在 CR 或气计划屏看到「正在自动运行 AI 空中辅助」，即证明该选项仍开着（截图最好）。
