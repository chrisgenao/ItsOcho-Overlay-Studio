# ItsOcho Studio — edición de código fuente (sin EXE compilado)

Este paquete está pensado para revisión antes de ejecutar o compartir con terceros. No incluye ningún ejecutable `.exe`, instalador, ni herramientas de compilación automática. Contiene código Python/HTML/JS, un launcher fuente en Go para inspección y scripts BAT legibles.

## Uso en Windows

1. Revisar primero `server.py`, los HTML y `INICIAR_PANEL.bat` si se desea.
2. Tener Python 3.10 o posterior instalado desde una fuente de confianza.
3. Descomprimir el paquete completo y ejecutar `INICIAR_PANEL.bat` o, desde terminal, `python server.py --no-browser`.
4. Abrir `http://127.0.0.1:8767/panel` en el navegador.

El servidor escucha solamente en `127.0.0.1:8767`, no en una interfaz pública. Puede comunicarse con OBS por WebSocket local cuando el usuario lo configura. La descarga de logos desde sitios externos no se hace automáticamente por defecto; es una función del panel. Revisa el código para comprender estas acciones.

Este empaquetado no es un certificado de seguridad ni elimina detecciones antivirus del EXE previo. Una alerta como `DeepInstinct: MALICIOUS` debe investigarse con el hash y el nombre exacto del archivo detectado. No se recomienda desactivar el antivirus ni añadir exclusiones para ejecutarlo.

## Integridad

`SHA256_ARCHIVOS.txt` contiene SHA-256 de los archivos distribuidos, calculados al generar este paquete. Los hashes permiten comprobar que los archivos no cambiaron respecto a este paquete, **no** garantizan que sean seguros.

## Notas sobre distribución

Para generar un ejecutable que terceros puedan verificar, publica la versión fuente con su historial en un repositorio, compila mediante un flujo reproducible, analiza el artefacto en varios antivirus y considera una firma Authenticode. El ejecutable original no se incluye aquí.
