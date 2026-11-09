# ItsOcho Timeline v5.13 — Studio Panel + Stream Deck

El overlay y music.html siguen igual que en v5.12. No necesitas cambiarlos en OBS.

## Nuevo /panel

El panel ahora tiene pestañas laterales: Directo, Cola de GTA, Música, OBS y PS5, Apariencia, Stream Deck y Ayuda.
Se mantiene la lógica anterior, sin duplicar controles. Los botones se reordenaron dentro de las pestañas para no hacer scroll por toda la aplicación.
En pantallas pequeñas la navegación se vuelve horizontal. Ctrl+1 a Ctrl+7 cambia de pestaña.

## Stream Deck sin plugins

1. Ejecuta INICIAR_PANEL.bat y ve a http://127.0.0.1:8767/panel.
2. Entra a la pestaña Stream Deck y pulsa «Copiar enlace» del comando que prefieras.
3. En la aplicación Elgato Stream Deck, arrastra Sistema > Sitio web (Website).
4. Pega el enlace copiado, y elige «GET request in background» (solicitud GET en segundo plano).
5. Asigna un nombre y repite el proceso con otros botones.

También puedes pulsar Probar dentro del panel. Los enlaces funcionan mientras el servidor local esté abierto.
Los comandos disponibles incluyen siguiente/anterior GTA, presentar, saltar, HUD, modos, música, cámara y marco PS5.

IMPORTANTE: los enlaces contienen un token privado único del equipo, almacenado en .streamdeck_token.
No incluyas ese token en capturas públicas. Si pierdes tu PC o compartiste enlaces, elimina ese archivo y reinicia el servidor para generar otro.

Los comandos Stream Deck de cámara y PS5 siempre cambian sus marcos del overlay.
Para sincronizar además la imagen real, conecta OBS WebSocket en la pestaña OBS y PS5 y deja abierto el panel; la sincronización desde Stream Deck requiere el panel conectado a OBS, ya que la contraseña no se almacena en el servidor.

## Actualización desde v5.12

Cierra el servidor. Extrae el ZIP en una carpeta nueva. Copia de tu instalación anterior las carpetas musica/, logos/ y, si existen, musica_config.json, timeline_config.json, ps5_layout.json.
Arranca INICIAR_PANEL.bat. Las URLs de OBS siguen siendo /overlay y /music.

## Seguridad

Servidor exclusivamente en 127.0.0.1:8767, sin acceso remoto. Clave de Stream Deck aleatoria en cada instalación y persistente en reinicios. No hay plugins ni librerías adicionales.


## Nuevo en v5.14
Cámara 4:3 movible con vista previa de arrastrar, coordenadas X/Y, tamaño y sincronización opcional con OBS. Ver GUIA_CAMARA_MOVIBLE_v5_14.md.
