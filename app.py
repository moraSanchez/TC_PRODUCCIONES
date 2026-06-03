from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from controllers.auth_controller import AuthController
import os

# 1. ACÁ SE DEFINE 'app' (Obligatorio que vaya primero)
app = Flask(__name__, 
            template_folder="views/templates", 
            static_folder="views/templates/static")

CORS(app) 
app.secret_key = os.getenv("SECRET_KEY", "tu_clave_secreta_aqui")

# -------------------------------------------------------------------------
# 💻 VISTAS: Rutas para mostrar tus páginas HTML en el navegador
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
# 🔌 API: Tus endpoints para procesar los datos
# -------------------------------------------------------------------------

@app.route('/api/auth/register', methods=['POST'])
def register():
    if request.form:
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        contrasenia = request.form.get('contrasenia')
    else:
        data = request.get_json() or {}
        nombre = data.get('nombre')
        apellido = data.get('apellido')
        email = data.get('email')
        contrasenia = data.get('contrasenia')
    
    if not all([nombre, apellido, email, contrasenia]):
        return jsonify({"error": "Faltan datos obligatorios"}), 400
        
    resultado, status_code = AuthController.registrar_usuario(nombre, apellido, email, contrasenia)
    
    if request.form:
        if status_code == 201:
            return f"<h2>{resultado['mensaje']}</h2><a href='/login'>Ir al Login</a>"
        else:
            return f"<h2>Error: {resultado['error']}</h2><a href='/registro'>Volver a intentar</a>", status_code
            
    return jsonify(resultado), status_code

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'contrasenia' not in data:
        return jsonify({"error": "Faltan credenciales"}), 400
        
    resultado, status_code = AuthController.iniciar_sesion(data['email'], data['contrasenia'])
    return jsonify(resultado), status_code

if __name__ == '__main__':
    app.run(debug=True, port=5000)