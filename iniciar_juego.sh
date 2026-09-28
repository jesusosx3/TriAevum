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

GAME_DIR="/home/jesus/Juegos/TriAevum-dev"

if [ -n "${MANDO:-}" ]; then
    "$GAME_DIR/cambiar_mando.sh" "$MANDO"
fi

# Configuración del entorno DualSense: Giroscopio (IMU Sixaxis) y Hápticos / Rumble
export SDL_JOYSTICK_HIDAPI=1
export SDL_JOYSTICK_HIDAPI_PS5=1
export SDL_JOYSTICK_HIDAPI_PS5_RUMBLE=1
export SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS=1
export SDL_HAPTIC_GAIN_MAX=100

# Configuración del entorno de ejecución optimizado
export LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:/home/linuxbrew/.linuxbrew/opt/bzip2/lib:/home/linuxbrew/.linuxbrew/opt/openssl@3/lib:${LD_LIBRARY_PATH:-}"

PROFILE="/home/jesus/.var/app/io.github.coccofresco.TriAevum/data/TriAevum/TriAevum.host.launch.json"
BINARY="$GAME_DIR/build-runtime/TriAevum"

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
echo " -> Sensores DualSense: Giroscopio y Hápticos (HIDAPI activos)"
echo "========================================================"

cd "$GAME_DIR"
exec $HUD_WRAPPER "$BINARY" --launch-profile "$PROFILE" "${EXTRA_EXEC_ARGS[@]}" "${PASSTHROUGH_ARGS[@]}"
