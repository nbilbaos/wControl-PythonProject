from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Por favor, inicia sesión para acceder.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificamos si es admin
        if not session.get('is_admin'):
            flash("Acceso denegado: Se requieren permisos de administrador.", "danger")
            # Redirigir al usuario a una página segura (su perfil o home)
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function