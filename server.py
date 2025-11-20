# Fichier: server.py
import socketio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Création du serveur
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()

# Gestion des fichiers statiques (HTML/JS/CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")
socket_app = socketio.ASGIApp(sio, app)

# -- État du monde (Mémoire vive) --
# On stocke juste une liste de points pour commencer
world_state = []

@sio.event
async def connect(sid, environ):
    print(f"Joueur connecté : {sid}")
    # On envoie l'état actuel au nouveau joueur uniquement
    await sio.emit('init_world', world_state, to=sid)

@sio.event
async def place_circle(sid, data):
    # data = {'x': int, 'y': int, 'color': str}
    print(f"Cercle placé : {data}")
    
    # 1. Sauvegarder
    world_state.append(data)
    
    # 2. Diffuser à TOUS les joueurs connectés
    await sio.emit('new_circle', data)

@sio.event
async def disconnect(sid):
    print(f"Joueur déconnecté : {sid}")