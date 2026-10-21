# 卡牌竞技 —— 回合制卡牌对战（人 vs AI）

> 交付标准见 `D:\project\zan-lang\docs\REAL_GAME_STANDARD.md`（真实位图资产 /
> 可玩核心闭环 / 音画反馈 三道关卡）。**素材清单见 `client/ASSETS.md`**。

## 这是什么

一个**能真正玩**的回合制卡牌对战：

- **牌组构筑**：开局前从 12 张候选牌里选 8 张（每张 2 副本 = 16 张牌库）。
  选满才能开战；构筑结果直接决定这局能不能赢（全选治疗没有输出、全选高费
  史诗抽不到牌）。
- **对战**：双方各 30 HP、每回合 3 能量、手牌上限 5 张。牌库抽牌，牌库空了
  用弃牌堆重洗。
- **卡牌类型**：攻击（造成伤害）、防御（格挡本回合伤害）、技能（抽牌 /
  回血 / 加能量 / 持续伤害）；稀有度分普通 / 精良 / 史诗，影响数值与卡面底板。
- **出牌流程**：点一张手牌 → 需要选目标的牌要点对手头像（不需要的直接按
  「出牌」）→ 扣能量 → **立即结算**。能量不足时**不扣能量、不出牌**，并在
  屏幕中央给出明确提示（绝不静默吞掉）。打出的牌**从手牌位飞向目标位**
  （指向对手的牌飞对手头像，自身增益飞自己头像），落点炸一圈金色光环。
- **AI 对手**：能打脸就打脸；自己快没血就回血 / 格挡；手牌少就用抽牌牌补
  手牌；能量牌抢先手。难度三档（只会打 / 会回血 / 会抢能量）。
- **结算**：任一方 HP ≤ 0 判胜负，面板显示回合数、双方剩余生命、剩余牌库，
  以及累计胜场 / 败场 / 场次 / 最高回合数。连续空过 8 次判平局。

## 怎么玩

| 操作 | 效果 |
|------|------|
| 鼠标左键点手牌 | 选中 / 取消选中 |
| 点「出牌」 | 打出选中的牌（攻击牌会切到「选择目标」） |
| 点对手头像 | 对攻击牌确认目标并立即结算 |
| 点「结束回合」 | 交出回合（对手行动、回合数 +1） |
| 点构筑界面的卡 | 选中 / 取消（选满 8 张才能开战） |
| Esc | 打开 / 关闭设置浮层 |

## 素材与美术路线

按 `REAL_GAME_STANDARD.md` §4 走 **底板位图 + 程序化花纹**，按
`GAME_UI_AND_FACING.md` 走 **UI 图形化**：

- **位图**：卡面底板 3 张（按稀有度：普通银 / 精良蓝 / 史诗紫金）、卡背、
  牌桌背景、角色徽记 2 张、HUD 底板 2 张、按钮底板 6 张、结算面板、
  标题铭牌 —— 共 **18 张**，全部由 `CDraw.BlitImage` /
  `CardPaint.NineSlice` 贴进画面（找不到贴图就退回纯色绘制，不崩）。
- **九宫格**：引擎没有 `border-image`，HUD 面板与按钮底板（128×128 源图、
  24 源像素角宽）由 `CardPaint.NineSlice` 自己切 9 块拼出来。
- **颜色只有一个出处**：`src/CardPalette.zan`（玄黑石台 + 暗金 + 深红 +
  羊皮纸白 + 银蓝）。卡面、牌桌、面板、按钮、血条、能量共用这一套色。
- **皮肤包**：`client/assets/skins/cardarena/skin.css`（竞技场风：暗金 +
  深红 + 玄黑）。构建拷到 exe 同级的 `build/cardarena/skins/cardarena/`，
  启动时 `UseSkin("dark")` → `UseSkin("cardarena")` 应用——设置浮层因此
  不再是系统默认黑卡片 + 灰按钮。
- **程序化**：卡名 / 费用 / 效果说明 / 数值 / 稀有度符号 / 类型图标全部用
  画布原语画（**中文不进位图**，AI 生成的中文字形会糊）。
- **音效**：9 个 WAV（出牌 / 命中 / 格挡 / 抽牌 / 治疗 / 回合 / 胜利 /
  失败 / 能量不足），走公共包 `Game.Foundation.SfxBank`（无音频设备时
  静默降级）。

## 目录

    cardarena/
      client/       src/ 源码、assets/ 素材、data/ 数据、tests/ 用例、tools/ 脚本
      build/        编译产物（不入库）

所有命令都在**项目根**下执行（路径相对项目根）。

## 源码分工

| 文件 | 职责 |
|------|------|
| `src/main.zan` | 入口：建 GuiHost 跑主循环 |
| `src/CardGame.zan` | 状态机（菜单 / 构筑 / 对战 / 结算）、输入、按钮、回合推进 |
| `src/CardCard.zan` | 卡牌目录（12 张候选）、效果类型、稀有度、卡面文案 |
| `src/CardDeck.zan` | 牌库 / 手牌 / 弃牌堆：抽牌、弃牌、**弃牌堆重洗** |
| `src/CardCombat.zan` | 战斗状态：HP / 能量 / 格挡 / 灼烧、回合推进、效果结算、胜负判定 |
| `src/CardAi.zan` | 对手策略（打脸 / 回血 / 补牌 / 抢能量，三档难度） |
| `src/CardBuild.zan` | 牌组构筑：12 选 8、随机选牌、洗牌、牌组与对手牌组 |
| `src/CardView.zan` | 渲染层：菜单 / 构筑 / 对战 / 结算四画面 + 卡面 + 贴图 |
| `src/CardPaint.zan` | 逻辑坐标画布原语（包 CDraw 的视口映射）+ 九宫格 + 带阴影文字 |
| `src/CardPalette.zan` | **色板**：整个项目唯一一处颜色定义 |
| `src/GameShell.zan` | 存档（胜场 / 败场 / 场次 / 最高回合数）+ 设置（强度 / 能量 / 自动出牌） |

## 编译

```powershell
pwsh -File client/tools/build.ps1 -PackageProject D:\project\zan-head
```

`-PackageProject` 指向**含 `packages/` 的仓库根**（公共包 `Zan.Game` /
`Zan.Gui` 住在那里）。编译器默认按 `$env:ZAN_HOME` → `$env:ZANC` → PATH →
`D:/project/zan-lang/build/zanc.exe` 依次找，也可用 `-Compiler` 显式指定。

素材会拷到 exe 旁（`build/cardarena/assets/`），运行时磁盘优先。
皮肤包另拷到 **exe 同级**的 `build/cardarena/skins/cardarena/skin.css`
（`Gui.Styling.Skin.Roots` 找的就是这个位置）。

## 测试

```powershell
pwsh -File client/tools/test.ps1 -PackageProject D:\project\zan-head
```

三段判据：

1. **玩法断言**（`client/tests/cardarena_test.zan`，无头，**147 条断言**）：
   卡牌目录、牌库抽牌与**弃牌堆重洗**、牌组构筑（8 张 / 2 副本 / 洗牌）、
   开局状态、能量扣减与**能量不足拒绝出牌**、攻击扣血、防御格挡、
   技能（抽牌 / 回血 / 加能量 / 灼烧）、回合推进、AI 策略、胜负判定，
   以及**3 个种子的完整对局**（能走到结束、牌的总数守恒、手牌不超 5 张）。
2. **存档两遍**：第一遍写盘、第二遍是新进程读回（场次 1 → 2）。
3. **无头冒烟**：程序自动打完一整局对战（双方 AI）后自行退出。

工作区批量冒烟：在 zan-lang 仓库侧跑 `pwsh -File scripts/smoke_all_game_projects.ps1`。

## 环境变量

| 变量 | 作用 |
|------|------|
| `CARDARENA_SMOKE=1` | 无头冒烟（双方自动对战，打完一局退出） |
| `CARDARENA_FRAMES=<n>` | 冒烟帧数上限（默认 900） |
| `CARDARENA_DEMO=1` | 演示模式：直接进对战，玩家座位空着（截图用） |
| `CARDARENA_BUILD=1` | 直接进构筑界面 |
| `CARDARENA_SETTINGS=1` | 启动即打开设置浮层（验收皮肤包用） |
| `CARDARENA_CAPTURE=<path>` | 抓一帧画布像素（后端画布，非窗口） |
| `CARDARENA_SAVE=<dir>` | 存档目录（测试脚本用临时目录） |

## 素材重建

```powershell
# 1) AI 原图生成到 build/raw/（不入库）
# 2) 抠黑底 → 裁边 → 缩放到显示尺寸 2 倍 → 量化成索引色 PNG
python client/tools/make_assets.py --raw build/raw --out client/assets
```

`client/tools/make_assets.py` 同时用纯 Python 合成 9 个音效 WAV
（22050Hz / 16bit / 单声道）。

## 参考源与授权边界

- **参考**：FreeKill（**只借鉴架构思路**）
- **抄什么**：借鉴「技能以声明式数据描述、执行器驱动」的架构思路与卡牌对战
  的流程分层。**卡面美术全部自研**，不使用任何现成立绘。
- **红线**：FreeKill 的 26 张武将立绘是**三国杀原作（游卡）美术**，未获原作
  再授权，不可商用移植——本项目零取用。本项目所有位图均由 AI 生成后自研
  后处理入库。
- 不做联网对战（P0 单机 AI 对手）。

## 当前状态

可玩：构筑 → 对战 → 结算全流程，位图 / 音效 / 存档 / 设置 / AI 全部到位。

观感（第二轮品质改造）：皮肤包 + 九宫格 HUD 底板 + 三态按钮 + 卡牌投影
+ 出牌飞行动画 + 角色徽记 + 渐变分段血条，颜色统一走 `CardPalette`。

截图见 `build/cardarena/ui_battle.png`（对局 HUD）、`ui_build.png`
（构筑界面）、`ui_settings.png`（设置浮层 · 竞技场皮肤）。

## 后续

1. 卡牌扩充到 24 张候选 + 关键词 / 装备 / 状态（FreeKill 的声明式技能表）。
2. 动画演出：伤害数字飘字、格挡特效（出牌飞入已做）。
3. 需要时再评估联网（`legend` 有服务端可参考）。
