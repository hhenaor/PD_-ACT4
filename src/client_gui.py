# client.py
import tkinter as tk
from tkinter import messagebox
import requests
import json, websocket
import threading, queue

USER_ID = None
ws = None
CHAT_CLIENT_NAME = "Simple Chat Client"
CLIENT_VERSION = "1.0.0"
CLIENT_VALIDATION = "bullet"
SERVER_URL = ""
# SERVER_URL = "http://0.0.0.0:8000" # Comment to disable
REQUEST_JSON = {}
RES = {}
INBOX = queue.Queue()
ONLINE = 0

def connectURL():
	REQUEST_JSON = {'CLIENT_VERSION': CLIENT_VERSION, 'CLIENT_VALIDATION': CLIENT_VALIDATION}
	SERVER_URL = SERVER_URL_TK.get()
	try:
		RES = (requests.post(f"{SERVER_URL}/validate", json=REQUEST_JSON)).json()

		if RES["ok"] == False:
			messagebox.showwarning("Error", f"Client and server missmatch!\n\nYour server and client have to run on the same version and have the same validation key.\n\nYour server expected, version {RES["EXPECTED_VERSION"]} and you're on {CLIENT_VERSION}.\n\nMaybe your client validation key was invalid?", parent=URLwindow)
			root.destroy()
		else:
			AUTH_LABEL_TK.set(f"Welcome to \"{RES["CHAT_ROOM_NAME"]}\" @ \"{SERVER_URL}\"")
			WELCOME_LABEL_TK.set(f"\"{RES["CHAT_ROOM_WELCOME"]}\"")
			URLwindow.withdraw()
			authWindow.deiconify()

	except:
		if SERVER_URL == "":
			messagebox.showwarning("Error", f"Type your server URL.", parent=URLwindow)
		else:
			messagebox.showwarning("Error", f"We couldn't connect to \"{SERVER_URL}\". Try again.", parent=URLwindow)

root = tk.Tk()
root.withdraw()

SERVER_URL_TK=tk.StringVar()

AUTH_LABEL_TK = tk.StringVar()
WELCOME_LABEL_TK = tk.StringVar()

USERNAME_TK=tk.StringVar()
PASSWORD_TK=tk.StringVar()

HEADER_TK = tk.StringVar()
MESSAGE_TK = tk.StringVar()

URLwindow = tk.Toplevel(root); URLwindow.withdraw()
authWindow = tk.Toplevel(root); authWindow.withdraw()
loginWindow = tk.Toplevel(root); loginWindow.withdraw()
signupWindow = tk.Toplevel(root); signupWindow.withdraw()
chatWindow = tk.Toplevel(root); chatWindow.withdraw()

URLwindow.title(CHAT_CLIENT_NAME)
URLwindow.resizable(False, False)
URLwindow.config(padx=20, pady=20)
URLwindow.protocol("WM_DELETE_WINDOW", root.destroy)

if SERVER_URL == "":
	URLwindow.deiconify()
	tk.Label(URLwindow, text="Please, set your server URL to connect").pack()
	tk.Entry(URLwindow,textvariable=SERVER_URL_TK, font=('calibre',10,'normal')).pack()
	tk.Button(URLwindow, text="Connect", command=connectURL).pack()
else:
	URLwindow.deiconify()
	tk.Label(URLwindow, text=f"A server URL was set on your client file, we're trying to connect...\n\nServer URL: \"{SERVER_URL}\"").pack()
	tk.Button(URLwindow, text="Quit", command=(root.destroy)).pack()
	SERVER_URL_TK.set(SERVER_URL)
	connectURL()

def show(win):
    for w in (authWindow, loginWindow, signupWindow, chatWindow):
        w.withdraw()
    win.deiconify()

def auth_setup(win):
    win.title(f"{CHAT_CLIENT_NAME} @ {SERVER_URL}")
    win.resizable(False, False)
    win.config(padx=20, pady=20)
    win.protocol("WM_DELETE_WINDOW", root.destroy)

def set_header():
	HEADER_TK.set(f"{ONLINE} on chat | {msg_count} messages")

def back_def():   show(authWindow)
def login_def():  show(loginWindow)
def signup_def(): show(signupWindow)
def chatroom():
	global ws
	ws = websocket.create_connection(SERVER_URL_TK.get().replace("http", "ws", 1) + "/chat")
	threading.Thread(target=listen, daemon=True).start()
	poll()
	set_header()
	show(chatWindow)

def signup_req():
	USERNAME = USERNAME_TK.get()
	PASSWORD = PASSWORD_TK.get()
	REQUEST_JSON = {'USERNAME': USERNAME, 'PASSWORD': PASSWORD}
	try:
		res = (requests.post(f"{SERVER_URL}/register", json=REQUEST_JSON)).json()

		if res["ok"] == False:
			messagebox.showwarning("Error", res["msg"], parent=signupWindow)
		else:
			messagebox.showinfo("Notice", res["msg"], parent=signupWindow)

	except:
			messagebox.showwarning("Error", f"We couldn't connect to \"{SERVER_URL}\". Try again.", parent=signupWindow)

def login_req():
	global USER_ID
	USERNAME = USERNAME_TK.get()
	PASSWORD = PASSWORD_TK.get()
	REQUEST_JSON = {'USERNAME': USERNAME, 'PASSWORD': PASSWORD}
	try:
		res = (requests.post(f"{SERVER_URL}/login", json=REQUEST_JSON)).json()

		if res["ok"] == False:
			messagebox.showwarning("Error", res["msg"], parent=signupWindow)
		else:
			USER_ID = res["ID"]
			chatroom()

	except Exception as e:
		print(repr(e))   # tipo + mensaje
		messagebox.showwarning("Error", f"{type(e).__name__}: {e}", parent=signupWindow)

# Auth
auth_setup(authWindow)
tk.Label(authWindow, textvariable=AUTH_LABEL_TK).pack()
tk.Label(authWindow, textvariable=WELCOME_LABEL_TK).pack()
tk.Button(authWindow, text="Login", command=login_def).pack()
tk.Button(authWindow, text="Sign up", command=signup_def).pack()

# Login
auth_setup(loginWindow)
tk.Label(loginWindow, text="Login").pack()
tk.Label(loginWindow, text="Username:").pack()
tk.Entry(loginWindow, textvariable=USERNAME_TK).pack()
tk.Label(loginWindow, text="Password:").pack()
tk.Entry(loginWindow, textvariable=PASSWORD_TK, show="*").pack()
tk.Label(loginWindow, text="Account recovery isn't availably yet.").pack()
tk.Button(loginWindow, text="Login", command=login_req).pack()
tk.Button(loginWindow, text="Back", command=back_def).pack()

# Signup
auth_setup(signupWindow)
tk.Label(signupWindow, text="Sign Up").pack()
tk.Label(signupWindow, text="Username:").pack()
tk.Entry(signupWindow, textvariable=USERNAME_TK).pack()
tk.Label(signupWindow, text="Password:").pack()
tk.Entry(signupWindow, textvariable=PASSWORD_TK, show="*").pack()
tk.Button(signupWindow, text="Sign up", command=signup_req).pack()
tk.Button(signupWindow, text="Back", command=back_def).pack()

# temporal
# USERNAME_TK.set("zynes")
# PASSWORD_TK.set("zynes")
# login_req()

# Chat
chatWindow.title(CHAT_CLIENT_NAME)
chatWindow.resizable(True, True)
chatWindow.config(padx=20, pady=20)
chatWindow.protocol("WM_DELETE_WINDOW", root.destroy)

msg_count = 0

def add_message(text):
	global msg_count
	chat_text.config(state="normal")   # se abre para escribir...
	chat_text.insert("end", text + "\n")
	chat_text.config(state="disabled") # ...y se vuelve a cerrar
	chat_text.see("end")
	msg_count += 1
	set_header()

def send_message(event=None):
	text = MESSAGE_TK.get().strip()
	if text == "":
		return
	ws.send(json.dumps({"U_ID": USER_ID, "CONTENT": text}))
	# add_message(text)
	MESSAGE_TK.set("")

def listen():
	while True:
		try:
			INBOX.put(json.loads(ws.recv()))
			print("listen")
		except Exception:
			INBOX.put({"type": "closed"})
			break

def poll():
	global ONLINE
	while not INBOX.empty():
		print("poll")
		data = INBOX.get()
		if data["type"] == "history":
			for m in data["msgs"]:
				add_message(f'{m["user"]}: {m["content"]}')
		elif data["type"] == "msg":
			add_message(f'{data["user"]}: {data["content"]}')
		elif data["type"] == "online":
			ONLINE = data["count"]
			set_header()
	root.after(100, poll)


tk.Label(chatWindow, textvariable=HEADER_TK, anchor="w").pack(fill="x")

# Centro: textbox seleccionable, no editable, con scroll
center = tk.Frame(chatWindow)
center.pack(fill="both", expand=True, pady=10)
scroll = tk.Scrollbar(center)
scroll.pack(side="right", fill="y")
chat_text = tk.Text(center, wrap="word", state="disabled", width=60, height=20, yscrollcommand=scroll.set)
chat_text.pack(side="left", fill="both", expand=True)
scroll.config(command=chat_text.yview)

# Abajo: input + botón
bottom = tk.Frame(chatWindow)
bottom.pack(fill="x")
entry = tk.Entry(bottom, textvariable=MESSAGE_TK)
entry.pack(side="left", fill="x", expand=True)
entry.bind("<Return>", send_message)
tk.Button(bottom, text="Send", command=send_message).pack(side="left", padx=(10, 0))

root.mainloop()