# ItsOcho Studio v5.14 — Cámara móvil

## Instalar

Cierra INICIAR_PANEL.bat, copia el contenido del parche sobre tu carpeta v5.13 (o descomprime el ZIP completo en otra carpeta y copia tus logos/musica). Reinicia el servidor y recarga `/panel` y la fuente `/overlay` en OBS.

## Mover la cámara

Abre **OBS y PS5 → Cámara y OBS Studio → Posición de cámara**. Arrastra el rectángulo rosa en la vista previa 16:9 o utiliza las coordenadas X/Y y el ancho. Al soltar se guarda automáticamente; también hay botón **Guardar posición**.

El marco es 4:3, se guarda en `camera_layout.json` y se actualiza en OBS sin volver a cargar la fuente. El marco no contiene la imagen de webcam: esa imagen es una fuente aparte de OBS.

### Mover también la captura real de OBS

1. En OBS: Herramientas → Ajustes del servidor WebSocket → Actívalo.
2. En el panel: conecta OBS y elige la fuente de tu cámara.
3. Marca **Mover también la fuente vinculada en OBS (ajustar a 4:3)**.
4. Arrastra el marco y suelta, o usa el botón Guardar posición.

Esto ajusta la posición y los límites del elemento de webcam en las escenas donde aparece directamente. Si está dentro de un grupo, se mantiene intacta para evitar coordenadas equivocadas. Escenas con recortes personalizados o transformaciones complejas pueden necesitar ajustes manuales. Si no conectas OBS, sigue funcionando el movimiento del marco.

**Nota:** La visibilidad de cámara y el control del Stream Deck continúan funcionando como antes. La contraseña de OBS no se guarda.
