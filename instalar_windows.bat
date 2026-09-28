@echo off
chcp 65001 >nul
title Instalador de TriAevum para Windows (OoT 3D Native Recomp)

echo ======================================================================
echo        Instalador y Configurador de TriAevum (Windows 10 / 11)
echo        The Legend of Zelda: Ocarina of Time 3D - Native Recomp
echo ======================================================================
echo.

echo [AVISO LEGAL / REQUISITO DE PRESERVACIÓN]
echo TriAevum es un proyecto de código abierto y no incluye ningún archivo
echo protegido por derechos de autor ni ROMs comerciales.
echo Debes utilizar tu propia copia legal de The Legend of Zelda: Ocarina
echo of Time 3D volcada desde tu consola Nintendo 3DS.
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [1/4] Comprobando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se encontro Python en el sistema.
    echo Por favor, instala Python 3 desde https://www.python.org/
    echo Asegurate de marcar la casilla "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)
echo  -^> Python detectado correctamente.
echo.

echo [2/4] Verificando libreria Pillow...
python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo Instalando Pillow para generar texturas de mandos...
    pip install Pillow
)
echo  -^> Librerias de Python listas.
echo.

echo [3/4] Generando texturas de mandos (PlayStation 5 y Xbox)...
python scripts\prepare_controller_textures.py
if exist "scripts\patch_atlas_overrides.py" (
    python scripts\patch_atlas_overrides.py
)
echo  -^> Texturas y glifos generados con exito.
echo.

echo [4/4] Comprobacion de ROM de Ocarina of Time 3D...
set "DATA_DIR=%APPDATA%\TriAevum"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

echo Por favor, arrastra o escribe la ruta de tu ROM descifrada (.3ds o .cci):
set /p "ROM_PATH=Ruta de la ROM: "

if exist "%ROM_PATH%" (
    echo Extrayendo recursos legítimos del juego con Forge...
    python tools\triaevum_release\forge.py --rom-path "%ROM_PATH%"
    echo  -^> Recursos instalados correctamente.
) else (
    echo [AVISO] No se especifico una ruta valida. Podras ejecutar Forge mas tarde:
    echo   python tools\triaevum_release\forge.py --rom-path "C:\ruta\a\tu_juego.3ds"
)

echo.
echo ======================================================================
echo        ¡Instalacion y configuracion en Windows finalizada!
echo ======================================================================
echo Puedes iniciar el juego haciendo doble clic en:
echo   iniciar_juego.bat
echo.
pause
