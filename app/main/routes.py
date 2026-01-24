import pymongo
from flask import Blueprint, render_template, session, current_app, request, url_for, flash ,redirect
from app.decorators import login_required
from bson.objectid import ObjectId
from datetime import datetime, timezone
from app.auth.forms import ProfileForm
from werkzeug.security import check_password_hash, generate_password_hash
main_bp = Blueprint('main', __name__)


@main_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    user = current_app.db.users.find_one({'_id': ObjectId(user_id)})

    # 1. Traemos solo lo esencial de la base de datos
    total_entries = current_app.db.weight_entries.count_documents({'user_id': user_id})

    # Traemos 11 para la tabla y cálculos de variación
    cursor = current_app.db.weight_entries.find({'user_id': user_id}) \
        .sort('recorded_date', pymongo.DESCENDING) \
        .limit(11)
    fetched_entries = list(cursor)

    # Traemos el primer registro histórico de forma eficiente
    first_entry = current_app.db.weight_entries.find_one(
        {'user_id': user_id},
        sort=[('recorded_date', pymongo.ASCENDING)]
    )

    # 2. Definición de variables base (Evitamos errores si no hay datos)
    current_weight = fetched_entries[0]['weight'] if fetched_entries else 0
    start_weight = first_entry['weight'] if first_entry else current_weight

    profile = user.get('profile', {})
    weight_goal = profile.get('weight_goal')
    height_cm = profile.get('height')
    height_m = (float(height_cm) / 100) if height_cm else None

    # 3. Cálculo de Progreso y Metas
    progress_pct = 0
    kg_remaining = 0

    if weight_goal and start_weight != weight_goal:
        total_distance = abs(start_weight - weight_goal)
        distance_covered = abs(start_weight - current_weight)

        # Lógica para evitar progreso negativo si el usuario se aleja de la meta
        if (start_weight > weight_goal and current_weight > start_weight) or \
                (start_weight < weight_goal and current_weight < start_weight):
            progress_pct = 0
        else:
            progress_pct = round((distance_covered / total_distance) * 100)

        kg_remaining = round(abs(current_weight - weight_goal), 1)

    progress_pct = min(progress_pct, 100)
    total_change = round(current_weight - start_weight, 1)

    # 4. Procesamiento de la tabla (IMC y Variación)
    for i in range(len(fetched_entries)):
        entry = fetched_entries[i]
        # IMC
        if height_m:
            entry['imc'] = round(entry['weight'] / (height_m ** 2), 1)
        else:
            entry['imc'] = None
        # Variación
        if i < len(fetched_entries) - 1:
            entry['variation'] = round(entry['weight'] - fetched_entries[i + 1]['weight'], 1)
        else:
            entry['variation'] = None

    # 5. Datos para el Gráfico y la Vista
    current_bmi = None
    if current_weight and height_m:
        current_bmi = round(current_weight / (height_m ** 2), 1)

    chart_data = fetched_entries[::-1]
    dates_labels = [entry['recorded_date'].strftime('%d/%m') for entry in chart_data]
    weights_data = [entry['weight'] for entry in chart_data]

    # Recorte final para mostrar solo 10 en la tabla
    display_history = fetched_entries[:10]

    # Definimos los hitos de los logros
    logros = {
        'bronce': progress_pct >= 25,
        'plata': progress_pct >= 50,
        'oro': progress_pct >= 75,
        'campeon': progress_pct >= 100
    }

    return render_template('main/dashboard.html',
                           user=user,
                           current_weight=current_weight,
                           current_bmi=current_bmi,
                           weight_history=display_history,
                           total_entries=total_entries,
                           weight_goal=weight_goal,
                           progress_pct=progress_pct,
                           logros=logros,
                           start_weight=start_weight,
                           kg_remaining=kg_remaining,
                           total_change=total_change,
                           dates_labels=dates_labels,
                           weights_data=weights_data)




@main_bp.route('/')
def index():
    # Una página de inicio pública (Landing page)
    return render_template('main/index.html')


@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    users_collection = current_app.db.users
    user = users_collection.find_one({'_id': ObjectId(user_id)})

    form = ProfileForm()

    if form.validate_on_submit():
        # 1. VERIFICACIÓN DE SEGURIDAD: ¿Es correcta la contraseña actual?
        if not check_password_hash(user['password'], form.current_password.data):
            flash('La contraseña actual es incorrecta.', 'danger')
            return redirect(url_for('main.profile'))

        # 2. Preparar datos básicos de actualización
        update_data = {
            'name': form.name.data,
            'email': form.email.data,
            'profile.gender': form.gender.data,
            'profile.height': form.height.data,
            'profile.weight_goal': form.weight_goal.data
        }

        # 3. ¿El usuario quiere cambiar su contraseña?
        if form.new_password.data:
            update_data['password'] = generate_password_hash(form.new_password.data)

        # 4. Ejecutar actualización en MongoDB
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )

        # 5. Actualizar sesión por si cambió el nombre o email
        session['name'] = form.name.data
        session['email'] = form.email.data

        flash('Perfil y credenciales actualizados con éxito.', 'success')
        return redirect(url_for('main.profile'))

    # Carga inicial de datos
    if request.method == 'GET':
        form.name.data = user.get('name')
        form.email.data = user.get('email')
        profile_data = user.get('profile', {})
        form.gender.data = profile_data.get('gender', '')
        form.height.data = profile_data.get('height')
        form.weight_goal.data = profile_data.get('weight_goal')

    return render_template('main/profile.html', form=form)


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
