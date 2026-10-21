# cardarena · 卡牌竞技 · 素材清单

**总量**：图片 **18 张** / 音频 **9 个** / 皮肤包 **1 份**（入库体量
**≈ 0.86 MB**，在 `REAL_GAME_STANDARD.md` §4 的 0.3~1.5 MB 口径内）。

美术路线：**底板位图 + 程序化花纹**。卡面底板 / 卡背 / 牌桌 / 头像 /
HUD 面板 / 按钮底板是位图；**卡名、费用、效果说明、数值、稀有度符号、
类型图标全部用 Canvas 文字与几何图画**——12 张卡不可能逐张生成位图，
AI 生成的中文字形也糊。

颜色只有一个出处：`client/src/CardPalette.zan`（玄黑石台 + 暗金 + 深红
+ 羊皮纸白 + 银蓝）。皮肤包 `skins/cardarena/skin.css` 用的是同一套
色的 CSS 写法——两边靠这张表对齐，改色先改它。

所有位图由 `client/tools/make_assets.py` 从 AI 原图（`build/raw/`，不入库）
后处理而来：洪泛抠黑底 → 裁边 → 缩放到**显示尺寸 2 倍** → 合成到底板 →
量化成索引色 PNG。原始生成图不留在项目里。

## 一、图片（18 张，全部由 `CDraw.BlitImage` / `CardPaint.NineSlice` 贴进画面）

| 文件 | 入库尺寸 | 显示尺寸 | 用途 |
|------|----------|----------|------|
| `assets/card_common.png` | 256×360 | 128×180 | **普通**卡面底板（银灰边框 + 冷灰渐变底） |
| `assets/card_refined.png` | 256×360 | 128×180 | **精良**卡面底板（蔚蓝边框 + 深蓝渐变底） |
| `assets/card_epic.png` | 256×360 | 128×180 | **史诗**卡面底板（紫金边框 + 紫罗兰渐变底） |
| `assets/card_back.png` | 256×360 | 128×180（对手手牌缩到 56×79） | 卡背（对称金红纹章） |
| `assets/table_bg.png` | 1024×640 | 满屏 1280×800 | 牌桌背景（深色石台 + 金色竞技环） |
| `assets/avatar_frame.png` | 176×176 | 88×88 | 金色纹章头像框（**合成底板**，不再直接上屏） |
| `assets/avatar_player.png` | 176×176 | 88×88 | 玩家徽记：AI 生成的骑士盔徽合成进纹章框 |
| `assets/avatar_ai.png` | 176×176 | 88×88 | 对手徽记：AI 生成的恶魔面具徽合成进纹章框 |
| `assets/panel.png` | 600×452 | 600×452 | 结算面板（圆角 + 金边 + 四角菱形） |
| `assets/title_plaque.png` | 600×150 | 600×150 | 标题铭牌（双层金框 + 两侧菱形） |
| `assets/hud_plate.png` | 128×128 | 九宫格 | **细框 HUD 底板**：顶栏 / 牌库计数 / 事件流水 |
| `assets/hud_frame.png` | 128×128 | 九宫格 | **厚框 HUD 底板**：双方信息盒 / 回合横幅（带角饰） |
| `assets/btn_primary.png` | 128×128 | 九宫格 | 主按钮常态（深红底 + 暗金边） |
| `assets/btn_primary_hover.png` | 128×128 | 九宫格 | 主按钮悬停 |
| `assets/btn_primary_pressed.png` | 128×128 | 九宫格 | 主按钮按下（变暗，像按进牌桌） |
| `assets/btn_plain.png` | 128×128 | 九宫格 | 次按钮常态（玄黑底 + 暗金边） |
| `assets/btn_plain_hover.png` | 128×128 | 九宫格 | 次按钮悬停 |
| `assets/btn_plain_pressed.png` | 128×128 | 九宫格 | 次按钮按下 |

渲染路径：`src/CardView.zan` 的 `DrawCard` / `DrawCardBack` / `DrawTable` /
`DrawAvatar` / `DrawHudPlate` / `DrawHudFrame` / `DrawButton` / `DrawResult` /
`DrawMenu` —— 找不到贴图就退回纯色绘制，不崩。

### 九宫格（引擎没有 border-image，只能自己切）

HUD 面板与按钮底板都是 **128×128 源图 + 24 源像素角宽**，运行时由
`CardPaint.NineSlice` 切成 9 块拼到任意尺寸：角固定、边横竖拉伸、中间
拉伸。底板按 2 倍入库，所以角宽折半后是 12 逻辑像素。

裁切用 `CDraw.BlitSource` 解析出的内存键 + `Canvas.BlitImage` 的源矩形
（`Canvas.BlitImage(path, dx, dy, dw, dh, sx, sy, sw, sh)`，源坐标是原图
像素）。⚠️ `mem:` 键**不能**再走 `CDraw.BlitSource`——那会把
`mem:xxx` 当文件名去读，抛 `FileNotFoundException`；因此有
`CardPaint.BlitKey` 单独走已解析的键。

### 头像徽记的做法

AI 生成的角色/职业图标（`build/raw/avatar_player.png`、
`avatar_ai.png`）→ 洪泛抠黑底 → 裁到 alpha 包围盒 → 方形化（短边贴满、
长边居中裁）→ 缩到 80×80 → **合成进 `avatar_frame.png` 金色纹章框的
盾心**（源像素 44..131 × 44..136）。取景框（只取头部，避免 AI 图自带
的盾牌外框和金色纹章打架）写在 `make_assets.py` 的 `focus` 参数里。

## 二、皮肤包（1 份）

| 文件 | 作用 |
|------|------|
| `assets/skins/cardarena/skin.css` | 竞技场风 UI：`:root` 令牌 + `button` / `label` / `panel.card` 规则 |

- 令牌覆盖：`--primary`（暗金）、`--bg-primary/secondary/tertiary/hover/active`、
  `--text-primary/secondary/tertiary/inverse`、`--border-primary/secondary/hover/focus`、
  `--divider`、`--shadow-color`、`--success/warning/error/info`、
  `--border-radius-small/medium/large`、`--font-size-tiny..huge`。
- 规则覆盖：`button`（含 `:hover` / `:active` / `:focus`）、`button.primary`
  （含两态）、`button:disabled`、`label`、`panel.card, card`（含
  `::title` / `::divider`）。
- 落地：构建脚本把 `client/assets/skins/` 拷到 **exe 同级**的
  `build/cardarena/skins/`（`Gui.Styling.Skin.Roots` 找
  `exe 同级/skins/` 与 `exe 同级/assets/skins/`）；启动时
  `host.App().UseSkin("dark")` → `UseSkin("cardarena")` 一次应用。
- ⚠️ 令牌名的坑：`Skin.ThemeOf` 把 CSS 名映射成 Theme 字段
  （`--bg-secondary` → `bgSecondary`），**圆角字段叫
  `borderRadiusSmall`**，所以真正生效的圆角令牌是 `--border-radius-*`，
  不是 `--radius-*`（后者只在本皮肤自己的规则里有效）。

## 三、音频（9 个 WAV，22050Hz / 16bit / 单声道）

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

## 四、制作链路

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

HUD 底板与按钮底板是**程序化几何**画的（面板/按钮属于"界面部件"，几何
绘制是规范允许的路线），但同样入库成位图、运行时由九宫格贴出。
头像图标是 AI 生成后抠 alpha 合成进纹章框的。

`client/assets/_check.py` 是**一次性自检脚本**（拼一张联络表到
`build/raw/_sheet.png`），已被 `.gitignore` 排除，构建时也不打包进 exe。

## 五、授权与红线

| 来源 | 问题 | 处置 |
|------|------|------|
| FreeKill 26 张武将立绘 | **三国杀原作（游卡）美术**，官方文档引导"尽情选择"皮肤，未获原作再授权 | 不可移植。cardarena 只借鉴架构思路，美术全自研，零取用 |
| AI 生成图（gpt-image-2.5） | 训练数据来源与商用条款由平台方承担；生成内容不可控 | 仅作**底板/边框/背景/图标**素材，卡面文字与数值一律程序化绘制；原图不入库 |
| 通用卡牌 PNG 素材站 | 授权多为"免费使用"，再分发条款不明 | 一律不取，卡面自研 |

所有入库位图均为本项目 AI 生成 + 自研后处理的产物。
