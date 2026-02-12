from datetime import datetime, timezone
from flask import Blueprint, render_template, current_app, session, redirect, url_for, request, flash, abort
from app.decorators import login_required, admin_required
import os
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename

# Configuración de subida (asegúrate de crear la carpeta static/uploads/screenshots)
UPLOAD_FOLDER = 'app/static/uploads/screenshots'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/panel')
@login_required  # 1. Primero debe estar logueado
@admin_required  # 2. Segundo, debe ser administrador
def panel():
    # Doble verificación de seguridad
    if not session.get('is_admin'):
        return redirect(url_for('main.dashboard'))

    return render_template('admin/panel.html')

@admin_bp.route('/delete_screenshot/<id>', methods=['POST'])
@login_required
def delete_screenshot(id):
    if session.get('is_admin'):
        screen = current_app.db.site_content.find_one_and_delete({'_id': ObjectId(id)})
        if screen:
            # Eliminar archivo físico
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, screen['url']))
            except:
                pass
            flash('Imagen eliminada.', 'info')
    return redirect(url_for('admin.manage_screenshots'))


# 1. RUTA PARA LISTAR USUARIOS
@admin_bp.route('/users')
@login_required
def manage_users():
    if not session.get('is_admin'):
        return redirect(url_for('main.dashboard'))

    # Traemos todos los usuarios (excluyendo la contraseña por seguridad)
    users = list(current_app.db.users.find({}, {'password': 0}).sort('created_at', -1))

    return render_template('admin/manage_users.html', users=users)


# 2. RUTA PARA ELIMINAR USUARIO
@admin_bp.route('/delete_user/<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('main.dashboard'))

    # PROTECCIÓN: Evitar que el admin se borre a sí mismo por error
    if user_id == session['user_id']:
        flash('No puedes eliminar tu propia cuenta de administrador desde aquí.', 'danger')
        return redirect(url_for('admin.manage_users'))

    # 1. Eliminar historial de pesos del usuario
    current_app.db.weight_entries.delete_many({'user_id': user_id})

    # 2. Eliminar al usuario
    current_app.db.users.delete_one({'_id': ObjectId(user_id)})

    flash('Usuario y sus datos eliminados correctamente.', 'success')
    return redirect(url_for('admin.manage_users'))


# Métricas

@admin_bp.route('/metrics')
@login_required
def platform_metrics():
    if not session.get('is_admin'):
        return redirect(url_for('main.dashboard'))

    # 1. Totales Generales
    total_users = current_app.db.users.count_documents({})
    total_entries = current_app.db.weight_entries.count_documents({})

    # 2. Cálculo de "Kilos Perdidos" (Igual que antes...)
    total_weight_lost = 0
    all_users = current_app.db.users.find({}, {'_id': 1})

    for u in all_users:
        history = list(current_app.db.weight_entries.find({'user_id': str(u['_id'])}).sort('recorded_date', 1))
        if len(history) > 1:
            start = history[0]['weight']
            current = history[-1]['weight']
            if start > current:
                total_weight_lost += (start - current)

    # 3. Datos para el Gráfico (CORREGIDO)
    pipeline = [
        # --- FILTRO DE SEGURIDAD NUEVO ---
        {
            "$match": {
                "created_at": {"$exists": True, "$ne": None, "$type": "date"}
            }
        },
        # ---------------------------------
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"}
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]

    monthly_stats = list(current_app.db.users.aggregate(pipeline))

    # Formatear para Chart.js
    labels = []
    data = []
    meses_nombres = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    for item in monthly_stats:
        # Protección extra por si acaso MongoDB deja pasar algo raro
        if item['_id']['month'] and item['_id']['year']:
            mes_num = item['_id']['month']
            year = item['_id']['year']
            labels.append(f"{meses_nombres[mes_num]} {year}")
            data.append(item['count'])

    return render_template('admin/platform_metrics.html',
                           total_users=total_users,
                           total_entries=total_entries,
                           total_weight_lost=round(total_weight_lost, 1),
                           chart_labels=labels,
                           chart_data=data)


# administración de imágen de fondo

@admin_bp.route('/manage_background', methods=['GET', 'POST'])
@login_required
def manage_background():
    if not session.get('is_admin'):
        return redirect(url_for('main.dashboard'))

    # Configuración de carpetas (Reutilizamos la carpeta de uploads)
    base_path = os.path.join(current_app.root_path, 'static', 'uploads', 'backgrounds')
    if not os.path.exists(base_path):
        os.makedirs(base_path, exist_ok=True)

    if request.method == 'POST':
        file = request.files.get('background_image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(base_path, filename))

            # 1. Desactivamos el fondo anterior (si quieres guardar historial)
            # O simplemente borramos el registro anterior para tener solo uno activo
            current_app.db.site_content.delete_many({'type': 'auth_background'})

            # 2. Guardamos el nuevo
            current_app.db.site_content.insert_one({
                'type': 'auth_background',
                'url': filename,
                'created_at': datetime.now(timezone.utc)
            })
            flash('Fondo de pantalla actualizado.', 'success')

    # Buscar la imagen actual
    current_bg = current_app.db.site_content.find_one({'type': 'auth_background'})

    return render_template('admin/manage_background.html', current_bg=current_bg)


# En app/admin/routes.py

@admin_bp.route('/manage_screenshots', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_screenshots():
    # 1. LÓGICA POST (Procesar subida o URL)
    if request.method == 'POST':
        description = request.form.get('description')
        external_url = request.form.get('external_url')
        filename = None

        # A) ¿Es URL Externa?
        if external_url and external_url.strip():
            filename = external_url.strip()

        # B) ¿Es Archivo Local?
        elif 'screenshot' in request.files:
            file = request.files['screenshot']
            if file.filename != '' and allowed_file(file.filename):
                safe_name = secure_filename(file.filename)
                # Timestamp para evitar duplicados
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"

                # Ruta absoluta segura
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'screenshots')
                os.makedirs(upload_folder, exist_ok=True)

                file.save(os.path.join(upload_folder, filename))
            else:
                flash('Archivo inválido o no permitido.', 'warning')
                return redirect(url_for('admin.manage_screenshots'))

        # C) Guardar en BD si tenemos un filename/url válido
        if filename:
            current_app.db.site_content.insert_one({
                'type': 'screenshot',
                'url': filename,
                'description': description,
                'created_at': datetime.now(timezone.utc)
            })
            flash('Imagen agregada exitosamente.', 'success')
        else:
            flash('Debes ingresar una URL o subir un archivo.', 'danger')

        return redirect(url_for('admin.manage_screenshots'))

    # 2. LÓGICA GET (Mostrar página)
    screenshots = list(current_app.db.site_content.find({'type': 'screenshot'}))
    return render_template('admin/manage_screenshots.html', screenshots=screenshots)