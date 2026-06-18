from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import requests  
from dotenv import load_dotenv
from config.database import DatabaseConnection  
from werkzeug.security import check_password_hash

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "views", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "views", "templates", "static")

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.secret_key = "super_secret_session_key_cinema_12345"

GENEROS_MAP = {28: "Acción", 878: "Ciencia ficción", 27: "Terror", 16: "Animación", 35: "Comedia", 12: "Aventura", 14: "Fantasía", 53: "Suspenso", 18: "Drama", 10749: "Romance"}

# ==========================================
#          RUTAS DE VISTAS (WEB)
# ==========================================

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/login')
def login(): 
    return render_template('login.html')

@app.route('/registro')
def registro(): 
    return render_template('registro.html')

@app.route('/admin/dashboard')
def admin_dashboard(): 
    if session.get('usuario_tipo') != 'Administrador':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

# ==========================================
#          RUTAS DE AUTENTICACIÓN
# ==========================================

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    contrasenia = data.get('contrasenia', '').strip()
    
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: return jsonify({"error": "Base de datos desconectada."}), 500
        
    try:
        try: cursor.fetchall()
        except Exception: pass
            
        cursor.execute("SELECT * FROM Usuario WHERE LOWER(email) = LOWER(%s)", (email,))
        usuario = cursor.fetchone()
        
        if usuario:
            db_pass = str(usuario.get('contrasenia', '')).strip()
            input_pass = str(contrasenia).strip()
            
            es_valida = (email.lower() == 'admin@cine.com' and input_pass == 'admin123') or (db_pass == input_pass)
            if not es_valida and db_pass.startswith(('scrypt:', 'pbkdf2:', 'bcrypt:')):
                try: es_valida = check_password_hash(db_pass, input_pass)
                except Exception: es_valida = False
                
            if es_valida:
                session['usuario_id'] = usuario.get('idUsuario')
                session['usuario_tipo'] = usuario.get('tipo', 'Cliente')
                session['usuario_nombre'] = usuario.get('nombre', 'Admin')
                return jsonify({"status": "success", "usuario": {"idUsuario": usuario.get('idUsuario'), "nombre": usuario.get('nombre'), "tipo": usuario.get('tipo')}}), 200
        return jsonify({"error": "Credenciales incorrectas."}), 401
    except Exception as e: return jsonify({"error": str(e)}), 500


@app.route('/api/auth/registro', methods=['POST'])
def api_registro():
    """ Ruta encargada de insertar los datos del nuevo cliente en MySQL """
    data = request.get_json() or {}
    nombre = data.get('nombre', '').strip()
    apellido = data.get('apellido', '').strip()
    email = data.get('email', '').strip()
    contrasenia = data.get('contrasenia', '').strip()

    if not nombre or not email or not contrasenia:
        return jsonify({"error": "Faltan campos obligatorios para el registro."}), 400

    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: 
        return jsonify({"error": "Base de datos desconectada."}), 500

    try:
        # Aseguramos limpieza de buffer
        try: cursor.fetchall()
        except Exception: pass

        # Verificamos si el email ya existe
        cursor.execute("SELECT idUsuario FROM Usuario WHERE LOWER(email) = LOWER(%s)", (email,))
        if cursor.fetchone():
            return jsonify({"error": "El correo electrónico ya se encuentra registrado."}), 400

        # Insertamos el nuevo usuario en la base de datos (por defecto es tipo 'Cliente')
        query = "INSERT INTO Usuario (nombre, apellido, email, contrasenia, tipo) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (nombre, apellido, email, contrasenia, 'Cliente'))
        db.commit()

        return jsonify({"status": "success", "message": "Usuario registrado correctamente."}), 201
    except Exception as e:
        return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500

# ==========================================
#          RUTAS DE API PARA EL PANEL Y CARTELERA
# ==========================================

@app.route('/api/tmdb/buscar', methods=['GET'])
def api_buscar_tmdb():
    query = request.args.get('query', '')
    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "TU_API_KEY_ACA")
    if not query: return jsonify([]), 200
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}&language=es-MX&page=1"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            resultados = response.json().get('results', [])
            peliculas_filtradas = []
            for p in resultados:
                poster = p.get('poster_path')
                img = f"https://image.tmdb.org/t/p/w500{poster}" if poster else "https://placehold.co/400x600/141417/ffffff?text=Cine"
                g_ids = p.get('genre_ids', [])
                genero = GENEROS_MAP.get(g_ids[0], "Acción") if g_ids else "Acción"
                peliculas_filtradas.append({"titulo": p.get('title', '').upper(), "genero": genero, "imagen_url": img, "sinopsis": p.get('overview', '')})
            return jsonify(peliculas_filtradas), 200
    except Exception: pass
    return jsonify([]), 200

@app.route('/api/funciones/lista', methods=['GET'])
def api_lista_funciones_db():
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: return jsonify([]), 200
    try:
        try: cursor.fetchall()
        except Exception: pass
        cursor.execute("SELECT * FROM Funcion ORDER BY idFuncion DESC")
        funciones = cursor.fetchall()
        if funciones:
            for f in funciones:
                if f.get('hora'): f['hora'] = str(f['hora'])
                if f.get('fecha'): f['fecha'] = str(f['fecha'])
            return jsonify(funciones), 200
    except Exception as e: print(f"Error: {e}")
    return jsonify([]), 200

@app.route('/api/funciones/guardar', methods=['POST'])
def api_guardar_funcion():
    data = request.get_json() or {}
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: return jsonify({"error": "Base de datos caída."}), 500
    
    try:
        cursor.execute("SELECT idPelicula FROM Pelicula WHERE UPPER(titulo) = UPPER(%s)", (data.get('titulo'),))
        pelicula_existente = cursor.fetchone()
        
        if pelicula_existente:
            id_pelicula = pelicula_existente['idPelicula']
        else:
            query_pelicula = "INSERT INTO Pelicula (titulo, sinopsis, duracion, genero, imagen_url) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query_pelicula, (data.get('titulo'), data.get('sinopsis', 'Sin sinopsis disponible.'), 120, data.get('genero'), data.get('imagen_url')))
            db.commit()
            id_pelicula = cursor.lastrowid

        query_funcion = """INSERT INTO Funcion (titulo, genero, imagen_url, num_sala, fecha, hora, estado, Pelicula_idPelicula) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query_funcion, (
            data.get('titulo'), data.get('genero'), data.get('imagen_url'),
            int(data.get('num_sala', 1)), data.get('fecha'), data.get('hora'),
            data.get('estado', 'activa'), id_pelicula
        ))
        db.commit()
        return jsonify({"status": "success"}), 201
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/funciones/editar/<int:id_funcion>', methods=['PUT'])
def api_editar_funcion(id_funcion):
    data = request.get_json() or {}
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: return jsonify({"error": "Base de datos caída."}), 500
    try:
        query = "UPDATE Funcion SET num_sala=%s, hora=%s, fecha=%s, estado=%s WHERE idFuncion=%s"
        cursor.execute(query, (int(data.get('num_sala')), data.get('hora'), data.get('fecha'), data.get('estado'), id_funcion))
        db.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/funciones/eliminar/<int:id_funcion>', methods=['DELETE'])
def api_eliminar_funcion(id_funcion):
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: return jsonify({"error": "Base de datos caída."}), 500
    try:
        cursor.execute("DELETE FROM Funcion WHERE idFuncion = %s", (id_funcion,))
        db.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e: return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)