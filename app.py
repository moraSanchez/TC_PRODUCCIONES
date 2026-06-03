from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from controllers.auth_controller import AuthController
import os

app = Flask(__name__, 
            template_folder="views/templates", 
            static_folder="views/templates/static")

CORS(app) 
app.secret_key = os.getenv("SECRET_KEY", "tu_clave_secreta_aqui")

# -------------------------------------------------------------------------
# VISTAS: Rutas para mostrar tus páginas HTML en el navegador
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
# API: Tus endpoints (Ahora devuelven estrictamente JSON para JS)
# -------------------------------------------------------------------------

@app.route('/api/auth/register', methods=['POST'])
def register():
    # Recibe el JSON plano enviado por el fetch de tu JavaScript
    data = request.get_json() or {}
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    email = data.get('email')
    contrasenia = data.get('contrasenia')
    
    if not all([nombre, apellido, email, contrasenia]):
        return jsonify({"error": "Faltan datos obligatorios"}), 400
        
    resultado, status_code = AuthController.registrar_usuario(nombre, apellido, email, contrasenia)
    
    # Devuelve solo el JSON. El JS del HTML se encarga del cartel y la redirección.
    return jsonify(resultado), status_code

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    contrasenia = data.get('contrasenia')
    
    if not email or not contrasenia:
        return jsonify({"error": "Faltan credenciales"}), 400
        
    resultado, status_code = AuthController.iniciar_sesion(email, contrasenia)
    return jsonify(resultado), status_code

if __name__ == '__main__':
    app.run(debug=True, port=5000)

    