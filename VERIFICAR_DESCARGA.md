# Verificar una descarga de ItsOcho Studio

**Un resultado de una atestación válida no prueba ausencia de malware.** Confirma
que los bytes de un archivo fueron generados por un workflow concreto del
repositorio. Revisa además el código, permisos, el historial de cambios y las
alertas de los antivirus. La detección histórica de Deep Instinct todavía
requiere una investigación específica.

Repositorio: https://github.com/chrisgenao/ItsOcho-Overlay-Studio

1. Descarga `ItsOcho_Studio_Windows.zip` desde Releases (no por mensajes privados).
2. Instala la CLI oficial de GitHub (https://cli.github.com/).
3. Desde PowerShell en la carpeta de descarga, verifica:

```powershell
gh attestation verify .\ItsOcho_Studio_Windows.zip -R chrisgenao/ItsOcho-Overlay-Studio
```

Puedes comprobar también el ejecutable directamente:

```powershell
gh attestation verify .\ItsOcho_Studio.exe -R chrisgenao/ItsOcho-Overlay-Studio
Get-FileHash .\ItsOcho_Studio.exe -Algorithm SHA256
```

Contrasta el resultado SHA-256 con el archivo `SHA256SUMS.txt` del mismo Release.
También puedes comprobar que coincida con la versión dentro del ZIP.

## Qué demuestra cada prueba

- **Checks de CI**: pruebas y análisis definidos por el proyecto terminaron.
- **Artifact Attestation**: procedencia criptográfica del archivo desde una ejecución de GitHub Actions.
- **SHA-256**: integridad/identidad del archivo, no bondad ni seguridad.
- **CodeQL**: detecta ciertas clases de vulnerabilidades, no todos los comportamientos maliciosos.
- **Antivirus**: es otra señal; una detección tampoco debe descartarse sin revisión.

El programa usa un servidor HTTP local para el panel y conecta con OBS si
el usuario habilita esa función. No requiere ejecutar con permisos de administrador.
Antes de compartir, comprueba que el repositorio NO incluya tokens, archivos
privados, canciones protegidas ni configuraciones personales.

**Release nuevo:** Un tag `v1.0.0` creará una Release en **borrador**. Revisa
los resultados y detecciones antes de pulsar Publicar. El script de Build no
publica automáticamente en cada commit.
