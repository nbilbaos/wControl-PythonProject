import os
import getpass
from app import create_app
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

# Inicializamos la app para tener acceso a la DB
app = create_app()


def create_admin_user():
    with app.app_context():
        db = app.db
        users = db.users

        # 1. Verificar si ya existe el admin
        # (Es buena práctica usar un email específico para admin o verificar por rol)
        admin_email = input("Ingresa el email del Administrador: ").strip()

        if users.find_one({'email': admin_email}):
            print(f"⚠️  El usuario {admin_email} ya existe. Abortando operación.")
            return

        # 2. Solicitar contraseña de forma segura (no se verá al escribir)
        print(f"Creando cuenta para: {admin_email}")
        while True:
            password = getpass.getpass("Ingresa la contraseña segura: ")
            confirm = getpass.getpass("Confirma la contraseña: ")

            if password == confirm and len(password) >= 8:
                break
            print("❌ Las contraseñas no coinciden o son muy cortas (min 8 caracteres). Intenta de nuevo.")

        # 3. Crear el usuario
        admin_user = {
            'name': 'Super Administrador',
            'email': admin_email,
            'password': generate_password_hash(password),  # ¡Siempre hasheada!
            'is_admin': True,
            'created_at': datetime.now(timezone.utc)
        }

        users.insert_one(admin_user)
        print(f"✅ ¡Éxito! Usuario administrador {admin_email} creado correctamente.")


if __name__ == '__main__':
    create_admin_user()