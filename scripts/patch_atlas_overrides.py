#!/usr/bin/env python3
"""
Generate controller-specific atlas_overrides.o3tu packs for TriAevum / OoT3D.
Supports:
  - PlayStation 5 (DualSense: ✖, ⭘, ◼, ▲, L1, R1, L2, R2, Options, Create)
  - Xbox Series / One (A, B, X, Y, LB, RB, LT, RT, Menu, View)
  - Nintendo Original (Switch / 3DS default)

Patches:
  1. menu_top_parts00.ctxb (Entries 0, 2, 4, 5, 6, 7: RGBA4444 512x256):
     - aux_126 (158, 126, 16, 16): R2 / RT / ZR
     - aux_142 (158, 142, 16, 16): Square / X / Y
     - aux_158 (158, 158, 16, 16): Triangle / Y / X
     - aux_174 (158, 174, 16, 16): R1 / RB / R
     - aux_190 (158, 190, 16, 16): L2 / LT / ZL
     - label_0 (440, 190, 17, 11): R2 / RT / ZR
     - label_1 (440, 201, 17, 11): L2 / LT / ZL
  2. custom_menu00.ctxb (Profile 0: RGBA8 512x512):
     - Bubble A (269, 253, 44, 44): Cross / A
     - Bubble B (335, 253, 44, 44): Circle / B
     - Bubble X (401, 253, 44, 44): Square / X
     - Bubble Y (269, 319, 44, 44): Triangle / Y
     - Bubble ZL (335, 319, 44, 44): L2 / LT
     - Bubble ZR (401, 319, 44, 44): R2 / RT
     - START (4, 414, 60, 12): OPTIONS / MENU / START
     - SELECT (436, 412, 60, 12): CREATE / VIEW / SELECT
  3. hud_all00.ctxb (In-game HUD: RGBA4444 256x256):
     - Action button A (67, 3, 40, 40): Cross / A
     - Sword button B (24, 15, 48, 48): Circle / B
"""

from __future__ import annotations

import io
import os
import struct
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.oot3d.decomp_support.scripts.build_topscreen_texture_override_pack import (
    read_level3_romfs_file, CTXB_HEADER_SIZE, LANGUAGES
)

def get_data_root() -> Path:
    if env := os.environ.get("TRIAEVUM_DATA_DIR"):
        return Path(env)
    flatpak = Path.home() / ".var/app/io.github.coccofresco.TriAevum/data/TriAevum"
    if flatpak.exists():
        return flatpak
    if xdg := os.environ.get("XDG_DATA_HOME"):
        p = Path(xdg) / "TriAevum"
        if p.exists():
            return p
    local_share = Path.home() / ".local/share/TriAevum"
    if local_share.exists():
        return local_share
    if appdata := os.environ.get("APPDATA"):
        p = Path(appdata) / "TriAevum"
        if p.exists():
            return p
    local_p = Path(__file__).resolve().parent.parent / "data" / "TriAevum"
    if local_p.exists():
        return local_p
    return flatpak

def find_original_o3tu(data_root: Path) -> Path:
    if env := os.environ.get("TRIAEVUM_O3TU_PATH"):
        p = Path(env)
        if p.is_file():
            return p
    backup = data_root / "mods" / "topscreen" / "atlas_overrides_original_backup.o3tu"
    if backup.is_file():
        return backup
    topscreen_dir = data_root / "mods" / "topscreen"
    if topscreen_dir.is_dir():
        matches = [p for p in topscreen_dir.glob("*/atlas_overrides.o3tu") if "packs" not in str(p)]
        if matches:
            return matches[0]
    return topscreen_dir / "9e96a47047e7be3492bdf2e4d8b08f150673792877a7d965c55cdb3aec663daf" / "atlas_overrides.o3tu"

def find_romfs(data_root: Path) -> Path:
    if env := os.environ.get("TRIAEVUM_ROMFS_PATH"):
        p = Path(env)
        if p.is_file():
            return p
    sources_dir = data_root / "sources"
    if sources_dir.is_dir():
        matches = list(sources_dir.glob("*/romfs.bin"))
        if matches:
            return matches[0]
    return sources_dir / "romfs.bin"

def find_font():
    candidates = [
        "/usr/share/fonts/abattis-cantarell-fonts/Cantarell-Bold.otf",
        "/usr/share/fonts/cantarell/Cantarell-Bold.otf",
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf",
    ]
    for c in candidates:
        if Path(c).is_file():
            return c
    return None

def get_font(size: int):
    f_path = find_font()
    if f_path:
        try:
            return ImageFont.truetype(f_path, size)
        except Exception:
            pass
    return ImageFont.load_default()

DATA_ROOT = get_data_root()
ORIGINAL_O3TU = find_original_o3tu(DATA_ROOT)
BACKUP_O3TU = DATA_ROOT / "mods" / "topscreen" / "atlas_overrides_original_backup.o3tu"
PACKS_DIR = DATA_ROOT / "mods" / "topscreen" / "packs"
ROMFS_PATH = find_romfs(DATA_ROOT)

def fnv1a64(data: bytes) -> int:
    value = 0xCBF29CE484222325
    for byte in data:
        value ^= byte
        value = (value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return value

def morton8(x: int, y: int) -> int:
    return ((x & 1) << 0) | ((y & 1) << 1) | ((x & 2) << 1) | ((y & 2) << 2) | ((x & 4) << 2) | ((y & 4) << 3)

def detile_rgba4444(payload: bytes, w: int, h: int) -> Image.Image:
    img = Image.new("RGBA", (w, h))
    pixels = img.load()
    aligned_w = (w + 7) & ~7
    for y in range(h):
        for x in range(w):
            tile_idx = (y // 8) * (aligned_w // 8) + (x // 8)
            mort = morton8(x % 8, y % 8)
            pixel_idx = tile_idx * 64 + mort
            offset = pixel_idx * 2
            val = payload[offset] | (payload[offset + 1] << 8)
            r = ((val >> 12) & 0xF) * 17
            g = ((val >> 8) & 0xF) * 17
            b = ((val >> 4) & 0xF) * 17
            a = (val & 0xF) * 17
            pixels[x, y] = (r, g, b, a)
    return img

def tile_rgba4444(img: Image.Image) -> bytes:
    w, h = img.size
    aligned_w = (w + 7) & ~7
    out = bytearray(w * h * 2)
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            r4 = (r + 8) // 17
            g4 = (g + 8) // 17
            b4 = (b + 8) // 17
            a4 = (a + 8) // 17
            val = (r4 << 12) | (g4 << 8) | (b4 << 4) | a4
            tile_idx = (y // 8) * (aligned_w // 8) + (x // 8)
            mort = morton8(x % 8, y % 8)
            pixel_idx = tile_idx * 64 + mort
            offset = pixel_idx * 2
            out[offset] = val & 0xFF
            out[offset + 1] = (val >> 8) & 0xFF
    return bytes(out)

def detile_rgba8(payload: bytes, w: int, h: int) -> Image.Image:
    img = Image.new("RGBA", (w, h))
    pixels = img.load()
    aligned_w = (w + 7) & ~7
    for y in range(h):
        for x in range(w):
            tile_idx = (y // 8) * (aligned_w // 8) + (x // 8)
            mort = morton8(x % 8, y % 8)
            pixel_idx = tile_idx * 64 + mort
            offset = pixel_idx * 4
            a = payload[offset]
            b = payload[offset + 1]
            g = payload[offset + 2]
            r = payload[offset + 3]
            pixels[x, y] = (r, g, b, a)
    return img

def tile_rgba8(img: Image.Image) -> bytes:
    w, h = img.size
    aligned_w = (w + 7) & ~7
    out = bytearray(w * h * 4)
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            tile_idx = (y // 8) * (aligned_w // 8) + (x // 8)
            mort = morton8(x % 8, y % 8)
            pixel_idx = tile_idx * 64 + mort
            offset = pixel_idx * 4
            out[offset] = a
            out[offset + 1] = b
            out[offset + 2] = g
            out[offset + 3] = r
    return bytes(out)

def make_glyph_16(style: str, name: str) -> Image.Image:
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 8.0, 8.0

    if style == "ps5":
        if name in ("cross", "circle", "square", "triangle"):
            d.ellipse((1, 1, 14, 14), fill=(20, 24, 32, 245), outline=(60, 70, 85, 255), width=1)
            r = 4.2
            if name == "cross":
                col = (80, 130, 245, 255)
                d.line((cx - r, cy - r, cx + r, cy + r), fill=col, width=2)
                d.line((cx - r, cy + r, cx + r, cy - r), fill=col, width=2)
            elif name == "circle":
                col = (235, 70, 70, 255)
                d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=2)
            elif name == "square":
                col = (235, 100, 165, 255)
                sr = r * 0.9
                d.rounded_rectangle((cx - sr, cy - sr, cx + sr, cy + sr), radius=1, outline=col, width=2)
            elif name == "triangle":
                col = (0, 175, 145, 255)
                h = r * 1.05
                pts = [(cx, cy - h), (cx - r * 1.05, cy + h * 0.7), (cx + r * 1.05, cy + h * 0.7)]
                d.polygon(pts, outline=col, width=2)
        elif name in ("l1", "r1", "l2", "r2"):
            d.rounded_rectangle((0, 2, 15, 13), radius=3, fill=(20, 24, 32, 245), outline=(75, 88, 105, 255), width=1)
            font = get_font(8)
            text = name.upper()
            bbox = d.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = (16 - tw) / 2.0 - bbox[0]
            ty = (16 - th) / 2.0 - bbox[1]
            d.text((tx, ty), text, font=font, fill=(245, 245, 250, 255))
    elif style == "xbox":
        colors = {
            "a": ((16, 124, 16, 255), (255, 255, 255, 255)),
            "b": ((232, 17, 35, 255), (255, 255, 255, 255)),
            "x": ((0, 120, 215, 255), (255, 255, 255, 255)),
            "y": ((255, 185, 0, 255), (20, 20, 20, 255)),
        }
        if name in colors:
            bg, fg = colors[name]
            d.ellipse((1, 1, 14, 14), fill=bg, outline=(240, 240, 240, 200), width=1)
            font = get_font(9)
            text = name.upper()
            bbox = d.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = (16 - tw) / 2.0 - bbox[0]
            ty = (16 - th) / 2.0 - bbox[1]
            d.text((tx, ty), text, font=font, fill=fg)
        elif name in ("lb", "rb", "lt", "rt"):
            d.rounded_rectangle((0, 2, 15, 13), radius=3, fill=(24, 28, 38, 245), outline=(0, 120, 215, 255), width=1)
            font = get_font(8)
            text = name.upper()
            bbox = d.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = (16 - tw) / 2.0 - bbox[0]
            ty = (16 - th) / 2.0 - bbox[1]
            d.text((tx, ty), text, font=font, fill=(245, 245, 250, 255))
    return im

def make_label_17x11(text: str, is_xbox: bool = False) -> Image.Image:
    im = Image.new("RGBA", (17, 11), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    border_col = (0, 120, 215, 255) if is_xbox else (75, 88, 105, 255)
    d.rounded_rectangle((0, 0, 16, 10), radius=2, fill=(18, 22, 28, 245), outline=border_col, width=1)
    font = get_font(8)
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (17 - tw) / 2.0 - bbox[0]
    ty = (11 - th) / 2.0 - bbox[1]
    d.text((tx, ty), text, font=font, fill=(245, 245, 250, 255))
    return im

def make_bubble_44(style: str, name: str) -> Image.Image:
    im = Image.new("RGBA", (44, 44), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 22.0, 22.0
    r = 15.0

    if style == "ps5":
        d.ellipse((1, 1, 42, 42), fill=(24, 28, 38, 250), outline=(50, 60, 75, 255), width=2)
        d.arc((3, 3, 40, 40), start=200, end=340, fill=(120, 140, 170, 200), width=2)
        if name == "cross":
            col = (85, 140, 255, 255)
            d.line((cx - r, cy - r, cx + r, cy + r), fill=col, width=4)
            d.line((cx - r, cy + r, cx + r, cy - r), fill=col, width=4)
        elif name == "circle":
            col = (240, 75, 75, 255)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=4)
        elif name == "square":
            col = (240, 105, 170, 255)
            sr = r * 0.88
            d.rounded_rectangle((cx - sr, cy - sr, cx + sr, cy + sr), radius=3, outline=col, width=4)
        elif name == "triangle":
            col = (0, 185, 155, 255)
            h = r * 1.05
            pts = [(cx, cy - h), (cx - r * 1.05, cy + h * 0.7), (cx + r * 1.05, cy + h * 0.7)]
            d.polygon(pts, outline=col, width=4)
        elif name in ("l2", "r2", "l1", "r1"):
            font = get_font(19)
            text = name.upper()
            bbox = d.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = (44 - tw) / 2.0 - bbox[0]
            ty = (44 - th) / 2.0 - bbox[1]
            d.text((tx, ty), text, font=font, fill=(245, 245, 255, 255))
    elif style == "xbox":
        colors = {
            "a": ((16, 124, 16, 255), (255, 255, 255, 255)),
            "b": ((232, 17, 35, 255), (255, 255, 255, 255)),
            "x": ((0, 120, 215, 255), (255, 255, 255, 255)),
            "y": ((255, 185, 0, 255), (20, 20, 20, 255)),
        }
        if name in colors:
            bg, fg = colors[name]
            d.ellipse((1, 1, 42, 42), fill=bg, outline=(255, 255, 255, 220), width=2)
            d.arc((3, 3, 40, 40), start=200, end=340, fill=(255, 255, 255, 180), width=2)
            font = get_font(24)
            text = name.upper()
            bbox = d.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = (44 - tw) / 2.0 - bbox[0]
            ty = (44 - th) / 2.0 - bbox[1]
            d.text((tx, ty), text, font=font, fill=fg)
        elif name in ("lt", "rt", "lb", "rb"):
            d.ellipse((1, 1, 42, 42), fill=(24, 28, 38, 250), outline=(0, 120, 215, 255), width=2)
            d.arc((3, 3, 40, 40), start=200, end=340, fill=(120, 180, 255, 180), width=2)
            font = get_font(19)
            text = name.upper()
            bbox = d.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = (44 - tw) / 2.0 - bbox[0]
            ty = (44 - th) / 2.0 - bbox[1]
            d.text((tx, ty), text, font=font, fill=(245, 245, 255, 255))
    return im

def make_pill_button(text: str, w: int = 60, h: int = 12) -> Image.Image:
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=4, fill=(18, 22, 28, 240), outline=(65, 75, 90, 255), width=1)
    font = get_font(8)
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (w - tw) / 2.0 - bbox[0]
    ty = (h - th) / 2.0 - bbox[1]
    d.text((tx, ty), text, font=font, fill=(240, 240, 245, 255))
    return im

def patch_menu_top_parts(img: Image.Image, style: str) -> Image.Image:
    out = img.copy()
    if style == "ps5":
        g_r2 = make_glyph_16("ps5", "r2")
        g_sq = make_glyph_16("ps5", "square")
        g_tr = make_glyph_16("ps5", "triangle")
        g_r1 = make_glyph_16("ps5", "r1")
        g_l2 = make_glyph_16("ps5", "l2")
        lbl_r2 = make_label_17x11("R2", is_xbox=False)
        lbl_l2 = make_label_17x11("L2", is_xbox=False)
        out.paste(g_r2, (158, 126), g_r2)
        out.paste(g_sq, (158, 142), g_sq)
        out.paste(g_tr, (158, 158), g_tr)
        out.paste(g_r1, (158, 174), g_r1)
        out.paste(g_l2, (158, 190), g_l2)
        out.paste(lbl_r2, (440, 190), lbl_r2)
        out.paste(lbl_l2, (440, 201), lbl_l2)
    elif style == "xbox":
        g_rt = make_glyph_16("xbox", "rt")
        g_x = make_glyph_16("xbox", "x")
        g_y = make_glyph_16("xbox", "y")
        g_rb = make_glyph_16("xbox", "rb")
        g_lt = make_glyph_16("xbox", "lt")
        lbl_rt = make_label_17x11("RT", is_xbox=True)
        lbl_lt = make_label_17x11("LT", is_xbox=True)
        out.paste(g_rt, (158, 126), g_rt)
        out.paste(g_x, (158, 142), g_x)
        out.paste(g_y, (158, 158), g_y)
        out.paste(g_rb, (158, 174), g_rb)
        out.paste(g_lt, (158, 190), g_lt)
        out.paste(lbl_rt, (440, 190), lbl_rt)
        out.paste(lbl_lt, (440, 201), lbl_lt)
    return out

def patch_custom_menu(img: Image.Image, style: str) -> Image.Image:
    out = img.copy()
    if style == "ps5":
        b_a = make_bubble_44("ps5", "cross")
        b_b = make_bubble_44("ps5", "circle")
        b_x = make_bubble_44("ps5", "square")
        b_y = make_bubble_44("ps5", "triangle")
        b_zl = make_bubble_44("ps5", "l2")
        b_zr = make_bubble_44("ps5", "r2")
        p_start = make_pill_button("OPTIONS")
        p_select = make_pill_button("CREATE")
        out.paste(b_a, (269, 253), b_a)
        out.paste(b_b, (335, 253), b_b)
        out.paste(b_x, (401, 253), b_x)
        out.paste(b_y, (269, 319), b_y)
        out.paste(b_zl, (335, 319), b_zl)
        out.paste(b_zr, (401, 319), b_zr)
        out.paste(p_start, (4, 414), p_start)
        out.paste(p_select, (436, 412), p_select)
    elif style == "xbox":
        b_a = make_bubble_44("xbox", "a")
        b_b = make_bubble_44("xbox", "b")
        b_x = make_bubble_44("xbox", "x")
        b_y = make_bubble_44("xbox", "y")
        b_zl = make_bubble_44("xbox", "lt")
        b_zr = make_bubble_44("xbox", "rt")
        p_start = make_pill_button("MENU")
        p_select = make_pill_button("VIEW")
        out.paste(b_a, (269, 253), b_a)
        out.paste(b_b, (335, 253), b_b)
        out.paste(b_x, (401, 253), b_x)
        out.paste(b_y, (269, 319), b_y)
        out.paste(b_zl, (335, 319), b_zl)
        out.paste(b_zr, (401, 319), b_zr)
        out.paste(p_start, (4, 414), p_start)
        out.paste(p_select, (436, 412), p_select)
    return out

def patch_hud_all(img_orig: Image.Image, style: str) -> Image.Image:
    img = img_orig.copy()
    d = ImageDraw.Draw(img)
    # A button center is (67 + 20, 3 + 20) = (87, 23)
    # B button center is (24 + 24, 15 + 24) = (48, 39)
    if style == "ps5":
        d.ellipse((78, 14, 96, 32), fill=(136, 136, 136, 102))
        r = 6
        cx, cy = 87, 23
        d.line((cx - r, cy - r, cx + r, cy + r), fill=(85, 85, 85, 51), width=3)
        d.line((cx - r, cy + r, cx + r, cy - r), fill=(85, 85, 85, 51), width=3)
        d.ellipse((39, 30, 57, 48), fill=(119, 119, 119, 85))
        r_b = 6
        cx_b, cy_b = 48, 39
        d.ellipse((cx_b - r_b, cy_b - r_b, cx_b + r_b, cy_b + r_b), outline=(68, 68, 68, 51), width=3)
    elif style == "xbox":
        d.ellipse((78, 14, 96, 32), fill=(136, 136, 136, 102))
        font = get_font(14)
        bbox = d.textbbox((0, 0), "A", font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text((87 - tw/2.0 - bbox[0], 23 - th/2.0 - bbox[1]), "A", font=font, fill=(85, 85, 85, 51))
        d.ellipse((39, 30, 57, 48), fill=(119, 119, 119, 85))
        bbox = d.textbbox((0, 0), "B", font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text((48 - tw/2.0 - bbox[0], 39 - th/2.0 - bbox[1]), "B", font=font, fill=(68, 68, 68, 51))
    return img

class OverridePack:
    def __init__(self, data: bytes):
        self.version = struct.unpack_from("<I", data, 4)[0]
        count, profile_count = struct.unpack_from("<II", data, 8)
        self.entries = []
        cursor = 16
        for _ in range(count):
            orig_hash, repl_hash, size = struct.unpack_from("<QQI", data, cursor)
            cursor += 20
            payload = data[cursor:cursor+size]
            cursor += size
            self.entries.append({
                "original_hash": orig_hash,
                "replacement_hash": repl_hash,
                "payload": payload,
            })
        self.profiles = []
        for _ in range(profile_count):
            name_len, w, h, fmt = struct.unpack_from("<IHHB", data, cursor)
            cursor += 9 + 3
            size, phash = struct.unpack_from("<IQ", data, cursor)
            cursor += 12
            name = data[cursor:cursor+name_len].decode("utf-8")
            cursor += name_len
            payload = data[cursor:cursor+size]
            cursor += size
            self.profiles.append({
                "name": name,
                "width": w,
                "height": h,
                "format": fmt,
                "hash": phash,
                "payload": payload,
            })

    def serialize(self) -> bytes:
        out = bytearray(b"O3TU")
        out += struct.pack("<III", 2, len(self.entries), len(self.profiles))
        for entry in self.entries:
            p = entry["payload"]
            h = fnv1a64(p)
            out += struct.pack("<QQI", entry["original_hash"], h, len(p))
            out += p
        for prof in self.profiles:
            p = prof["payload"]
            h = fnv1a64(p)
            enc_name = prof["name"].encode("utf-8")
            out += struct.pack("<IHHB3xIQ", len(enc_name), prof["width"], prof["height"],
                               prof["format"], len(p), h)
            out += enc_name
            out += p
        return bytes(out)

def load_romfs_hud_entries():
    hud_entries = []
    seen_hashes = set()
    if not ROMFS_PATH.is_file():
        return hud_entries
    for lang in LANGUAGES:
        try:
            data = read_level3_romfs_file(ROMFS_PATH, f"menu/{lang}/hud_all00.ctxb")
            payload = data[CTXB_HEADER_SIZE:]
            h = fnv1a64(payload)
            if h not in seen_hashes:
                seen_hashes.add(h)
                hud_entries.append((h, payload, lang))
        except Exception:
            pass
    return hud_entries

def build_all_packs():
    print(f"Reading original O3TU pack from: {ORIGINAL_O3TU}")
    if not ORIGINAL_O3TU.is_file():
        raise FileNotFoundError(f"Original O3TU not found: {ORIGINAL_O3TU}")

    with open(ORIGINAL_O3TU, "rb") as f:
        orig_bytes = f.read()

    if not BACKUP_O3TU.is_file():
        BACKUP_O3TU.parent.mkdir(parents=True, exist_ok=True)
        BACKUP_O3TU.write_bytes(orig_bytes)
        print(f"Backed up original O3TU to: {BACKUP_O3TU}")

    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    hud_originals = load_romfs_hud_entries()
    print(f"Loaded {len(hud_originals)} original HUD variants from RomFS")

    styles = ["nintendo", "ps5", "xbox"]
    for style in styles:
        print(f"\nProcessing pack: [{style.upper()}]...")
        pack = OverridePack(orig_bytes)

        if style != "nintendo":
            # 1. Patch menu_top_parts entries
            for idx, entry in enumerate(pack.entries):
                if len(entry["payload"]) == 262144:
                    img = detile_rgba4444(entry["payload"], 512, 256)
                    patched = patch_menu_top_parts(img, style)
                    entry["payload"] = tile_rgba4444(patched)

            # 2. Patch Profile 0 (custom_menu00)
            for prof in pack.profiles:
                if prof["name"] == "oot3d/topscreen/2.1.1/menu_atlas":
                    img = detile_rgba8(prof["payload"], prof["width"], prof["height"])
                    patched = patch_custom_menu(img, style)
                    prof["payload"] = tile_rgba8(patched)

            # 3. Add hud_all00 entries
            for orig_hash, payload, lang in hud_originals:
                img = detile_rgba4444(payload, 256, 256)
                patched = patch_hud_all(img, style)
                patched_payload = tile_rgba4444(patched)
                pack.entries.append({
                    "original_hash": orig_hash,
                    "replacement_hash": fnv1a64(patched_payload),
                    "payload": patched_payload,
                })
        else:
            # For Nintendo, also keep unpatched hud_all00 entries if desired or keep 8 entries
            pass

        out_data = pack.serialize()
        out_path = PACKS_DIR / f"atlas_overrides_{style}.o3tu"
        out_path.write_bytes(out_data)
        print(f"  Saved: {out_path} ({len(pack.entries)} entries, {len(out_data)} bytes)")

    print("\nAll packs successfully generated in:", PACKS_DIR)

if __name__ == "__main__":
    build_all_packs()
