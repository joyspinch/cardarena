#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cardarena 素材流水线：AI 原图 → 入库位图 + 程序化音效。

用法（在项目根下）：
    python client/tools/make_assets.py --raw build/raw --out client/assets

位图链路（AI 图默认没有 alpha，背景是纯黑）：
    1. 读原图（1024²）；
    2. 从画布四边洪泛，把**与边界连通**的近黑背景抠成透明（内部暗部保留）；
    3. 裁到 alpha 包围盒；
    4. 缩放到显示尺寸的 2 倍；
    5. 合成到不透明底板（卡面底板 = 稀有度渐变）；
    6. 量化成索引色 PNG 入库（体量压到几百 KB 以内）。

UI 面板 / 铭牌用程序化几何画（面板属于"界面部件"，几何绘制是规范允许的
路线），但它们同样是**入库位图**，运行时由 CDraw.BlitImage 贴出来。

第二轮（观感品质改造）新增：
    - **九宫格底板**（hud_plate / hud_frame / btn_*）：128×128 源图，
      角宽 24 源像素（12 逻辑像素），运行时由 CardPaint.NineSlice 切成
      9 块拼到任意尺寸——引擎没有 border-image，九宫格只能自己切。
    - **头像徽记**（avatar_player / avatar_ai）：AI 职业图标抠 alpha 后
      合成进金色纹章框的盾心，替掉原来的几何剪影。

音效链路：纯 Python 合成 WAV（22050Hz / 16bit / 单声道）。
"""

import argparse
import math
import os
import struct
import wave
from array import array

from PIL import Image, ImageDraw

# 卡面底板显示尺寸 128×180，入库 2 倍 = 256×360。
CARD_W, CARD_H = 256, 360
# 牌桌：显示 1280×800，入库 1024×640（运行时拉伸）。
TABLE_W, TABLE_H = 1024, 640
# 头像徽记：显示 88×88，入库 176×176。
AVATAR = 176
# 结算面板：显示 600×452。
PANEL_W, PANEL_H = 600, 452
# 标题铭牌：显示 600×150。
PLAQUE_W, PLAQUE_H = 600, 150

# 九宫格底板：源 128×128（= 2 倍入库），角宽 24 源像素 = 12 逻辑像素。
PLATE_SRC = 128
PLATE_INSET = 24
# 头像框里图标边长（源像素）+ 盾心中心（源像素，量自 avatar_frame 的
# 红色盾心连通区域 44..131 × 44..136）。
ICON_BOX = 80
ICON_CENTER = (87, 90)

# 竞技场配色（与 client/src/CardPalette.zan 一一对应）：
#   玄黑石台 + 暗金 + 深红 + 羊皮纸白。
GOLD = (216, 169, 78)
GOLD_BRIGHT = (242, 215, 154)
GOLD_DIM = (138, 106, 46)
GOLD_DEEP = (78, 58, 24)
CRIMSON = (142, 32, 40)
INK = (10, 9, 8)



def flood_background(img, thresh=30):
    """把与画布边界连通的近黑背景抠成透明（内部暗部不动）。"""
    img = img.convert("RGBA")
    ImageDraw.floodfill(img, (0, 0), (0, 0, 0, 0), thresh=thresh)
    # 洪泛会填成纯透明；把残留的"暗但连通"像素统一成透明。
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if r < thresh and g < thresh and b < thresh:
                px[x, y] = (0, 0, 0, 0)
    return img


def crop_to_alpha(img):
    bbox = img.split()[3].getbbox()
    if bbox is None:
        return img
    return img.crop(bbox)


def gradient(size, top, bottom):
    """竖直线性渐变。"""
    w, h = size
    strip = Image.new("RGB", (1, h))
    px = strip.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px[0, y] = (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
        )
    return strip.resize(size, Image.BILINEAR)


def save_indexed(img, path, colors=64):
    """量化成索引色 PNG（体积压到几十 KB）。"""
    q = img.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT)
    q.save(path, optimize=True)
    return os.path.getsize(path)


def build_plate(raw_path, out_path, top, bottom, size=(CARD_W, CARD_H), colors=64):
    """卡面底板：AI 边框 + 稀有度渐变底。"""
    src = Image.open(raw_path).convert("RGBA")
    art = crop_to_alpha(flood_background(src))
    art = art.resize(size, Image.LANCZOS)
    base = gradient(size, top, bottom)
    base.paste(art, (0, 0), art)
    return save_indexed(base, out_path, colors)


def build_back(raw_path, out_path):
    """卡背：整幅图案直接铺在暗红底板上。"""
    src = Image.open(raw_path).convert("RGBA")
    art = crop_to_alpha(flood_background(src))
    art = art.resize((CARD_W, CARD_H), Image.LANCZOS)
    base = gradient((CARD_W, CARD_H), (92, 30, 34), (34, 12, 16))
    base.paste(art, (0, 0), art)
    return save_indexed(base, out_path, 64)


def build_table(raw_path, out_path):
    """牌桌背景：整幅铺底，不抠 alpha（环境贴图）。"""
    src = Image.open(raw_path).convert("RGB")
    # 源图 1024²，先裁成 4:3 再缩到 1024×640——纵向只压 0.83，变形可接受。
    crop = src.crop((0, 128, 1024, 896)).resize((TABLE_W, TABLE_H), Image.LANCZOS)
    return save_indexed(crop, out_path, 128)


def build_avatar(raw_path, out_path):
    """头像徽记：AI 纹章 + 暗底，贴到头像框位置。"""
    src = Image.open(raw_path).convert("RGBA")
    art = crop_to_alpha(flood_background(src))
    art = art.resize((AVATAR, AVATAR), Image.LANCZOS)
    base = gradient((AVATAR, AVATAR), (56, 46, 34), (20, 17, 14))
    base.paste(art, (0, 0), art)
    return save_indexed(base, out_path, 64)


def rounded_panel(size, fill_top, fill_bottom, border, radius=18, width=3):
    """程序化面板：圆角 + 渐变 + 金边（透明外角）。"""
    w, h = size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    body = gradient((w, h), fill_top, fill_bottom).convert("RGBA")
    body.putalpha(mask)
    draw = ImageDraw.Draw(body)
    draw.rounded_rectangle((width // 2, width // 2, w - 1 - width // 2, h - 1 - width // 2),
                           radius=radius, outline=border, width=width)
    draw.rounded_rectangle((width + 3, width + 3, w - 1 - width - 3, h - 1 - width - 3),
                           radius=max(2, radius - 5), outline=(90, 68, 36, 160), width=1)
    # 四角小菱形装饰。
    for (cx, cy) in ((width + 12, width + 12), (w - width - 12, width + 12),
                     (width + 12, h - width - 12), (w - width - 12, h - width - 12)):
        draw.polygon([(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)],
                     fill=(214, 168, 88, 220))
    return body


def build_plaque(size):
    """标题铭牌：双层金框 + 中心菱形。"""
    w, h = size
    img = rounded_panel(size, (58, 44, 28), (24, 18, 12), (198, 152, 78, 255), radius=24, width=3)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((10, 10, w - 11, h - 11), radius=18,
                           outline=(120, 92, 48, 200), width=2)
    for (cx, cy) in ((24, h // 2), (w - 24, h // 2)):
        draw.polygon([(cx, cy - 9), (cx + 7, cy), (cx, cy + 9), (cx - 7, cy)],
                     fill=(214, 168, 88, 230))
    return img


# ----- 九宫格底板 ---------------------------------------------------------


def nine_plate(fill_top, fill_bottom, border, inner, radius=0, stud=0,
               sheen=True):
    """九宫格底板：源 128×128，角宽 24 源像素。

    角固定、边横竖拉伸、中间平铺——引擎没有 border-image，运行时由
    CardPaint.NineSlice 自己切 9 块。底板按 2 倍入库，描边宽度因此是
    逻辑像素的 2 倍。

    radius = 0 → 直角（HUD 面板）；radius > 0 → 圆角（按钮）。
    stud  → 角上装饰菱形的半径（源像素，0 = 不画）。
    """
    w = h = PLATE_SRC
    body = gradient((w, h), fill_top, fill_bottom).convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    body.putalpha(mask)
    draw = ImageDraw.Draw(body)
    if sheen:
        # 顶部一道高光：让底板有"被打亮"的立体感（纯色块做不到）。
        draw.rectangle((4, 3, w - 5, 5), fill=(255, 236, 196, 26))
    if radius > 0:
        draw.rounded_rectangle((1, 1, w - 2, h - 2), radius=radius,
                               outline=border, width=4)
        draw.rounded_rectangle((9, 9, w - 10, h - 10), radius=max(2, radius - 6),
                               outline=inner, width=2)
    else:
        draw.rectangle((1, 1, w - 3, h - 3), outline=border, width=4)
        draw.rectangle((9, 9, w - 10, h - 10), outline=inner, width=2)
    if stud > 0:
        for (cx, cy) in ((18, 18), (w - 18, 18), (18, h - 18), (w - 18, h - 18)):
            draw.polygon([(cx, cy - stud), (cx + stud, cy), (cx, cy + stud),
                          (cx - stud, cy)], fill=GOLD_BRIGHT + (235,))
    return body


def build_avatar_icon(raw_path, out_path, frame_path, focus):
    """头像徽记：AI 职业图标抠 alpha → 方形化 → 合成进金色纹章框盾心。

    focus = 原图里的取景框 (l, t, r, b)（像素），用来只取头部——
    AI 图里的整块盾牌外框会和金色纹章框打架。
    """
    frame = Image.open(frame_path).convert("RGBA")
    src = Image.open(raw_path).convert("RGBA").crop(focus)
    art = crop_to_alpha(flood_background(src))
    if art.width < 1 or art.height < 1:
        return None
    # 方形化：短边贴满 ICON_BOX，长边居中裁掉。
    scale = ICON_BOX / float(min(art.width, art.height))
    art = art.resize((max(1, int(round(art.width * scale))),
                      max(1, int(round(art.height * scale)))), Image.LANCZOS)
    side = min(art.width, art.height)
    left = (art.width - side) // 2
    top = (art.height - side) // 2
    art = art.crop((left, top, left + side, top + side)).resize(
        (ICON_BOX, ICON_BOX), Image.LANCZOS)
    px = ICON_CENTER[0] - ICON_BOX // 2
    py = ICON_CENTER[1] - ICON_BOX // 2
    frame.alpha_composite(art, (px, py))
    frame.save(out_path, optimize=True)
    return os.path.getsize(out_path)



# ----- 音效 ---------------------------------------------------------------

RATE = 22050


def write_wav(path, samples):
    data = array("h")
    for s in samples:
        v = int(max(-1.0, min(1.0, s)) * 32000)
        data.append(v)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())
    return os.path.getsize(path)


def env(i, n, attack=0.01, release=0.6):
    """简单包络：起音 + 指数衰减。"""
    a = max(1, int(n * attack))
    if i < a:
        return i / a
    t = (i - a) / max(1, (n - a))
    return math.exp(-t / max(0.01, release))


def tone(freq, dur, gain=0.6, release=0.35, harm=(1.0, 0.35, 0.15)):
    n = int(RATE * dur)
    out = []
    for i in range(n):
        t = i / RATE
        v = 0.0
        for k, amp in enumerate(harm):
            v += amp * math.sin(2 * math.pi * freq * (k + 1) * t)
        out.append(v * gain * env(i, n, 0.02, release))
    return out


def noise(dur, gain=0.6, release=0.25, lp=0.35, seed=1):
    """带低通的白噪声（简单一阶滤波）。"""
    n = int(RATE * dur)
    out = []
    state = 0.0
    x = seed
    for i in range(n):
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        w = (x / 0x3FFFFFFF) - 1.0
        state += lp * (w - state)
        out.append(state * gain * env(i, n, 0.005, release))
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    peak = max(1e-6, max(abs(v) for v in out))
    if peak > 1.0:
        out = [v / peak for v in out]
    return out


def seq(parts):
    """把若干音轨按顺序接起来。"""
    out = []
    for p in parts:
        out.extend(p)
    return out


def silence(dur):
    return [0.0] * int(RATE * dur)


def build_sfx(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    made = {}

    # 出牌：木质轻拍（噪声 + 短促中频）。
    made["card_play"] = write_wav(os.path.join(out_dir, "card_play.wav"),
                                  mix(noise(0.12, 0.55, 0.12, 0.5, 7),
                                      tone(320, 0.12, 0.35, 0.1, (1.0, 0.2))))

    # 命中：低频冲击 + 脆裂噪声。
    made["card_hit"] = write_wav(os.path.join(out_dir, "card_hit.wav"),
                                 mix(noise(0.26, 0.6, 0.2, 0.8, 13),
                                     tone(110, 0.26, 0.7, 0.18, (1.0, 0.5, 0.2))))

    # 格挡：金属双音。
    made["card_block"] = write_wav(os.path.join(out_dir, "card_block.wav"),
                                   mix(tone(880, 0.24, 0.35, 0.16, (1.0, 0.4, 0.25)),
                                       tone(1320, 0.24, 0.22, 0.12, (1.0, 0.3))))

    # 抽牌：轻微摩擦。
    made["card_draw"] = write_wav(os.path.join(out_dir, "card_draw.wav"),
                                  noise(0.18, 0.4, 0.22, 0.22, 29))

    # 治疗：上行两音。
    made["card_heal"] = write_wav(os.path.join(out_dir, "card_heal.wav"),
                                  seq([tone(660, 0.12, 0.4, 0.2), tone(990, 0.24, 0.4, 0.25)]))

    # 回合开始：钟声两下。
    made["card_turn"] = write_wav(os.path.join(out_dir, "card_turn.wav"),
                                  seq([tone(523, 0.14, 0.4, 0.25),
                                       tone(784, 0.26, 0.4, 0.3)]))

    # 胜利：上行琶音。
    made["card_win"] = write_wav(os.path.join(out_dir, "card_win.wav"),
                                 seq([tone(523, 0.11, 0.45, 0.3),
                                      tone(659, 0.11, 0.45, 0.3),
                                      tone(784, 0.11, 0.45, 0.3),
                                      tone(1046, 0.34, 0.5, 0.4)]))

    # 失败：下行小三度。
    made["card_lose"] = write_wav(os.path.join(out_dir, "card_lose.wav"),
                                  seq([tone(440, 0.14, 0.4, 0.3),
                                       tone(392, 0.14, 0.4, 0.3),
                                       tone(311, 0.36, 0.45, 0.4)]))

    # 能量不足：低频短促方波感。
    n = int(RATE * 0.16)
    buzz = []
    for i in range(n):
        t = i / RATE
        v = 1.0 if math.sin(2 * math.pi * 150 * t) > 0 else -1.0
        buzz.append(v * 0.35 * env(i, n, 0.01, 0.3))
    made["card_deny"] = write_wav(os.path.join(out_dir, "card_deny.wav"), buzz)

    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="build/raw")
    ap.add_argument("--out", default="client/assets")
    args = ap.parse_args()

    raw = os.path.abspath(args.raw)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    sizes = {}
    sizes["card_common.png"] = build_plate(
        os.path.join(raw, "card_common.png"), os.path.join(out, "card_common.png"),
        (74, 82, 92), (24, 28, 34))
    sizes["card_refined.png"] = build_plate(
        os.path.join(raw, "card_refined.png"), os.path.join(out, "card_refined.png"),
        (38, 68, 112), (14, 26, 44))
    sizes["card_epic.png"] = build_plate(
        os.path.join(raw, "card_epic.png"), os.path.join(out, "card_epic.png"),
        (86, 44, 112), (30, 16, 42))
    sizes["card_back.png"] = build_back(
        os.path.join(raw, "card_back.png"), os.path.join(out, "card_back.png"))
    sizes["table_bg.png"] = build_table(
        os.path.join(raw, "table_bg.png"), os.path.join(out, "table_bg.png"))
    sizes["avatar_frame.png"] = build_avatar(
        os.path.join(raw, "avatar_frame.png"), os.path.join(out, "avatar_frame.png"))

    panel = rounded_panel((PANEL_W, PANEL_H), (46, 36, 24), (22, 17, 12),
                          (168, 128, 66, 255), radius=20, width=4)
    panel.save(os.path.join(out, "panel.png"), optimize=True)
    sizes["panel.png"] = os.path.getsize(os.path.join(out, "panel.png"))

    plaque = build_plaque((PLAQUE_W, PLAQUE_H))
    plaque.save(os.path.join(out, "title_plaque.png"), optimize=True)
    sizes["title_plaque.png"] = os.path.getsize(os.path.join(out, "title_plaque.png"))

    # ---- 九宫格底板（第二轮：HUD 面板 + 按钮三态）----
    # HUD 细框面板：顶栏 / 计数盒 / 事件流水。
    plate = nine_plate((34, 28, 20), (14, 12, 9), GOLD_DIM + (255,),
                       GOLD_DEEP + (255,), radius=0, stud=0)
    plate.save(os.path.join(out, "hud_plate.png"), optimize=True)
    sizes["hud_plate.png"] = os.path.getsize(os.path.join(out, "hud_plate.png"))

    # HUD 厚框面板：双方信息盒 / 回合横幅（带角上菱形装饰）。
    frame = nine_plate((44, 35, 23), (18, 14, 10), GOLD + (255,),
                       GOLD_DEEP + (255,), radius=0, stud=6)
    frame.save(os.path.join(out, "hud_frame.png"), optimize=True)
    sizes["hud_frame.png"] = os.path.getsize(os.path.join(out, "hud_frame.png"))

    # 按钮三态：主按钮（暗金 + 深红）/ 次按钮（玄黑 + 暗金）。
    buttons = {
        "btn_primary.png": ((120, 48, 42), (58, 22, 20), GOLD + (255,),
                            GOLD_BRIGHT + (255,)),
        "btn_primary_hover.png": ((152, 64, 52), (76, 30, 26), GOLD_BRIGHT + (255,),
                                  (255, 236, 190, 255)),
        "btn_primary_pressed.png": ((78, 32, 28), (38, 16, 14), GOLD_DIM + (255,),
                                    GOLD + (255,)),
        "btn_plain.png": ((44, 37, 27), (22, 18, 13), GOLD_DIM + (255,),
                          GOLD_DEEP + (255,)),
        "btn_plain_hover.png": ((62, 51, 35), (30, 25, 18), GOLD + (255,),
                                GOLD_BRIGHT + (255,)),
        "btn_plain_pressed.png": ((26, 21, 15), (14, 12, 9), GOLD_DEEP + (255,),
                                  GOLD_DIM + (255,)),
    }
    for name, (top, bottom, border, inner) in buttons.items():
        img = nine_plate(top, bottom, border, inner, radius=20, stud=5)
        img.save(os.path.join(out, name), optimize=True)
        sizes[name] = os.path.getsize(os.path.join(out, name))

    # ---- 头像徽记（AI 职业图标 → 金色纹章框）----
    frame_path = os.path.join(out, "avatar_frame.png")
    size = build_avatar_icon(os.path.join(raw, "avatar_player.png"),
                             os.path.join(out, "avatar_player.png"),
                             frame_path, (320, 110, 710, 700))
    if size:
        sizes["avatar_player.png"] = size
    size = build_avatar_icon(os.path.join(raw, "avatar_ai.png"),
                             os.path.join(out, "avatar_ai.png"),
                             frame_path, (280, 60, 760, 860))
    if size:
        sizes["avatar_ai.png"] = size

    for name in sorted(sizes):
        print("bitmap %-20s %8d bytes" % (name, sizes[name]))

    sfx = build_sfx(os.path.join(out, "sfx"))
    total = sum(sizes.values()) + sum(sfx.values())
    for name in sorted(sfx):
        print("sfx    %-20s %8d bytes" % (name + ".wav", sfx[name]))
    print("TOTAL assets %d bytes (%.2f MB)" % (total, total / 1048576.0))


if __name__ == "__main__":
    main()
