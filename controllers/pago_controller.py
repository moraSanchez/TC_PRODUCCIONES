import os
import random
import string
import mercadopago
from flask import Blueprint, request, jsonify, render_template, session, url_for
from config.database import DatabaseConnection

pago_bp = Blueprint('pago_bp', __name__)

# Inicializamos el SDK de Mercado Pago con las credenciales del .env
sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN"))

@pago_bp.route('/checkout', methods=['GET'])
def vista_pago():
    public_key = os.getenv("MERCADOPAGO_PUBLIC_KEY")
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

        # 🔥 CORREGIDO: JOIN exacto con la tabla Pelicula usando Pelicula_idPelicula
        query_funcion = """
            SELECT p.titulo, f.formato
            FROM Funcion f
            JOIN Pelicula p ON f.Pelicula_idPelicula = p.idPelicula
            WHERE f.idFuncion = %s
        """
        cursor.execute(query_funcion, (id_funcion,))
        funcion_info = cursor.fetchone()

        if not funcion_info:
            cursor.close()
            return jsonify({"error": "La función especificada no existe en el sistema."}), 404

        titulo_pelicula = funcion_info['titulo']
        formato_funcion = funcion_info['formato']
        
        # Seteamos el precio base de la entrada (coincidiendo con tus $4500.00 del frontend)
        precio_unitario = 4500.00  

        cantidad_butacas = int(data.get("cantidad", 1))
        
        # Consolidamos el ID del usuario de la sesión activa
        id_usuario = session.get('usuario_id') or session.get('user_id')
        if not id_usuario:
            cursor.close()
            return jsonify({"error": "Usuario no autenticado en la sesión."}), 401

        # Estructura oficial de la preferencia para Mercado Pago Sandbox/Production
        preference_data = {
            "items": [{
                "title": f"Cine - {titulo_pelicula} ({formato_funcion})",
                "quantity": cantidad_butacas,
                "unit_price": float(precio_unitario),
                "currency_id": "ARS"
            }],
            "back_urls": {
                "success": url_for('pago_bp.pago_exitoso', _external=True),
                "failure": url_for('pago_bp.vista_pago', _external=True),
                "pending": url_for('pago_bp.vista_pago', _external=True)
            },
            "external_reference": f"USR_{id_usuario}_FUN_{id_funcion}",
            "metadata": {
                "id_funcion": str(id_funcion),
                "asientos": asientos_str,
                "id_usuario": str(id_usuario)
            }
        }

        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        
        cursor.close()
        return jsonify({"id": preference["id"]}), 200
        
    except Exception as e:
        print(f"❌ Error crítico en crear_preferencia: {str(e)}")
        return jsonify({"error": str(e)}), 500

@pago_bp.route('/process_payment', methods=['POST'])
def process_payment():
    try:
        payment_data = request.get_json()
        payment_response = sdk.payment().create(payment_data)
        payment = payment_response.get("response", {})
        status_detail = payment.get("status_detail", "")
        
        errores_mp = {
            "cc_rejected_bad_filled_card_number": "Revisá el número de tarjeta, es incorrecto.",
            "cc_rejected_bad_filled_date": "Revisá la fecha de vencimiento.",
            "cc_rejected_bad_filled_security_code": "El código de seguridad (CVV) es incorrecto.",
            "cc_rejected_blacklist": "Tarjeta bloqueada por robo o pérdida.",
            "cc_rejected_call_for_authorize": "Debés autorizar el pago en tu entidad bancaria.",
            "cc_rejected_card_disabled": "La tarjeta se encuentra inactiva.",
            "cc_rejected_insufficient_amount": "Fondos insuficientes en la tarjeta.",
            "cc_rejected_high_risk": "Rechazado por controles de prevención de fraude."
        }

        mensaje_error = errores_mp.get(status_detail, "El pago fue rechazado. Verificá los datos.")
        return jsonify({"status": payment.get("status"), "payment_id": payment.get("id"), "message": mensaje_error}), 200
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
        asientos = asientos_str.split(",") if asientos_str else []
        
        db = DatabaseConnection()
        cursor = db.get_cursor()

        if cursor and asientos:
            # Traemos la sala de la función para mapear las butacas ocupadas
            cursor.execute("SELECT Sala_idSala FROM Funcion WHERE idFuncion = %s", (id_funcion,))
            info_funcion = cursor.fetchone()
            id_sala = int(info_funcion['Sala_idSala'])
            
            precio_unitario = 4500.00
            monto_total_pago = precio_unitario * len(asientos)

            # 1. Insertar la Reserva principal (coincidiendo con las columnas de tu schema.sql)
            query_reserva = """
                INSERT INTO Reserva (Usuario_idUsuario, Funcion_idFuncion, fecha_reserva, total, estado_pago, mercadopago_preference_id) 
                VALUES (%s, %s, NOW(), %s, 'aprobado', %s)
            """
            cursor.execute(query_reserva, (id_usuario, id_funcion, monto_total_pago, preference_id))
            id_reserva = cursor.lastrowid

            # 2. Procesar y guardar cada asiento individual
            for codigo_asiento in asientos:
                if not codigo_asiento or len(codigo_asiento) < 2: 
                    continue
                fila = codigo_asiento[0]
                try:
                    numero = int(codigo_asiento[1:])
                except ValueError:
                    continue

                # Verificamos si el asiento ya está registrado físicamente en esa sala
                cursor.execute("SELECT idAsiento FROM Asiento WHERE fila = %s AND numero = %s AND Sala_idSala = %s", (fila, numero, id_sala))
                asiento_existente = cursor.fetchone()

                if asiento_existente:
                    id_asiento = asiento_existente['idAsiento']
                else:
                    cursor.execute("INSERT INTO Asiento (fila, numero, Sala_idSala) VALUES (%s, %s, %s)", (fila, numero, id_sala))
                    id_asiento = cursor.lastrowid

                # Guardamos la relación en la tabla intermedia ReservaAsiento
                cursor.execute("INSERT INTO ReservaAsiento (Reserva_idReserva, Asiento_idAsiento) VALUES (%s, %s)", (id_reserva, id_asiento))

            db.commit()
            cursor.close()  # Fin de la transacción exitosa, liberamos el cursor.
            
            # Generamos un código visual de ticket para la interfaz de confirmación
            codigo_ticket = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            return render_template('pago_exitoso.html', payment_id=payment_id, codigo_ticket=codigo_ticket)

    except Exception as e:
        print(f"❌ Error crítico guardando la compra: {str(e)}")
        if 'cursor' in locals() and cursor:
            cursor.close()

    return render_template('pago_exitoso.html', payment_id=payment_id, codigo_ticket="RESERVADO")