#!/usr/bin/env bash
set -e

MANDO="${1:-ps5}"
DATA_ROOT="/home/jesus/.var/app/io.github.coccofresco.TriAevum/data/TriAevum"
PACK_DIR="$DATA_ROOT/texture_packs/$MANDO/load/textures/0004000000033600/UI"
ACTIVE_UI_DIR="$DATA_ROOT/textures/load/textures/0004000000033600/UI"

case "$MANDO" in
    ps5|playstation|dualsense)
        MANDO="ps5"
        NOMBRE="PlayStation 5 (DualSense: ✖, ⭘, ◼, ▲, L1, R1, L2, R2)"
        ;;
    xbox|one|series)
        MANDO="xbox"
        NOMBRE="Xbox Series / One (A, B, X, Y, LB, RB, LT, RT)"
        ;;
    nintendo|original|3ds|switch)
        MANDO="nintendo"
        NOMBRE="Nintendo Original (A, B, X, Y, L, R, ZL, ZR)"
        ;;
    *)
        echo "Uso: $0 [ps5 | xbox | nintendo]"
        exit 1
        ;;
esac

PACK_DIR="$DATA_ROOT/texture_packs/$MANDO/load/textures/0004000000033600/UI"

if [ ! -d "$PACK_DIR" ]; then
    echo "Generando texturas para $MANDO..."
    python3 /home/jesus/Juegos/TriAevum-dev/scripts/prepare_controller_textures.py
fi

echo "========================================================"
echo " Aplicando paquete de botones: $NOMBRE"
echo "========================================================"

mkdir -p "$ACTIVE_UI_DIR"
cp -r "$PACK_DIR/"* "$ACTIVE_UI_DIR/"
echo "$MANDO" > "$ACTIVE_UI_DIR/.active_controller_style"

# También sincronizar con directorio de desarrollo si existe
DEV_UI_DIR="/home/jesus/Juegos/TriAevum-dev/textures/load/textures/0004000000033600/UI"
if [ -d "$(dirname "$DEV_UI_DIR")" ]; then
    mkdir -p "$DEV_UI_DIR"
    cp -r "$PACK_DIR/"* "$DEV_UI_DIR/"
    echo "$MANDO" > "$DEV_UI_DIR/.active_controller_style"
fi

echo "¡Listo! Botones de $NOMBRE configurados en la UI de TriAevum."
