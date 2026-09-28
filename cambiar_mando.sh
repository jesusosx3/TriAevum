#!/usr/bin/env bash
set -e

MANDO="${1:-ps5}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -n "$TRIAEVUM_DATA_DIR" ] && [ -d "$TRIAEVUM_DATA_DIR" ]; then
    DATA_ROOT="$TRIAEVUM_DATA_DIR"
elif [ -d "$HOME/.var/app/io.github.coccofresco.TriAevum/data/TriAevum" ]; then
    DATA_ROOT="$HOME/.var/app/io.github.coccofresco.TriAevum/data/TriAevum"
elif [ -n "$XDG_DATA_HOME" ] && [ -d "$XDG_DATA_HOME/TriAevum" ]; then
    DATA_ROOT="$XDG_DATA_HOME/TriAevum"
elif [ -d "$HOME/.local/share/TriAevum" ]; then
    DATA_ROOT="$HOME/.local/share/TriAevum"
else
    DATA_ROOT="$SCRIPT_DIR/data/TriAevum"
fi

MOD_DIR=$(find "$DATA_ROOT/mods/topscreen" -maxdepth 1 -mindepth 1 -type d ! -name "packs" 2>/dev/null | head -n 1)
if [ -z "$MOD_DIR" ]; then
    MOD_DIR="$DATA_ROOT/mods/topscreen/9e96a47047e7be3492bdf2e4d8b08f150673792877a7d965c55cdb3aec663daf"
fi
PACKS_O3TU_DIR="$DATA_ROOT/mods/topscreen/packs"
PACK_DIR="$DATA_ROOT/texture_packs/$MANDO/load/textures/0004000000033600/UI"
ACTIVE_UI_DIR="$DATA_ROOT/textures/load/textures/0004000000033600/UI"
CONTROLS_JSON="$DATA_ROOT/config/controls.json"

case "$MANDO" in
    ps5|playstation|dualsense)
        MANDO="ps5"
        NOMBRE="PlayStation 5 (DualSense: ✖, ⭘, ◼, ▲, L1, R1, L2, R2)"
        DUALSENSE_GUID=""
        AIM_SOURCE="automatic"
        ;;
    xbox|one|series)
        MANDO="xbox"
        NOMBRE="Xbox Series / One (A, B, X, Y, LB, RB, LT, RT)"
        DUALSENSE_GUID=""
        AIM_SOURCE="automatic"
        ;;
    nintendo|original|3ds|switch)
        MANDO="nintendo"
        NOMBRE="Nintendo Original (A, B, X, Y, L, R, ZL, ZR)"
        DUALSENSE_GUID=""
        AIM_SOURCE="automatic"
        ;;
    *)
        echo "Uso: $0 [ps5 | xbox | nintendo]"
        exit 1
        ;;
esac

# 1. Asegurar que los paquetes O3TU existan
if [ ! -f "$PACKS_O3TU_DIR/atlas_overrides_ps5.o3tu" ]; then
    echo "Generando paquetes atlas_overrides.o3tu..."
    python3 "$SCRIPT_DIR/scripts/patch_atlas_overrides.py"
fi

# 2. Aplicar el paquete binario O3TU al mod TopScreen activo
if [ -f "$PACKS_O3TU_DIR/atlas_overrides_${MANDO}.o3tu" ]; then
    mkdir -p "$MOD_DIR"
    cp -f "$PACKS_O3TU_DIR/atlas_overrides_${MANDO}.o3tu" "$MOD_DIR/atlas_overrides.o3tu"
    echo "-> Paquete binario TopScreen aplicado: atlas_overrides_${MANDO}.o3tu"
fi

# 3. Configurar giroscopio y GUID en controls.json
if [ -f "$CONTROLS_JSON" ]; then
    python3 - "$CONTROLS_JSON" "$DUALSENSE_GUID" "$AIM_SOURCE" << 'EOF'
import json, sys
path, guid, source = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, "r") as f:
    cfg = json.load(f)
cfg["controller_guid"] = guid
if "aim" in cfg:
    cfg["aim"]["source"] = source
if "calibration" in cfg:
    cfg["calibration"]["controller_guid"] = guid
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
EOF

    if [ "$MANDO" = "ps5" ]; then
        echo "-> Giroscopio DualSense configurado: source=$AIM_SOURCE (Stick derecho + Giroscopio activo), guid=$DUALSENSE_GUID (Auto-detección activa)"
    else
        echo "-> Controles configurados: source=$AIM_SOURCE"
    fi
fi

# 4. Asegurar texturas PNG de apoyo
PACK_DIR="$DATA_ROOT/texture_packs/$MANDO/load/textures/0004000000033600/UI"
if [ ! -d "$PACK_DIR" ]; then
    echo "Generando texturas PNG para $MANDO..."
    python3 "$SCRIPT_DIR/scripts/prepare_controller_textures.py"
fi

echo "========================================================"
echo " Aplicando paquete de botones: $NOMBRE"
echo "========================================================"

mkdir -p "$ACTIVE_UI_DIR"
cp -r "$PACK_DIR/"* "$ACTIVE_UI_DIR/"
echo "$MANDO" > "$ACTIVE_UI_DIR/.active_controller_style"

DEV_UI_DIR="$SCRIPT_DIR/textures/load/textures/0004000000033600/UI"
if [ -d "$(dirname "$DEV_UI_DIR")" ]; then
    mkdir -p "$DEV_UI_DIR"
    cp -r "$PACK_DIR/"* "$DEV_UI_DIR/"
    echo "$MANDO" > "$DEV_UI_DIR/.active_controller_style"
fi

echo "¡Listo! Botones de $NOMBRE configurados en la UI de TriAevum."
