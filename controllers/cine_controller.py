from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from config.database import DatabaseConnection
from datetime import datetime

cine_bp = Blueprint('cine', __name__)

@cine_bp.route('/')
def inicio():
    return render_template('index.html')

@cine_bp.route('/pelicula/<int:id_pelicula>/funciones')
def seleccionar_funcion(id_pelicula):
    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: return "Error al conectar con la base de datos", 500
        
    try:
        cursor.execute("SELECT * FROM Pelicula WHERE idPelicula = %s", (id_pelicula,))
        pelicula = cursor.fetchone()
        if not pelicula:
            cursor.close()
            return redirect(url_for('cine.inicio'))

        cursor.execute("""
            SELECT idFuncion, fecha, hora, Sala_idSala, estado, COALESCE(idioma, 'Doblada') as idioma, COALESCE(formato, '2D') as formato
            FROM Funcion 
            WHERE Pelicula_idPelicula = %s AND LOWER(estado) = 'activa'
            ORDER BY fecha ASC, hora ASC
        """, (id_pelicula,))
        funciones = cursor.fetchall()

        funciones_agrupadas = {}
        for f in funciones:
            fecha_str = str(f['fecha'])
            
            # 🌟 Controlamos si la hora viene de MySQL como objeto timedelta o string puro
            if hasattr(f['hora'], 'total_seconds'):
                horas = f['hora'].seconds // 3600
                minutos = (f['hora'].seconds // 60) % 60
                hora_str = f"{horas:02d}:{minutos:02d}"
            else:
                hora_str = str(f['hora'])[:5]

            idioma_str = str(f['idioma'])
            
            try:
                dt = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_formateada = dt.strftime("%d de %B, %Y").upper()
            except Exception:
                fecha_formateada = fecha_str.upper()
                
            if fecha_formateada not in funciones_agrupadas:
                funciones_agrupadas[fecha_formateada] = {}
                
            if idioma_str not in funciones_agrupadas[fecha_formateada]:
                funciones_agrupadas[fecha_formateada][idioma_str] = []
                
            funciones_agrupadas[fecha_formateada][idioma_str].append({
                "idFuncion": f['idFuncion'],
                "hora": hora_str,
                "num_sala": f['Sala_idSala'],
                "formato": f['formato']
            })

        cursor.close()
        # 🌟 Arreglado el nombre de la variable para que coincida exactamente con lo que espera tu HTML 'seleccionar_funcion.html'
        return render_template('seleccionar_funcion.html', pelicula=pelicula, funciones_agrupadas=funciones_agrupadas)
                               
    except Exception as e:
        if cursor: cursor.close()
        print(f"❌ Error en seleccionar_funcion: {e}")
        return redirect(url_for('cine.inicio'))

@cine_bp.route('/reserva/funcion/<int:id_funcion>', methods=['GET'])
def seleccionar_butacas(id_funcion):
    if 'user_id' not in session and 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
        
    if 'user_id' in session and 'usuario_id' not in session:
        session['usuario_id'] = session['user_id']
    elif 'usuario_id' in session and 'user_id' not in session:
        session['user_id'] = session['usuario_id']

    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor: return "Error al conectar con la base de datos", 500

    try:
        query = """
            SELECT f.*, p.titulo, p.imagen_url 
            FROM Funcion f
            LEFT JOIN Pelicula p ON f.Pelicula_idPelicula = p.idPelicula
            WHERE f.idFuncion = %s
        """
        cursor.execute(query, (id_funcion,))
        funcion = cursor.fetchone()

        if not funcion:
            cursor.close()
            return redirect(url_for('cine.inicio'))

        if isinstance(funcion, dict):
            funcion['num_sala'] = funcion.get('Sala_idSala')
            if funcion.get('hora'):
                funcion['hora'] = str(funcion['hora'])[:5]
        
        cursor.close()
        return render_template('butacas.html', funcion=funcion)
    except Exception as e:
        if cursor: cursor.close()
        print(f"❌ Error en seleccionar_butacas: {e}")
        return redirect(url_for('cine.inicio'))

@cine_bp.route('/api/funciones/<int:id_funcion>/asientos_ocupados', methods=['GET'])
def asientos_ocupados(id_funcion):
    try:
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if not cursor: return jsonify([]), 500

        query = """
            SELECT a.fila, a.numero 
            FROM ReservaAsiento ra
            JOIN Reserva r ON ra.Reserva_idReserva = r.idReserva
            JOIN Asiento a ON ra.Asiento_idAsiento = a.idAsiento
            WHERE r.Funcion_idFuncion = %s
        """
        cursor.execute(query, (id_funcion,))
        asientos = cursor.fetchall()

        lista_ocupados = []
        for a in asientos:
            if isinstance(a, dict):
                lista_ocupados.append(f"{str(a['fila']).strip().upper()}{a['numero']}")
            else:
                lista_ocupados.append(f"{str(a[0]).strip().upper()}{a[1]}")

        cursor.close()
        return jsonify(lista_ocupados), 200
    except Exception as e:
        print(f"❌ Error en API asientos_ocupados: {e}")
        return jsonify([]), 500