from flask import Flask
from pymongo import MongoClient
from config import Config

from flask import Flask
from pymongo import MongoClient
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar conexión a MongoDB
    client = MongoClient(app.config['MONGO_URI'])
    app.db = client[app.config['MONGO_DB_NAME']]

    # Registrar Blueprints (Módulos)
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.main.routes import main_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)

    # Ruta raíz temporal para no ver un error 404 al inicio
    @app.route('/')
    def index():
        return "Bienvenido. Ve a <a href='/auth/login'>/auth/login</a> para entrar."

    return app