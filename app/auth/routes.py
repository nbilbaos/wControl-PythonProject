from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from bson.objectid import ObjectId

# Definimos el Blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        gender = request.form.get('gender')

        # Manejo de campos opcionales vacíos
        height_val = request.form.get('height')
        weight_val = request.form.get('weight')

        users_collection = current_app.db.users

        if users_collection.find_one({'email': email}):
            flash('El correo ya está registrado.', 'danger')
            return redirect(url_for('auth.register'))

        # 1. Crear el documento del Usuario (SIN el peso)
        user_data = {
            'email': email,
            'password': generate_password_hash(password),
            'name': name,
            'is_admin': False,
            'created_at': datetime.now(timezone.utc),
            'profile': {
                'gender': gender,
                'height': height_val if height_val else None,
                # NOTA: Ya no guardamos current_weight aquí
            }
        }

        # Insertamos y obtenemos el ID del nuevo usuario
        result = users_collection.insert_one(user_data)
        new_user_id = str(result.inserted_id)

        # 2. Si el usuario ingresó peso, lo guardamos en la colección de HISTORIAL
        if weight_val:
            current_app.db.weight_entries.insert_one({
                'user_id': new_user_id,  # Vinculamos con el ID recién creado
                'weight': float(weight_val),
                'recorded_date': datetime.now(timezone.utc),  # Fecha registro = Fecha pesaje
                'created_at': datetime.now(timezone.utc)
            })

        flash('Registro exitoso.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        users_collection = current_app.db.users
        user = users_collection.find_one({'email': email})

        # 5. Verificación segura de la contraseña
        if user and check_password_hash(user['password'], password):
            # Guardamos datos esenciales en la sesión
            session.clear()
            session['user_id'] = str(user['_id'])
            session['email'] = user['email']
            session['is_admin'] = user.get('is_admin', False)

            flash(f'Bienvenido de nuevo, {email}', 'success')
            return redirect(url_for('main.dashboard'))  # ruta al dashboard de usuario

        flash('Correo o contraseña incorrectos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))