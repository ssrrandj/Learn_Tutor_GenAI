import json, os, hashlib

Base_folder = "storage"
FILE = os.path.join(Base_folder, "users.json")

os.makedirs(Base_folder, exist_ok=True)

#FILE = f"{folder}/users.json"

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def load():
    if not os.path.exists(FILE):
        return {}
    return json.load(open(FILE))

def save(u):
    json.dump(u, open(FILE, "w"))

def signup(u, p):
    users = load()
    if u in users:
        return False
    users[u] = hash_password(p)
    save(users)
    return True

def login(u, p):
    return load().get(u) == hash_password(p)