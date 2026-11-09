#!/usr/bin/env python3
"""Project-independent CI build for the local ItsOcho Studio Python app.

Searches for server.py at the root or under one subfolder; never packages
credentials, user settings, user audio, or random files from a checkout.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

REPO=Path(__file__).resolve().parents[1]
HTML=('panel.html','overlay.html','music.html')
DIRS=('logos','assets')
IGNORE={'.git','.venv','venv','.build_env','build','dist','release','SALIDA_LISTA_PARA_COMPARTIR','__pycache__'}

def app_dir() -> Path:
    override=os.environ.get('ITSOCHO_APP_DIR','').strip()
    if override:
        d=(REPO/override).resolve()
        if REPO not in d.parents and d!=REPO:
            raise SystemExit('ITSOCHO_APP_DIR must be inside the checkout')
        candidates=[d]
    else:
        candidates=[REPO]+[p for p in sorted(REPO.iterdir()) if p.is_dir() and p.name not in IGNORE]
    matches=[p for p in candidates if (p/'server.py').is_file() and all((p/n).is_file() for n in HTML)]
    if len(matches)!=1:
        raise SystemExit(f'Expected exactly one application directory with server.py + {HTML}, found: {matches}. Set ITSOCHO_APP_DIR if needed.')
    return matches[0]

def verify(d:Path)->None:
    for private in ('.streamdeck_token','.env','RUTA_PYTHON.txt'):
        if (d/private).exists():
            raise SystemExit(f'Private local file must not be in GitHub checkout: {private}')
    py_compile.compile(str(d/'server.py'),doraise=True)
    for n in HTML:
        if not (d/n).read_text(encoding='utf-8').strip():
            raise SystemExit(f'Empty required app file: {n}')
    # Only a syntax/structure check, never described as a malware clearance.
    print('Verified syntax and required sources in',d)

def smoke(d:Path)->None:
    # Smoke tests execute the app in an isolated directory. The server creates
    # .streamdeck_token and other runtime state on startup: never write those
    # private/generated files into the repository checkout.
    with tempfile.TemporaryDirectory(prefix='itsocho-ci-smoke-') as tmp:
        runtime=Path(tmp)
        for name in ('server.py',)+HTML:
            shutil.copy2(d/name,runtime/name)
        for dn in DIRS:
            src=d/dn
            if src.is_dir():
                shutil.copytree(src,runtime/dn,symlinks=False)
        (runtime/'musica').mkdir(exist_ok=True)

        # Don't open a browser or attempt to download logos.
        env=dict(os.environ)
        env.pop('ITSOCHO_AUTO_DOWNLOAD_LOGOS',None)
        child=subprocess.Popen([sys.executable,'-u','server.py','--no-browser'],cwd=runtime,env=env,
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            urls={'/panel':'text/html','/overlay':'text/html','/music':'text/html','/api/state':'application/json'}
            last_error=None
            for _ in range(40):
                if child.poll() is not None:
                    raise RuntimeError('Server exited early with status '+str(child.returncode))
                try:
                    with urllib.request.urlopen('http://127.0.0.1:8767/api/state',timeout=.5) as r:
                        if r.status==200:break
                except Exception as e:
                    last_error=e;time.sleep(.25)
            else:
                raise RuntimeError(f'Server did not become ready: {last_error}')
            for path,_ in urls.items():
                with urllib.request.urlopen('http://127.0.0.1:8767'+path,timeout=3) as r:
                    if r.status!=200:raise RuntimeError(f'{path} returned HTTP {r.status}')
                    if not r.read(256):raise RuntimeError(f'{path} returned empty body')
            print('HTTP smoke checks passed for panel, overlay, music, state (isolated runtime)')
        finally:
            child.terminate()
            try:child.wait(timeout=3)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=3)

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()

def build(d:Path)->None:
    if sys.platform!='win32':raise SystemExit('Autonomous Windows build requires Windows runner')
    subprocess.run([sys.executable,'-m','PyInstaller','--clean','--noconfirm','--onefile','--console',
                    '--name','ItsOcho_Studio','--distpath',str(REPO/'_build_dist'),
                    '--workpath',str(REPO/'_build_work'),
                    '--specpath',str(REPO/'_build_spec'),str(d/'server.py')],cwd=d,check=True)
    exe=REPO/'_build_dist'/'ItsOcho_Studio.exe'
    if not exe.is_file():raise RuntimeError('PyInstaller failed to produce the Windows executable')
    dest=REPO/'release';dest.mkdir(exist_ok=True)
    shutil.copy2(exe,dest/'ItsOcho_Studio.exe')
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)/'ItsOcho_Studio';folder.mkdir()
        shutil.copy2(exe,folder/'ItsOcho_Studio.exe')
        # The HTML remains external: server.py searches next to its executable.
        for name in ('server.py',)+HTML:
            shutil.copy2(d/name,folder/name)
        for dn in DIRS:
            src=d/dn
            if src.exists() and src.is_dir():
                shutil.copytree(src,folder/dn,symlinks=False)
        (folder/'musica').mkdir()
        (folder/'musica'/'README.txt').write_text('No music is bundled. Import audio you are authorized to use through the panel.\n',encoding='utf-8')
        docs=REPO/'VERIFICAR_DESCARGA.md'
        if docs.exists():shutil.copy2(docs,folder/docs.name)
        archive=dest/'ItsOcho_Studio_Windows.zip'
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for file in sorted(folder.rglob('*')):
                if file.is_file():z.write(file,file.relative_to(Path(tmp)))
    (dest/'SHA256SUMS.txt').write_text(''.join(f'{sha256(dest/n)}  {n}\n' for n in
        ('ItsOcho_Studio.exe','ItsOcho_Studio_Windows.zip')),encoding='ascii')
    print('Built',dest,'\nSHA256:\n',(dest/'SHA256SUMS.txt').read_text())

if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ('verify','smoke','build'):
        raise SystemExit('Usage: python tools/ci_release.py verify|smoke|build')
    d=app_dir();verify(d)
    {'verify':lambda:None,'smoke':lambda:smoke(d),'build':lambda:build(d)}[sys.argv[1]]()
