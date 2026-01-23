from flask import Blueprint, render_template, current_app
from app.decorators import login_required, admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/panel')
@login_required  # 1. Primero debe estar logueado
@admin_required  # 2. Segundo, debe ser administrador
def panel():
    # Ejemplo: Listar todos los usuarios registrados
    users_collection = current_app.db.users
    all_users = list(users_collection.find())

    return render_template('admin/panel.html', users=all_users)