import socketio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
<<<<<<< HEAD
from fastapi.responses import RedirectResponse  # <--- AJOUT 1

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
socket_app = socketio.ASGIApp(sio, app)

world_state = []

# --- AJOUT 2 : La redirection automatique ---
=======
from fastapi.responses import RedirectResponse
import time
import asyncio
from collections import Counter

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
socket_app = socketio.ASGIApp(sio, app)

# --- DONNÉES ---
world_state = []
connected_sids = set() # Pour compter les utilisateurs uniques
action_timestamps = [] # Liste des temps des clics (pour le calcul "dernières 60s")

>>>>>>> 046f9bf (Initialisation du dépôt local et préparation a la synchronisation)
@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

<<<<<<< HEAD
@sio.event
async def connect(sid, environ):
    print(f"Joueur connecté : {sid}")
    await sio.emit('init_world', world_state, to=sid)

@sio.event
async def place_circle(sid, data):
    world_state.append(data)
    await sio.emit('new_circle', data)

@sio.event
async def disconnect(sid):
    print(f"Joueur déconnecté : {sid}")
=======
# --- GESTION DES TASCHES DE FOND (STATS) ---
async def broadcast_stats():
    """Calcule et envoie les stats toutes les 2 secondes"""
    global action_timestamps
    while True:
        await asyncio.sleep(2)
        
        # 1. Nettoyer les clics vieux de plus de 60 secondes
        now = time.time()
        action_timestamps = [t for t in action_timestamps if now - t <= 60]
        
        # 2. Analyser les couleurs
        colors = [c['color'] for c in world_state]
        color_counts = dict(Counter(colors).most_common(5)) # Top 5 couleurs
        
        # 3. Préparer le rapport
        stats = {
            'users_count': len(connected_sids),
            'total_pixels': len(world_state),
            'actions_last_60s': len(action_timestamps),
            'top_colors': color_counts
        }
        
        # 4. Envoyer aux admins (on diffuse à tout le monde pour l'instant)
        await sio.emit('stats_update', stats)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_stats())

# --- ÉVÉNEMENTS SOCKET.IO ---

@sio.event
async def connect(sid, environ):
    connected_sids.add(sid) # Ajouter l'ID du joueur
    await sio.emit('init_world', world_state, to=sid)

@sio.event
async def disconnect(sid):
    if sid in connected_sids:
        connected_sids.remove(sid)

@sio.event
async def place_circle(sid, data):
    world_state.append(data)
    action_timestamps.append(time.time()) # On note l'heure du clic
    await sio.emit('new_circle', data)

# --- PING / PONG pour la latence ---
@sio.event
async def ping(sid):
    # Le client dit "ping", on répond "pong"
    await sio.emit('pong', to=sid)
>>>>>>> 046f9bf (Initialisation du dépôt local et préparation a la synchronisation)
