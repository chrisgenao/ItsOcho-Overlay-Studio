# ItsOcho Studio v5.16 — Modo Tráiler y marcos sincronizados

## Qué cambia

- **Modo Tráiler:** oculta el marco PS5 del overlay y, con OBS WebSocket vinculado en el panel, la fuente real de PS5. **La webcam y su marco permanecen visibles** si la cámara estaba activada.
- Al salir de Modo Tráiler, PS5 vuelve a su visibilidad configurada. No se borra ni se modifica su posición.
- **OBS y PS5:** la vista previa de 1920×1080 tiene dos marcos arrastrables: rosa para la cámara (4:3) y cyan para PS5 (16:9). También se pueden cambiar X/Y/ancho por separado.
- Mientras arrastras, el panel guarda la ubicación y, si hay conexión WebSocket, ajusta la fuente real correspondiente en OBS. Las actualizaciones se agrupan para no saturar WebSocket.
- La biblioteca de asignación de música por GTA de **v5.15** se conserva.

## Cómo activar la sincronización con OBS

1. En OBS, activa **Herramientas > Ajustes del servidor WebSocket**, normalmente puerto `4455`.
2. Abre `http://127.0.0.1:8767/panel`, entra en **OBS y PS5** y conecta OBS.
3. Selecciona la **fuente real de cámara** y la **fuente real de PS5**. Deben ser dos fuentes diferentes.
4. Mantén marcadas **Sincronizar posición en OBS** para la cámara, **Sincronizar posición de la captura PS5 en OBS**, y **Sincronizar visibilidad con OBS**.
5. Arrastra los marcos en el lienzo o modifica X/Y/ancho y pulsa **Guardar**.
6. En **Directo**, activa/desactiva **Modo Tráiler** para probar la ocultación/restauración de PS5 sin tocar la cámara.

**Importante:** los movimientos sobre fuentes OBS son administrados por el navegador del panel. **Debes mantener `/panel` abierto y conectado a OBS** para mover u ocultar las fuentes reales. El overlay y su marco sí obedecen los comandos del servidor con el panel cerrado; las fuentes reales no pueden sincronizarse si el panel está cerrado o WebSocket desconectado.

Las posiciones corresponden a un lienzo de **1920×1080**. Si tu OBS usa una resolución distinta, las coordenadas no serán equivalentes. El panel mueve fuentes colocadas **directamente en escenas**; no altera fuentes dentro de grupos porque sus coordenadas son relativas al grupo. Las fuentes de OBS se ajustan al marco usando límites `OBS_BOUNDS_SCALE_OUTER`.

## Cómo instalar sin perder canciones y ajustes

**Parche**: cierra ItsOcho Studio y reemplaza solo `panel.html` y `overlay.html` por los del parche v5.16. **No elimines** `musica/`, `musica_config.json`, `timeline_config.json`, `camera_layout.json` ni `ps5_layout.json`. Reinicia la aplicación, y en la fuente Navegador de OBS actualiza la caché.

**Proyecto completo**: descomprímelo en una nueva carpeta, o copia sus archivos de código sobre tu instalación existente sin reemplazar tus datos locales. Conserva los archivos de configuración y música de tu PC.

Si usas un `.exe` autónomo de la versión anterior, conserva el ejecutable y actualiza los HTML **a su lado**; no es necesario recompilar el EXE porque las funciones nuevas usan las API del servidor actual.

## Verificaciones efectuadas

- Sintaxis JavaScript de las dos secciones de `panel.html` comprobada con Node.
- Prueba en Chromium con OBS WebSocket simulado: arrastre cámara→transform de Webcam, arrastre PS5→transform de PS5, activar/desactivar Modo Tráiler→oculta/restaura PS5 sin ocultar la webcam.
- Servidor Python real: endpoints `/panel`, `/overlay`, `/music`, posiciones independientes y conmutación de modo tráiler.

**Pendiente de verificar con tu configuración particular:** una sesión con OBS Studio real en Windows y las fuentes exactas seleccionadas. No se incluye música comercial.