from flask import Blueprint, jsonify, request, session
from models.cliente import Cliente

cliente_bp = Blueprint('cliente', __name__)


def _get_usuario_id():
    """Helper: devuelve el id del usuario autenticado desde la sesión."""
    return session.get('usuario_id') or session.get('user_id')


# ─────────────────────────────────────────────────────────────
# GET /api/cliente/perfil
# Devuelve los datos del usuario autenticado (sin contraseña).
# ─────────────────────────────────────────────────────────────
@cliente_bp.route('/api/cliente/perfil', methods=['GET'])
def api_perfil():
    id_usuario = _get_usuario_id()
    if not id_usuario:
        return jsonify({"error": "No autenticado."}), 401

    perfil = Cliente.obtener_perfil(id_usuario)
    if not perfil:
        return jsonify({"error": "Usuario no encontrado."}), 404

    return jsonify(perfil), 200


# ─────────────────────────────────────────────────────────────
# PUT /api/cliente/perfil
# Actualiza nombre y apellido del usuario autenticado.
# Body JSON: { "nombre": "...", "apellido": "..." }
# ─────────────────────────────────────────────────────────────
@cliente_bp.route('/api/cliente/perfil', methods=['PUT'])
def api_actualizar_perfil():
    id_usuario = _get_usuario_id()
    if not id_usuario:
        return jsonify({"error": "No autenticado."}), 401

    data = request.get_json() or {}
    nombre = data.get('nombre', '').strip()
    apellido = data.get('apellido', '').strip()

    exito, mensaje = Cliente.actualizar_nombre(id_usuario, nombre, apellido)

    if exito:
        # Actualizamos el nombre en la sesión para que el navbar refleje el cambio de inmediato
        session['usuario_nombre'] = nombre
        return jsonify({"status": "success", "message": mensaje, "nombre": nombre}), 200

    return jsonify({"error": mensaje}), 400


# ─────────────────────────────────────────────────────────────
# GET /api/cliente/reservas
# Devuelve el historial completo de reservas del usuario.
# ─────────────────────────────────────────────────────────────
@cliente_bp.route('/api/cliente/reservas', methods=['GET'])
def api_historial_reservas():
    id_usuario = _get_usuario_id()
    if not id_usuario:
        return jsonify({"error": "No autenticado."}), 401

    historial = Cliente.obtener_historial_reservas(id_usuario)
    return jsonify(historial), 200


# ─────────────────────────────────────────────────────────────
# DELETE /api/cliente/reservas/<id_reserva>
# Cancela una reserva propia del usuario autenticado.
# ─────────────────────────────────────────────────────────────
@cliente_bp.route('/api/cliente/reservas/<int:id_reserva>', methods=['DELETE'])
def api_cancelar_reserva(id_reserva):
    id_usuario = _get_usuario_id()
    if not id_usuario:
        return jsonify({"error": "No autenticado."}), 401

    exito, mensaje = Cliente.cancelar_reserva(id_reserva, id_usuario)

    if exito:
        return jsonify({"status": "success", "message": mensaje}), 200

    return jsonify({"error": mensaje}), 400