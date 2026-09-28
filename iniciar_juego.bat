@echo off
chcp 65001 >nul
title TriAevum: The Legend of Zelda: Ocarina of Time 3D

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "DATA_DIR=%APPDATA%\TriAevum"
set "PROFILE=%DATA_DIR%\TriAevum.host.launch.json"

if not exist "%PROFILE%" (
    if exist "%DATA_DIR%\data\TriAevum\TriAevum.host.launch.json" (
        set "PROFILE=%DATA_DIR%\data\TriAevum\TriAevum.host.launch.json"
    )
)

set "EXE_PATH=TriAevum.exe"
if not exist "%EXE_PATH%" (
    if exist "build-runtime\TriAevum.exe" (
        set "EXE_PATH=build-runtime\TriAevum.exe"
    ) else if exist "build\TriAevum.exe" (
        set "EXE_PATH=build\TriAevum.exe"
    )
)

rem Habilitar sensores HIDAPI para mandos PlayStation DualSense
set SDL_JOYSTICK_HIDAPI=1
set SDL_JOYSTICK_HIDAPI_PS5=1
set SDL_JOYSTICK_HIDAPI_PS5_RUMBLE=1
set SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS=1

rem Habilitar Oclusion Ambiental (FidelityFX CACAO)
set OOT3D_GRAPHICS_CACAO=1
set OOT3D_GRAPHICS_CACAO_QUALITY=1

echo ======================================================================
echo    TriAevum (The Legend of Zelda: Ocarina of Time 3D) - Windows
echo ======================================================================
echo  -^> Pulsa F1 dentro del juego para abrir el menu de configuracion
echo  -^> Soporte para DualSense (Giroscopio y Hapticos) activo
echo  -^> Oclusion Ambiental: FidelityFX CACAO activo
echo ======================================================================
echo.

if exist "%PROFILE%" (
    "%EXE_PATH%" --launch-profile "%PROFILE%" --presentation-rate 120 --width 1920 --height 1080 %*
) else (
    echo [ERROR] No se encontro el perfil de juego TriAevum.host.launch.json.
    echo Por favor ejecuta primero: instalar_windows.bat
    pause
)
