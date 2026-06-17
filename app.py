from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from controllers.auth_controller import AuthController
import os
import sys

app = Flask(__name__, 
            template_folder="views/templates", 
            static_folder="views/templates/static")

# Habilitamos CORS para todas las rutas de forma masiva para evitar bloqueos del navegador
CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = os.getenv("SECRET_KEY", "tu_clave_secreta_aqui")

# -------------------------------------------------------------------------
# VISTAS
# -------------------------------------------------------------------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def vista_login():
    return render_template('login.html')

@app.route('/registro')
def vista_registro():
    return render_template('registro.html')

# -------------------------------------------------------------------------
# API (Maneja el registro tanto con /api/ como sin /api/ por las dudas)
# -------------------------------------------------------------------------

@app.route('/api/auth/register', methods=['POST'])
@app.route('/auth/register', methods=['POST']) # Doble ruta por si tu JS apunta acá
def register():
    # Detectamos si viene como JSON o como formulario tradicional de HTML
    data = request.get_json() or request.form or {}
    
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    email = data.get('email')
    contrasenia = data.get('contrasenia')
    
    # 💡 Truco de emergencia: Si tu formulario web no tiene apellido o email, 
    # le ponemos datos temporales para que MySQL no salte por el aire.
    if not apellido:
        apellido = "Defecto"
    if not email and nombre:
        email = f"{nombre.lower()}@test.com"

    # Verificamos los campos críticos indispensables
    if not nombre or not contrasenia:
        return jsonify({"error": "Faltan datos obligatorios (Nombre o Contraseña)"}), 400
        
    try:
        resultado, status_code = AuthController.registrar_usuario(nombre, apellido, email, contrasenia)
        return jsonify(resultado), status_code
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR EN EL BACKEND: {e}\n", file=sys.stderr)
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route('/api/auth/login', methods=['POST'])
@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json() or request.form or {}
    email = data.get('email')
    contrasenia = data.get('contrasenia')
    
    if not email or not contrasenia:
        return jsonify({"error": "Faltan credenciales"}), 400
        
    resultado, status_code = AuthController.iniciar_sesion(email, contrasenia)
    return jsonify(resultado), status_code

if __name__ == '__main__':
    # Forzamos a que corra en el puerto 5000 de forma limpia
    app.run(debug=True, port=5000)