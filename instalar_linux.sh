#!/usr/bin/env bash
set -e

# ==============================================================================
#  TriAevum: The Legend of Zelda: Ocarina of Time 3D - Instalador para Linux
#  Compatible con: Bazzite, Steam Deck (SteamOS), Fedora, Ubuntu, Debian, Arch
# ==============================================================================

BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}======================================================================${RESET}"
echo -e "${BOLD}       Instalador y Configurador Automático de TriAevum (Linux)${RESET}"
echo -e "       The Legend of Zelda: Ocarina of Time 3D - Native Recomp"
echo -e "${BOLD}${BLUE}======================================================================${RESET}"
echo ""

# 1. Verificación de directorio base
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 2. Aviso de cumplimiento legal
echo -e "${YELLOW}[AVISO LEGAL / REQUISITO DE PRESERVACIÓN]${RESET}"
echo -e "TriAevum es un motor de recompilación abierta (Clean-Room)."
echo -e "Este repositorio ${BOLD}NO contiene ni distribuye ningún archivo con derechos de autor${RESET},"
echo -e "ni ROMs, ni texturas de Nintendo. Para jugar, debes proveer tu propia copia"
echo -e "legítima de ${BOLD}The Legend of Zelda: Ocarina of Time 3D${RESET} (EUR o USA) volcada"
echo -e "desde tu propia consola Nintendo 3DS."
echo ""

# 3. Comprobación de dependencias del sistema
echo -e "${BOLD}[1/5] Verificando dependencias del sistema...${RESET}"

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

MISSING_DEPS=()
if ! command_exists python3; then
    MISSING_DEPS+=("python3")
fi

if ! python3 -c "from PIL import Image" >/dev/null 2>&1; then
    echo -e "${YELLOW} -> Instalando Pillow para Python (necesario para texturas)...${RESET}"
    pip install Pillow >/dev/null 2>&1 || pip3 install Pillow --user >/dev/null 2>&1 || true
    if ! python3 -c "from PIL import Image" >/dev/null 2>&1; then
        MISSING_DEPS+=("python3-pillow / python3-pil")
    fi
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${RED}[ERROR] Faltan dependencias necesarias: ${MISSING_DEPS[*]}${RESET}"
    echo -e "Por favor, instálalas con el gestor de paquetes de tu distribución:"
    echo -e "  - Fedora / Bazzite: sudo dnf install python3 python3-pillow"
    echo -e "  - Ubuntu / Debian:  sudo apt install python3 python3-pil"
    echo -e "  - Arch Linux:       sudo pacman -S python python-pillow"
    exit 1
fi
echo -e "${GREEN} -> Dependencias básicas comprobadas con éxito.${RESET}"

# 4. Configurar biblioteca SDL nativa para sensores y giroscopio DualSense
echo ""
echo -e "${BOLD}[2/5] Configurando soporte HIDAPI para DualSense / Mandos...${RESET}"
mkdir -p "$SCRIPT_DIR/build-runtime/lib"
if [ -f "/usr/lib64/libSDL2-2.0.so.0" ]; then
    ln -sf /usr/lib64/libSDL2-2.0.so.0 "$SCRIPT_DIR/build-runtime/lib/libSDL2-2.0.so.0"
fi
if [ -f "/usr/lib/x86_64-linux-gnu/libSDL2-2.0.so.0" ]; then
    ln -sf /usr/lib/x86_64-linux-gnu/libSDL2-2.0.so.0 "$SCRIPT_DIR/build-runtime/lib/libSDL2-2.0.so.0"
fi
if [ -f "/usr/lib64/libSDL3.so.0" ]; then
    ln -sf /usr/lib64/libSDL3.so.0 "$SCRIPT_DIR/build-runtime/lib/libSDL3.so.0"
fi
if [ -f "/usr/lib/x86_64-linux-gnu/libSDL3.so.0" ]; then
    ln -sf /usr/lib/x86_64-linux-gnu/libSDL3.so.0 "$SCRIPT_DIR/build-runtime/lib/libSDL3.so.0"
fi
echo -e "${GREEN} -> Enlaces de bibliotecas SDL configurados para detección HIDAPI.${RESET}"

# 5. Generar paquetes de texturas y botones (PS5, Xbox, Nintendo)
echo ""
echo -e "${BOLD}[3/5] Generando paquetes de texturas y glifos de botones (PS5 / Xbox)...${RESET}"
chmod +x scripts/prepare_controller_textures.py cambiar_mando.sh iniciar_juego.sh
if [ -f "scripts/patch_atlas_overrides.py" ]; then
    chmod +x scripts/patch_atlas_overrides.py
fi

python3 scripts/prepare_controller_textures.py
if [ -f "scripts/patch_atlas_overrides.py" ]; then
    python3 scripts/patch_atlas_overrides.py || true
fi
echo -e "${GREEN} -> Paquetes de mandos generados correctamente.${RESET}"

# 6. Verificación o extracción de la ROM legítima
echo ""
echo -e "${BOLD}[4/5] Comprobando datos de juego...${RESET}"
DATA_ROOT="$HOME/.var/app/io.github.coccofresco.TriAevum/data/TriAevum"
PROFILE="$DATA_ROOT/TriAevum.host.launch.json"

if [ -f "$PROFILE" ]; then
    echo -e "${GREEN} -> Perfil de juego nativo ya instalado y listo en:${RESET}"
    echo -e "    $PROFILE"
else
    echo -e "${YELLOW} -> No se encontró una instalación previa en $DATA_ROOT.${RESET}"
    echo -e "Introduce la ruta completa de tu ROM descifrada de OoT3D (.3ds o .cci):"
    read -r -p "Ruta de la ROM: " USER_ROM_PATH
    if [ -f "$USER_ROM_PATH" ]; then
        echo -e "Extrayendo y construyendo datos con Forge..."
        python3 tools/triaevum_release/forge.py --rom-path "$USER_ROM_PATH"
        echo -e "${GREEN} -> Datos de juego extraídos y vinculados con éxito.${RESET}"
    else
        echo -e "${YELLOW}[AVISO] Archivo no encontrado. Podrás ejecutar Forge más tarde con:${RESET}"
        echo -e "  python3 tools/triaevum_release/forge.py --rom-path /ruta/a/tu_juego.3ds"
    fi
fi

# 7. Aplicar configuración de mando preferido
echo ""
echo -e "${BOLD}[5/5] Selecciona tu estilo de botones preferido:${RESET}"
echo "  1) PlayStation 5 (DualSense: ✖, ⭘, ◼, ▲, L1, R1, L2, R2 + Giroscopio)"
echo "  2) Xbox Series / One (A, B, X, Y, LB, RB, LT, RT)"
echo "  3) Nintendo Original (A, B, X, Y, L, R, ZL, ZR)"
read -r -p "Opción [1-3] (Por defecto 1): " MANDO_OPT

case "$MANDO_OPT" in
    2) ./cambiar_mando.sh xbox ;;
    3) ./cambiar_mando.sh nintendo ;;
    *) ./cambiar_mando.sh ps5 ;;
esac

# 8. Crear acceso directo en el escritorio / menú de aplicaciones
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
cat << DESKTOP_EOF > "$DESKTOP_DIR/TriAevum.desktop"
[Desktop Entry]
Name=TriAevum (OoT 3D Remaster)
Comment=The Legend of Zelda: Ocarina of Time 3D PC Native Port
Exec=$SCRIPT_DIR/iniciar_juego.sh --mando ps5 --fps 120 --res 1080p
Path=$SCRIPT_DIR
Icon=$SCRIPT_DIR/resources/app_icon.png
Terminal=false
Type=Application
Categories=Game;Emulator;
DESKTOP_EOF
chmod +x "$DESKTOP_DIR/TriAevum.desktop"

echo ""
echo -e "${BOLD}${GREEN}======================================================================${RESET}"
echo -e "${BOLD}${GREEN}        ¡Instalación y Configuración Completada con Éxito!           ${RESET}"
echo -e "${BOLD}${GREEN}======================================================================${RESET}"
echo -e "Acceso directo creado en: $DESKTOP_DIR/TriAevum.desktop"
echo ""
echo -e "Para iniciar el juego en cualquier momento, usa:"
echo -e "  ${BOLD}./iniciar_juego.sh --mando ps5 --fps 120 --res 1080p${RESET}"
echo ""
echo -e "Opciones disponibles:"
echo -e "  --mando [ps5 | xbox | nintendo]   Seleccionar paquete de botones"
echo -e "  --fps   [60 | 90 | 120 | 144 | free] Tasa de refresco objetivo"
echo -e "  --res   [720p | 1080p | 1440p | 4k]   Resolución de renderizado"
echo -e "  (También puedes pulsar F1 dentro del juego para abrir el menú de ajustes)"
echo -e "${BOLD}${BLUE}======================================================================${RESET}"
