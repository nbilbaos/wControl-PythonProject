from pymongo import MongoClient
from werkzeug.security import generate_password_hash
import os

# Configuración manual rápida
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "wcontrol"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def create_admin_user(email, password):
    if db.users.find_one({'email': email}):
        print("El admin ya existe.")
        return

    hashed_pw = generate_password_hash(password)
    db.users.insert_one({
        'email': email,
        'password': hashed_pw,
        'is_admin': True # <--- Aquí te das el poder
    })
    print(f"Administrador {email} creado con éxito.")

if __name__ == "__main__":
    create_admin_user("admin@example.com", "Admin123!")