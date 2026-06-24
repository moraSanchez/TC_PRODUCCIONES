from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from config.database import DatabaseConnection
from datetime import datetime

cine_bp = Blueprint('cine', __name__)


@cine_bp.route('/')
def inicio():
    return render_template('index.html')


@cine_bp.route('/pelicula/<int:id_pelicula>/funciones')
def seleccionar_funcion(id_pelicula):
    db     = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor:
        return "Error al conectar con la base de datos", 500

    try:
        cursor.execute("SELECT * FROM Pelicula WHERE idPelicula = %s", (id_pelicula,))
        pelicula = cursor.fetchone()
        if not pelicula:
            cursor.close()
            return redirect(url_for('cine.inicio'))

        cursor.execute("""
            SELECT idFuncion, fecha, hora, Sala_idSala, estado,
                   COALESCE(idioma,  'Doblada') AS idioma,
                   COALESCE(formato, '2D')      AS formato
            FROM Funcion
            WHERE Pelicula_idPelicula = %s AND LOWER(estado) = 'activa'
            ORDER BY fecha ASC, hora ASC
        """, (id_pelicula,))
        funciones = cursor.fetchall()

        funciones_agrupadas = {}
        for f in funciones:
            fecha_str = str(f['fecha'])

            if hasattr(f['hora'], 'total_seconds'):
                seg      = f['hora'].seconds
                hora_str = f"{seg // 3600:02d}:{(seg % 3600) // 60:02d}"
            else:
                hora_str = str(f['hora'])[:5]

            idioma_str = str(f['idioma'])

            try:
                dt               = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_formateada = dt.strftime("%d de %B, %Y").upper()
            except Exception:
                fecha_formateada = fecha_str.upper()

            if fecha_formateada not in funciones_agrupadas:
                funciones_agrupadas[fecha_formateada] = {}
            if idioma_str not in funciones_agrupadas[fecha_formateada]:
                funciones_agrupadas[fecha_formateada][idioma_str] = []

            funciones_agrupadas[fecha_formateada][idioma_str].append({
                "idFuncion": f['idFuncion'],
                "hora":      hora_str,
                "num_sala":  f['Sala_idSala'],
                "formato":   f['formato']
            })

        cursor.close()
        return render_template('seleccionar_funcion.html',
                               pelicula=pelicula,
                               funciones_agrupadas=funciones_agrupadas)

    except Exception as e:
        if cursor: cursor.close()
        print(f"❌ Error en seleccionar_funcion: {e}")
        return redirect(url_for('cine.inicio'))


@cine_bp.route('/reserva/funcion/<int:id_funcion>', methods=['GET'])
def seleccionar_butacas(id_funcion):
    id_usuario = session.get('usuario_id') or session.get('user_id')

    if not id_usuario:
        return redirect(url_for('auth.login'))

    session['usuario_id'] = id_usuario
    session['user_id']    = id_usuario

    db     = DatabaseConnection()
    cursor = db.get_cursor()
    if not cursor:
        return "Error al conectar con la base de datos", 500

    try:
        cursor.execute("""
            SELECT f.*, p.titulo, p.imagen_url
            FROM Funcion f
            LEFT JOIN Pelicula p ON f.Pelicula_idPelicula = p.idPelicula
            WHERE f.idFuncion = %s
        """, (id_funcion,))
        funcion = cursor.fetchone()

        if not funcion:
            cursor.close()
            return redirect(url_for('cine.inicio'))

        funcion = dict(funcion)
        funcion['num_sala'] = funcion.get('Sala_idSala')

        # ── Buscamos el precio según el formato (2D, 3D, 4D, XD) en la tabla Entrada ──  ★ NUEVO
        cursor.execute("SELECT precio FROM Entrada WHERE id_entrada = %s", (funcion.get('formato'),))
        entrada_precio = cursor.fetchone()
        funcion['precio_unitario'] = float(entrada_precio['precio']) if entrada_precio else 4500.00

        if funcion.get('hora'):
            if hasattr(funcion['hora'], 'total_seconds'):
                seg             = funcion['hora'].seconds
                funcion['hora'] = f"{seg // 3600:02d}:{(seg % 3600) // 60:02d}"
            else:
                funcion['hora'] = str(funcion['hora'])[:5]

        if funcion.get('fecha'):
            funcion['fecha'] = str(funcion['fecha'])

        cursor.execute("""
            SELECT a.fila, a.numero
            FROM ReservaAsiento ra
            JOIN Reserva  r ON ra.Reserva_idReserva = r.idReserva
            JOIN Asiento  a ON ra.Asiento_idAsiento = a.idAsiento
            WHERE r.Funcion_idFuncion = %s
              AND r.estado_pago IN ('pendiente', 'aprobado')
        """, (id_funcion,))
        ocupados_raw = cursor.fetchall()
        asientos_ocupados = [
            f"{str(row['fila']).upper()}{row['numero']}"
            for row in ocupados_raw
        ]

        cursor.close()
        return render_template('butacas.html',
                               funcion=funcion,
                               asientos_ocupados=asientos_ocupados)

    except Exception as e:
        if cursor: cursor.close()
        print(f"❌ Error en seleccionar_butacas: {e}")
        return redirect(url_for('cine.inicio'))


@cine_bp.route('/api/funciones/<int:id_funcion>/asientos_ocupados', methods=['GET'])
def asientos_ocupados(id_funcion):
    try:
        db     = DatabaseConnection()
        cursor = db.get_cursor()
        if not cursor:
            return jsonify([]), 500

        cursor.execute("""
            SELECT a.fila, a.numero
            FROM ReservaAsiento ra
            JOIN Reserva  r ON ra.Reserva_idReserva = r.idReserva
            JOIN Asiento  a ON ra.Asiento_idAsiento = a.idAsiento
            WHERE r.Funcion_idFuncion = %s
              AND r.estado_pago IN ('pendiente', 'aprobado')
        """, (id_funcion,))

        lista = [
            f"{str(a['fila']).upper()}{a['numero']}"
            for a in cursor.fetchall()
        ]
        cursor.close()
        return jsonify(lista), 200

    except Exception as e:
        print(f"❌ Error en API asientos_ocupados: {e}")
        return jsonify([]), 500