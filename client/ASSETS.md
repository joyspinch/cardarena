# cardarena · 卡牌竞技 · 素材清单

**总量**：图片 **8 张** / 音频 **9 个**（入库体量 **≈ 0.78 MB**，在
`REAL_GAME_STANDARD.md` §4 的 0.3~1.5 MB 口径内）。

美术路线：**底板位图 + 程序化花纹**。卡面底板 / 卡背 / 牌桌 / 头像框 /
面板是位图；**卡名、费用、效果说明、数值、稀有度符号、类型图标全部用
Canvas 文字与几何图画**——12 张卡不可能逐张生成位图，AI 生成的中文字形也
会糊。

所有位图由 `client/tools/make_assets.py` 从 AI 原图（`build/raw/`，不入库）
后处理而来：洪泛抠黑底 → 裁边 → 缩放到**显示尺寸 2 倍** → 合成到底板 →
量化成索引色 PNG。原始生成图不留在项目里。

## 一、图片（8 张，全部由 `CDraw.BlitImage` 贴进画面）

| 文件 | 入库尺寸 | 显示尺寸 | 用途 |
|------|----------|----------|------|
| `assets/card_common.png` | 256×360 | 128×180 | **普通**卡面底板（银灰边框 + 冷灰渐变底） |
| `assets/card_refined.png` | 256×360 | 128×180 | **精良**卡面底板（蔚蓝边框 + 深蓝渐变底） |
| `assets/card_epic.png` | 256×360 | 128×180 | **史诗**卡面底板（紫金边框 + 紫罗兰渐变底） |
| `assets/card_back.png` | 256×360 | 128×180（对手手牌缩到 56×79） | 卡背（对称金红纹章） |
| `assets/table_bg.png` | 1024×640 | 满屏 1280×800 | 牌桌背景（深色石台 + 金色竞技环） |
| `assets/avatar_frame.png` | 176×176 | 88×88 | 头像徽记（金色纹章盾牌，框内几何剪影） |
| `assets/panel.png` | 600×452 | 600×452 | 结算面板（圆角 + 金边 + 四角菱形） |
| `assets/title_plaque.png` | 600×150 | 600×150 | 标题铭牌（双层金框 + 两侧菱形） |

渲染路径：`src/CardView.zan` 的 `DrawCard` / `DrawCardBack` / `DrawTable` /
`DrawAvatar` / `DrawResult` / `DrawMenu` —— 找不到贴图时退回纯色绘制，不崩。

## 二、音频（9 个 WAV，22050Hz / 16bit / 单声道）

| 文件 | 触发时机 |
|------|----------|
| `assets/sfx/card_play.wav` | 任意一方打出卡牌 |
| `assets/sfx/card_hit.wav` | 造成伤害（含灼烧结算） |
| `assets/sfx/card_block.wav` | 获得格挡 |
| `assets/sfx/card_draw.wav` | 抽牌 |
| `assets/sfx/card_heal.wav` | 回复生命 |
| `assets/sfx/card_turn.wav` | 回合切换（进入新回合） |
| `assets/sfx/card_win.wav` | 本局判胜 |
| `assets/sfx/card_lose.wav` | 本局判负 |
| `assets/sfx/card_deny.wav` | 能量不足，出牌被拒 |

音效走公共包 `Game.Foundation.SfxBank`（磁盘优先 + 内嵌兜底 + 限频 +
**无音频设备时静默降级**）；`src/CardGame.zan` 的 `PlaySound` 按事件名触发。

## 三、制作链路

```powershell
# 1) AI 原图（生成到 build/raw/，不入库、不进 exe）
& "$HOME\.codex\skills\local-image2\scripts\image2.ps1" generate --model gpt-image-2.5 `
  --prompt "<英文提示词>" --size 1024x1024 --quality high --output-format png `
  --out "build/raw/card_common.png" --force

# 2) 后处理 + 音效合成（一步到位）
python client/tools/make_assets.py --raw build/raw --out client/assets
```

后处理链路：洪泛抠黑底（只抠**与画布边界连通**的近黑背景，内部暗部保留）
→ 裁到 alpha 包围盒 → 缩放到显示尺寸 2 倍 → 合成到不透明底板（稀有度渐变）
→ MEDIANCUT 量化成索引色 PNG（体量从 MB 级压到几十 KB）。

`client/assets/_check.py` 是**一次性自检脚本**（拼一张联络表到
`build/raw/_sheet.png`），已被 `.gitignore` 排除，构建时也不打包进 exe。

## 四、授权与红线

| 来源 | 问题 | 处置 |
|------|------|------|
| FreeKill 26 张武将立绘 | **三国杀原作（游卡）美术**，官方文档引导"尽情选择"皮肤，未获原作再授权 | 不可移植。cardarena 只借鉴架构思路，美术全自研，零取用 |
| AI 生成图（gpt-image-2.5） | 训练数据来源与商用条款由平台方承担；生成内容不可控 | 仅作**底板/边框/背景**素材，卡面文字与数值一律程序化绘制；原图不入库 |
| 通用卡牌 PNG 素材站 | 授权多为"免费使用"，再分发条款不明 | 一律不取，卡面自研 |

所有入库位图均为本项目 AI 生成 + 自研后处理的产物。
