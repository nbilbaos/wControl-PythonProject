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

    # 1. OPTIMIZACIÓN: Contar el total sin traer los documentos (muy rápido)
    total_entries = current_app.db.weight_entries.count_documents({'user_id': user_id})

    # 2. OPTIMIZACIÓN: Traer solo 16 documentos (15 para mostrar + 1 para calcular la variación del #15)
    # Esto asegura que la carga sea instantánea aunque haya 1 millón de registros.
    cursor = current_app.db.weight_entries.find({'user_id': user_id}) \
        .sort('recorded_date', pymongo.DESCENDING) \
        .limit(16)

    # Convertimos a lista solo estos 16 elementos
    fetched_entries = list(cursor)

    # 3. Procesamiento (Igual que antes, pero solo sobre la lista pequeña)
    profile = user.get('profile', {})
    height_cm = profile.get('height')
    height_m = (float(height_cm) / 100) if height_cm else None

    for i in range(len(fetched_entries)):
        entry = fetched_entries[i]

        # Cálculo de IMC (solo depende del propio registro)
        if height_m:
            entry['imc'] = round(entry['weight'] / (height_m ** 2), 1)
        else:
            entry['imc'] = None

        # Cálculo de Variación (necesita al vecino siguiente)
        # Si estamos en el índice 14 (el elemento 15), miramos el índice 15 (el elemento 16)
        if i < len(fetched_entries) - 1:
            prev_entry = fetched_entries[i + 1]
            entry['variation'] = round(entry['weight'] - prev_entry['weight'], 1)
        else:
            # Si estamos en el último elemento traído (sea el 16 o menos si hay pocos datos)
            # no podemos calcular variación hacia atrás.
            entry['variation'] = None

    # 4. Datos Finales para la Vista
    # El peso actual es el más reciente
    current_weight = fetched_entries[0]['weight'] if fetched_entries else None

    # IMC actual para la barra visual
    current_bmi = None
    if current_weight and height_m:
        current_bmi = round(current_weight / (height_m ** 2), 1)

    # 5. RECORTE FINAL: Enviamos solo los primeros 15 a la tabla
    # El elemento 16 (si existe) se usó solo para el cálculo y aquí se descarta visualmente.
    display_history = fetched_entries[:15]

    return render_template('main/dashboard.html',
                           user=user,
                           current_weight=current_weight,
                           current_bmi=current_bmi,
                           weight_history=display_history,  # Lista de máximo 15 items
                           total_entries=total_entries)  # Total real (ej: 100, 500) para el botón

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


# --- RUTA FALTANTE: HISTORIAL COMPLETO ---
@main_bp.route('/history')
@login_required
def full_history():
    user_id = session['user_id']
    user = current_app.db.users.find_one({'_id': ObjectId(user_id)})

    # 1. Traer TODO el historial sin límite
    full_history = list(current_app.db.weight_entries.find(
        {'user_id': user_id}
    ).sort('recorded_date', pymongo.DESCENDING))

    # 2. Cálculos (Variación e IMC) para la tabla completa
    profile = user.get('profile', {})
    height_cm = profile.get('height')
    height_m = (float(height_cm) / 100) if height_cm else None

    for i in range(len(full_history)):
        entry = full_history[i]

        # Variación
        if i < len(full_history) - 1:
            entry['variation'] = round(entry['weight'] - full_history[i + 1]['weight'], 1)
        else:
            entry['variation'] = None

        # IMC
        if height_m:
            entry['imc'] = round(entry['weight'] / (height_m ** 2), 1)
        else:
            entry['imc'] = None

    # 3. Renderizar la plantilla específica del historial
    return render_template('main/history.html', weight_history=full_history)
