from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from app.auth.forms import RegistrationForm, LoginForm


# Definimos el Blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        # 1. Obtener datos limpios del formulario
        email = form.email.data
        name = form.name.data
        password = form.password.data
        gender = form.gender.data
        height = form.height.data
        weight = form.weight.data

        users_collection = current_app.db.users

        # 2. Verificar si el usuario ya existe
        if users_collection.find_one({'email': email}):
            flash('Este correo electrónico ya está registrado.', 'danger')
            return redirect(url_for('auth.register'))

        # 3. Hashear contraseña
        hashed_pw = generate_password_hash(password)

        # 4. Crear objeto de Usuario
        user_data = {
            'email': email,
            'password': hashed_pw,
            'name': name,
            'is_admin': False,
            'created_at': datetime.now(timezone.utc),
            'profile': {
                'gender': gender if gender else None,
                'height': height if height else None
                # NOTA: No guardamos el peso aquí para evitar duplicidad
            }
        }

        # 5. Insertar usuario en MongoDB
        result = users_collection.insert_one(user_data)
        new_user_id = str(result.inserted_id)

        # 6. Si ingresó un peso inicial, guardarlo en el HISTORIAL
        if weight:
            current_app.db.weight_entries.insert_one({
                'user_id': new_user_id,
                'weight': float(weight),
                'recorded_date': datetime.now(timezone.utc),  # Fecha del registro
                'created_at': datetime.now(timezone.utc),  # Fecha de auditoría
                # Calculamos el IMC inicial si hay altura, para que el registro esté completo
                'imc': round(float(weight) / ((height / 100) ** 2), 1) if height else None
            })

        flash('Cuenta creada exitosamente. Por favor, inicia sesión.', 'success')
        return redirect(url_for('auth.login'))

    # Si hay errores o es GET, renderizamos el template pasando el formulario
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 1. Instanciamos el formulario (Esto soluciona el error 'form undefined')
    form = LoginForm()

    # 3. Validación del Formulario
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        users_collection = current_app.db.users
        user = users_collection.find_one({'email': email})

        # 4. Verificación de credenciales
        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = str(user['_id'])
            session['email'] = user['email']
            # IMPORTANTE: Recuperamos el nombre para el menú superior
            session['name'] = user.get('name', 'Usuario')
            session['is_admin'] = user.get('is_admin', False)
            # Redirección inteligente: Si es admin va al panel, si no al dashboard
            if session['is_admin']:
                return redirect(url_for('admin.panel'))
            else:
                return redirect(url_for('main.dashboard'))

        flash('Correo o contraseña incorrectos.', 'danger')

    # 5. Renderizado (Ahora 'form' y 'background_url' existen y son correctos)
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))