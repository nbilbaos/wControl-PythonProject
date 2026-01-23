import pymongo
from flask import Blueprint, render_template, session, current_app, request, url_for, flash ,redirect
from app.decorators import login_required
from bson.objectid import ObjectId
from datetime import datetime, timezone

main_bp = Blueprint('main', __name__)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']

    # 1. Obtener datos del usuario (Nombre, Altura, etc.)
    user = current_app.db.users.find_one({'_id': ObjectId(user_id)})

    # 2. Obtener el registro de peso MÁS RECIENTE
    # Buscamos en weight_entries, filtramos por usuario, ordenamos descendente por fecha y tomamos 1.
    latest_weight_entry = current_app.db.weight_entries.find_one(
        {'user_id': user_id},
        sort=[('recorded_date', pymongo.DESCENDING)]
    )

    # Si encontramos un registro, ese es el peso actual. Si no, es None.
    current_weight = latest_weight_entry['weight'] if latest_weight_entry else None

    return render_template('main/dashboard.html',
                           user=user,
                           current_weight=current_weight)

@main_bp.route('/')
def index():
    # Una página de inicio pública (Landing page)
    return render_template('main/index.html')

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    users_collection = current_app.db.users
    user_id = session['user_id']

    if request.method == 'POST':
        # Recolectar datos del formulario
        profile_data = {
            'gender': request.form.get('gender'),
            'age': request.form.get('age'),
            'height': request.form.get('height'),  # En cm
            'current_weight': request.form.get('weight'), # En kg
            'activity_level': request.form.get('activity_level'), # Sedentario, Activo, etc.
            'goal': request.form.get('goal') # Perder peso, mantener, ganar
        }

        # Actualizamos solo el campo 'profile' del usuario usando $set
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'profile': profile_data}}
        )

        flash('Información actualizada correctamente.', 'success')
        return redirect(url_for('main.profile'))

    # Método GET: Buscamos al usuario para pre-llenar el formulario
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    user_profile = user.get('profile', {})

    return render_template('main/profile.html', profile=user_profile)


@main_bp.route('/add_weight_entry', methods=['POST'])
@login_required
def add_weight_entry():
    user_id = session['user_id']
    weight = float(request.form.get('weight'))
    date_str = request.form.get('date')  # Viene como string "2026-01-22"

    # Convertimos la fecha del string a objeto datetime (para poder ordenar después)
    # Asumimos que la hora de ese día es las 00:00:00
    recorded_date = datetime.strptime(date_str, '%Y-%m-%d')

    entry_data = {
        'user_id': user_id,
        'weight': weight,
        'recorded_date': recorded_date,  # Fecha que eligió el usuario (para el gráfico)
        'created_at': datetime.now(timezone.utc)  # Fecha real de auditoría (cuándo hizo clic)
    }

    # 1. Guardamos en la colección de HISTORIAL
    current_app.db.weight_entries.insert_one(entry_data)

    # 2. Actualizamos el PESO ACTUAL en el perfil del usuario (Sincronización)
    # Así el dashboard siempre muestra el último dato ingresado
    current_app.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'profile.current_weight': weight}}
    )

    flash('Peso registrado exitosamente.', 'success')
    return redirect(url_for('main.dashboard'))