from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import requests  
from dotenv import load_dotenv
from config.database import DatabaseConnection  
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "views", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "views", "templates", "static")

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
# Clave estática para asegurar que las sesiones de Flask no se destruyan al reiniciar
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
    # Forzado de seguridad en backend para evitar accesos falsos
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
    
    if not email or not contrasenia:
        return jsonify({"error": "Faltan datos obligatorios."}), 400
        
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: 
        return jsonify({"error": "Base de datos desconectada."}), 500
        
    try:
        try:
            cursor.fetchall()
        except Exception:
            pass
            
        # Buscamos ignorando mayúsculas y minúsculas en la tabla de tu SQL
        cursor.execute("SELECT * FROM Usuario WHERE LOWER(email) = LOWER(%s)", (email,))
        usuario = cursor.fetchone()
        
        if usuario:
            db_pass = str(usuario.get('contrasenia', '')).strip()
            input_pass = str(contrasenia).strip()
            
            # BYPASS HARDCODEADO PARA TU ADMIN DE PRUEBAS
            if email.lower() == 'admin@cine.com' and input_pass == 'admin123':
                es_valida = True
            else:
                # Validación tradicional por Texto Plano o por Hash de Flask
                es_valida = (db_pass == input_pass)
                if not es_valida and db_pass.startswith(('scrypt:', 'pbkdf2:', 'bcrypt:')):
                    try:
                        es_valida = check_password_hash(db_pass, input_pass)
                    except Exception:
                        es_valida = False
                
            if es_valida:
                session['usuario_id'] = usuario.get('idUsuario')
                session['usuario_tipo'] = usuario.get('tipo', 'Cliente')
                session['usuario_nombre'] = usuario.get('nombre', 'Admin')
                
                return jsonify({
                    "status": "success",
                    "usuario": {
                        "idUsuario": usuario.get('idUsuario'),
                        "nombre": usuario.get('nombre'),
                        "tipo": usuario.get('tipo')
                    }
                }), 200
                
        return jsonify({"error": "El usuario o la contraseña son incorrectos."}), 401
    except Exception as e:
        return jsonify({"error": f"Error en la consulta: {str(e)}"}), 500


# ==========================================
#          RUTAS DE API PARA EL PANEL
# ==========================================

@app.route('/api/tmdb/buscar', methods=['GET'])
def api_buscar_tmdb():
    query = request.args.get('query', '')
    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "TU_API_KEY_ACA") # Reemplazar con tu clave real si usas .env
    if not query: 
        return jsonify([]), 200
        
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
                
                peliculas_filtradas.append({
                    "titulo": p.get('title', '').upper(),
                    "genero": genero,
                    "imagen_url": img
                })
            return jsonify(peliculas_filtradas), 200
    except Exception: 
        pass
    return jsonify([]), 200


@app.route('/api/funciones/lista', methods=['GET'])
def api_lista_funciones_db():
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if cursor:
        try:
            try: cursor.fetchall()
            except Exception: pass
            
            cursor.execute("SELECT * FROM Funcion ORDER BY idFuncion DESC")
            funciones = cursor.fetchall()
            if funciones:
                for f in funciones:
                    if 'hora' in f and f['hora'] is not None: f['hora'] = str(f['hora'])
                    if 'fecha' in f and f['fecha'] is not None: f['fecha'] = str(f['fecha'])
                return jsonify(funciones), 200
        except Exception as e:
            print(f"Error base de datos: {e}")
            
    return jsonify([]), 200


@app.route('/api/funciones/guardar', methods=['POST'])
def api_guardar_funcion():
    data = request.get_json() or {}
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: 
        return jsonify({"error": "Base de datos caída."}), 500
    
    try:
        # Consulta sanitizada y adaptada perfectamente a tu tabla 'Funcion'
        query = """INSERT INTO Funcion (titulo, genero, imagen_url, num_sala, fecha, hora, estado) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (
            data.get('titulo'), 
            data.get('genero'), 
            data.get('imagen_url'), 
            int(data.get('num_sala', 1)), 
            data.get('fecha'), 
            data.get('hora'), 
            data.get('estado', 'activa')
        ))
        db.commit()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)