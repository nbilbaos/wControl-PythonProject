from datetime import datetime, timezone
from flask import Blueprint, render_template, current_app, session, redirect, url_for, request, flash
from app.decorators import login_required, admin_required
import os
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

    # Ejemplo: Listar todos los usuarios registrados
    users_collection = current_app.db.users
    all_users = list(users_collection.find())

    return render_template('admin/panel.html', users=all_users)

@admin_bp.route('/manage_screenshots', methods=['GET', 'POST'])
@login_required
def manage_screenshots():
    if not session.get('is_admin'):
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        file = request.files.get('screenshot')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # --- MEJORA: RUTA ABSOLUTA Y CREACIÓN AUTOMÁTICA ---

            # 1. Construimos la ruta absoluta usando la ubicación real de la app
            # Esto evita errores de "ruta no encontrada" en servidores Linux/Render
            base_path = os.path.join(current_app.root_path, 'static', 'uploads', 'screenshots')

            # 2. Verificamos si existe, y si no, la creamos (incluyendo subcarpetas)
            if not os.path.exists(base_path):
                os.makedirs(base_path, exist_ok=True)
                print(f"Directorio creado: {base_path}")  # Log para tu consola de Render

            # 3. Guardamos el archivo
            save_path = os.path.join(base_path, filename)
            file.save(save_path)

            # ---------------------------------------------------

            # Guardar referencia en MongoDB
            current_app.db.site_content.insert_one({
                'type': 'screenshot',
                'url': filename,
                'description': request.form.get('description'),
                'created_at': datetime.now(timezone.utc)
            })
            flash('Imagen subida con éxito.', 'success')

    screenshots = list(current_app.db.site_content.find({'type': 'screenshot'}))
    return render_template('admin/manage_screenshots.html', screenshots=screenshots)

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