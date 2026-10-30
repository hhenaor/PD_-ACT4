# server.py

# Importar librerias
import aiohttp, json
from aiohttp import web
import bcrypt
import sqlite3

# Crear nombre de la sala
CHAT_ROOM_NAME = "Simple chat"
# Crear mensaje de bienvenida
CHAT_ROOM_WELCOME = "Welcome to this chat room, have fun!"
# Version esperado para conectarse
EXPECTED_VERSION = "1.0.0"
# String de validación
EXPECTED_VALIDATION = "bullet"

# inicio
async def hello(request: web.Request):
    return web.Response(text=f"Welcome to my \"{CHAT_ROOM_NAME}\" chat server.\nPlease set your client to connect at \"{request.url.origin()}\".")

# registro
async def register(request):
	data = await request.json()
	print(data)
	if data["USERNAME"] == "" and data["PASSWORD"] == "":
		return web.json_response({"ok": False, "msg": "Missing user data."})
	cur.execute("SELECT USER FROM users WHERE USER = ? LIMIT 1", (data["USERNAME"],))
	if cur.fetchone() is not None:
		return web.json_response({"ok": False, "msg": "User already exist."})

	hashed_pass = bcrypt.hashpw(data["PASSWORD"].encode(), bcrypt.gensalt())
	cur.execute("INSERT INTO users (USER, PASS) VALUES (?, ?)", (data["USERNAME"], hashed_pass))
	conn.commit()
	return web.json_response({"ok": True, "msg": "User created."})

# acceso
async def login(request):
	data = await request.json()
	print(data)
	if data["USERNAME"] == "" and data["PASSWORD"] == "":
		return web.json_response({"ok": False, "msg": "Missing login data."})
	cur.execute("SELECT * FROM users WHERE USER = ? LIMIT 1", (data["USERNAME"],))
	row = cur.fetchone()
	if row is None:
		return web.json_response({"ok": False, "msg": "User not found."})

	hashed_pass = bcrypt.hashpw(data["PASSWORD"].encode(), bcrypt.gensalt())
	if not bcrypt.checkpw(data["PASSWORD"].encode(), row[2]):
		return web.json_response({"ok": False, "msg": "Invalid credentials."})

	return web.json_response({"ok": True, "ID": row[0]})

# historial
def history():
	cur.execute("""SELECT u.USER, m.CONTENT FROM msgs m
	               JOIN users u ON u.ID = m.U_ID
	               ORDER BY m.ID DESC LIMIT 30""")
	return cur.fetchall()[::-1]

# broadcast
async def broadcast(payload):
	for c in clients:
		await c.send_json(payload)

# chat
async def chat(request):
	ws = web.WebSocketResponse()
	await ws.prepare(request)
	clients.add(ws)
	await ws.send_json({"type": "history", "msgs": [{"user": u, "content": c} for u, c in history()]})
	await broadcast({"type": "online", "count": len(clients)})
	try:
		async for msg in ws:
			if msg.type == aiohttp.WSMsgType.TEXT:
				data = json.loads(msg.data)
				cur.execute("INSERT INTO msgs (U_ID, CONTENT) VALUES (?, ?)", (data["U_ID"], data["CONTENT"]))
				conn.commit()
				cur.execute("SELECT USER FROM users WHERE ID = ?", (data["U_ID"],))
				await broadcast({"type": "msg", "user": cur.fetchone()[0], "content": data["CONTENT"]})
	finally:
		clients.discard(ws)
		await broadcast({"type": "online", "count": len(clients)})
	return ws

# validacion
async def validate_client(request):
	data = await request.json()
	if data["CLIENT_VERSION"] == EXPECTED_VERSION and data["CLIENT_VALIDATION"] == EXPECTED_VALIDATION:
		return web.json_response({"ok": True, "CHAT_ROOM_NAME": CHAT_ROOM_NAME, "CHAT_ROOM_WELCOME": CHAT_ROOM_WELCOME})
	else:
		return web.json_response({"ok": False, "EXPECTED_VERSION": EXPECTED_VERSION})

clients = set()

conn = sqlite3.connect("chat.db")
global cur
cur = conn.cursor()

print("Database connected successfully")

cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        ID INTEGER PRIMARY KEY,
        USER TEXT NOT NULL UNIQUE,
        PASS TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS msgs (
        ID INTEGER PRIMARY KEY,
        U_ID INTEGER NOT NULL,
        CONTENT TEXT NOT NULL,
        FOREIGN KEY (U_ID) REFERENCES users(ID)
    );
""")

app = web.Application()
app.add_routes([
    web.get("/", hello),
    web.post("/register", register),
    web.post("/login", login),
    web.post("/validate", validate_client),
    web.get("/chat", chat),
])

web.run_app(app, port=8000)
