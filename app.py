from flask import Flask
import os
from dotenv import load_dotenv

# Importamos los controladores (Blueprints)
from controllers.auth_controller import auth_bp
from controllers.cine_controller import cine_bp
from controllers.admin_controller import admin_bp
from controllers.pago_controller import pago_bp
from controllers.cliente_controller import cliente_bp   # ← NUEVO

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "views", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "views", "templates", "static")

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_session_key_cinema_12345")

# Registramos las rutas de la app
app.register_blueprint(auth_bp)
app.register_blueprint(cine_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(pago_bp)
app.register_blueprint(cliente_bp)   # ← NUEVO

if __name__ == '__main__':
    app.run(debug=True, port=5000)