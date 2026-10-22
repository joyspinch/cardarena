# 卡牌竞技 · CARDARENA

> 回合制卡牌对战（人 vs AI）：开局前构筑 8 张牌，开战、结算、记战绩。

用 [Zan](https://github.com/joyspinch/zan-lang) 语言写的独立游戏项目（仓库根自带 git 仓库）。完整设计与实现说明见 [`PROJECT.md`](PROJECT.md)。

## 玩法

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

| 操作 | 效果 |
|------|------|
| 鼠标左键点手牌 | 选中 / 取消选中 |
| 点「出牌」 | 打出选中的牌（攻击牌会切到「选择目标」） |
| 点对手头像 | 对攻击牌确认目标并立即结算 |
| 点「结束回合」 | 交出回合（对手行动、回合数 +1） |
| 点构筑界面的卡 | 选中 / 取消（选满 8 张才能开战） |
| Esc | 打开 / 关闭设置浮层 |

## 构建

需要 [zan-lang](https://github.com/joyspinch/zan-lang) 仓库（`zanc` 编译器、公共包与 stdlib 都在里面）：

```powershell
git clone https://github.com/joyspinch/zan-lang.git
$env:ZAN_HOME = 'D:/path/to/zan-lang'   # 指到刚克隆的 zan-lang 仓库根

pwsh -File client/tools/build.ps1
```

产物：`build/cardarena/Cardarena.exe`（运行目录要带上它旁边的 `assets/` 与 `skins/`）。

## 运行

```powershell
cd build/cardarena
.\Cardarena.exe
```

## 测试

```powershell
pwsh -File client/tools/test.ps1
```

## 目录结构

```
cardarena/
client/
  src/      # 游戏源码（.zan 源码 + HTML 界面设计稿）
  assets/   # 位图 / 音频素材
  data/     # 数值表与数据文件
  tests/    # 玩法断言用例
  tools/    # 构建与测试脚本
PROJECT.md
```

## 素材与授权

- 素材清单与授权说明见 [`client/ASSETS.md`](client/ASSETS.md)。

## 许可

本仓库暂未附带 `LICENSE` 文件，开源许可待作者选定后补充。依赖的 zan-lang 仓库采用 ZCSL（Zan Community Source License 1.0）。

## 更多文档

- [`PROJECT.md`](PROJECT.md) —— 完整设计与实现说明
- [`client/ASSETS.md`](client/ASSETS.md) —— 素材清单
