# Guía de Instalación y Uso de TriAevum (OoT 3D Native PC Port)

Bienvenido a la guía oficial en español de **TriAevum**, la recompilación nativa para PC de ***The Legend of Zelda: Ocarina of Time 3D***. Esta guía te explicará cómo instalarlo y configurarlo de forma muy sencilla tanto en **Linux** como en **Windows 10 / 11**, disfrutando de gráficos en alta definición, tasas de refresco de hasta 120 FPS / VRR, paquetes de botones de **PlayStation 5 (DualSense)** y **Xbox**, y **apuntado por giroscopio** con sensores de movimiento en tiempo real.

---

## ⚖️ Aviso Legal y Cumplimiento de Derechos de Autor

> [!IMPORTANT]
> **Filosofía de Recompilación Limpia (*Clean-Room Engine*):**
> - **TriAevum NO contiene, no distribuye ni enlaza ningún material protegido por derechos de autor de Nintendo.**
> - El repositorio contiene únicamente el motor en C++ de código abierto, herramientas de extracción y generadores procedurales de glifos.
> - Para poder jugar, **debes proveer tu propia copia legítima y descifrada** de *The Legend of Zelda: Ocarina of Time 3D* (EUR o USA), volcada legalmente desde tu propio cartucho físico usando tu consola Nintendo 3DS.
> - La extracción de los recursos del juego se realiza **100% de manera local** en tu equipo durante el proceso de instalación mediante la herramienta `forge.py`.

---

## 📋 Requisitos del Sistema

- **Procesador (CPU):** Procesador de 64 bits (x86_64) con al menos 4 núcleos.
- **Gráficos (GPU):** Tarjeta gráfica con soporte para **Vulkan 1.2 o superior** (AMD Radeon, NVIDIA GeForce o Intel Arc / Iris Xe).
- **Sistema Operativo:**
  - **Linux:** Bazzite, SteamOS (Steam Deck), Fedora 39+, Ubuntu 22.04+, Debian 12+, Arch Linux.
  - **Windows:** Windows 10 (64-bit) o Windows 11.
- **Mandos recomendados:**
  - Sony DualSense (PlayStation 5) — *Recomendado: giroscopio y hápticos por HIDAPI nativo.*
  - Xbox Series X|S / Xbox One.
  - Nintendo Switch Pro Controller.
  - Teclado y ratón.
- **Copia del juego:** Archivo descifrado `.3ds` o `.cci` de *The Legend of Zelda: Ocarina of Time 3D* (versión Europea `CTR-P-AQEP` o Americana `CTR-P-AQEE`).

---

## 🕹️ Cómo Volcar tu Cartucho con GodMode9 (Nintendo 3DS)

Si aún no tienes tu ROM descifrada, puedes volcarla desde tu propia consola con Custom Firmware (Luma3DS / GodMode9):

1. Enciende tu Nintendo 3DS manteniendo pulsado el botón **START** para entrar en **GodMode9**.
2. Inserta tu cartucho físico de *The Legend of Zelda: Ocarina of Time 3D*.
3. Ve a `[C:] GAMECART`.
4. Selecciona el archivo del juego (`.trim.3ds` o `.3ds`) y presiona el botón **A**.
5. Selecciona la opción **NCCH image options...** y luego **Build decrypted CIA/3DS** o **Decrypt inline**.
6. Copia el archivo `.3ds` descifrado resultante desde tu tarjeta SD (`/gm9/out/`) a tu ordenador.

---

## 🐧 Instalación en Linux (Steam Deck, Bazzite, Fedora, Ubuntu, Arch)

Hemos creado un instalador automático de 1 solo clic que prepara todo el entorno, configura los sensores de tu DualSense y genera los paquetes de texturas.

### Método 1: Instalador Automático (Recomendado)

1. Abre una terminal en la carpeta del proyecto:
   ```bash
   cd ~/Juegos/TriAevum-dev
   ```
2. Ejecuta el instalador:
   ```bash
   ./instalar_linux.sh
   ```
3. El instalador:
   - Comprobará las dependencias necesarias (`vulkan`, `python3`, `pillow`).
   - Te pedirá la ruta de tu ROM descifrada de OoT 3D (si no lo has instalado antes) y la procesará localmente.
   - Configurará la biblioteca SDL para lectura directa de sensores IMU del DualSense vía `/dev/hidraw`.
   - Creará un acceso directo en tu menú de aplicaciones y escritorio (`TriAevum.desktop`).

### Método 2: Iniciar el juego desde la terminal

Puedes lanzar el juego en cualquier momento con tus opciones preferidas:

```bash
# Lanzamiento con mando de PS5 a 1080p y 120 FPS
./iniciar_juego.sh --mando ps5 --fps 120 --res 1080p

# Lanzamiento con mando de Xbox en 1440p
./iniciar_juego.sh --mando xbox --fps 60 --res 1440p

# Tasa de cuadros sin límite (VRR / G-Sync / FreeSync)
./iniciar_juego.sh --mando ps5 --fps free --res 1080p
```

### Integración en Steam Deck / Steam

1. Abre Steam en modo escritorio.
2. Haz clic en **Productos** > **Añadir un producto que no es de Steam a mi biblioteca...**.
3. Selecciona `iniciar_juego.sh` o el acceso directo `TriAevum.desktop`.
4. En las propiedades del acceso directo en Steam, añade los parámetros deseados en Parámetros de lanzamiento:
   ```
   --mando ps5 --fps 60 --res 720p
   ```

---

## 🪟 Instalación en Windows 10 / 11

### Método 1: Instalador Automático

1. Descarga o clona el repositorio en una carpeta de tu preferencia (por ejemplo `C:\Juegos\TriAevum`).
2. Asegúrate de tener instalado **Python 3** (marcando la casilla *"Add Python to PATH"* durante su instalación).
3. Haz doble clic en el archivo:
   ```
   instalar_windows.bat
   ```
4. El asistente preparará las texturas de los mandos y te pedirá la ubicación de tu ROM descifrada de OoT 3D.
5. Para jugar, haz doble clic en:
   ```
   iniciar_juego.bat
   ```

---

## 🎮 Configuración del Mando DualSense (PS5) y Giroscopio

TriAevum incluye soporte nativo para los sensores del mando **Sony DualSense (PS5)**:

### 1. Conexión recomendada y Auto-Detección Inteligente
- **Auto-Detección:** TriAevum detecta automáticamente si conectas un mando de **PlayStation 5 (DualSense)**, **Xbox** o **Nintendo** y adapta al instante todos los botones y glifos en pantalla sin necesidad de tocar nada.
- **Vía Bluetooth:** Empareja el DualSense manteniendo pulsados el botón **Create (Share)** + botón **PS** hasta que la barra de luz parpadee rápidamente. Conéctalo desde la configuración de Bluetooth de tu sistema.
- **Vía Cable USB-C:** Conecta el mando directamente por cable. TriAevum lo reconocerá automáticamente.

### 2. Apuntado por Giroscopio (Modo Híbrido Moderno)
- El juego está preconfigurado con `"aim": { "source": "automatic" }`:
  - **Stick analógico derecho:** Movimiento rápido y amplio de la retícula.
  - **Giroscopio (Inclinación física del mando):** Micro-ajustes de precisión extrema para el arco de hadas, el tirachinas y la vista en primera persona.
- Si Steam está ejecutándose en segundo plano, te recomendamos deshabilitar la configuración de escritorio de Steam Input para el mando de PS5 para permitir que el juego acceda de forma directa y exclusiva a los sensores por hardware.

---

## ⚙️ Menú de Ajustes en el Juego (Tecla F1)

Durante la partida, pulsa la tecla **F1** para abrir el menú de superposición en tiempo real:

1. **Selector de Mandos:**
   - Permite forzar manualmente los botones si prefieres jugar con iconos de PlayStation 5, Xbox o Nintendo independientemente del mando conectado.
2. **Gráficos y Rendimiento:**
   - **Oclusión Ambiental (FidelityFX CACAO):** Activa sombras de contacto de alta fidelidad en esquinas, mazmorras y alrededor de Link. (Viene activo por defecto en los scripts de inicio).
   - **Escalado:** Selección entre NIS y FSR con ajuste de nitidez (*Sharpness*).
   - **Anti-Aliasing:** Filtros SMAA 1x o TAA cinemático.
   - **Tasa de Refresco:** Sincronización a 30, 60, 90, 120, 144 FPS o desbloqueado.

---

## ❓ Preguntas Frecuentes (FAQ)

### ¿El juego se congela en las cinemáticas?
Esta versión incluye el parche de estabilidad de Vulkan para la cola de presentación gráfica, eliminando por completo cualquier congelamiento en las cinemáticas de introducción y transiciones de templos.

### ¿Puedo cambiar la resolución de pantalla?
Sí, tanto desde el menú `F1` como pasando los parámetros `--res 1080p`, `--res 1440p` o `--res 4k` al script de inicio.

### ¿Dónde se guardan mis partidas?
- En Linux: `~/.var/app/io.github.coccofresco.TriAevum/data/TriAevum/savedata/`
- En Windows: `%APPDATA%\TriAevum\savedata\`
Tus partidas guardadas son 100% compatibles entre plataformas.
