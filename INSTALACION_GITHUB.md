# Integrar GitHub Actions en ItsOcho-Overlay-Studio

Estos archivos se han preparado a partir del ZIP de ItsOcho Studio v5.14.
**No se ha confirmado el contenido actual del repositorio GitHub.** Revisa las rutas
antes de fusionar estos archivos. No sobrescribas los que ya tenga el repositorio.

1. Copia `.github/workflows/`, `tools/ci_release.py` y `VERIFICAR_DESCARGA.md` en la RAÍZ del repositorio. Conserva los archivos originales.
2. Los workflows esperan `server.py`, `panel.html`, `overlay.html` y `music.html` juntos, ya sea en raíz o en una sola subcarpeta directa. Si hay más de un proyecto, define `ITSOCHO_APP_DIR` en los pasos que ejecutan ci_release.py.
3. Comprueba que el repositorio no contiene claves WebSocket, token Stream Deck, música no autorizada o configuraciones personales.
4. Confirma los cambios y abre la pestaña **Actions**. El workflow `CI - Verify source` debe pasar.
5. Desde **Actions → Windows - Build, attest and draft release → Run workflow**, prueba una compilación manual; descarga los Artifacts y comprueba las atestaciones. La ejecución manual no genera una Release.
6. Cuando todo funcione, crea un tag de versión `v1.0.0` y súbelo:

   ```powershell
   git tag v1.0.0
   git push origin v1.0.0
   ```

7. El workflow del tag crea una **Release en borrador**. Valida sus resultados y el análisis antivirus antes de publicarla.
8. La Release contiene un ZIP ejecutable, el EXE por separado y `SHA256SUMS.txt`. No contiene canciones ni credenciales de usuario.

Si el repositorio es PRIVADO, GitHub artifact attestations puede requerir
un plan Enterprise Cloud. En público es compatible con los planes actuales.

**No marques la aplicación como segura solo por pasar CI.** Si Deep Instinct
sigue detectando el ejecutable, revisa el motivo y solicita un análisis de
falso positivo al fabricante antes de distribuir.
