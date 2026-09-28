#!/usr/bin/env python3
"""
Generate high-definition PS5 DualSense and Xbox Series/One controller prompt packs
for TriAevum / OoT3D TopScreen HUD.
"""

import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

DATA_ROOT = Path("/home/jesus/.var/app/io.github.coccofresco.TriAevum/data/TriAevum")
BASE_UI_DIR = DATA_ROOT / "textures" / "load" / "textures" / "0004000000033600" / "UI"
PACKS_ROOT = DATA_ROOT / "texture_packs"
FONT_PATH = "/usr/share/fonts/abattis-cantarell-fonts/Cantarell-Bold.otf"

MENU_FILES = [
    "tex1_512x256_7D6716CEB0D7F7FA_4_mip0.png",
    "06_EU_SPANISH/tex1_512x256_6664660F78E9D8C4_4_mip0.png",
    "01_US_ENGLISH/tex1_512x256_BB00B25B152582B6_4_mip0.png",
    "02_EU_ENGLISH/tex1_512x256_164411C4E5F37729_4_mip0.png",
    "07_US_SPANISH/tex1_512x256_9623362A9111CEDA_4_mip0.png",
]

def make_ps5_glyph(name, size=128):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = 4
    cx, cy = size / 2, size / 2
    r = (size - pad * 2) * 0.32

    if name in ("cross", "circle", "square", "triangle"):
        d.ellipse((pad, pad, size - pad, size - pad), fill=(22, 25, 34, 235), outline=(55, 62, 75, 255), width=3)

    if name == "cross":
        col = (84, 122, 227, 255)  # PS Blue
        w = max(4, int(size * 0.09))
        d.line((cx - r, cy - r, cx + r, cy + r), fill=col, width=w)
        d.line((cx - r, cy + r, cx + r, cy - r), fill=col, width=w)
    elif name == "circle":
        col = (229, 75, 75, 255)  # PS Red
        w = max(4, int(size * 0.08))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=w)
    elif name == "square":
        col = (233, 101, 160, 255)  # PS Pink
        w = max(4, int(size * 0.08))
        sr = r * 0.88
        d.rounded_rectangle((cx - sr, cy - sr, cx + sr, cy + sr), radius=int(size * 0.06), outline=col, width=w)
    elif name == "triangle":
        col = (0, 168, 143, 255)  # PS Green
        w = max(4, int(size * 0.08))
        h = r * 1.05
        pts = [(cx, cy - h), (cx - r * 1.05, cy + h * 0.7), (cx + r * 1.05, cy + h * 0.7)]
        d.polygon(pts, outline=col, width=w)
    elif name in ("l1", "r1", "l2", "r2"):
        d.rounded_rectangle((pad, int(size * 0.18), size - pad, int(size * 0.82)),
                            radius=int(size * 0.2), fill=(22, 25, 34, 235), outline=(72, 84, 96, 255), width=3)
        font = ImageFont.truetype(FONT_PATH, int(size * 0.42))
        text = name.upper()
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (size - tw) / 2 - bbox[0]
        ty = (size - th) / 2 - bbox[1]
        d.text((tx, ty), text, font=font, fill=(240, 240, 245, 255))
    return im

def make_xbox_glyph(name, size=128):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = 4
    colors = {
        "a": ((16, 124, 16, 255), (255, 255, 255, 255)),   # Xbox Green
        "b": ((232, 17, 35, 255), (255, 255, 255, 255)),   # Xbox Red
        "x": ((0, 120, 215, 255), (255, 255, 255, 255)),   # Xbox Blue
        "y": ((255, 185, 0, 255), (20, 20, 20, 255)),      # Xbox Yellow
    }
    if name in colors:
        bg, fg = colors[name]
        d.ellipse((pad, pad, size - pad, size - pad), fill=bg, outline=(255, 255, 255, 220), width=2)
        font = ImageFont.truetype(FONT_PATH, int(size * 0.6))
        text = name.upper()
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (size - tw) / 2 - bbox[0]
        ty = (size - th) / 2 - bbox[1]
        d.text((tx, ty), text, font=font, fill=fg)
    elif name in ("lb", "rb", "lt", "rt"):
        d.rounded_rectangle((pad, int(size * 0.18), size - pad, int(size * 0.82)),
                            radius=int(size * 0.2), fill=(25, 30, 40, 235), outline=(0, 120, 215, 255), width=3)
        font = ImageFont.truetype(FONT_PATH, int(size * 0.42))
        text = name.upper()
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (size - tw) / 2 - bbox[0]
        ty = (size - th) / 2 - bbox[1]
        d.text((tx, ty), text, font=font, fill=(240, 240, 245, 255))
    return im

def make_label(text, width=136, height=88, is_xbox=False):
    im = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    border_col = (0, 120, 215, 255) if is_xbox else (80, 90, 110, 255)
    d.rounded_rectangle((2, 2, width - 2, height - 2), radius=14,
                        fill=(20, 24, 32, 240), outline=border_col, width=2)
    font = ImageFont.truetype(FONT_PATH, int(height * 0.58))
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (width - tw) / 2 - bbox[0]
    ty = (height - th) / 2 - bbox[1]
    d.text((tx, ty), text, font=font, fill=(255, 255, 255, 255))
    return im

def patch_menu_texture(src_path, dst_path, controller_type):
    im = Image.open(src_path).convert("RGBA")
    w, h = im.size
    scale = w // 512  # Should be 8 for 4096x2048

    is_xbox = controller_type == "xbox"

    if is_xbox:
        g_x = make_xbox_glyph("x", 16 * scale)
        g_y = make_xbox_glyph("y", 16 * scale)
        g_r1 = make_xbox_glyph("rb", 16 * scale)
        g_r2 = make_xbox_glyph("rt", 16 * scale)
        g_l2 = make_xbox_glyph("lt", 16 * scale)
        lbl_r2 = make_label("RT", 17 * scale, 11 * scale, is_xbox=True)
        lbl_l2 = make_label("LT", 17 * scale, 11 * scale, is_xbox=True)
    else:
        g_x = make_ps5_glyph("square", 16 * scale)
        g_y = make_ps5_glyph("triangle", 16 * scale)
        g_r1 = make_ps5_glyph("r1", 16 * scale)
        g_r2 = make_ps5_glyph("r2", 16 * scale)
        g_l2 = make_ps5_glyph("l2", 16 * scale)
        lbl_r2 = make_label("R2", 17 * scale, 11 * scale, is_xbox=False)
        lbl_l2 = make_label("L2", 17 * scale, 11 * scale, is_xbox=False)

    # 1. aux_142 (X / Square): (158, 142, 16, 16) * scale
    im.paste(g_x, (158 * scale, 142 * scale), g_x)
    # 2. aux_158 (Y / Triangle): (158, 158, 16, 16) * scale
    im.paste(g_y, (158 * scale, 158 * scale), g_y)
    # 3. aux_126 (ZR / R2 / RT): (158, 126, 16, 16) * scale
    im.paste(g_r2, (158 * scale, 126 * scale), g_r2)
    # 4. aux_190 (ZL / L2 / LT): (158, 190, 16, 16) * scale
    im.paste(g_l2, (158 * scale, 190 * scale), g_l2)
    # 5. aux_174 (R / R1 / RB): (158, 174, 16, 16) * scale
    im.paste(g_r1, (158 * scale, 174 * scale), g_r1)
    # 6. label_0 (ZR label): (440, 190, 17, 11) * scale
    im.paste(lbl_r2, (440 * scale, 190 * scale), lbl_r2)
    # 7. label_1 (ZL label): (440, 201, 17, 11) * scale
    im.paste(lbl_l2, (440 * scale, 201 * scale), lbl_l2)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst_path)
    print(f"Patched [{controller_type.upper()}] -> {dst_path}")

def main():
    print("Preparing Controller Texture Packs...")
    PACKS_ROOT.mkdir(parents=True, exist_ok=True)
    nintendo_dir = PACKS_ROOT / "nintendo" / "load" / "textures" / "0004000000033600" / "UI"
    ps5_dir = PACKS_ROOT / "ps5" / "load" / "textures" / "0004000000033600" / "UI"
    xbox_dir = PACKS_ROOT / "xbox" / "load" / "textures" / "0004000000033600" / "UI"

    # 1. First backup Nintendo original if not present
    for rel in MENU_FILES:
        src = BASE_UI_DIR / rel
        if not src.is_file():
            continue
        dst_nintendo = nintendo_dir / rel
        if not dst_nintendo.is_file():
            dst_nintendo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst_nintendo)
            print(f"Backed up Nintendo original: {rel}")

        # Patch PS5
        dst_ps5 = ps5_dir / rel
        patch_menu_texture(dst_nintendo, dst_ps5, "ps5")

        # Patch Xbox
        dst_xbox = xbox_dir / rel
        patch_menu_texture(dst_nintendo, dst_xbox, "xbox")

    # Copy all other UI textures (custom_menu, numbers, etc.) to all packs so they are fully self-contained
    for other in BASE_UI_DIR.glob("**/*.png"):
        rel = other.relative_to(BASE_UI_DIR)
        for target_dir in (nintendo_dir, ps5_dir, xbox_dir):
            dest = target_dir / rel
            if not dest.is_file():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(other, dest)

    print("All texture packs successfully created in:", PACKS_ROOT)

if __name__ == "__main__":
    main()
