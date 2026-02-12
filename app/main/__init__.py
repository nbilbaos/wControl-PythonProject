# app/main/__init__.py
from flask import Blueprint

main_bp = Blueprint('main', __name__)

from app.main import routes, api  # Importamos api también