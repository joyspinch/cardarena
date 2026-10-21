# 千军牌局 —— 2D 卡牌对战（单机 AI）

> 本文件是 cardarena 项目的落地说明。**素材清单见 `client/ASSETS.md`**，全局规格见工作区根的 `ASSET-PIPELINE.md`。

## 参考源与授权边界

- **参考**：FreeKill（**只借 Lua 声明式技能系统结构**）
- **抄什么**：借鉴「技能用声明式脚本描述、执行器驱动」的架构。**卡面美术全部自研**，不使用任何现成立绘。

**红线与差异**：

- **FreeKill 的 26 张武将立绘是三国杀原作（游卡）美术**，未获再授权，不可移植。
- 只借架构不借内容：武将、技能、数值、文案全部原创。
- 不做联网对战（P0 单机 AI 对手）。

## 渲染路线

2D 贴图批。卡面底板 6 稀有度程序化生成（矢量出图），符号化图标 64×64，牌桌底图 1920×1080。

## 目录

    cardarena/
      client/       src/ 源码、assets/ 素材、data/ 数据、skins/ 皮肤、tools/ 脚本、tests/ 用例
      build/        编译产物（不入库）

所有命令都在**项目根**下执行（路径相对项目根）。

## 编译

```powershell
$env:ZAN_HOME = 'D:/project/zan-lang'   # 编译器与 stdlib 同源；公共包在它的 packages/ 下
pwsh -File client/tools/build.ps1
```

ZAN_HOME 指向 zan-lang 仓库时用它的 `build/zanc.exe` 与 `stdlib/`；不设则用 PATH 上的 `zanc`。
编译时加 `--package-project $env:ZAN_HOME` 可直接吃仓库里的 `packages/`。

## 测试

```powershell
pwsh -File client/tools/test.ps1     # 无头冒烟：跑满 90 帧后自行退出
```

工作区批量冒烟：在 zan-lang 仓库侧跑 `pwsh -File scripts/smoke_all_game_projects.ps1`（一次跑完仓库外全部游戏项目）。

## 当前状态

骨架可编译可运行（90 帧无头冒烟通过）：手牌/出牌/弃牌流程、回合结算、AI 对手。

## 后续（按优先级）

1. 接入真实位图 sprite 与音效（素材见 `client/ASSETS.md`）。
2. 补玩法深度：参照源的关卡/数值/AI 三个维度逐项对齐。
3. 需要时再评估联网（`legend` 有服务端可参考）。