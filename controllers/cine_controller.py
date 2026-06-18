import os
import requests
from flask import Blueprint, jsonify
# Suponiendo que usás tu conexión a base de datos (reemplazar por tu lógica de BD)
from models.conexion import obtener_conexion 

cine_api = Blueprint('cine_api', __name__)

@cine_api.route('/api/funciones', methods=['GET'])
def obtener_funciones():
    conexion = obtener_conexion()
    funciones = []
    
    try:
        with conexion.cursor() as cursor:
            # 1. Consultamos si ya existen funciones cargadas en la BDD
            cursor.execute("SELECT titulo, genero, num_sala, hora, fecha, estado, imagen_url FROM funciones")
            resultados = cursor.fetchall()
            
            if resultados:
                # Si ya hay películas, las formateamos y las enviamos al frontend
                for r in resultados:
                    funciones.append({
                        "titulo": r[0], "genero": r[1], "num_sala": r[2],
                        "hora": str(r[3]), "fecha": str(r[4]), "estado": r[5], "imagen_url": r[6]
                    })
                return jsonify(funciones)
            
            # 2. Si la BDD está VACÍA, traemos datos reales desde la API de TMDB
            print("Base de datos vacía. Cargando películas iniciales desde la API...")
            api_key = os.getenv('TMDB_API_KEY', 'ACA_TU_API_KEY') # O tu API key hardcodeada si preferís
            url = f"https://api.themoviedb.org/3/movie/now_playing?api_key={api_key}&language=es-AR&page=1"
            
            response = requests.get(url)
            if response.status_code == 200:
                datos_tmdb = response.json().get('results', [])
                generos_map = {28: "Acción", 12: "Aventura", 16: "Animación", 35: "Comedia", 27: "Terror", 878: "Ciencia ficción"}
                
                # Vamos a insertar y guardar las primeras 6 películas en tu MySQL
                for index, peli in enumerate(datos_tmdb[:6]):
                    titulo = peli.get('title')
                    genero_id = peli.get('genre_ids', [28])[0]
                    genero = generos_map.get(genero_id, "Drama")
                    num_sala = (index % 4) + 1
                    hora = f"{16 + index}:30:00"
                    fecha = "2026-06-18" if index < 4 else "2026-06-25"
                    estado = "activa" if index < 4 else "proximamente"
                    imagen_url = f"https://image.tmdb.org/t/p/w500{peli.get('poster_path')}"
                    
                    # Ejecutamos el INSERT para que queden guardadas para siempre de base
                    sql_insert = """
                        INSERT INTO funciones (titulo, genero, num_sala, hora, fecha, estado, imagen_url) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_insert, (titulo, genero, num_sala, hora, fecha, estado, imagen_url))
                    
                    # Las agregamos a la lista que le responderemos al frontend en este momento
                    funciones.append({
                        "titulo": titulo, "genero": genero, "num_sala": num_sala,
                        "hora": hora, "fecha": fecha, "estado": estado, "imagen_url": imagen_url
                    })
                
                # Confirmamos los cambios en MySQL
                conexion.commit()
                return jsonify(funciones)
                
            else:
                return jsonify([]) # Si la API de TMDB falla, devuelve vacío seguro
                
    except Exception as e:
        print(f"Error procesando la cartelera: {e}")
        return jsonify([])
    finally:
        conexion.close()