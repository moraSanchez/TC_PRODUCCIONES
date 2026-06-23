import os
import random
import string
import mercadopago
from flask import Blueprint, request, jsonify, render_template, session, url_for
from config.database import DatabaseConnection

pago_bp = Blueprint('pago_bp', __name__)

sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN"))

@pago_bp.route('/checkout', methods=['GET'])
def vista_pago():
    public_key = os.getenv("MERCADOPAGO_PUBLIC_KEY")
    return render_template('pago.html', public_key=public_key)

@pago_bp.route('/api/crear_preferencia', methods=['POST'])
def crear_preferencia():
    try:
        data = request.get_json()
        id_funcion = data.get("id_funcion")
        asientos_lista = data.get("asientos", [])
        
        asientos_str = ",".join(asientos_lista) if isinstance(asientos_lista, list) else str(asientos_lista)

        db = DatabaseConnection()
        cursor = db.get_cursor()
        
        if not cursor:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        query_precio = """
            SELECT f.titulo, f.formato, p.precio
            FROM funcion f
            JOIN precio_formato p ON f.formato = p.formato
            WHERE f.idFuncion = %s
        """
        cursor.execute(query_precio, (id_funcion,))
        funcion_info = cursor.fetchone()

        if not funcion_info:
            return jsonify({"error": "La función especificada o su formato de precio no existen."}), 404

        if isinstance(funcion_info, dict):
            titulo_pelicula = funcion_info['titulo']
            formato_funcion = funcion_info['formato']
            precio_unitario_bdd = float(funcion_info['precio'])
        else:
            titulo_pelicula = funcion_info[0]
            formato_funcion = funcion_info[1]
            precio_unitario_bdd = float(funcion_info[2])

        cantidad_butacas = int(data.get("cantidad", 1))
        id_usuario = str(session.get('user_id', ''))

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
                "id_usuario": id_usuario
            }
        }

        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        
        return jsonify({"id": preference["id"]}), 200

    except Exception as e:
        print(f"❌ Error en crear_preferencia: {str(e)}")
        return jsonify({"error": str(e)}), 500

@pago_bp.route('/process_payment', methods=['POST'])
def process_payment():
    try:
        payment_data = request.get_json()
        payment_response = sdk.payment().create(payment_data)
        payment = payment_response.get("response", {})
        
        status_detail = payment.get("status_detail", "")
        
        # Diccionario completo con todos los motivos de rechazo de Mercado Pago
        errores_mp = {
            "cc_rejected_bad_filled_card_number": "Revisá el número de tarjeta, es incorrecto.",
            "cc_rejected_bad_filled_date": "Revisá la fecha de vencimiento.",
            "cc_rejected_bad_filled_other": "Revisá los datos ingresados de la tarjeta.",
            "cc_rejected_bad_filled_security_code": "El código de seguridad (CVV) es incorrecto.",
            "cc_rejected_blacklist": "No pudimos procesar el pago. La tarjeta se encuentra bloqueada por robo o pérdida.",
            "cc_rejected_call_for_authorize": "Pago rechazado. Debés llamar a la entidad de tu tarjeta para autorizar el consumo a Mercado Pago.",
            "cc_rejected_card_disabled": "La tarjeta se encuentra inactiva. Llamá a tu banco para activarla.",
            "cc_rejected_card_error": "Hubo un error con tu tarjeta. Por favor, intentá con otra.",
            "cc_rejected_duplicated_payment": "Rechazamos este pago porque detectamos uno igual hace instantes. Revisá tus movimientos.",
            "cc_rejected_high_risk": "El pago fue rechazado por seguridad (riesgo de fraude). Intentá con otro medio de pago.",
            "cc_rejected_insufficient_amount": "Fondos insuficientes. No tenés saldo o límite suficiente en la tarjeta.",
            "cc_rejected_invalid_installments": "Tu tarjeta no procesa la cantidad de cuotas elegida.",
            "cc_rejected_max_attempts": "Excediste el límite de intentos permitidos. Intentá con otra tarjeta o más tarde.",
            "cc_rejected_other_reason": "El banco emisor no procesó el pago. Por favor, intentá con otra tarjeta."
        }

        # Buscamos el error en el diccionario. Si es un error desconocido, mandamos el texto por defecto.
        mensaje_error = errores_mp.get(
            status_detail, 
            "El pago fue rechazado o cancelado. Por favor, verificá los datos e intentá de nuevo."
        )

        return jsonify({
            "status": payment.get("status"), 
            "payment_id": payment.get("id"),
            "message": mensaje_error
        }), 200
        
    except Exception as e:
        print(f"❌ Error al procesar pago: {str(e)}")
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
        asientos = asientos_str.split(",") if asientos_str else []
        
        db = DatabaseConnection()
        cursor = db.get_cursor()

        if cursor and asientos:
            query_precio = """
                SELECT p.precio, f.Sala_idSala
                FROM funcion f
                JOIN precio_formato p ON f.formato = p.formato
                WHERE f.idFuncion = %s
            """
            cursor.execute(query_precio, (id_funcion,))
            info_pago = cursor.fetchone()
            
            if isinstance(info_pago, dict):
                precio_unitario = float(info_pago['precio'])
                id_sala = int(info_pago['Sala_idSala'])
            else:
                precio_unitario = float(info_pago[0])
                id_sala = int(info_pago[1])
                
            monto_total_pago = precio_unitario * len(asientos)

            query_reserva = """
                INSERT INTO reserva (Usuario_idUsuario, Funcion_idFuncion, cantidad_butacas, fecha_reserva)
                VALUES (%s, %s, %s, NOW())
            """
            cursor.execute(query_reserva, (id_usuario, id_funcion, len(asientos)))
            id_reserva = cursor.lastrowid

            for codigo_asiento in asientos:
                if not codigo_asiento:
                    continue
                
                fila = codigo_asiento[0]
                numero = int(codigo_asiento[1:])

                cursor.execute("""
                    SELECT idAsiento FROM asiento
                    WHERE fila = %s AND numero = %s AND Sala_idSala = %s
                """, (fila, numero, id_sala))
                asiento_existente = cursor.fetchone()

                if asiento_existente:
                    id_asiento = asiento_existente['idAsiento'] if isinstance(asiento_existente, dict) else asiento_existente[0]
                else:
                    cursor.execute("""
                        INSERT INTO asiento (fila, numero, Sala_idSala)
                        VALUES (%s, %s, %s)
                    """, (fila, numero, id_sala))
                    id_asiento = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO reservaasiento (Reserva_idReserva, Asiento_idAsiento)
                    VALUES (%s, %s)
                """, (id_reserva, id_asiento))

            query_pago = """
                INSERT INTO pago (monto, fecha_pago, metodo, estado, Reserva_idReserva)
                VALUES (%s, NOW(), 'Mercado Pago', 'aprobado', %s)
            """
            cursor.execute(query_pago, (monto_total_pago, id_reserva))

            codigo_ticket = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            query_ticket = """
                INSERT INTO ticket (codigo_unico, Reserva_idReserva)
                VALUES (%s, %s)
            """
            cursor.execute(query_ticket, (codigo_ticket, id_reserva))
            
            db.commit()
            print(f"✅ Compra procesada con éxito completa. Reserva #{id_reserva}, Ticket: {codigo_ticket}")

            return render_template('pago_exitoso.html', payment_id=payment_id, codigo_ticket=codigo_ticket)

    except Exception as e:
        print(f"❌ Error crítico en el guardado relacional de la compra: {str(e)}")

    return render_template('pago_exitoso.html', payment_id=payment_id, codigo_ticket="RESERVADO")
