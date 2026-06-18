# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import requests  
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# DETECTAR LA RUTA ABSOLUTA AUTOMÁTICAMENTE PARA EVITAR ERRORES DE RUTA EN WINDOWS
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "views", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "views", "templates", "static")

app = Flask(__name__, 
            template_folder=TEMPLATES_DIR, 
            static_folder=STATIC_DIR)

# Lee la clave secreta desde el archivo .env de forma segura
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_session_key_cinema")

# ==========================================
#          RUTAS DE VISTAS (WEB)
# ==========================================

@app.route('/')
def inicio():
    return render_template('index.html')  # Tu landing o cartelera pública

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

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email')
    contrasenia = data.get('contrasenia')
    
    if not email or not contrasenia:
        return jsonify({"error": "Faltan datos obligatorios."}), 400
        
    return jsonify({"status": "success"}), 200

@app.route('/api/funciones', methods=['GET'])
def api_obtener_funciones():
    """Retorna las funciones consumiendo datos EN VIVO de la API de TMDb filtradas por idioma."""
    try:
        # Extrae la API KEY desde tu archivo .env
        TMDB_API_KEY = os.getenv("TMDB_API_KEY")
        
        if not TMDB_API_KEY or TMDB_API_KEY == "PEGA_AQUI_TU_CLAVE_DE_TMDB":
            print("Error: No se configuró una TMDB_API_KEY válida en el archivo .env")
            return jsonify([]), 200
            
        # Consulta a TMDb pidiendo los datos localizados en español latino (es-MX)
        url_tmdb = f"https://api.themoviedb.org/3/movie/now_playing?api_key={TMDB_API_KEY}&language=es-MX&page=1"
        
        response = requests.get(url_tmdb, timeout=5)
        
        if response.status_code == 200:
            datos_tmdb = response.json().get('results', [])
            funciones_formateadas = []
            
            # Mapeo de IDs de géneros numéricos de TMDb a los textos que maneja tu frontend
            generos_map = {
                28: "Acción",
                878: "Ciencia ficción",
                27: "Terror",
                16: "Animación",
                35: "Comedia"
            }
            
            # Usamos enumerate para recuperar el 'index' idéntico a tu primer código estable
            for index, peli in enumerate(datos_tmdb):
                # Si ya metimos las 12 películas deseadas, cortamos el bucle
                if len(funciones_formateadas) >= 12:
                    break
                    
                idioma_original = peli.get('original_language')
                
                # FILTRO ESTRICTO: Descartar todo lo que no sea Español ('es') o Inglés ('en')
                if idioma_original not in ['es', 'en']:
                    continue  
                
                # REPARADO: Volvemos a usar 'index' para la distribución idéntica de estados y salas
                estado_peli = "activa" if index < 6 else "proximamente"
                
                # Mapear géneros válidos
                genre_ids = peli.get('genre_ids', [])
                genero_texto = "Acción"  
                for g_id in genre_ids:
                    if g_id in generos_map:
                        genero_texto = generos_map[g_id]
                        break
                
                # Construcción de la URL de la portada oficial desde los servidores CDN de TMDb
                poster_path = peli.get('poster_path')
                imagen_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://placehold.co/400x600/141417/ffffff?text=Cine"
                
                # REPARADO: Estructura exacta con cálculos basados en 'index' para que tu JS lo lea perfecto
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
            print(f"Error: TMDb respondió con código de estado HTTP {response.status_code}")
            return jsonify([]), 200

    except Exception as e:
        print(f"Error crítico al conectar con la API de TMDb: {e}")
        return jsonify([]), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)