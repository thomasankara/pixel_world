import socketio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse  # <--- AJOUT 1

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
socket_app = socketio.ASGIApp(sio, app)

world_state = []

# --- AJOUT 2 : La redirection automatique ---
@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

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
