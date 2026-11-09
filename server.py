#!/usr/bin/env python3
"""ItsOcho Timeline · Panel local para OBS (stdlib, sin instalaciones extra)."""
import json
import threading
import time
import webbrowser
import argparse
import traceback
import urllib.request
import urllib.parse
import base64
import binascii
import concurrent.futures
import shutil
import re
import os
import mimetypes
import ssl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import sys

# For an autonomous PyInstaller EXE, persistent user files live alongside the EXE.
# Normal Python/BAT launch still uses the directory containing server.py.
HERE=(Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False)
      else Path(__file__).resolve().parent)
HOST='127.0.0.1'
PORT=8767
N_GAMES=19
STATE={'index':0,'camera':False,'timeline':True,'hudVisible':True,'cinema':False,'logos':True,'flash':0,'revision':0,'musicEnabled':True,'musicVolume':55,'musicSeconds':20,'musicCue':0,'musicStop':0,'transitionEnabled':True,'transitionPhase':'idle','transitionToken':0,'phaseSince':0,'introToken':0,'beatLevel':0.0,'ps5Frame':False,'ps5X':1345,'ps5Y':130,'ps5Width':520,'camX':1588,'camY':799,'camWidth':280,'enabledGames':[True]*N_GAMES,'gameTitles':[True]*N_GAMES,'gameLogos':[True]*N_GAMES,'titleVisible':True,'brandMarkVisible':True,'brandNameVisible':True,'brandSubtitleVisible':True,'brandName':'ITSOCHO','brandSubtitle':'THE ROAD TO GTA VI','deckSeq':0,'deckAction':''}
# Saved positioning of the independent 16:9 PS5 download frame.
PS5_SETTINGS=HERE/'ps5_layout.json'
try:
    saved=json.loads(PS5_SETTINGS.read_text('utf-8')) if PS5_SETTINGS.is_file() else {}
    w=saved.get('width',520); x=saved.get('x',1345); y=saved.get('y',130)
    if all(type(n)==int for n in (w,x,y)) and 320<=w<=850 and 0<=x<=1920-w and 0<=y<=1080-round(w*9/16):
        STATE.update(ps5Width=w,ps5X=x,ps5Y=y)
except (OSError,ValueError,TypeError,UnicodeError):
    pass
# v5.14: separately persisted 4:3 camera frame position, independent of PS5.
CAM_SETTINGS=HERE/'camera_layout.json'
try:
    saved=json.loads(CAM_SETTINGS.read_text('utf-8')) if CAM_SETTINGS.is_file() else {}
    w=saved.get('width',280);x=saved.get('x',1588);y=saved.get('y',799)
    if all(type(v)==int for v in (w,x,y)) and 180<=w<=700 and 0<=x<=1920-w and 0<=y<=1080-round(w*3/4):
        STATE.update(camWidth=w,camX=x,camY=y)
except (OSError,ValueError,TypeError,UnicodeError):
    pass
LOCK=threading.Lock()
# v5.12: permanent queue and per-element presentation. File is separate from
# music configuration so migrating from an earlier ZIP keeps custom MP3s.
TIMELINE_SETTINGS=HERE/'timeline_config.json'
CONFIG_KEYS=('enabledGames','gameTitles','gameLogos','titleVisible','logos',
             'brandMarkVisible','brandNameVisible','brandSubtitleVisible',
             'brandName','brandSubtitle')
def validate_config(data):
    if not isinstance(data,dict):raise ValueError('Configuración incorrecta')
    clean={}
    for key in ('enabledGames','gameTitles','gameLogos'):
        if key in data:
            value=data[key]
            if not isinstance(value,list) or len(value)!=N_GAMES or any(type(b)!=bool for b in value):
                raise ValueError('La lista de juegos debe contener 19 casillas válidas.')
            if key=='enabledGames' and not any(value):
                raise ValueError('Deja al menos un GTA activado para el directo.')
            clean[key]=value[:]
    for key in ('titleVisible','logos','brandMarkVisible','brandNameVisible','brandSubtitleVisible'):
        if key in data:
            if type(data[key])!=bool:raise ValueError('La visibilidad debe ser verdadera o falsa.')
            clean[key]=data[key]
    for key in ('brandName','brandSubtitle'):
        if key in data:
            value=data[key]
            if not isinstance(value,str) or len(value)>80 or any(ord(c)<32 for c in value):
                raise ValueError('El texto debe tener como máximo 80 caracteres.')
            clean[key]=value.strip()[:48] if key=='brandName' else value.strip()[:64]
    return clean

def persist_config(data):
    # os.replace prevents corrupting the preference file on power loss.
    tmp=TIMELINE_SETTINGS.with_suffix('.json.tmp')
    tmp.write_text(json.dumps({k:data[k] for k in CONFIG_KEYS},ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(tmp,TIMELINE_SETTINGS)

try:
    loaded=validate_config(json.loads(TIMELINE_SETTINGS.read_text(encoding='utf-8')))
    STATE.update(loaded)
except (OSError,ValueError,UnicodeError):
    pass

def queue_locked():
    return [i for i,enabled in enumerate(STATE['enabledGames']) if enabled]

def nearest_enabled_locked(old):
    q=queue_locked()
    return next((i for i in q if i>old),q[-1])

STATE['index']=next(i for i,x in enumerate(STATE['enabledGames']) if x)

def snapshot_locked():
    queue=queue_locked()
    snap=dict(STATE)
    snap['enabledGames']=list(STATE['enabledGames'])
    snap['gameTitles']=list(STATE['gameTitles'])
    snap['gameLogos']=list(STATE['gameLogos'])
    snap['queue']=queue
    snap['queueCount']=len(queue)
    snap['queuePosition']=(queue.index(STATE['index'])+1 if STATE['index'] in queue else 0)
    snap['transitionTarget']=TRANS['target']
    now=time.time()
    snap['beatLive']=(snap['transitionPhase']=='intro' and now-TRANS['beatAt']<0.75 and snap['beatLevel']>0.035)
    snap['audioConnected']=(snap['transitionPhase']=='intro' and now-TRANS['audioAt']<0.75)
    if not snap['beatLive']:snap['beatLevel']=0.0
    return snap
LOGOS=HERE/'logos'
LOGOS.mkdir(exist_ok=True)
FALLBACKS=HERE/'assets'  # Read-only assets bundled with the ZIP (offline).
# Official GTA title logos, mostly Wikimedia Commons / Grand Theft Wiki.
# A duplicate entry reuses the same game logo. Once downloaded, all images
# are served locally from this app and OBS no longer needs Internet.
SOURCE_FILES=[
 [('gtw','GTA1-logo.png'),('commons','Grand Theft Auto (1997) logo (SGDB 88763).png')],
 [('gtw','GTALondon1969-logo.png'),('commons','Grand Theft Auto London Logo.png')],
 [('commons','Grand Theft Auto 2 logo.svg'),('gtw','GTA2-logo.png')],
 [('commons','Grand Theft Auto III logo.svg'),('gtw','GTAIII-logo-bare.png')],
 [('commons','Grand Theft Auto Vice City logo.svg'),('gtw','GTAViceCity-logo-bare.png')],
 [('commons','Grand Theft Auto San Andreas logo.svg'),('gtw','GTASanAndreas-logo-bare-white.png')],
 [('commons','Grand Theft Auto Advance logo.svg'),('gtw','GTAAdvance-logo-bare.png')],
 [('commons','Grand Theft Auto Liberty City Stories logo.svg'),('gtw','GTALibertyCityStories-logo-bare.png')],
 [('commons','GTA Vice City Stories Logo.svg'),('gtw','GTAViceCityStories-logo-bare.png')],
 [('commons','GTA IV logo.svg'),('gtw','GTAIV-logo-bare.png')],
 [('commons','Grand Theft Auto The Lost and Damned Logo.png'),('gtw','TheLostandDamned-logo.png')],
 [('commons','Grand Theft Auto Chinatown Wars logo.svg'),('gtw','GTAChinatownWars-logo-bare.png')],
 [('commons','Grand Theft Auto The Ballad of Gay Tony logo.png'),('gtw','TheBalladofGayTony-logo.png')],
 [('gtw','GTAV-logo.png')],
 [('commons','Grand Theft Auto Online Logo.svg'),('gtw','GTAO-logo.png')],
 [('commons','Grand Theft Auto - The Trilogy - The Definitive Edition logo.svg')],
 [('gtw','GTAV-logo.png')],
 [('gtw','GTAV-logo.png')],
 [('commons','Grand Theft Auto VI logo (with gradient).svg'),('commons','Grand Theft Auto VI logo.svg')],
]
ALIAS={16:13,17:13}
LOGO_REVISIONS={'revision':0,'downloading':False,'failures':[]}
LOGOS_LOCK=threading.RLock()

def canonical(i):return ALIAS.get(i,i)
def logo_local_path(index):
    # A per-chapter custom image wins over the shared default.
    candidates=[index] + ([canonical(index)] if canonical(index)!=index else [])
    for idx in candidates:
        for ext in ('.png','.svg','.webp','.jpg','.jpeg'):
            p=LOGOS/f'{idx+1:02d}{ext}'
            if p.is_file():return p
    return None

def logo_path(index):
    # Prioritize authentic downloaded/uploaded logos; use built-in fallback offline.
    local=logo_local_path(index)
    if local:return local
    embedded=FALLBACKS/f'{index+1:02d}.png'
    return embedded if embedded.is_file() else None

def guess_type(data):
    raw=data.lstrip()
    if data.startswith(b'\x89PNG\r\n\x1a\n'):return '.png'
    if data.startswith(b'\xff\xd8\xff'):return '.jpg'
    if data[:4]==b'RIFF' and data[8:12]==b'WEBP':return '.webp'
    if raw.startswith(b'<svg') or raw.startswith(b'<?xml') and b'<svg' in raw[:1024]:return '.svg'
    return None

def wiki_image_urls(site,filename):
    host='commons.wikimedia.org' if site=='commons' else 'www.grandtheftwiki.com'
    api=f'https://{host}/w/api.php' if site=='commons' else f'https://{host}/api.php'
    args=urllib.parse.urlencode({'action':'query','titles':f'File:{filename}','prop':'imageinfo','iiprop':'url','format':'json'})
    yield f'{api}?{args}',True
    # MediaWiki normally handles FilePath redirects even if its API is blocked.
    yield f'https://{host}/wiki/Special:FilePath/{urllib.parse.quote(filename)}' if site=='commons' else f'https://{host}/Special:FilePath/{urllib.parse.quote(filename)}',False

def fetch_image(index):
    if logo_local_path(index):return True
    import json as _json
    if index==18:
        direct='https://upload.wikimedia.org/wikipedia/commons/9/94/Grand_Theft_Auto_VI_logo.svg'
        try:
            req=urllib.request.Request(direct,headers={'User-Agent':'Mozilla/5.0 (compatible; ItsOchoTimeline/5.2)','Accept':'image/svg+xml,image/*'})
            with urllib.request.urlopen(req,timeout=8) as response: content=response.read(180000)
            ext=guess_type(content)
            if ext in ('.svg','.png') and 100<len(content)<170000 and b'<script' not in content.lower():
                with LOGOS_LOCK:
                    if logo_local_path(index):return True
                    (LOGOS/f'19{ext}').write_bytes(content)
                    LOGO_REVISIONS['revision']+=1
                return True
        except Exception:pass
    for site,filename in SOURCE_FILES[index]:
        for url,is_api in wiki_image_urls(site,filename):
            try:
                request=urllib.request.Request(url,headers={'User-Agent':'ItsOchoTimeline/5.0 (GTA-history-stream-logo-cache; contact: local-app)','Accept':'application/json,image/png,image/svg+xml,image/webp,image/jpeg,*/*'})
                with urllib.request.urlopen(request,timeout=6) as response:
                    content=response.read(2500000)
                if is_api:
                    try:
                        items=_json.loads(content).get('query',{}).get('pages',{})
                        if isinstance(items,dict):items=items.values()
                        actual=next((item['imageinfo'][0]['url'] for item in items if item.get('imageinfo')),None)
                    except (ValueError,KeyError,StopIteration):actual=None
                    if not actual or not actual.startswith('https://'):continue
                    request=urllib.request.Request(actual,headers={'User-Agent':'ItsOchoTimeline/5.0','Accept':'image/*'})
                    with urllib.request.urlopen(request,timeout=8) as response:content=response.read(2500000)
                ext=guess_type(content)
                if not ext or not 100<len(content)<2450000:continue
                if ext=='.svg' and b'<script' in content.lower():continue
                with LOGOS_LOCK:
                    # A user-uploaded logo takes precedence over remote downloads.
                    if logo_local_path(index):return True
                    (LOGOS/f'{index+1:02d}{ext}').write_bytes(content)
                    LOGO_REVISIONS['revision']+=1
                return True
            except Exception:
                continue
    return False

def download_missing_logos():
    with LOGOS_LOCK:
        LOGO_REVISIONS['failures']=[]
    indices=[i for i in range(N_GAMES) if i not in ALIAS and not logo_local_path(i)]
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda i:(i,fetch_image(i)),indices))
        with LOGOS_LOCK:LOGO_REVISIONS['failures']=[i+1 for i,ok in results if not ok]
    finally:
        with LOGOS_LOCK:LOGO_REVISIONS['downloading']=False

def start_logo_download():
    with LOGOS_LOCK:
        if LOGO_REVISIONS['downloading']:return
        LOGO_REVISIONS['downloading']=True
    threading.Thread(target=download_missing_logos,daemon=True).start()

def logo_status():
    with LOGOS_LOCK:
        return {'ready':[bool(logo_path(i)) for i in range(N_GAMES)],
                'fallback':[bool(logo_path(i)) and not bool(logo_local_path(i)) for i in range(N_GAMES)],
                'versions':[str(logo_path(i).stat().st_mtime_ns) if logo_path(i) else '' for i in range(N_GAMES)],
                'downloading':LOGO_REVISIONS['downloading'],
                'revision':LOGO_REVISIONS['revision'],
                'failures':list(LOGO_REVISIONS['failures'])}



# Music is user-provided only; no copyrighted audio is distributed with the project.
MUSIC_DIR=HERE/'musica'
MUSIC_DIR.mkdir(exist_ok=True)
MUSIC_META_FILE=HERE/'musica_config.json'
MUSIC_LOCK=threading.RLock()
MAX_MUSIC_SIZE=30 * 1024 * 1024
MUSIC_MIME={'.mp3':'audio/mpeg','.wav':'audio/wav','.ogg':'audio/ogg','.m4a':'audio/mp4','.webm':'audio/webm','.flac':'audio/flac'}

def read_music_meta():
    try:
        data=json.loads(MUSIC_META_FILE.read_text(encoding='utf-8'))
        return data if isinstance(data,dict) else {}
    except (OSError,ValueError):
        return {}

MUSIC_META=read_music_meta()
for key,minimum,maximum,default in (('musicVolume',0,100,55),('musicSeconds',3,120,20)):
    v=MUSIC_META.get(key,default)
    STATE[key]=max(minimum,min(maximum,int(v))) if type(v) is int else default

def save_music_meta():
    with MUSIC_LOCK:
        with LOCK:
            settings={k:STATE[k] for k in ('musicVolume','musicSeconds')}
        settings['names']=MUSIC_META.get('names',{})
        temp=MUSIC_META_FILE.with_suffix('.tmp')
        temp.write_text(json.dumps(settings,ensure_ascii=False,indent=2),encoding='utf-8')
        temp.replace(MUSIC_META_FILE)

def current_music_file(index):
    if type(index)!=int or not 0<=index<N_GAMES:return None
    for ext in MUSIC_MIME:
        f=MUSIC_DIR/f'{index+1:02d}{ext}'
        if f.is_file():return f
    return None

def music_status():
    with MUSIC_LOCK:
        tracks=[]
        for i in range(N_GAMES):
            f=current_music_file(i)
            tracks.append({'index':i,'ready':f is not None,
                'name':MUSIC_META.get('names',{}).get(str(i),f.name if f else ''),
                'version':str(f.stat().st_mtime_ns) if f else ''})
        return {'tracks':tracks}

def validate_music_file(content,ext):
    if ext not in MUSIC_MIME:raise ValueError('Formatos admitidos: MP3, WAV, OGG, M4A, WEBM y FLAC.')
    if ext=='.mp3' and not (content.startswith(b'ID3') or content[:1]==b'\xff' and (content[1]&0xe0)==0xe0):raise ValueError('El archivo no parece MP3.')
    if ext=='.wav' and not (content.startswith(b'RIFF') and content[8:12]==b'WAVE'):raise ValueError('El archivo no parece WAV.')
    if ext=='.ogg' and not content.startswith(b'OggS'):raise ValueError('El archivo no parece OGG.')
    if ext=='.m4a' and b'ftyp' not in content[4:12]:raise ValueError('El archivo no parece M4A.')
    if ext=='.webm' and not content.startswith(b'\x1a\x45\xdf\xa3'):raise ValueError('El archivo no parece WEBM.')
    if ext=='.flac' and not content.startswith(b'fLaC'):raise ValueError('El archivo no parece FLAC.')



# OBS cinematic chapter sequence. One server-owned state machine means that the
# visual browser source and the audio-only browser source stay synchronized.
# Clock timestamps are wall-clock values; phases are advanced under LOCK.
PHASE_TIME={'hud_out':0.84,'door_close':0.92,'door_open':1.02,'hud_in':0.96}
TRANS={'target':None,'deadline':0.0,'bootArmed':True,'beatAt':0.0,'audioAt':0.0}

def phase_locked(phase,now):
    STATE['transitionPhase']=phase
    STATE['phaseSince']=now
    STATE['transitionToken']+=1
    if phase=='intro':
        target=TRANS['target']
        if target is not None:STATE['index']=target
        STATE['introToken']+=1
        STATE['musicCue']+=1
        ready=current_music_file(STATE['index']) is not None
        duration=STATE['musicSeconds'] if ready and STATE['musicEnabled'] else 1.8
        TRANS['deadline']=now+duration
    elif phase in PHASE_TIME:
        TRANS['deadline']=now+PHASE_TIME[phase]
    else:
        TRANS['deadline']=0.0
        TRANS['target']=None
        STATE['beatLevel']=0.0
    STATE['revision']+=1

def advance_locked(now):
    for _ in range(7):
        phase=STATE['transitionPhase']
        if phase=='idle' or now<TRANS['deadline']:break
        event_time=TRANS['deadline']
        if phase=='hud_out':new='door_close'
        elif phase=='door_close':new='intro'
        elif phase=='intro':new='door_open';STATE['musicStop']+=1
        elif phase=='door_open':new='hud_in'
        elif phase=='hud_in':new='idle'
        else:new='idle'
        phase_locked(new,event_time)

def start_cinematic_locked(target,now,immediate=False):
    advance_locked(now)
    if STATE['transitionPhase']!='idle':return False
    TRANS['target']=target
    phase_locked('intro' if immediate else 'hud_out',now)
    return True

def state_snapshot():
    with LOCK:
        now=time.time()
        advance_locked(now)
        return snapshot_locked()

def apply_update(request):
    with LOCK:
        now=time.time();advance_locked(now)
        action=request.get('action')
        if action in ('next','prev','first','last','jump','cinematic_replay'):
            i=STATE['index']
            queue=queue_locked()
            pos=queue.index(i) if i in queue else -1
            if action=='next':target=queue[min(len(queue)-1,pos+1)]
            elif action=='prev':target=queue[max(0,pos-1)]
            elif action=='first':target=queue[0]
            elif action=='last':target=queue[-1]
            elif action=='cinematic_replay':target=i
            else:
                target=request.get('index')
                if type(target)!=int or not 0<=target<N_GAMES:raise ValueError('Capítulo incorrecto')
                if target not in queue:raise ValueError('Ese GTA está desactivado. Actívalo en la cola primero.')
            if STATE['transitionPhase']!='idle':
                raise ValueError('Transición en curso. Usa «Saltar animación» para terminarla.')
            if target!=i or action=='cinematic_replay':
                if STATE['transitionEnabled']:
                    start_cinematic_locked(target,now)
                else:
                    STATE['index']=target
                    STATE['musicCue']+=1
        elif action=='cinematic_skip':
            if STATE['transitionPhase']!='idle':
                if TRANS['target'] is not None:STATE['index']=TRANS['target']
                STATE['musicStop']+=1
                phase_locked('idle',now)
        elif action=='cinematic_toggle':
            STATE['transitionEnabled']=not STATE['transitionEnabled']
            if not STATE['transitionEnabled'] and STATE['transitionPhase']!='idle':
                if TRANS['target'] is not None:STATE['index']=TRANS['target']
                STATE['musicStop']+=1
                phase_locked('idle',now)
        elif action=='queue_update':
            # A single atomic request updates the entire selection and its
            # presentation options, making queue+counter agree instantly.
            clean=validate_config(request.get('config'))
            if not clean:raise ValueError('No se recibieron cambios.')
            STATE.update(clean)
            queue=queue_locked()
            if STATE['index'] not in queue:
                STATE['index']=nearest_enabled_locked(STATE['index'])
                STATE['musicStop']+=1
                if STATE['transitionPhase']!='idle':phase_locked('idle',now)
            elif TRANS['target'] is not None and TRANS['target'] not in queue:
                # Cancel only the invalid pending animation; keep the
                # existing enabled game rather than skipping one.
                STATE['musicStop']+=1
                phase_locked('idle',now)
            # Save validated snapshot before claiming success.
            persist_config(STATE)
        elif action=='ps5_toggle':
            STATE['ps5Frame']=not STATE['ps5Frame']
        elif action=='ps5_layout':
            x=request.get('x'); y=request.get('y'); width=request.get('width')
            if not all(type(v)==int for v in (x,y,width)) or not 320<=width<=850 or not 0<=x<=1920-width or not 0<=y<=1080-round(width*9/16):
                raise ValueError('El marco PS5 debe permanecer dentro del lienzo 1920×1080. Ancho permitido: 320–850.')
            STATE.update(ps5X=x,ps5Y=y,ps5Width=width)
        elif action=='camera_layout':
            x=request.get('x');y=request.get('y');width=request.get('width')
            if not all(type(v)==int for v in (x,y,width)) or not 180<=width<=700 or not 0<=x<=1920-width or not 0<=y<=1080-round(width*3/4):
                raise ValueError('La cámara 4:3 debe caber dentro del lienzo 1920×1080. Ancho permitido: 180–700 px.')
            STATE.update(camX=x,camY=y,camWidth=width)
        elif action=='camera':
            STATE['camera']=not STATE['camera']
        elif action=='hud_toggle':
            STATE['hudVisible']=not STATE['hudVisible']
        elif action=='timeline':
            STATE['timeline']=not STATE['timeline']
        elif action=='cinema':
            STATE['cinema']=not STATE['cinema']
        elif action=='logos':
            STATE['logos']=not STATE['logos']
            persist_config(STATE)
        elif action=='music_toggle':
            STATE['musicEnabled']=not STATE['musicEnabled']
            if not STATE['musicEnabled']:STATE['musicStop']+=1
        elif action=='music_play':
            STATE['musicCue']+=1
        elif action=='music_stop':
            STATE['musicStop']+=1
            if STATE['transitionPhase']=='intro':
                TRANS['deadline']=now;advance_locked(now)
        elif action=='music_settings':
            vol=request.get('volume')
            secs=request.get('seconds')
            if type(vol)!=int or not 0<=vol<=100 or type(secs)!=int or not 3<=secs<=120:
                raise ValueError('Volumen/duración incorrectos')
            STATE['musicVolume']=vol
            STATE['musicSeconds']=secs
        elif action=='flash':
            STATE['flash']+=1
        else:
            raise ValueError('Acción incorrecta')
        STATE['revision']+=1
        response=snapshot_locked()
    return response, action

# Stream Deck uses the official Website action: GET request in background.
# A random local secret prevents accidental/external requests from controlling the show.
import secrets
import hmac
DECK_SECRET_FILE=HERE/'.streamdeck_token'
def ensure_deck_token():
    try:
        token=DECK_SECRET_FILE.read_text(encoding='ascii').strip()
        if re.fullmatch(r'[A-Za-z0-9_-]{32,128}',token):return token
    except (OSError,UnicodeError):pass
    token=secrets.token_urlsafe(32)
    temp=DECK_SECRET_FILE.with_suffix('.tmp')
    temp.write_text(token,encoding='ascii')
    temp.replace(DECK_SECRET_FILE)
    return token
DECK_TOKEN=ensure_deck_token()
DECK_COMMANDS={
 'next':('Siguiente GTA','next'),
 'prev':('GTA anterior','prev'),
 'first':('Primer GTA','first'),
 'last':('Último GTA','last'),
 'present':('Presentar juego','cinematic_replay'),
 'skip':('Saltar animación','cinematic_skip'),
 'hud':('Mostrar / ocultar HUD','hud_toggle'),
 'camera':('Marco de cámara','camera'),
 'ps5':('Marco PS5','ps5_toggle'),
 'music-play':('Reproducir canción','music_play'),
 'music-stop':('Detener canción','music_stop'),
 'music-toggle':('Activar / desactivar música','music_toggle'),
 'cinema':('Modo tráiler','cinema'),
 'timeline':('Línea del tiempo','timeline'),
 'logos':('Mostrar / ocultar logos','logos'),
 'flash':('Mostrar descripción','flash'),
 'transitions':('Transiciones cinematográficas','cinematic_toggle'),
}
DECK_SEQUENCE=0

class Handler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        """Silenciar consultas GET correctas; conservar acciones y errores.

        OBS y el panel necesitan consultar el estado frecuentemente. Esas
        peticiones HTTP 200 son normales, no advertencias. Los errores HTTP
        y las acciones POST siguen apareciendo en la consola para depuración.
        """
        try:
            success = 200 <= int(code) < 400
        except (ValueError, TypeError):
            success = False
        if (self.command in ('GET', 'HEAD') or self.path.startswith('/api/beat')) and success:
            return
        super().log_request(code, size)

    def send_bytes(self, data, type_, status=200):
        self.send_response(status)
        self.send_header('Content-Type',type_)
        self.send_header('Cache-Control','no-store, no-cache, must-revalidate')
        self.send_header('Content-Length',str(len(data)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Access-Control-Allow-Origin','http://127.0.0.1:8767')
        self.end_headers()
        self.wfile.write(data)

    def json(self, value, status=200):
        self.send_bytes(json.dumps(value,ensure_ascii=False).encode('utf-8'),'application/json; charset=utf-8',status)

    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/api/streamdeck/actions':
            self.json({'items':[{'id':key,'name':name,'url':f'http://{HOST}:{PORT}/deck/{DECK_TOKEN}/{key}'} for key,(name,_) in DECK_COMMANDS.items()]})
            return
        if p.startswith('/deck/'):
            parts=p.strip('/').split('/')
            if len(parts)!=3 or parts[0]!='deck' or not hmac.compare_digest(parts[1],DECK_TOKEN):
                self.json({'ok':False,'error':'Enlace de Stream Deck no autorizado'},403);return
            action=DECK_COMMANDS.get(parts[2])
            if action is None:
                self.json({'ok':False,'error':'Acción desconocida'},404);return
            try:
                response, applied=apply_update({'action':action[1]})
            except ValueError as err:
                self.json({'ok':False,'error':str(err)},409);return
            global DECK_SEQUENCE
            with LOCK:
                DECK_SEQUENCE+=1
                STATE['deckSeq']=DECK_SEQUENCE
                STATE['deckAction']=action[1]
                # Expose deck origin so a connected browser can also mirror
                # camera/PS5 source visibility inside OBS.
                STATE['revision']+=1
            print('[STREAM DECK]',action[0],flush=True)
            self.json({'ok':True,'action':parts[2],'chapter':response['index']+1,'hud':response['hudVisible']})
            return
        if p=='/':
            self.send_response(302)
            self.send_header('Location','/panel')
            self.send_header('Content-Length','0')
            self.end_headers()
            return
        if p=='/api/music/status':
            self.json(music_status())
            return
        if p.startswith('/music/file/'):
            token=p.rsplit('/',1)[-1]
            if not token.isdigit() or len(token)!=2:
                self.json({'error':'Archivo no encontrado'},404);return
            index=int(token)-1
            with MUSIC_LOCK:
                f=current_music_file(index)
                if not f:self.json({'error':'Sin audio asignado'},404);return
                data=f.read_bytes()
                mime=MUSIC_MIME[f.suffix.lower()]
            # Support byte-range requests required by some audio decoders.
            start,end=0,len(data)-1
            range_header=self.headers.get('Range','')
            if range_header:
                match=re.fullmatch(r'bytes=(\d*)-(\d*)',range_header.strip())
                if not match or (not match.group(1) and not match.group(2)):
                    self.send_response(416);self.send_header('Content-Range',f'bytes */{len(data)}');self.send_header('Content-Length','0');self.end_headers();return
                if match.group(1):start=int(match.group(1))
                if match.group(2):end=min(int(match.group(2)),end) if match.group(1) else end
                if not match.group(1):start=max(0,len(data)-int(match.group(2)))
                if start>end or start>=len(data):
                    self.send_response(416);self.send_header('Content-Range',f'bytes */{len(data)}');self.send_header('Content-Length','0');self.end_headers();return
            body=data[start:end+1]
            self.send_response(206 if range_header else 200)
            self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Accept-Ranges','bytes')
            self.send_header('Cache-Control','no-store')
            if range_header:self.send_header('Content-Range',f'bytes {start}-{end}/{len(data)}')
            self.end_headers();self.wfile.write(body);return
        if p=='/api/logos/status':
            self.json(logo_status())
            return
        if p.startswith('/logos/'):
            name=p.split('/')[-1]
            if len(name)!=2 or not name.isdigit() or not 1<=int(name)<=N_GAMES:
                self.json({'error':'Logo incorrecto'},404);return
            path=logo_path(int(name)-1)
            if path is None:self.json({'error':'Logo todavía no disponible'},404);return
            type_={'.png':'image/png','.svg':'image/svg+xml','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}.get(path.suffix,'application/octet-stream')
            self.send_bytes(path.read_bytes(),type_)
            return
        if p=='/api/state':
            self.json(state_snapshot())
            return
        if p in ('/panel','/overlay','/music'):
            if p=='/overlay':
                with LOCK:
                    if TRANS['bootArmed']:
                        TRANS['bootArmed']=False
                        TRANS['target']=STATE['index']
                        start_cinematic_locked(STATE['index'],time.time(),immediate=True)
            filename={'/panel':'panel.html','/overlay':'overlay.html','/music':'music.html'}[p]
            data=(HERE/filename).read_bytes()
            self.send_bytes(data,'text/html; charset=utf-8')
            return
        self.json({'error':'No encontrado'},404)

    def do_POST(self):
        route=urlparse(self.path).path
        if route not in ('/api/update','/api/logos/retry','/api/logos/upload','/api/music/upload','/api/music/delete','/api/beat','/api/intro/finished'):
            self.json({'error':'No encontrado'},404)
            return
        # Solo acepta peticiones del panel local, sin exponer el servidor a la red.
        origin=self.headers.get('Origin','')
        if origin and origin!='http://127.0.0.1:8767':
            self.json({'error':'Origen no permitido'},403)
            return
        if route=='/api/music/upload':
            try:
                if self.headers.get('Content-Type','').split(';',1)[0]!='application/octet-stream':
                    self.json({'error':'Se requiere un archivo de audio.'},415);return
                q=urllib.parse.parse_qs(urlparse(self.path).query)
                i=int(q.get('index',['-1'])[0])
                if not 0<=i<N_GAMES:raise ValueError('Capítulo inválido')
                name=urllib.parse.unquote(q.get('name',[''])[0])
                ext=Path(name).suffix.lower()
                length=int(self.headers.get('Content-Length','0'))
                if not 100<=length<=MAX_MUSIC_SIZE:raise ValueError('Archivo demasiado grande; máximo 30 MB.')
                content=self.rfile.read(length)
                if len(content)!=length:raise ValueError('La carga no se completó.')
                validate_music_file(content,ext)
                with MUSIC_LOCK:
                    dest=MUSIC_DIR/f'{i+1:02d}{ext}'
                    tmp=MUSIC_DIR/f'.upload-{i+1:02d}.tmp'
                    tmp.write_bytes(content)
                    tmp.replace(dest)
                    for f in MUSIC_DIR.glob(f'{i+1:02d}.*'):
                        if f!=dest:f.unlink()
                    MUSIC_META.setdefault('names',{})[str(i)]=Path(name).name[:140]
                    save_music_meta()
                self.json(music_status());return
            except (ValueError,OverflowError,OSError) as err:
                self.json({'error':str(err)},400);return
        if route in ('/api/beat','/api/intro/finished'):
            # Local, bounded JSON from the music Browser Source. The token prevents
            # delayed events from an earlier track from touching a new chapter.
            try:
                if not self.headers.get('Content-Type','').startswith('application/json'):
                    self.json({'error':'JSON esperado'},415);return
                size=int(self.headers.get('Content-Length','0'))
                if size<2 or size>512:raise ValueError('Tamaño inválido')
                body=json.loads(self.rfile.read(size))
                token=body.get('token')
                if type(token)!=int:raise ValueError('Token inválido')
                with LOCK:
                    now=time.time();advance_locked(now)
                    valid=(STATE['transitionPhase']=='intro' and token==STATE['introToken'])
                    if valid and route=='/api/beat':
                        value=body.get('level',0)
                        if type(value) not in (int,float):raise ValueError('Nivel incorrecto')
                        STATE['beatLevel']=max(0.0,min(1.0,float(value)))
                        if STATE['beatLevel']>0.035:TRANS['beatAt']=now
                        if body.get('playing') is True:TRANS['audioAt']=now
                    elif valid and route=='/api/intro/finished':
                        TRANS['deadline']=now
                        advance_locked(now)
                self.json({'ok':True,'accepted':valid});return
            except (ValueError,TypeError,OverflowError,json.JSONDecodeError) as err:
                self.json({'error':str(err)},400);return
        if not self.headers.get('Content-Type','').startswith('application/json'):
            self.json({'error':'Se requiere JSON'},415)
            return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<1 or length>3000000: raise ValueError('Tamaño incorrecto')
            request=json.loads(self.rfile.read(length).decode('utf-8'))
            if not isinstance(request,dict): raise ValueError('Datos incorrectos')
            if route=='/api/music/delete':
                i=request.get('index')
                if type(i)!=int or not 0<=i<N_GAMES:raise ValueError('Capítulo inválido')
                with MUSIC_LOCK:
                    for file in MUSIC_DIR.glob(f'{i+1:02d}.*'):file.unlink()
                    MUSIC_META.setdefault('names',{}).pop(str(i),None)
                    save_music_meta()
                with LOCK:
                    if STATE['index']==i: STATE['musicStop']+=1;STATE['revision']+=1
                self.json(music_status());return
            if route=='/api/logos/retry':
                start_logo_download()
                self.json(logo_status());return
            if route=='/api/logos/upload':
                i=request.get('index')
                payload=request.get('data','')
                if type(i)!=int or not 0<=i<N_GAMES or not isinstance(payload,str) or not payload.startswith('data:image/') or ';base64,' not in payload:
                    raise ValueError('Logo o índice inválido')
                if len(payload)>2800000:raise ValueError('Logo demasiado grande (máximo 2 MB)')
                content=base64.b64decode(payload.split(';base64,',1)[1],validate=True)
                ext=guess_type(content)
                if not ext or not 50<len(content)<2100000:raise ValueError('Usa PNG, SVG, WEBP o JPG de menos de 2 MB')
                if ext=='.svg' and (b'<script' in content.lower() or b'onload=' in content.lower()):raise ValueError('SVG no seguro')
                with LOGOS_LOCK:
                    for p in LOGOS.glob(f'{i+1:02d}.*'):p.unlink()
                    (LOGOS/f'{i+1:02d}{ext}').write_bytes(content)
                    LOGO_REVISIONS['revision']+=1
                self.json(logo_status());return
            response, action=apply_update(request)
            if action=='camera_layout':
                try:
                    data={'x':response['camX'],'y':response['camY'],'width':response['camWidth']}
                    tmp=CAM_SETTINGS.with_suffix('.tmp')
                    tmp.write_text(json.dumps(data),encoding='utf-8')
                    tmp.replace(CAM_SETTINGS)
                except OSError as e:
                    print('[CAM] Error guardando la posicion:',e,flush=True)
            if action=='ps5_layout':
                # Persist only the layout, not the toggle or any OBS credentials.
                try:
                    data={'x':response['ps5X'],'y':response['ps5Y'],'width':response['ps5Width']}
                    temp=PS5_SETTINGS.with_suffix('.tmp')
                    temp.write_text(json.dumps(data),encoding='utf-8')
                    temp.replace(PS5_SETTINGS)
                except OSError as e:
                    print('[PS5] No se pudo guardar la posicion:',e,flush=True)
            if action=='music_settings':save_music_meta()
            self.json(response)
        except (ValueError,json.JSONDecodeError,UnicodeError,binascii.Error) as error:
            self.json({'error':str(error)},400)

def main():
    parser=argparse.ArgumentParser(description='ItsOcho OBS Timeline · Panel v5.14')
    parser.add_argument('--no-browser',action='store_true',help='No abrir navegador (pruebas)')
    args=parser.parse_args()
    try:
        server=ThreadingHTTPServer((HOST,PORT),Handler)
    except OSError as error:
        print(f'[ERROR] No se pudo iniciar el servidor en el puerto {PORT}: {error}', flush=True)
        try:
            with urllib.request.urlopen(f'http://{HOST}:{PORT}/api/state', timeout=1) as response:
                state = json.load(response)
            if all(k in state for k in ('index', 'camera', 'timeline')):
                print('[INFO] Ya hay un panel ItsOcho funcionando en este ordenador.', flush=True)
                print(f'Abre http://{HOST}:{PORT}/panel', flush=True)
                if not args.no_browser:
                    webbrowser.open(f'http://{HOST}:{PORT}/panel')
            else:
                print('[ERROR] Otro programa está usando el puerto. Ciérralo antes de reiniciar el panel.', flush=True)
        except Exception:
            print('[ERROR] Otro programa puede estar usando ese puerto. Cierra el otro proceso y vuelve a intentarlo.', flush=True)
        return 12
    print('\n'+'='*60)
    print(' ITSOCHO · TIMELINE v5.12 · COLA Y MARCA')
    print('='*60)
    print(' Panel:  http://127.0.0.1:8767/panel')
    print(' OBS:    http://127.0.0.1:8767/overlay')
    print(' MÚSICA: http://127.0.0.1:8767/music (fuente Navegador AUDIO)')
    print(' Las consultas de OBS y logos quedan silenciosas; errores y acciones visibles.')
    print(' Deja esta ventana abierta mientras transmites.')
    print(' Para cerrar el panel: Ctrl+C o cerrar esta ventana.')
    print('='*60+'\n')
    # Public-safe default: no automatic requests to download missing logos.
    # Users can still request downloads explicitly from the panel.
    if os.environ.get('ITSOCHO_AUTO_DOWNLOAD_LOGOS') == '1':
        start_logo_download()
    if not args.no_browser:
        threading.Thread(target=lambda:(time.sleep(.6),webbrowser.open('http://127.0.0.1:8767/panel')),daemon=True).start()
    try:
        server.serve_forever(poll_interval=.25)
    except KeyboardInterrupt:
        print('\nPanel detenido por el usuario.', flush=True)
    except Exception:
        details = traceback.format_exc()
        print('[ERROR] El servidor se detuvo inesperadamente:', details, flush=True)
        try:
            (HERE/'ultimo_error.txt').write_text(details, encoding='utf-8')
            print('Se guardó una copia del error en ultimo_error.txt', flush=True)
        except OSError:
            pass
        return 13
    finally:
        server.server_close()
    return 0

if __name__=='__main__': raise SystemExit(main())
