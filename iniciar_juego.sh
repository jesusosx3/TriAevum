#!/usr/bin/env bash
set -e

# Manejo de opciones rápidas: --mando, --fps, --res
PASSTHROUGH_ARGS=()
FPS_ARG=""
RES_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mando|-m)
            MANDO="$2"
            shift 2
            ;;
        --mando=*)
            MANDO="${1#*=}"
            shift 1
            ;;
        --fps)
            FPS_VAL="$2"
            shift 2
            case "$FPS_VAL" in
                free|uncapped|vrr|0) FPS_ARG="free" ;;
                30|60|90|120|144|165|240) FPS_ARG="$FPS_VAL" ;;
                *) echo "Aviso: FPS desconocido '$FPS_VAL', usando '$FPS_VAL'"; FPS_ARG="$FPS_VAL" ;;
            esac
            ;;
        --fps=*)
            FPS_VAL="${1#*=}"
            shift 1
            FPS_ARG="$FPS_VAL"
            ;;
        --cacao)
            CACAO_OPT=1
            shift 1
            ;;
        --no-cacao)
            CACAO_OPT=0
            shift 1
            ;;
        --res)
            RES_VAL="$2"
            shift 2
            case "$RES_VAL" in
                720p|720) RES_ARGS=("--width" "1280" "--height" "720") ;;
                1080p|1080) RES_ARGS=("--width" "1920" "--height" "1080") ;;
                1440p|1440|2k) RES_ARGS=("--width" "2560" "--height" "1440") ;;
                4k|2160p|2160) RES_ARGS=("--width" "3840" "--height" "2160") ;;
                *) echo "Resolución '$RES_VAL' no estándar";;
            esac
            ;;
        --res=*)
            RES_VAL="${1#*=}"
            shift 1
            case "$RES_VAL" in
                720p|720) RES_ARGS=("--width" "1280" "--height" "720") ;;
                1080p|1080) RES_ARGS=("--width" "1920" "--height" "1080") ;;
                1440p|1440|2k) RES_ARGS=("--width" "2560" "--height" "1440") ;;
                4k|2160p|2160) RES_ARGS=("--width" "3840" "--height" "2160") ;;
            esac
            ;;
        *)
            PASSTHROUGH_ARGS+=("$1")
            shift 1
            ;;
    esac
done

GAME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -n "${MANDO:-}" ]; then
    "$GAME_DIR/cambiar_mando.sh" "$MANDO"
fi

# Configuración del entorno DualSense: Giroscopio (IMU Sixaxis) y Hápticos / Rumble
export SDL_JOYSTICK_HIDAPI=1
export SDL_JOYSTICK_HIDAPI_PS5=1
export SDL_JOYSTICK_HIDAPI_PS5_RUMBLE=1
export SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS=1
export SDL_HAPTIC_GAIN_MAX=100

# Configuración del entorno de ejecución optimizado (priorizar SDL del sistema con soporte HIDAPI/udev para sensores)
mkdir -p "$GAME_DIR/build-runtime/lib"
for sdl_lib in /usr/lib64/libSDL2-2.0.so.0 /usr/lib/x86_64-linux-gnu/libSDL2-2.0.so.0; do
    if [ -f "$sdl_lib" ]; then
        ln -sf "$sdl_lib" "$GAME_DIR/build-runtime/lib/libSDL2-2.0.so.0"
        break
    fi
done
for sdl3_lib in /usr/lib64/libSDL3.so.0 /usr/lib/x86_64-linux-gnu/libSDL3.so.0; do
    if [ -f "$sdl3_lib" ]; then
        ln -sf "$sdl3_lib" "$GAME_DIR/build-runtime/lib/libSDL3.so.0"
        break
    fi
done
export LD_LIBRARY_PATH="$GAME_DIR/build-runtime/lib:${LD_LIBRARY_PATH:-}"

# Búsqueda del perfil de lanzamiento TriAevum.host.launch.json
PROFILE=""
for candidate in \
    "${TRIAEVUM_LAUNCH_PROFILE:-}" \
    "$HOME/.var/app/io.github.coccofresco.TriAevum/data/TriAevum/TriAevum.host.launch.json" \
    "${XDG_DATA_HOME:-}/TriAevum/TriAevum.host.launch.json" \
    "$HOME/.local/share/TriAevum/TriAevum.host.launch.json" \
    "$GAME_DIR/data/TriAevum/TriAevum.host.launch.json" \
    "$GAME_DIR/TriAevum.host.launch.json"; do
    if [ -n "$candidate" ] && [ -f "$candidate" ]; then
        PROFILE="$candidate"
        break
    fi
done

BINARY=""
for candidate in \
    "$GAME_DIR/TriAevum" \
    "$GAME_DIR/build-runtime/TriAevum" \
    "$GAME_DIR/build/TriAevum"; do
    if [ -x "$candidate" ]; then
        BINARY="$candidate"
        break
    fi
done
if [ -z "$BINARY" ]; then
    BINARY="TriAevum"
fi

# Detección y activación de MangoHud para monitoreo de FPS y frametimes
HUD_WRAPPER=""
if command -v mangohud >/dev/null 2>&1; then
    HUD_WRAPPER="mangohud"
fi

# Preparar argumentos adicionales de rendimiento
EXTRA_EXEC_ARGS=()
if [ -n "$FPS_ARG" ]; then
    EXTRA_EXEC_ARGS+=("--presentation-rate" "$FPS_ARG")
    case "$FPS_ARG" in
        120|144|165|240) export OOT3D_GRAPHICS_FRAME_RATE="Interpolated4x" ;;
        90) export OOT3D_GRAPHICS_FRAME_RATE="Interpolated3x" ;;
        60) export OOT3D_GRAPHICS_FRAME_RATE="Interpolated2x" ;;
        30) export OOT3D_GRAPHICS_FRAME_RATE="Original30" ;;
        free) export OOT3D_GRAPHICS_FRAME_RATE="Uncapped" ;;
    esac
fi
if [ ${#RES_ARGS[@]} -gt 0 ]; then
    EXTRA_EXEC_ARGS+=("${RES_ARGS[@]}")
fi

# Oclusión Ambiental (CACAO) de FidelityFX de alta fidelidad
if [ "${CACAO_OPT:-1}" = "1" ]; then
    export OOT3D_GRAPHICS_CACAO="1"
    export OOT3D_GRAPHICS_CACAO_QUALITY="1"
fi

echo "========================================================"
echo "    TriAevum (The Legend of Zelda: Ocarina of Time 3D)  "
echo "    Edición Remaster 10/10 (DualSense + 120 FPS + HD UI)"
echo "========================================================"
if [ -n "$FPS_ARG" ]; then
    echo " -> Tasa de refresco objetivo: ${FPS_ARG} Hz"
fi
if [ ${#RES_ARGS[@]} -gt 0 ]; then
    echo " -> Resolución configurada: ${RES_ARGS[1]}x${RES_ARGS[3]}"
fi
if [ "${CACAO_OPT:-1}" = "1" ]; then
    echo " -> Oclusión Ambiental: FidelityFX CACAO activo"
fi
echo " -> Sensores DualSense: Giroscopio y Hápticos (HIDAPI activos)"
echo "========================================================"

cd "$GAME_DIR"
exec $HUD_WRAPPER "$BINARY" --launch-profile "$PROFILE" "${EXTRA_EXEC_ARGS[@]}" "${PASSTHROUGH_ARGS[@]}"
