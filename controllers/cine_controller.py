from flask import Blueprint, render_template, request, session, redirect, url_for
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
    if not cursor:
        return "Error al conectar con la base de datos", 500
        
    try:
        try: cursor.fetchall()
        except Exception: pass

        cursor.execute("SELECT * FROM Pelicula WHERE idPelicula = %s", (id_pelicula,))
        pelicula = cursor.fetchone()
        if not pelicula:
            return redirect(url_for('cine.inicio'))

        cursor.execute("""
            SELECT idFuncion, fecha, hora, num_sala, estado, COALESCE(idioma, 'Doblada') as idioma, COALESCE(formato, '2D') as formato
            FROM Funcion 
            WHERE Pelicula_idPelicula = %s AND LOWER(estado) = 'activa'
            ORDER BY fecha ASC, hora ASC
        """, (id_pelicula,))
        funciones = cursor.fetchall()

        funciones_agrupadas = {}
        for f in funciones:
            fecha_str = str(f['fecha'])
            hora_str = str(f['hora'])
            idioma_str = str(f['idioma'])
            
            try:
                dt = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_formateada = dt.strftime("%d de %B, %Y").upper()
            except Exception:
                fecha_formateada = fecha_str
                
            if fecha_formateada not in funciones_agrupadas:
                funciones_agrupadas[fecha_formateada] = {}
                
            if idioma_str not in funciones_agrupadas[fecha_formateada]:
                funciones_agrupadas[fecha_formateada][idioma_str] = []
                
            funciones_agrupadas[fecha_formateada][idioma_str].append({
                "idFuncion": f['idFuncion'],
                "hora": hora_str,
                "num_sala": f['num_sala'],
                "formato": f['formato']
            })

        return render_template('seleccionar_funcion.html', pelicula=pelicula, funciones_agrupadas=funciones_agrupadas)
                               
    except Exception as e:
        print(f"Error en seleccionar_funcion: {e}")
        return redirect(url_for('cine.inicio'))

@cine_bp.route('/reserva/funcion/<int:id_funcion>', methods=['GET', 'POST'])
def seleccionar_butacas(id_funcion):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    db = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor:
        return "Error al conectar con la base de datos", 500

    if request.method == 'POST':
        asientos_elegidos = request.form.get('asientos')
        if asientos_elegidos:
            lista_asientos = asientos_elegidos.split(',')
            session['reserva_actual'] = {
                'id_funcion': id_funcion,
                'asientos': lista_asientos,
                'cantidad': len(lista_asientos),
                'precio_total': len(lista_asientos) * 4500.00
            }
            return redirect(url_for('cine.inicio'))

    try:
        try: cursor.fetchall()
        except Exception: pass

        query = """
            SELECT f.*, p.titulo, p.imagen_url 
            FROM Funcion f
            LEFT JOIN Pelicula p ON f.Pelicula_idPelicula = p.idPelicula
            WHERE f.idFuncion = %s
        """
        cursor.execute(query, (id_funcion,))
        funcion = cursor.fetchone()

        if not funcion:
            return redirect(url_for('cine.inicio'))

        return render_template('butacas.html', funcion=funcion)
    except Exception as e:
        print(f"Error en seleccionar_butacas: {e}")
        return redirect(url_for('cine.inicio'))
