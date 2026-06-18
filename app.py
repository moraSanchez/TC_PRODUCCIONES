from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import os
import requests  
from dotenv import load_dotenv
from config.database import DatabaseConnection
from werkzeug.security import check_password_hash, generate_password_hash

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# DETECTAR LA RUTA ABSOLUTA AUTOMÁTICAMENTE PARA EVITAR ERRORES DE RUTA EN WINDOWS
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "views", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "views", "templates", "static")

app = Flask(__name__, 
            template_folder=TEMPLATES_DIR, 
            static_folder=STATIC_DIR)

# Clave secreta para manejo de sesiones seguras
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_session_key_cinema")

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

@app.route('/admin/funciones')
def admin_panel():
    return render_template('admin_panel.html') 

@app.route('/admin/funciones/nueva')
def nueva_funcion():
    return render_template('nueva_funcion.html')


# ==========================================
#          RUTAS DE API (ASINCRÓNICAS)
# ==========================================

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email')
    contrasenia = data.get('contrasenia')
    
    if not email or not contrasenia:
        return jsonify({"error": "Faltan datos obligatorios."}), 400
        
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor:
        return jsonify({"error": "No hay conexión con la Base de Datos. Iniciá XAMPP."}), 500
        
    try:
        cursor.execute("SELECT * FROM Usuario WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        
        if usuario:
            # Soporte dual: hashes seguros de Flask y texto plano (para tus inserts de prueba)
            if usuario['contrasenia'].startswith('scrypt:') or usuario['contrasenia'].startswith('pbkdf2:'):
                es_valida = check_password_hash(usuario['contrasenia'], contrasenia)
            else:
                es_valida = (usuario['contrasenia'] == contrasenia)
                
            if es_valida:
                session['usuario_id'] = usuario['idUsuario']
                session['usuario_tipo'] = usuario['tipo']
                
                # RETORNO EXACTO: Con el formato 'result.usuario.xxx' que espera tu Javascript
                return jsonify({
                    "status": "success",
                    "usuario": {
                        "idUsuario": usuario['idUsuario'],
                        "nombre": usuario['nombre'],
                        "tipo": usuario['tipo']
                    }
                }), 200
                
        return jsonify({"error": "Correo o contraseña incorrectos."}), 401
    except Exception as e:
        return jsonify({"error": f"Error interno en el servidor: {str(e)}"}), 500


@app.route('/api/auth/register', methods=['POST'])
def api_registro():
    data = request.get_json() or {}
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    email = data.get('email')
    contrasenia = data.get('contrasenia')
    
    if not all([nombre, apellido, email, contrasenia]):
        return jsonify({"error": "Todos los campos son obligatorios."}), 400
        
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor:
        return jsonify({"error": "No hay conexión con la Base de Datos. Iniciá XAMPP."}), 500
        
    try:
        cursor.execute("SELECT idUsuario FROM Usuario WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "El correo electrónico ya se encuentra registrado."}), 400
            
        # Encriptamos la contraseña antes de guardarla
        hash_clave = generate_password_hash(contrasenia)
        
        query = "INSERT INTO Usuario (nombre, apellido, email, contrasenia, tipo) VALUES (%s, %s, %s, %s, 'Cliente')"
        cursor.execute(query, (nombre, apellido, email, hash_clave))
        db.commit()
        
        return jsonify({"status": "success", "message": "Usuario creado con éxito"}), 201
    except Exception as e:
        return jsonify({"error": f"Error al procesar el registro: {str(e)}"}), 500


@app.route('/api/funciones', methods=['GET'])
def api_obtener_funciones():
    """Retorna las funciones consumiendo datos EN VIVO de la API de TMDb filtradas por idioma."""
    try:
        TMDB_API_KEY = os.getenv("TMDB_API_KEY")
        
        if not TMDB_API_KEY or TMDB_API_KEY == "PEGA_AQUI_TU_CLAVE_DE_TMDB":
            return jsonify([]), 200
            
        url_tmdb = f"https://api.themoviedb.org/3/movie/now_playing?api_key={TMDB_API_KEY}&language=es-MX&page=1"
        response = requests.get(url_tmdb, timeout=5)
        
        if response.status_code == 200:
            datos_tmdb = response.json().get('results', [])
            funciones_formateadas = []
            
            generos_map = {
                28: "Acción",
                878: "Ciencia ficción",
                27: "Terror",
                16: "Animación",
                35: "Comedia"
            }
            
            for index, peli in enumerate(datos_tmdb):
                if len(funciones_formateadas) >= 12:
                    break
                    
                idioma_original = peli.get('original_language')
                if idioma_original not in ['es', 'en']:
                    continue  
                
                estado_peli = "activa" if index < 6 else "proximamente"
                
                genre_ids = peli.get('genre_ids', [])
                genero_texto = "Acción"  
                for g_id in genre_ids:
                    if g_id in generos_map:
                        genero_texto = generos_map[g_id]
                        break
                
                poster_path = peli.get('poster_path')
                imagen_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://placehold.co/400x600/141417/ffffff?text=Cine"
                
                funciones_formateadas.append({
                    "titulo": peli.get('title', 'Película de Estrenos').upper(),
                    "genero": genero_texto,
                    "num_sala": (index % 4) + 1,  
                    "hora": f"{15 + (index % 5)}:15:00",  
                    "fecha": peli.get('release_date', '2026-06-17'),
                    "estado": estado_peli,
                    "imagen_url": imagen_url
                })
                
            return jsonify(funciones_formateadas), 200
        else:
            return jsonify([]), 200

    except Exception as e:
        return jsonify([]), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)