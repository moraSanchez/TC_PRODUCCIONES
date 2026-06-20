import os
import requests
from flask import Blueprint, jsonify, request, render_template
from models.conexion import obtener_conexion 

cine_api = Blueprint('cine_api', __name__)

GENEROS_MAP = {
    28: "Acción", 12: "Aventura", 16: "Animación", 35: "Comedia", 
    27: "Terror", 878: "Ciencia ficción", 18: "Drama", 53: "Suspense",
    10749: "Romance", 9648: "Misterio", 14: "Fantasía"
}

# ==========================================
# RUTAS DE ADMINISTRACIÓN
# ==========================================

@cine_api.route('/api/funciones/lista', methods=['GET'])
def listar_funciones_admin():
    conexion = obtener_conexion()
    try:
        with conexion.cursor(dictionary=True) as cursor:
            # Hacemos un JOIN correcto trayendo los datos visuales desde la tabla Pelicula
            sql = """
                SELECT f.idFuncion, f.fecha, f.hora, f.estado,
                       p.titulo, p.genero, p.imagen_url,
                       f.Sala_idSala as num_sala, p.idPelicula
                FROM Funcion f
                LEFT JOIN Pelicula p ON f.Pelicula_idPelicula = p.idPelicula
                ORDER BY f.fecha ASC, f.hora ASC
            """
            cursor.execute(sql)
            resultados = cursor.fetchall()
            for r in resultados:
                if r['fecha']: r['fecha'] = str(r['fecha'])
                if r['hora']: r['hora'] = str(r['hora'])
            return jsonify(resultados)
    except Exception as e:
        print(f"Error en listar_funciones_admin: {e}")
        return jsonify([])
    finally:
        conexion.close()

@cine_api.route('/api/funciones/guardar', methods=['POST'])
def guardar_funcion():
    data = request.json
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # 1. Verificamos si la película ya existe o la creamos en la tabla Pelicula
            cursor.execute("SELECT idPelicula FROM Pelicula WHERE titulo = %s", (data['titulo'],))
            peli_existente = cursor.fetchone()
            
            if peli_existente:
                id_pelicula = peli_existente[0]
            else:
                sql_peli = "INSERT INTO Pelicula (titulo, sinopsis, genero, imagen_url, duracion) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql_peli, (data['titulo'], data.get('sinopsis', ''), data['genero'], data['imagen_url'], data.get('duracion', 120)))
                id_pelicula = cursor.lastrowid
            
            # 2. Capturamos el arreglo de múltiples horarios enviado por el frontend
            horarios = data.get('horarios_multiples', [])
            
            # Fallback por si la lista llega vacía
            if not horarios:
                horarios = [{'fecha': data['fecha'], 'hora': data['hora']}]
            
            # 3. SQL corregido basado EN TU BASE DE DATOS REAL (solo las columnas que existen)
            sql_funcion = """
                INSERT INTO Funcion (fecha, hora, estado, Pelicula_idPelicula, Sala_idSala)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            # Limpiamos el valor de num_sala para obtener el ID numérico de la sala
            num_sala_crudo = str(data.get('num_sala', '1'))
            num_sala_filtrado = ''.join(filter(str.isdigit, num_sala_crudo))
            id_sala_seleccionada = int(num_sala_filtrado) if num_sala_filtrado else 1
            
            # 4. Iteramos sobre cada horario guardándolo de forma limpia
            for h in horarios:
                cursor.execute(sql_funcion, (
                    h['fecha'], 
                    h['hora'], 
                    'activa', # El estado que espera el cliente
                    id_pelicula, 
                    id_sala_seleccionada
                ))
            
            conexion.commit()
            return jsonify({"mensaje": f"{len(horarios)} función(es) guardada(s) con éxito"}), 200
    except Exception as e:
        print(f"--- ERROR CRÍTICO EN GUARDAR_FUNCION ---: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conexion.close()

@cine_api.route('/api/funciones/editar/<int:id_funcion>', methods=['PUT'])
def editar_funcion(id_funcion):
    data = request.json
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                UPDATE Funcion 
                SET fecha = %s, hora = %s, Sala_idSala = %s
                WHERE idFuncion = %s
            """
            cursor.execute(sql, (data['fecha'], data['hora'], data['num_sala'], id_funcion))
            conexion.commit()
            return jsonify({"mensaje": "Horarios actualizados con éxito"}), 200
    except Exception as e:
        print(f"Error en editar_funcion: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conexion.close()

# ==========================================
# RUTAS DEL CLIENTE (VISTA DE COMPRA)
# ==========================================

@cine_api.route('/pelicula/<int:id_pelicula>/funciones', methods=['GET'])
def ver_funciones_pelicula(id_pelicula):
    """Renderiza la página web para ver horarios de una película"""
    return render_template('funciones_pelicula.html', id_pelicula=id_pelicula)

@cine_api.route('/api/funciones/pelicula/<int:id_pelicula>', methods=['GET'])
def obtener_horarios_pelicula(id_pelicula):
    """Devuelve los horarios activos de la película en formato JSON"""
    conexion = obtener_conexion()
    try:
        with conexion.cursor(dictionary=True) as cursor:
            # Traemos los datos dinámicamente juntando Funcion con Pelicula mediante el JOIN
            sql = """
                SELECT f.idFuncion, f.fecha, f.hora, f.estado, f.Sala_idSala as num_sala,
                       p.titulo, p.imagen_url, p.sinopsis, p.genero, p.duracion
                FROM Funcion f
                JOIN Pelicula p ON f.Pelicula_idPelicula = p.idPelicula
                WHERE f.Pelicula_idPelicula = %s
                ORDER BY f.fecha ASC, f.hora ASC
            """
            cursor.execute(sql, (id_pelicula,))
            resultados = cursor.fetchall()
            
            for r in resultados:
                if r['fecha']: r['fecha'] = str(r['fecha'])
                if r['hora']: r['hora'] = str(r['hora'])
                
            return jsonify(resultados)
    except Exception as e:
        print(f"Error en obtener_horarios_pelicula: {e}")
        return jsonify([])
    finally:
        conexion.close()