# Resultado de la revisión del EXE original

Archivo inspeccionado: `ItsOcho_Studio.exe` del paquete anterior `ItsOcho_Studio_v5_14_WINDOWS_EXE_Y_BAT.zip`.

SHA-256: `9dbce10f87c4fdf464cc77892bd54c75c12dedf29f874bb92b0f0c1f3f0283de`

Formato: ejecutable Windows x64 (Go, consola). Se comprobó su información de compilación: Go 1.23.2, `CGO_ENABLED=0`, `GOOS=windows`, `GOARCH=amd64`, `-trimpath=true`.

Se reconstruyó desde `SOURCE/ItsOcho_Studio_launcher.go` utilizando Go 1.23.2, en entorno Linux con cross-compilación a Windows:

```bash
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o ItsOcho_Studio.exe ./SOURCE/ItsOcho_Studio_launcher.go
```

**La reconstrucción obtuvo un SHA-256 idéntico, byte por byte, al ejecutable entregado.** Esto permite verificar la procedencia del binario a partir del código fuente incluido. No supone un análisis dinámico en Windows ni confirma ausencia de vulnerabilidades o malware en las dependencias o funciones del programa.

El launcher Go, según el código fuente inspeccionado, localiza Python y ejecuta el `server.py` local (127.0.0.1:8767). Se inspeccionaron indicadores habituales de persistencia, cambios de registro, descarga de ejecutables y comandos remotos en el launcher y no se encontraron en dicho archivo. Las descargas de logos en el servidor Python solo se activan explícitamente o mediante variable de entorno.

**No se comprobó con Deep Instinct ni con Acronis desde este entorno**. Si se obtuvo una alerta, no se debe asumir que es un falso positivo solo porque otro motor no detectó nada. Identifica el hash exacto del archivo escaneado para saber si corresponde al launcher Go original o a un EXE autónomo recompilado con PyInstaller.

No deshabilites el antivirus ni añadas una exclusión para ejecutar un archivo señalado como malicioso. La alternativa para revisión es el paquete de código fuente sin EXE compilado.
