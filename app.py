from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from controllers.auth_controller import AuthController
from models.funcion import Funcion
from werkzeug.utils import secure_filename
import os
import sys

app = Flask(__name__, 
            template_folder="views/templates", 
            static_folder="views/templates/static")

CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = os.getenv("SECRET_KEY", "tu_clave_secreta_aqui")

# CONFIGURACIÓN ABSOLUTA PARA SUBIDA DE IMÁGENES
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'views', 'templates', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Forzar la creación de la carpeta uploads si no existe en el disco duro
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def archivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------------------------------------------------------------
# VISTAS (PÁGINAS HTML)
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

@app.route('/admin/dashboard')
def admin_dashboard(): 
    return render_template('admin_dashboard.html')

@app.route('/admin/funciones/nueva')
def vista_nueva_funcion(): 
    return render_template('nueva_funcion.html')

# -------------------------------------------------------------------------
# API - AUTENTICACIÓN
# -------------------------------------------------------------------------
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    resultado, status_code = AuthController.registrar_usuario(
        data.get('nombre'), 
        data.get('apellido', 'Defecto'), 
        data.get('email'), 
        data.get('contrasenia')
    )
    return jsonify(resultado), status_code

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    resultado, status_code = AuthController.iniciar_sesion(data.get('email'), data.get('contrasenia'))
    return jsonify(resultado), status_code

# -------------------------------------------------------------------------
# API - GESTIÓN DE FUNCIONES Y PELÍCULAS
# -------------------------------------------------------------------------
@app.route('/api/funciones', methods=['GET'])
def listar_funciones():
    try:
        funciones = Funcion.buscar_todas()
        for f in funciones:
            if 'fecha' in f and f['fecha'] is not None: f['fecha'] = str(f['fecha'])
            if 'hora' in f and f['hora'] is not None: f['hora'] = str(f['hora'])
        return jsonify(funciones), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/funciones/detalle/<int:id_funcion>', methods=['GET'])
def obtener_detalle_funcion(id_funcion):
    try:
        from config.database import DatabaseConnection
        db = DatabaseConnection()
        cursor = db.get_cursor()
        cursor.execute("""
            SELECT f.idFuncion, f.fecha, f.hora, f.Sala_idSala,
                   p.idPelicula, p.titulo, p.genero, p.duracion, p.sinopsis, p.imagen_url
            FROM Funcion f
            JOIN Pelicula p ON f.Pelicula_idPelicula = p.idPelicula
            WHERE f.idFuncion = %s
        """, (id_funcion,))
        f = cursor.fetchone()
        if f:
            f['fecha'] = str(f['fecha'])
            f['hora'] = str(f['hora'])
            return jsonify(f), 200
        return jsonify({"error": "No encontrada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/funciones', methods=['POST'])
def crear_funcion():
    try:
        from config.database import DatabaseConnection
        db = DatabaseConnection()
        cursor = db.get_cursor()
        
        # Obtener campos desde el formulario multipart
        titulo = request.form.get('titulo')
        sinopsis = request.form.get('sinopsis')
        duracion = request.form.get('duracion')
        genero = request.form.get('genero')
        id_sala = request.form.get('idSala')
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')
        
        # Subida de archivo de imagen
        imagen_url = ""
        if 'imagen_file' in request.files:
            file = request.files['imagen_file']
            if file and archivo_permitido(file.filename):
                filename = secure_filename(file.filename)
                # Guardar el archivo físicamente en la carpeta del servidor
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Guardar la ruta web relativa para usar en los src del HTML
                imagen_url = f"/static/uploads/{filename}"
        
        # 1. Insertar Película
        cursor.execute("""
            INSERT INTO Pelicula (titulo, sinopsis, duracion, genero, imagen_url)
            VALUES (%s, %s, %s, %s, %s)
        """, (titulo, sinopsis, duracion, genero, imagen_url))
        db.commit()
        id_peli = cursor.lastrowid
        
        # 2. Insertar Función vinculada
        nueva_f = Funcion(fecha=fecha, hora=hora, estado='activa', id_pelicula=id_peli, id_sala=id_sala)
        if nueva_f.guardar():
            return jsonify({"mensaje": "Guardado exitosamente"}), 201
        return jsonify({"error": "Falló guardar función"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/funciones/<int:id_funcion>', methods=['PUT'])
def modificar_funcion(id_funcion):
    try:
        from config.database import DatabaseConnection
        db = DatabaseConnection()
        cursor = db.get_cursor()
        
        titulo = request.form.get('titulo')
        sinopsis = request.form.get('sinopsis')
        duracion = request.form.get('duracion')
        genero = request.form.get('genero')
        id_sala = request.form.get('idSala')
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')
        
        cursor.execute("SELECT Pelicula_idPelicula FROM Funcion WHERE idFuncion = %s", (id_funcion,))
        res = cursor.fetchone()
        if not res: 
            return jsonify({"error": "No encontrada"}), 404
        id_pelicula = res['Pelicula_idPelicula']

        # Si no se sube un archivo nuevo, se mantiene la imagen que ya estaba
        imagen_url = request.form.get('imagen_url_actual')
        if 'imagen_file' in request.files:
            file = request.files['imagen_file']
            if file and archivo_permitido(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                imagen_url = f"/static/uploads/{filename}"

        # Actualizar Película
        cursor.execute("""
            UPDATE Pelicula 
            SET titulo=%s, sinopsis=%s, duracion=%s, genero=%s, imagen_url=%s
            WHERE idPelicula=%s
        """, (titulo, sinopsis, duracion, genero, imagen_url, id_pelicula))

        # Actualizar Función
        cursor.execute("""
            UPDATE Funcion 
            SET fecha=%s, hora=%s, Sala_idSala=%s
            WHERE idFuncion=%s
        """, (fecha, hora, id_sala, id_funcion))
        
        db.commit()
        return jsonify({"mensaje": "Actualizado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/funciones/<int:id_funcion>', methods=['DELETE'])
def borrar_funcion(id_funcion):
    funcion_a_eliminar = Funcion(id_funcion=id_funcion)
    if funcion_a_eliminar.eliminar():
        return jsonify({"mensaje": "Eliminada con éxito"}), 200
    return jsonify({"error": "No se pudo borrar"}), 500

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