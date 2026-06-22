import os
import random
import string
import mercadopago
from flask import Blueprint, request, jsonify, render_template, session, url_for
from config.database import DatabaseConnection

pago_bp = Blueprint('pago_bp', __name__)

sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN", "TU_ACCESS_TOKEN"))

@pago_bp.route('/checkout', methods=['GET'])
def vista_pago():
    public_key = os.getenv("MERCADOPAGO_PUBLIC_KEY", "TU_PUBLIC_KEY")
    return render_template('pago.html', public_key=public_key)

@pago_bp.route('/api/crear_preferencia', methods=['POST'])
def crear_preferencia():
    try:
        data = request.get_json() or {}
        id_funcion = data.get("id_funcion")
        asientos_lista = data.get("asientos", [])
        
        asientos_str = ",".join(asientos_lista) if isinstance(asientos_lista, list) else str(asientos_lista)

        db = DatabaseConnection()
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        query_precio = """
            SELECT p.titulo, f.formato, f.precio
            FROM funcion f
            JOIN pelicula p ON f.Pelicula_idPelicula = p.idPelicula
            WHERE f.idFuncion = %s
        """
        cursor.execute(query_precio, (id_funcion,))
        funcion_info = cursor.fetchone()

        if not funcion_info:
            query_fallback = "SELECT titulo, formato, precio FROM funcion WHERE idFuncion = %s"
            cursor.execute(query_fallback, (id_funcion,))
            fallback_info = cursor.fetchone()
            if not fallback_info:
                return jsonify({"error": "La función especificada no existe."}), 404
            titulo_pelicula = fallback_info.get('titulo', 'Película')
            formato_funcion = fallback_info.get('formato', 'Normal')
            precio_unitario_bdd = float(fallback_info.get('precio', 4500.0))
        else:
            titulo_pelicula = funcion_info.get('titulo', 'Película')
            formato_funcion = funcion_info.get('formato', 'Normal')
            precio_unitario_bdd = float(funcion_info.get('precio', 4500.0))

        cantidad_butacas = int(data.get("cantidad", 1))
        id_usuario = str(session.get('usuario_id', ''))

        preference_data = {
            "items": [
                {
                    "title": f"Cine - {titulo_pelicula} ({formato_funcion})",
                    "quantity": cantidad_butacas,
                    "unit_price": precio_unitario_bdd,
                    "currency_id": "ARS"
                }
            ],
            "back_urls": {
                "success": url_for('pago_bp.pago_exitoso', _external=True),
                "failure": url_for('pago_bp.vista_pago', _external=True),
                "pending": url_for('pago_bp.vista_pago', _external=True)
            },
            "external_reference": f"USR_{id_usuario}_FUN_{id_funcion}",
            "metadata": {
                "id_funcion": str(id_funcion),
                "asientos": asientos_str,
                "id_usuario": id_usuario,
                "precio_unitario": precio_unitario_bdd
            }
        }

        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        return jsonify({"id": preference["id"]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pago_bp.route('/process_payment', methods=['POST'])
def process_payment():
    try:
        payment_data = request.get_json() or {}
        payment_response = sdk.payment().create(payment_data)
        payment = payment_response.get("response", {})
        status_detail = payment.get("status_detail", "")
        
        errores_mp = {
            "cc_rejected_bad_filled_card_number": "Número de tarjeta incorrecto.",
            "cc_rejected_bad_filled_date": "Fecha de vencimiento incorrecta.",
            "cc_rejected_bad_filled_security_code": "Código de seguridad (CVV) incorrecto.",
            "cc_rejected_insufficient_amount": "Fondos insuficientes en la tarjeta."
        }
        mensaje_error = errores_mp.get(status_detail, "El pago fue rechazado. Verifique los datos.")

        return jsonify({
            "status": payment.get("status"), 
            "payment_id": payment.get("id"),
            "message": mensaje_error
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pago_bp.route('/pago/exitoso', methods=['GET'])
def pago_exitoso():
    payment_id = request.args.get('payment_id')
    preference_id = request.args.get('preference_id')

    try:
        pref_info = sdk.preference().get(preference_id)
        metadata = pref_info["response"]["metadata"]
        
        id_funcion = metadata.get("id_funcion")
        id_usuario = metadata.get("id_usuario")
        asientos_str = metadata.get("asientos", "")
        precio_unitario = float(metadata.get("precio_unitario", 4500.0))
        asientos = asientos_str.split(",") if asientos_str else []
        
        db = DatabaseConnection()
        cursor = db.get_cursor()

        if cursor and asientos:
            cursor.execute("SELECT Sala_idSala FROM funcion WHERE idFuncion = %s", (id_funcion,))
            info_pago = cursor.fetchone()
            id_sala = int(info_pago['Sala_idSala']) if info_pago else 1
                
            monto_total_pago = precio_unitario * len(asientos)

            cursor.execute("""
                INSERT INTO reserva (Usuario_idUsuario, Funcion_idFuncion, cantidad_butacas, fecha_reserva)
                VALUES (%s, %s, %s, NOW())
            """, (id_usuario, id_funcion, len(asientos)))
            id_reserva = cursor.lastrowid

            for codigo_asiento in asientos:
                if not codigo_asiento: continue
                fila = codigo_asiento[0]
                numero = int(codigo_asiento[1:])

                cursor.execute("""
                    SELECT idAsiento FROM asiento WHERE fila = %s AND numero = %s AND Sala_idSala = %s
                """, (fila, numero, id_sala))
                asiento_existente = cursor.fetchone()

                if asiento_existente:
                    id_asiento = asiento_existente['idAsiento']
                else:
                    cursor.execute("""
                        INSERT INTO asiento (fila, numero, Sala_idSala) VALUES (%s, %s, %s)
                    """, (fila, numero, id_sala))
                    id_asiento = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO reservaasiento (Reserva_idReserva, Asiento_idAsiento) VALUES (%s, %s)
                """, (id_reserva, id_asiento))

            cursor.execute("""
                INSERT INTO pago (monto, fecha_pago, metodo, estado, Reserva_idReserva)
                VALUES (%s, NOW(), 'Mercado Pago', 'aprobado', %s)
            """, (monto_total_pago, id_reserva))

            codigo_ticket = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            cursor.execute("""
                INSERT INTO ticket (codigo_unico, Reserva_idReserva) VALUES (%s, %s)
            """, (codigo_ticket, id_reserva))
            
            db.commit()
            return render_template('pago_exitoso.html', payment_id=payment_id, codigo_ticket=codigo_ticket)

    except Exception as e:
        print(f"Error: {str(e)}")

    return render_template('pago_exitoso.html', payment_id=payment_id, codigo_ticket="RESERVADO")