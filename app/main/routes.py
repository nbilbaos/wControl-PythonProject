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
    user = current_app.db.users.find_one({'_id': ObjectId(user_id)})

    # Obtenemos historial ordenado
    weight_history = list(current_app.db.weight_entries.find(
        {'user_id': user_id}
    ).sort('recorded_date', pymongo.DESCENDING))

    # Obtenemos altura del perfil (en cm)
    profile = user.get('profile', {})
    height_cm = profile.get('height')

    # Preparamos la altura en metros para la fórmula (evitar división por cero)
    height_m = (float(height_cm) / 100) if height_cm else None

    # --- BUCLE ÚNICO: Calculamos Variación e IMC ---
    for i in range(len(weight_history)):
        entry = weight_history[i]  # Alias para escribir menos

        # 1. CÁLCULO DE VARIACIÓN (Lógica anterior)
        if i < len(weight_history) - 1:
            prev_entry = weight_history[i + 1]
            entry['variation'] = round(entry['weight'] - prev_entry['weight'], 1)
        else:
            entry['variation'] = None

        # 2. CÁLCULO DE IMC (Nueva lógica)
        if height_m:
            bmi = entry['weight'] / (height_m ** 2)
            entry['imc'] = round(bmi, 1)
        else:
            entry['imc'] = None  # Si no hay altura, no hay IMC

    current_weight = weight_history[0]['weight'] if weight_history else None

    # --- NUEVO: Calcular IMC actual para la barra visual ---
    current_bmi = None
    if current_weight and height_m:
        current_bmi = round(current_weight / (height_m ** 2), 1)

    return render_template('main/dashboard.html',
                           user=user,
                           current_weight=current_weight,
                           current_bmi=current_bmi,  # <--- Enviamos este dato nuevo
                           weight_history=weight_history)

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


# --- RUTA PARA EDITAR ---
@main_bp.route('/edit_weight/<entry_id>', methods=['POST'])
@login_required
def edit_weight(entry_id):
    # Recibimos los nuevos datos
    new_weight = float(request.form.get('weight'))
    new_date_str = request.form.get('date')
    new_date = datetime.strptime(new_date_str, '%Y-%m-%d')

    # Actualizamos en MongoDB
    current_app.db.weight_entries.update_one(
        {'_id': ObjectId(entry_id), 'user_id': session['user_id']},  # Seguridad: verificar que pertenezca al usuario
        {'$set': {
            'weight': new_weight,
            'recorded_date': new_date
        }}
    )

    flash('Registro actualizado correctamente.', 'success')
    return redirect(url_for('main.dashboard'))

# --- RUTA PARA ELIMINAR ---
@main_bp.route('/delete_weight/<entry_id>', methods=['POST'])
@login_required
def delete_weight(entry_id):
    current_app.db.weight_entries.delete_one(
        {'_id': ObjectId(entry_id), 'user_id': session['user_id']}
    )
    flash('Registro eliminado.', 'warning')
    return redirect(url_for('main.dashboard'))