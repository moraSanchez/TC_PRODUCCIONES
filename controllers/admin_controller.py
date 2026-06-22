from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import os
import requests
from datetime import datetime, timedelta
from config.database import DatabaseConnection

admin_bp = Blueprint('admin', __name__)

GENEROS_MAP = {
    28: "Acción", 878: "Ciencia ficción", 27: "Terror", 16: "Animación", 
    35: "Comedia", 12: "Aventura", 14: "Fantasía", 53: "Suspenso", 
    18: "Drama", 10749: "Romance"
}

@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    if session.get('usuario_tipo') != 'Administrador':
        return redirect(url_for('auth.login'))
    return render_template('admin_dashboard.html')

@admin_bp.route('/api/tmdb/buscar', methods=['GET'])
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

@admin_bp.route('/api/funciones/lista', methods=['GET'])
def api_lista_funciones_db():
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: return jsonify([]), 200
        
    try:
        try: cursor.fetchall()
        except Exception: pass
        
        cursor.execute("""
            SELECT idFuncion, titulo, genero, imagen_url, num_sala, fecha, hora, estado, Pelicula_idPelicula, COALESCE(idioma, 'Doblada') as idioma, COALESCE(formato, '2D') as formato
            FROM Funcion ORDER BY fecha ASC, hora ASC
        """)
        funciones = cursor.fetchall()
        
        if funciones:
            agrupadas = {}
            for f in funciones:
                f['hora'] = str(f['hora'])
                f['fecha'] = str(f['fecha'])
                key = f['Pelicula_idPelicula']
                if key not in agrupadas:
                    f['horarios_completos'] = [{"fecha": f['fecha'], "hora": f['hora'], "idFuncion": f['idFuncion']}]
                    agrupadas[key] = f
                else:
                    agrupadas[key]['horarios_completos'].append({
                        "fecha": f['fecha'], "hora": f['hora'], "idFuncion": f['idFuncion']
                    })
            return jsonify(list(agrupadas.values())), 200

        TMDB_API_KEY = os.getenv("TMDB_API_KEY", "TU_API_KEY_ACA")
        url_now_playing = f"https://api.themoviedb.org/3/movie/now_playing?api_key={TMDB_API_KEY}&language=es-MX&region=AR&page=1"
        url_upcoming = f"https://api.themoviedb.org/3/movie/upcoming?api_key={TMDB_API_KEY}&language=es-MX&region=AR&page=1"
        peliculas_a_guardar = []
        
        res_np = requests.get(url_now_playing, timeout=5)
        if res_np.status_code == 200:
            for index, peli in enumerate(res_np.json().get('results', [])[:5]):
                peliculas_a_guardar.append({"peli": peli, "estado": "activa", "fecha": datetime.today().strftime('%Y-%m-%d'), "index": index})
                
        res_up = requests.get(url_upcoming, timeout=5)
        if res_up.status_code == 200:
            for index, peli in enumerate(res_up.json().get('results', [])[:5]):
                fecha_estreno = (datetime.today().date() + timedelta(days=14)).strftime('%Y-%m-%d')
                peliculas_a_guardar.append({"peli": peli, "estado": "proximamente", "fecha": peli.get('release_date', fecha_estreno), "index": index})

        funciones_retorno = []
        for item in peliculas_a_guardar:
            peli = item["peli"]
            titulo = peli.get('title', '').upper()
            sinopsis = peli.get('overview', 'Sin sinopsis disponible.')
            poster = peli.get('poster_path')
            img_url = f"https://image.tmdb.org/t/p/w500{poster}" if poster else "https://placehold.co/400x600/141417/ffffff?text=Cine"
            genero = GENEROS_MAP.get(peli.get('genre_ids', [])[0], "Acción") if peli.get('genre_ids', []) else "Acción"
            
            cursor.execute("SELECT idPelicula FROM Pelicula WHERE UPPER(titulo) = UPPER(%s)", (titulo,))
            pelicula_existente = cursor.fetchone()
            if pelicula_existente:
                id_pelicula = pelicula_existente['idPelicula']
            else:
                cursor.execute("INSERT INTO Pelicula (titulo, sinopsis, duracion, genero, imagen_url) VALUES (%s, %s, %s, %s, %s)", (titulo, sinopsis, 120, genero, img_url))
                db.commit()
                id_pelicula = cursor.lastrowid
            
            num_sala = (item["index"] % 4) + 1
            hora = f"{16 + item['index']}:30:00"
            estado_final = item["estado"]
            fecha_final = item["fecha"]
            
            query_funcion = "INSERT INTO Funcion (titulo, genero, imagen_url, num_sala, fecha, hora, estado, Pelicula_idPelicula, idioma, formato) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query_funcion, (titulo, genero, img_url, num_sala, fecha_final, hora, estado_final, id_pelicula, "Doblada", "2D"))
            db.commit()
            
            funciones_retorno.append({
                "idFuncion": cursor.lastrowid, "titulo": titulo, "genero": genero, "imagen_url": img_url,
                "num_sala": num_sala, "fecha": str(fecha_final), "hora": str(hora),
                "estado": estado_final, "Pelicula_idPelicula": id_pelicula, "idioma": "Doblada", "formato": "2D"
            })
        return jsonify(funciones_retorno), 200
    except Exception as e: return jsonify([]), 200

@admin_bp.route('/api/funciones/guardar', methods=['POST'])
def api_guardar_funcion():
    data = request.get_json() or {}
    fechas_horarios = data.get('fechas_horarios', [])

    if not fechas_horarios: return jsonify({"error": "Debe proporcionar al menos un horario para la función."}), 400

    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: return jsonify({"error": "Conexión a la base de datos caída."}), 500
    
    try:
        cursor.execute("SELECT idPelicula FROM Pelicula WHERE UPPER(titulo) = UPPER(%s)", (data.get('titulo'),))
        pelicula_existente = cursor.fetchone()
        
        if pelicula_existente:
            id_pelicula = pelicula_existente['idPelicula']
        else:
            cursor.execute("INSERT INTO Pelicula (titulo, sinopsis, duracion, genero, imagen_url) VALUES (%s, %s, %s, %s, %s)", (data.get('titulo'), data.get('sinopsis', ''), 120, data.get('genero'), data.get('imagen_url')))
            db.commit()
            id_pelicula = cursor.lastrowid

        idioma_crudo = data.get('idioma', 'Doblada')
        idioma_final = "Subtitulada" if "sub" in idioma_crudo.lower() else "Doblada"

        query_funcion = "INSERT INTO Funcion (titulo, genero, imagen_url, num_sala, fecha, hora, estado, Pelicula_idPelicula, idioma, formato) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
         
        for item in fechas_horarios:
            cursor.execute(query_funcion, (data.get('titulo'), data.get('genero'), data.get('imagen_url'), int(data.get('num_sala', 1)), item['fecha'], item['hora'], data.get('estado', 'activa'), id_pelicula, idioma_final, item.get('formato', '2D')))
        db.commit()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/funciones/editar/<int:id_funcion>', methods=['PUT'])
def api_editar_funcion(id_funcion):
    data = request.get_json() or {}
    fechas_horarios = data.get('fechas_horarios', [])
    
    if not fechas_horarios: return jsonify({"error": "La función editada debe contener al menos un horario."}), 400
        
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: return jsonify({"error": "Conexión a la base de datos caída."}), 500
    
    try:
        cursor.execute("SELECT Pelicula_idPelicula FROM Funcion WHERE idFuncion = %s", (id_funcion,))
        funcion_actual = cursor.fetchone()
        if not funcion_actual: return jsonify({"error": "La función que intenta editar no existe."}), 404
             
        id_pelicula = funcion_actual['Pelicula_idPelicula']
        cursor.execute("UPDATE Pelicula SET titulo=%s, genero=%s, sinopsis=%s, duracion=%s, imagen_url=%s WHERE idPelicula=%s", (data.get('titulo'), data.get('genero'), data.get('sinopsis'), 120, data.get('imagen_url'), id_pelicula))
        cursor.execute("DELETE FROM Funcion WHERE Pelicula_idPelicula = %s", (id_pelicula,))
         
        idioma_crudo = data.get('idioma', 'Doblada')
        idioma_final = "Subtitulada" if "sub" in idioma_crudo.lower() else "Doblada"
        
        query_reinsertar = "INSERT INTO Funcion (titulo, genero, imagen_url, num_sala, fecha, hora, estado, Pelicula_idPelicula, idioma, formato) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                           
        for item in fechas_horarios:
            cursor.execute(query_reinsertar, (data.get('titulo'), data.get('genero'), data.get('imagen_url'), int(data.get('num_sala', 1)), item['fecha'], item['hora'], data.get('estado', 'activa'), id_pelicula, idioma_final, item.get('formato', '2D')))
        db.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@admin_bp.route('/api/funciones/eliminar/<int:id_funcion>', methods=['DELETE'])
def api_eliminar_funcion(id_funcion):
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: return jsonify({"error": "Base de datos caída."}), 500
    try:
        cursor.execute("SELECT Pelicula_idPelicula FROM Funcion WHERE idFuncion = %s", (id_funcion,))
        f = cursor.fetchone()
        if f: cursor.execute("DELETE FROM Funcion WHERE Pelicula_idPelicula = %s", (f['Pelicula_idPelicula'],))
        else: cursor.execute("DELETE FROM Funcion WHERE idFuncion = %s", (id_funcion,))
        db.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e: 
        db.rollback()
        return jsonify({"error": str(e)}), 500