#!/usr/bin/env python3
"""
Script para agregar TriAevum automáticamente como Non-Steam Game en Steam / Steam Deck.
Analiza y actualiza shortcuts.vdf sin corromperlo.
"""
import os
import sys
import struct
import zlib
from pathlib import Path

def find_steam_userdata_dirs():
    candidates = [
        Path.home() / ".local" / "share" / "Steam" / "userdata",
        Path.home() / ".steam" / "steam" / "userdata",
        Path.home() / ".steam" / "root" / "userdata",
        Path.home() / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam" / "userdata",
    ]
    found = []
    for c in candidates:
        if c.exists() and c.is_dir():
            for user in c.iterdir():
                if user.is_dir() and user.name.isdigit() and (user / "config").exists():
                    found.append(user / "config")
    return list(dict.fromkeys(found))

def generate_app_id(exe_path, app_name):
    unique = f'"{exe_path}""{app_name}"'
    crc = zlib.crc32(unique.encode("utf-8")) | 0x80000000
    return crc

def parse_vdf_shortcuts(path):
    if not path.exists():
        return []
    with open(path, "rb") as f:
        data = f.read()
    
    shortcuts = []
    idx = 0
    # Basic binary VDF parser for shortcuts
    if b"shortcuts\x00" not in data:
        return []
    
    pos = data.find(b"shortcuts\x00") + len(b"shortcuts\x00")
    
    current_shortcut = {}
    while pos < len(data):
        type_byte = data[pos]
        pos += 1
        if type_byte == 0x08: # End of map
            if current_shortcut:
                shortcuts.append(current_shortcut)
                current_shortcut = {}
            if pos < len(data) and data[pos] == 0x08:
                break
            continue
        elif type_byte == 0x00: # Nested map
            null_pos = data.find(b"\x00", pos)
            key = data[pos:null_pos].decode("utf-8", "ignore")
            pos = null_pos + 1
            if current_shortcut:
                shortcuts.append(current_shortcut)
                current_shortcut = {}
        elif type_byte == 0x01: # String
            k_end = data.find(b"\x00", pos)
            key = data[pos:k_end].decode("utf-8", "ignore")
            pos = k_end + 1
            v_end = data.find(b"\x00", pos)
            val = data[pos:v_end].decode("utf-8", "ignore")
            pos = v_end + 1
            current_shortcut[key] = val
        elif type_byte == 0x02: # 32-bit int
            k_end = data.find(b"\x00", pos)
            key = data[pos:k_end].decode("utf-8", "ignore")
            pos = k_end + 1
            val = struct.unpack("<I", data[pos:pos+4])[0]
            pos += 4
            current_shortcut[key] = val
    if current_shortcut:
        shortcuts.append(current_shortcut)
    return shortcuts

def build_vdf_shortcuts(shortcuts):
    out = bytearray()
    out.extend(b"\x00shortcuts\x00")
    for idx, sc in enumerate(shortcuts):
        out.extend(f"\x00{idx}\x00".encode("utf-8"))
        for k, v in sc.items():
            if isinstance(v, str):
                out.append(0x01)
                out.extend(f"{k}\x00{v}\x00".encode("utf-8"))
            elif isinstance(v, int):
                out.append(0x02)
                out.extend(f"{k}\x00".encode("utf-8"))
                out.extend(struct.pack("<I", v))
        out.append(0x08)
    out.append(0x08)
    out.append(0x08)
    return bytes(out)

def add_triaevum_to_steam():
    project_dir = Path(__file__).resolve().parent.parent
    launcher_sh = project_dir / "iniciar_juego.sh"
    icon_path = project_dir / "resources" / "app_icon.png"
    banner_path = project_dir / "resources" / "steam_banner.png"
    
    app_name = "TriAevum (Zelda OoT 3D)"
    exe_str = f'"{launcher_sh}"'
    start_dir = f'"{project_dir}"'
    
    user_configs = find_steam_userdata_dirs()
    if not user_configs:
        print("❌ No se encontró ninguna instalación de Steam local en ~/.local/share/Steam ni en ~/.steam")
        return False
        
    for cfg in user_configs:
        shortcuts_vdf = cfg / "shortcuts.vdf"
        existing = parse_vdf_shortcuts(shortcuts_vdf) if shortcuts_vdf.exists() else []
        
        # Check if already exists
        already_present = False
        for sc in existing:
            if sc.get("AppName") == app_name or sc.get("Exe") == exe_str:
                already_present = True
                sc["Exe"] = exe_str
                sc["StartDir"] = start_dir
                sc["icon"] = str(icon_path)
                sc["LaunchOptions"] = "--fps 120 --res 1080p"
                break
                
        if not already_present:
            new_entry = {
                "appid": generate_app_id(str(launcher_sh), app_name),
                "AppName": app_name,
                "Exe": exe_str,
                "StartDir": start_dir,
                "icon": str(icon_path),
                "ShortcutPath": "",
                "LaunchOptions": "--fps 120 --res 1080p",
                "IsHidden": 0,
                "AllowDesktopConfig": 1,
                "AllowOverlay": 1,
                "OpenVR": 0,
                "Devkit": 0,
                "DevkitGameID": "",
                "DevkitOverrideAppID": 0,
                "LastPlayTime": 0,
                "FlatpakAppID": "",
                "tags": ""
            }
            existing.append(new_entry)
            
        # Write back
        vdf_bytes = build_vdf_shortcuts(existing)
        # Backup old
        if shortcuts_vdf.exists():
            backup_path = shortcuts_vdf.with_suffix(".vdf.bak")
            with open(backup_path, "wb") as bf:
                with open(shortcuts_vdf, "rb") as orig:
                    bf.write(orig.read())
                    
        with open(shortcuts_vdf, "wb") as f:
            f.write(vdf_bytes)
            
        print(f"✅ ¡TriAevum añadido con éxito a Steam en: {shortcuts_vdf}")
        
        # Also copy grid banner if grid folder exists
        grid_dir = cfg / "grid"
        if grid_dir.exists():
            try:
                import shutil
                app_id_signed = generate_app_id(str(launcher_sh), app_name)
                shutil.copyfile(banner_path, grid_dir / f"{app_id_signed}.png")
                shutil.copyfile(banner_path, grid_dir / f"{app_id_signed}p.png")
                print(f"🖼️ Carátula instalada en la biblioteca de Steam ({grid_dir})")
            except Exception as e:
                pass
                
    print("\n👉 Por favor, reinicia Steam si está abierto para ver TriAevum en tu Biblioteca.")
    return True

if __name__ == "__main__":
    add_triaevum_to_steam()
