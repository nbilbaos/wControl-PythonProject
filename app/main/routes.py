import pymongo
from flask import render_template, session, current_app, request, url_for, flash ,redirect
from app.decorators import login_required
from bson.objectid import ObjectId
from datetime import datetime, timezone, timedelta
from app.auth.forms import ProfileForm
from werkzeug.security import check_password_hash, generate_password_hash
from app.main import main_bp


@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Si es administrador, lo expulsamos del dashboard de usuarios y lo mandamos a su panel
    if session.get('is_admin'):
        return redirect(url_for('admin.panel'))

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
    new_achievement_unlocked = session.pop('new_achievement', None)

    return render_template('main/dashboard.html',
                           user=user,
                           current_weight=current_weight,
                           current_bmi=current_bmi,
                           weight_history=display_history,
                           total_entries=total_entries,
                           weight_goal=weight_goal,
                           progress_pct=progress_pct,
                           logros=logros,
                           new_achievement_unlocked=new_achievement_unlocked,  # <--- Variable Nueva
                           start_weight=start_weight,
                           kg_remaining=kg_remaining,
                           total_change=total_change,
                           dates_labels=dates_labels,
                           weights_data=weights_data)
#landig page
@main_bp.route('/')
def index():
    # Buscamos las capturas registradas por el admin
    screenshots = list(current_app.db.site_content.find({'type': 'screenshot'}).sort('created_at', -1))
    return render_template('main/index.html', screenshots=screenshots)


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
    date_str = request.form.get('date')
    recorded_date = datetime.strptime(date_str, '%Y-%m-%d')

    # 1. OBTENER DATOS ACTUALES (ANTES DE INSERTAR)
    user = current_app.db.users.find_one({'_id': ObjectId(user_id)})
    profile = user.get('profile', {})
    weight_goal = profile.get('weight_goal')

    # Buscamos historial previo para calcular progreso anterior
    history = list(current_app.db.weight_entries.find({'user_id': user_id}).sort('recorded_date', pymongo.DESCENDING))

    current_weight_old = history[0]['weight'] if history else weight  # Si es el primero, usame a mi mismo
    start_weight = history[-1]['weight'] if history else weight

    # --- FUNCIÓN HELPER PARA CALCULAR PROGRESO ---
    def calculate_progress(start, current, goal):
        if not goal or start == goal: return 0
        total_dist = abs(start - goal)
        covered_dist = abs(start - current)

        # Validación de dirección (si se aleja es 0)
        if (start > goal and current > start) or (start < goal and current < start):
            return 0

        return min(round((covered_dist / total_dist) * 100), 100)

    # 2. CALCULAR PORCENTAJE ANTES
    pct_before = calculate_progress(start_weight, current_weight_old, weight_goal)

    # 3. INSERTAR EL NUEVO PESO
    entry_data = {
        'user_id': user_id,
        'weight': weight,
        'recorded_date': recorded_date,
        'created_at': datetime.now(timezone.utc)
    }
    current_app.db.weight_entries.insert_one(entry_data)

    # Actualizar perfil (opcional, pero mantenemos tu lógica)
    current_app.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'profile.current_weight': weight}})

    # 4. CALCULAR PORCENTAJE DESPUÉS
    pct_after = calculate_progress(start_weight, weight, weight_goal)

    # 5. DETECTAR DESBLOQUEO (CRUCE DE UMBRALES)
    new_badge = None
    thresholds = {25: 'bronce', 50: 'plata', 75: 'oro', 100: 'campeon'}

    for limit, badge_name in thresholds.items():
        # Si antes estaba abajo del límite Y ahora estoy igual o arriba
        if pct_before < limit <= pct_after:
            new_badge = badge_name
            break  # Solo celebramos el logro más alto alcanzado

    # SI HAY LOGRO, LO GUARDAMOS EN LA SESIÓN PARA MOSTRARLO EN EL DASHBOARD
    if new_badge:
        session['new_achievement'] = new_badge

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

    # 2. REDIRECCIÓN INTELIGENTE
    # Buscamos si el formulario envió una señal de "next"
    next_page = request.form.get('next')

    if next_page == 'history':
        return redirect(url_for('main.full_history'))

    # Por defecto, si no hay señal, volvemos al dashboard
    return redirect(url_for('main.dashboard'))

# --- RUTA PARA ELIMINAR ---
@main_bp.route('/delete_weight/<entry_id>', methods=['POST'])
@login_required
def delete_weight(entry_id):
    current_app.db.weight_entries.delete_one(
        {'_id': ObjectId(entry_id), 'user_id': session['user_id']}
    )

    flash('Registro eliminado.', 'warning')

    # REDIRECCIÓN INTELIGENTE
    next_page = request.form.get('next') or request.args.get('next')

    if next_page == 'history':
        return redirect(url_for('main.full_history'))

    return redirect(url_for('main.dashboard'))


# --- HISTORIAL COMPLETO ---
@main_bp.route('/history')
@login_required
def full_history():
    user_id = session['user_id']
    user = current_app.db.users.find_one({'_id': ObjectId(user_id)})
    profile = user.get('profile', {})

    # 1. PARAMETROS DE FILTRO (Default: 3 meses)
    time_filter = request.args.get('filter', '3m')  # 3m, 6m, all, custom
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    query = {'user_id': user_id}

    # Lógica de fechas
    now = datetime.now()
    filter_label = "Últimos 3 Meses"  # Para el título del PDF

    if time_filter == '3m':
        query['recorded_date'] = {'$gte': now - timedelta(days=90)}
        filter_label = "Últimos 3 Meses"
    elif time_filter == '6m':
        query['recorded_date'] = {'$gte': now - timedelta(days=180)}
        filter_label = "Últimos 6 Meses"
    elif time_filter == 'custom' and start_date_str:
        try:
            s_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            e_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else now
            # Ajustamos el final del día para incluir el registro de ese día
            e_date = e_date.replace(hour=23, minute=59)
            query['recorded_date'] = {'$gte': s_date, '$lte': e_date}
            filter_label = f"Del {start_date_str} al {end_date_str}"
        except:
            pass  # Fallback a todo si hay error
    elif time_filter == 'all':
        filter_label = "Historial Completo"
        # No agregamos filtro de fecha

    # 2. CONSULTA (Ordenada Descendente: Nuevo -> Viejo)
    # Importante: Para calcular variaciones necesitamos el registro ANTERIOR al periodo seleccionado
    # pero para simplificar, calcularemos variaciones sobre lo visible.
    cursor = current_app.db.weight_entries.find(query).sort('recorded_date', pymongo.DESCENDING)
    history = list(cursor)

    # 3. ESTADÍSTICAS CLÍNICAS (Calculadas sobre los datos FILTRADOS)
    stats = {
        'current_weight': 0,
        'start_weight_period': 0,
        'total_change': 0,
        'avg_monthly_change': 0,
        'days_elapsed': 0,
        'bmi': 0,
        'height': profile.get('height', 0)
    }

    if history:
        stats['current_weight'] = history[0]['weight']  # El más reciente (index 0)
        stats['start_weight_period'] = history[-1]['weight']  # El más antiguo del periodo
        stats['total_change'] = round(stats['current_weight'] - stats['start_weight_period'], 1)

        # Calcular días entre el primer y último registro del periodo
        delta = history[0]['recorded_date'] - history[-1]['recorded_date']
        stats['days_elapsed'] = delta.days

        # Promedio Mensual (Aprox 30.44 días por mes)
        if stats['days_elapsed'] > 30:
            months = stats['days_elapsed'] / 30.44
            stats['avg_monthly_change'] = round(stats['total_change'] / months, 2)
        else:
            stats['avg_monthly_change'] = stats['total_change']  # Si es menos de un mes, es el cambio total

        # IMC Actual
        if stats['height']:
            h_m = float(stats['height']) / 100
            stats['bmi'] = round(stats['current_weight'] / (h_m ** 2), 1)

    # 4. PROCESAR TABLA (Variaciones fila a fila)
    for i in range(len(history)):
        entry = history[i]
        # IMC por registro
        if stats['height']:
            h_m = float(stats['height']) / 100
            entry['imc'] = round(entry['weight'] / (h_m ** 2), 1)

        # Variación respecto al registro anterior (que en la lista es i+1 porque está invertida)
        if i < len(history) - 1:
            entry['variation'] = round(entry['weight'] - history[i + 1]['weight'], 1)
        else:
            entry['variation'] = None

    return render_template('main/history.html',
                           weight_history=history,
                           stats=stats,
                           filter_label=filter_label,
                           current_filter=time_filter)

@main_bp.route('/privacidad')
def privacidad():
    return render_template('privacidad.html')