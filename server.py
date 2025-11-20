import socketio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import json
import asyncio
import time
from collections import Counter

# --- CONFIGURATION DU SERVEUR ---
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()

# Montage des fichiers statiques (HTML/CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
socket_app = socketio.ASGIApp(sio, app)

# --- DONNÉES GLOBALES ---
SAVE_FILE = "world_data.json"
world_state = []        # Liste des pixels {'x', 'y', 'color'}
connected_sids = set()  # Liste des joueurs connectés
action_timestamps = []  # Historique des clics pour le calcul du RPM

# --- FONCTIONS DE SAUVEGARDE (PERSISTANCE) ---

def load_world():
    """Charge le monde depuis le fichier JSON au démarrage."""
    global world_state
    try:
        with open(SAVE_FILE, 'r') as f:
            world_state = json.load(f)
            print(f"✅ Monde chargé : {len(world_state)} pixels récupérés.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Pas de sauvegarde trouvée ou fichier corrompu. Démarrage d'un monde vide.")
        world_state = []

def save_world():
    """Écrit l'état actuel du monde dans le fichier JSON."""
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(world_state, f)
            print(f"💾 Sauvegarde effectuée ({len(world_state)} pixels).")
    except Exception as e:
        print(f"❌ Erreur de sauvegarde : {e}")

# --- TÂCHES DE FOND (BACKGROUND TASKS) ---

async def periodic_save():
    """Sauvegarde le monde toutes les 60 secondes."""
    while True:
        await asyncio.sleep(60)
        save_world()

async def broadcast_stats():
    """Calcule et envoie les statistiques Admin toutes les 2 secondes."""
    global action_timestamps
    while True:
        await asyncio.sleep(2)
        
        # 1. Nettoyer les vieux clics (> 60 secondes)
        now = time.time()
        action_timestamps = [t for t in action_timestamps if now - t <= 60]
        
        # 2. Calculer les tops couleurs
        colors = [p['color'] for p in world_state]
        if colors:
            top_colors = dict(Counter(colors).most_common(5))
        else:
            top_colors = {}

        # 3. Préparer le paquet de stats
        stats = {
            'users_count': len(connected_sids),
            'total_pixels': len(world_state),
            'actions_last_60s': len(action_timestamps),
            'top_colors': top_colors
        }
        
        # 4. Envoyer à tout le monde (Idéalement, à sécuriser plus tard)
        await sio.emit('stats_update', stats)

# --- ÉVÉNEMENT DE DÉMARRAGE ---

@app.on_event("startup")
async def startup_event():
    print("🚀 Démarrage du serveur...")
    load_world()
    # Lancer les boucles infinies en arrière-plan
    asyncio.create_task(periodic_save())
    asyncio.create_task(broadcast_stats())

# --- ROUTES WEB ---

@app.get("/")
async def root():
    """Redirige automatiquement vers le jeu."""
    return RedirectResponse(url="/static/index.html")

# --- ÉVÉNEMENTS WEBSOCKET (SOCKET.IO) ---

@sio.event
async def connect(sid, environ):
    print(f"Joueur connecté : {sid}")
    connected_sids.add(sid)
    # Envoyer la carte actuelle au nouveau joueur
    await sio.emit('init_world', world_state, to=sid)

@sio.event
async def disconnect(sid):
    print(f"Joueur déconnecté : {sid}")
    if sid in connected_sids:
        connected_sids.remove(sid)

@sio.event
async def place_circle(sid, data):
    # data = {'x': 123, 'y': 456, 'color': '#ff0000'}
    
    # 1. Mettre à jour la mémoire
    world_state.append(data)
    
    # 2. Enregistrer l'activité pour les stats
    action_timestamps.append(time.time())
    
    # 3. Diffuser le nouveau pixel à TOUS les joueurs
    await sio.emit('new_circle', data)

@sio.event
async def ping(sid):
    """Répond au ping du client pour calculer la latence."""
    await sio.emit('pong', to=sid)
