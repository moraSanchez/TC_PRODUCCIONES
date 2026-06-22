import os
import mercadopago
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from config.database import DatabaseConnection

pago_bp = Blueprint('pago_bp', __name__)

# Inicializamos el SDK de Mercado Pago
sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN"))

@pago_bp.route('/checkout', methods=['GET'])
def vista_pago():
    """Muestra la pantalla final de pago (el wireframe)"""
    public_key = os.getenv("MERCADOPAGO_PUBLIC_KEY")
    return render_template('pago.html', public_key=public_key)


@pago_bp.route('/api/crear_preferencia', methods=['POST'])
def crear_preferencia():
    """Genera el token de pago seguro con Mercado Pago"""
    try:
        data = request.get_json()
        
        # Convertimos la lista de asientos a String plano para la metadata
        asientos_lista = data.get("asientos", [])
        asientos_str = ",".join(asientos_lista) if isinstance(asientos_lista, list) else str(asientos_lista)

        # Estructura oficial requerida por la API de Mercado Pago
        preference_data = {
            "items": [
                {
                    "title": f"Cine - {data.get('titulo')}",
                    "quantity": int(data.get("cantidad", 1)),
                    "unit_price": float(data.get("precio_unitario", 0)),
                    "currency_id": "ARS"
                }
            ],
            "back_urls": {
                "success": url_for('pago_bp.pago_exitoso', _external=True),
                "failure": url_for('pago_bp.pago_fallido', _external=True),
                "pending": url_for('pago_bp.pago_pendiente', _external=True)
            },
            "metadata": {
                "id_funcion": str(data.get("id_funcion")),
                "asientos": asientos_str,  
                "id_usuario": str(session.get('user_id', ''))
            }
        }

        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        
        if "id" not in preference:
            print("Error de Mercado Pago:", preference)
            return jsonify({"error": "Respuesta inválida de Mercado Pago", "details": preference}), 400
        
        return jsonify({"id": preference["id"]}), 200

    except Exception as e:
        print(f"Error interno en crear_preferencia: {str(e)}")
        return jsonify({"error": str(e)}), 500


@pago_bp.route('/pago/exitoso', methods=['GET'])
def pago_exitoso():
    """Ruta a la que redirige MP cuando la tarjeta pasa con éxito"""
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
            query_reserva = """
                INSERT INTO Reserva (Usuario_idUsuario, Funcion_idFuncion, cantidad_butacas, fecha_reserva)
                VALUES (%s, %s, %s, NOW())
            """
            cursor.execute(query_reserva, (id_usuario, id_funcion, len(asientos)))
            id_reserva = cursor.lastrowid

            # Registrar u ocupar cada butaca de la lista
            for codigo_asiento in asientos:
                if not codigo_asiento:
                    continue
                
                query_asiento = """
                    INSERT INTO Asiento (numero, fila, estado, Funcion_idFuncion, Reserva_idReserva)
                    VALUES (%s, %s, 'ocupado', %s, %s)
                    ON DUPLICATE KEY UPDATE estado='ocupado', Reserva_idReserva=%s
                """
                # Separamos la letra de la fila y el número del asiento
                fila = codigo_asiento[0]
                numero = codigo_asiento[1:]
                cursor.execute(query_asiento, (numero, fila, id_funcion, id_reserva, id_reserva))
            
            db.commit()
            print("Reserva y asientos insertados en la Base de Datos con éxito.")

    except Exception as e:
        print(f"Error al guardar la reserva en DB: {str(e)}")

    return render_template('pago_exitoso.html', payment_id=payment_id)


@pago_bp.route('/pago/fallido')
def pago_fallido():
    return render_template('pago_fallido.html', mensaje="El pago fue rechazado o cancelado.")

@pago_bp.route('/pago/pendiente')
def pago_pendiente():
    return render_template('pago_fallido.html', mensaje="El pago está en proceso de acreditación (Rapipago/PagoFácil).")