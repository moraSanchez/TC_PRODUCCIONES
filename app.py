from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from controllers.auth_controller import AuthController
from models.funcion import Funcion
import os
import sys

app = Flask(__name__, 
            template_folder="views/templates", 
            static_folder="views/templates/static")

# Habilitamos CORS masivo para evitar bloqueos del navegador
CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = os.getenv("SECRET_KEY", "tu_clave_secreta_aqui")

# -------------------------------------------------------------------------
# VISTAS - CLIENTES
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
# VISTAS - ADMINISTRADOR (Gestión de cartelera)
# -------------------------------------------------------------------------

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/funciones/nueva')
def vista_nueva_funcion():
    return render_template('nueva_funcion.html')

# -------------------------------------------------------------------------
# API - AUTENTICACIÓN Y ROLES
# -------------------------------------------------------------------------

@app.route('/api/auth/register', methods=['POST'])
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json() or request.form or {}
    nombre = data.get('nombre')
    apellido = data.get('apellido', 'Defecto')
    email = data.get('email')
    contrasenia = data.get('contrasenia')
    
    if not email and nombre:
        email = f"{nombre.lower()}@test.com"

    if not nombre or not contrasenia:
        return jsonify({"error": "Faltan datos obligatorios"}), 400
        
    try:
        resultado, status_code = AuthController.registrar_usuario(nombre, apellido, email, contrasenia)
        return jsonify(resultado), status_code
    except Exception as e:
        print(f"\n❌ ERROR EN REGISTRO: {e}\n", file=sys.stderr)
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

# -------------------------------------------------------------------------
# API - GESTIÓN DE FUNCIONES (AGREGAR, VER, EDITAR, BORRAR)
# -------------------------------------------------------------------------

@app.route('/api/funciones', methods=['GET'])
def listar_funciones():
    try:
        funciones = Funcion.buscar_todas()
        
        # BLINDAJE CRÍTICO: Convertimos objetos datetime/date/time a string para evitar caídas de JSON
        for f in funciones:
            if 'fecha' in f and f['fecha'] is not None:
                f['fecha'] = str(f['fecha'])
            if 'hora' in f and f['hora'] is not None:
                f['hora'] = str(f['hora'])
                
        return jsonify(funciones), 200
    except Exception as e:
        print(f"❌ Error en listar_funciones: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

@app.route('/api/funciones', methods=['POST'])
def crear_funcion():
    data = request.get_json() or {}
    fecha = data.get('fecha')
    hora = data.get('hora')
    id_pelicula = data.get('idPelicula')
    id_sala = data.get('idSala')
    
    if not all([fecha, hora, id_pelicula, id_sala]):
        return jsonify({"error": "Faltan datos obligatorios para programar la función"}), 400
        
    nueva_funcion = Funcion(fecha=fecha, hora=hora, id_pelicula=id_pelicula, id_sala=id_sala)
    if nueva_funcion.guardar():
        return jsonify({"mensaje": "Función programada con éxito"}), 201
    return jsonify({"error": "Error interno al guardar la función"}), 500

@app.route('/api/funciones/<int:id_funcion>', methods=['PUT'])
def modificar_funcion(id_funcion):
    data = request.get_json() or {}
    fecha = data.get('fecha')
    hora = data.get('hora')
    id_pelicula = data.get('idPelicula')
    id_sala = data.get('idSala')
    
    funcion_editada = Funcion(id_funcion=id_funcion, fecha=fecha, hora=hora, id_pelicula=id_pelicula, id_sala=id_sala)
    if funcion_editada.actualizar():
        return jsonify({"mensaje": "Función modificada con éxito"}), 200
    return jsonify({"error": "No se pudo actualizar la función"}), 500

@app.route('/api/funciones/<int:id_funcion>', methods=['DELETE'])
def borrar_funcion(id_funcion):
    funcion_a_eliminar = Funcion(id_funcion=id_funcion)
    if funcion_a_eliminar.eliminar():
        return jsonify({"mensaje": "Función eliminada con éxito"}), 200
    return jsonify({"error": "No se pudo borrar la función"}), 500

# Auxiliares para cargar catálogos del Admin
@app.route('/api/peliculas', methods=['GET'])
def listar_peliculas_aux():
    from config.database import DatabaseConnection
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if cursor:
        cursor.execute("SELECT idPelicula, titulo FROM Pelicula")
        return jsonify(cursor.fetchall()), 200
    return jsonify([]), 200

@app.route('/api/salas', methods=['GET'])
def listar_salas_aux():
    from config.database import DatabaseConnection
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if cursor:
        cursor.execute("SELECT idSala, numero, capacidad FROM Sala")
        return jsonify(cursor.fetchall()), 200
    return jsonify([]), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)