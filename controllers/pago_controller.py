import os
import random
import string
import mercadopago
from flask import Blueprint, request, jsonify, render_template, session, url_for, redirect
from config.database import DatabaseConnection

pago_bp = Blueprint('pago_bp', __name__)

sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN"))


# vista del formulario de pago
@pago_bp.route('/checkout', methods=['GET'])
def vista_pago():
    if 'usuario_id' not in session and 'user_id' not in session:
        return redirect(url_for('auth.login'))
    public_key = os.getenv("MERCADOPAGO_PUBLIC_KEY")
    return render_template('pago.html', public_key=public_key)

# Crea la preferencia en MercadoPago y pre-guarda la reserva
# en estado 'pendiente' para reservar los asientos de inmediato.
@pago_bp.route('/api/crear_preferencia', methods=['POST'])
def crear_preferencia():
    id_usuario = session.get('usuario_id') or session.get('user_id')
    if not id_usuario:
        return jsonify({"error": "Usuario no autenticado."}), 401

    try:
        data = request.get_json() or {}
        id_funcion      = data.get("id_funcion")
        asientos_lista  = data.get("asientos", [])
        cantidad        = int(data.get("cantidad", len(asientos_lista)))

        if not id_funcion or not asientos_lista:
            return jsonify({"error": "Faltan datos de función o asientos."}), 400

        db     = DatabaseConnection()
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({"error": "Sin conexión a la base de datos."}), 500

        # ── Verificar que la función existe
        cursor.execute("""
            SELECT p.titulo, f.formato, f.Sala_idSala
            FROM Funcion f
            JOIN Pelicula p ON f.Pelicula_idPelicula = p.idPelicula
            WHERE f.idFuncion = %s
        """, (id_funcion,))
        funcion_info = cursor.fetchone()
        if not funcion_info:
            cursor.close()
            return jsonify({"error": "Función no encontrada."}), 404

        id_sala         = int(funcion_info['Sala_idSala'])
        titulo_pelicula = funcion_info['titulo']
        formato_funcion = funcion_info['formato']

        # ── Precio real según el formato (2D, 3D, 4D, XD), tomado de la tabla Entrada 
        cursor.execute("SELECT precio FROM Entrada WHERE id_entrada = %s", (formato_funcion,))
        entrada_precio  = cursor.fetchone()
        precio_unitario = float(entrada_precio['precio']) if entrada_precio else 4500.00

        total           = precio_unitario * cantidad
        asientos_str    = ",".join(asientos_lista)

        # ── Verificar que los asientos no estén ya ocupados ──
        asientos_ocupados = _obtener_asientos_ocupados_bd(cursor, id_funcion)
        for cod in asientos_lista:
            if cod.upper() in asientos_ocupados:
                cursor.close()
                return jsonify({"error": f"El asiento {cod} ya fue reservado. Seleccioná otro."}), 409

        # ── Pre-guardar Reserva en estado 'pendiente' 
        # Esto bloquea los asientos para que nadie más los tome
        cursor.execute("""
            INSERT INTO Reserva
                (Usuario_idUsuario, Funcion_idFuncion, fecha_reserva, total, estado_pago, mercadopago_preference_id)
            VALUES (%s, %s, NOW(), %s, 'pendiente', 'PENDIENTE')
        """, (id_usuario, id_funcion, total))
        db.commit()
        id_reserva = cursor.lastrowid

        # ── Guardar cada asiento en ReservaAsiento
        for cod in asientos_lista:
            id_asiento = _obtener_o_crear_asiento(cursor, db, cod, id_sala)
            if id_asiento:
                cursor.execute("""
                    INSERT INTO ReservaAsiento (Reserva_idReserva, Asiento_idAsiento)
                    VALUES (%s, %s)
                """, (id_reserva, id_asiento))
        db.commit()
        cursor.close()

        # ── Crear preferencia en MercadoPago
        preference_data = {
            "items": [{
                "title": f"Cine - {titulo_pelicula} ({formato_funcion})",
                "quantity": cantidad,
                "unit_price": float(precio_unitario),
                "currency_id": "ARS"
            }],
            "back_urls": {
                "success": url_for('pago_bp.pago_exitoso', _external=True),
                "failure": url_for('pago_bp.vista_pago',   _external=True),
                "pending": url_for('pago_bp.vista_pago',   _external=True)
            },
            "external_reference": f"RES_{id_reserva}",
            "metadata": {
                "id_reserva":  str(id_reserva),
                "id_funcion":  str(id_funcion),
                "asientos":    asientos_str,
                "id_usuario":  str(id_usuario)
            }
        }

        pref_response = sdk.preference().create(preference_data)
        preference    = pref_response["response"]
        preference_id = preference.get("id", "")

        # Actualizar la reserva con el preference_id real
        cursor2 = db.get_cursor()
        if cursor2:
            cursor2.execute(
                "UPDATE Reserva SET mercadopago_preference_id = %s WHERE idReserva = %s",
                (preference_id, id_reserva)
            )
            db.commit()
            cursor2.close()

        return jsonify({"id": preference_id, "id_reserva": id_reserva}), 200

    except Exception as e:
        print(f"Error en crear_preferencia: {e}")
        return jsonify({"error": str(e)}), 500


# procesa el pago desde el Brick
@pago_bp.route('/process_payment', methods=['POST'])
def process_payment():
    try:
        payment_data     = request.get_json()
        payment_response = sdk.payment().create(payment_data)
        payment          = payment_response.get("response", {})
        status           = payment.get("status")
        status_detail    = payment.get("status_detail", "")

        errores_mp = {
            "cc_rejected_bad_filled_card_number": "Revisá el número de tarjeta.",
            "cc_rejected_bad_filled_date":        "Revisá la fecha de vencimiento.",
            "cc_rejected_bad_filled_security_code": "El CVV es incorrecto.",
            "cc_rejected_blacklist":              "Tarjeta bloqueada.",
            "cc_rejected_call_for_authorize":     "Autorizá el pago en tu banco.",
            "cc_rejected_card_disabled":          "La tarjeta está inactiva.",
            "cc_rejected_insufficient_amount":    "Fondos insuficientes.",
            "cc_rejected_high_risk":              "Rechazado por prevención de fraude."
        }
        mensaje_error = errores_mp.get(status_detail, "El pago fue rechazado.")

        if status == 'approved':
            preference_id = payment_data.get("transaction_amount") and payment.get("order", {}).get("id")
            _confirmar_reserva_por_preferencia(payment.get("external_reference", ""), payment.get("id"))

        return jsonify({
            "status":     status,
            "payment_id": payment.get("id"),
            "message":    mensaje_error
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# confirma la reserva y muestra resumen
@pago_bp.route('/pago/exitoso', methods=['GET'])
def pago_exitoso():
    payment_id    = request.args.get('payment_id', '')
    preference_id = request.args.get('preference_id', '')

    codigo_ticket   = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    pelicula_titulo = ''
    funcion_fecha   = ''
    funcion_hora    = ''
    num_sala        = ''
    formato         = ''
    asientos        = ''
    total           = 0.0

    try:
        db     = DatabaseConnection()
        cursor = db.get_cursor()

        id_reserva = None

        if preference_id and preference_id != 'simulado_ok':
            cursor.execute(
                "SELECT idReserva FROM Reserva WHERE mercadopago_preference_id = %s",
                (preference_id,)
            )
            row = cursor.fetchone()
            if row:
                id_reserva = row['idReserva']

        # buscar la reserva más reciente del usuario en sesión
        if not id_reserva:
            id_usuario = session.get('usuario_id') or session.get('user_id')
            if id_usuario:
                cursor.execute("""
                    SELECT idReserva FROM Reserva
                    WHERE Usuario_idUsuario = %s
                    ORDER BY fecha_reserva DESC LIMIT 1
                """, (id_usuario,))
                row = cursor.fetchone()
                if row:
                    id_reserva = row['idReserva']

        if id_reserva:
            # ── Confirmar la reserva 
            cursor.execute(
                "UPDATE Reserva SET estado_pago = 'aprobado' WHERE idReserva = %s",
                (id_reserva,)
            )
            db.commit()

            # ── Traer detalle completo para mostrar en la vista 
            cursor.execute("""
                SELECT
                    r.total,
                    p.titulo        AS pelicula_titulo,
                    f.fecha         AS funcion_fecha,
                    f.hora          AS funcion_hora,
                    f.Sala_idSala   AS num_sala,
                    f.formato,
                    GROUP_CONCAT(CONCAT(a.fila, a.numero) ORDER BY a.fila, a.numero SEPARATOR ', ') AS asientos
                FROM Reserva r
                JOIN Funcion  f  ON r.Funcion_idFuncion  = f.idFuncion
                JOIN Pelicula p  ON f.Pelicula_idPelicula = p.idPelicula
                LEFT JOIN ReservaAsiento ra ON ra.Reserva_idReserva = r.idReserva
                LEFT JOIN Asiento a         ON a.idAsiento = ra.Asiento_idAsiento
                WHERE r.idReserva = %s
                GROUP BY r.idReserva
            """, (id_reserva,))
            detalle = cursor.fetchone()

            if detalle:
                pelicula_titulo = detalle.get('pelicula_titulo', '')
                funcion_fecha   = str(detalle.get('funcion_fecha', ''))
                num_sala        = detalle.get('num_sala', '')
                formato         = detalle.get('formato', '')
                asientos        = detalle.get('asientos', '')
                total           = float(detalle.get('total') or 0)

                hora = detalle.get('funcion_hora')
                if hasattr(hora, 'total_seconds'):
                    seg = hora.seconds
                    funcion_hora = f"{seg // 3600:02d}:{(seg % 3600) // 60:02d}"
                else:
                    funcion_hora = str(hora)[:5]

        cursor.close()

    except Exception as e:
        print(f"Error en pago_exitoso: {e}")
        if 'cursor' in locals() and cursor:
            cursor.close()

    return render_template(
        'pago_exitoso.html',
        payment_id    = payment_id,
        codigo_ticket = codigo_ticket,
        pelicula_titulo = pelicula_titulo,
        funcion_fecha   = funcion_fecha,
        funcion_hora    = funcion_hora,
        num_sala        = num_sala,
        formato         = formato,
        asientos        = asientos,
        total           = total
    )



def _obtener_asientos_ocupados_bd(cursor, id_funcion):
    """Devuelve un set con los códigos de asientos ya reservados (ej: {'A1','B3'})."""
    cursor.execute("""
        SELECT a.fila, a.numero
        FROM ReservaAsiento ra
        JOIN Reserva  r ON ra.Reserva_idReserva  = r.idReserva
        JOIN Asiento  a ON ra.Asiento_idAsiento  = a.idAsiento
        WHERE r.Funcion_idFuncion = %s
          AND r.estado_pago IN ('pendiente', 'aprobado')
    """, (id_funcion,))
    ocupados = set()
    for row in cursor.fetchall():
        ocupados.add(f"{str(row['fila']).upper()}{row['numero']}")
    return ocupados


def _obtener_o_crear_asiento(cursor, db, codigo, id_sala):
    """
    Dado un código de asiento como 'A3', busca el idAsiento en la BD.
    Si no existe lo crea. Retorna el idAsiento.
    """
    try:
        if not codigo or len(codigo) < 2:
            return None
        fila   = codigo[0].upper()
        numero = int(codigo[1:])

        cursor.execute(
            "SELECT idAsiento FROM Asiento WHERE fila = %s AND numero = %s AND Sala_idSala = %s",
            (fila, numero, id_sala)
        )
        row = cursor.fetchone()
        if row:
            return row['idAsiento']

        cursor.execute(
            "INSERT INTO Asiento (fila, numero, Sala_idSala) VALUES (%s, %s, %s)",
            (fila, numero, id_sala)
        )
        db.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error en _obtener_o_crear_asiento ({codigo}): {e}")
        return None


def _confirmar_reserva_por_preferencia(external_ref, payment_id):
    """Marca como 'aprobado' la reserva identificada por external_reference."""
    try:
        if not external_ref or not external_ref.startswith("RES_"):
            return
        id_reserva = int(external_ref.replace("RES_", ""))
        db     = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            cursor.execute(
                "UPDATE Reserva SET estado_pago = 'aprobado' WHERE idReserva = %s",
                (id_reserva,)
            )
            db.commit()
            cursor.close()
    except Exception as e:
        print(f"Error confirmando reserva por preferencia: {e}")