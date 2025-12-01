import json
import os
import logging
import random
import hashlib
from datetime import datetime, timedelta
import db_utils

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    path = event.get('path', '') or event.get('rawPath', '')
    http_method = event.get('httpMethod', '') or event.get('requestContext', {}).get('http', {}).get('method')
    
    logger.info(f"Request: {http_method} {path}")

    if http_method == 'OPTIONS':
        return db_utils.format_response(200, {})

    # 1. Ver Lockers Disponibles
    if 'available' in path and http_method == 'GET':
        return get_available_lockers()
    
    # 2. Asignar Locker
    elif 'assign' in path and http_method == 'POST':
        return assign_locker(event)
    
    # 3. Rutas de "Mi Locker"
    elif 'my-locker' in path: 
        # Refrescar OTP
        if 'otp/refresh' in path and http_method == 'POST':
            return refresh_otp(event)
        # Cancelar Locker (NUEVO)
        elif 'request-cancel' in path and http_method == 'POST':
            return request_cancel(event)
        # Pedir más tiempo (NUEVO)
        elif 'request-time-change' in path and http_method == 'POST':
            return request_time_change(event)
        # Ver mi locker
        elif http_method == 'GET':
            return get_my_locker(event)
    
    return db_utils.format_response(404, {'message': 'Ruta lockers no encontrada'})

# --- FUNCIONES AUXILIARES ---
def generate_otp():
    otp = str(random.randint(100000, 999999))
    salt = os.urandom(16).hex()
    otp_hash = hashlib.sha256((otp + salt).encode('utf-8')).hexdigest()
    return otp, salt, otp_hash

# --- LOGICA DE NEGOCIO ---

def request_cancel(event):
    """Libera el locker del usuario inmediatamente"""
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        if not user_id: return db_utils.format_response(400, {'message': 'Falta user_id'})

        conn = db_utils.get_db_connection()
        with conn.cursor() as cur:
            # Verificar si tiene locker
            cur.execute("SELECT id FROM lockers WHERE current_user_id = %s", (user_id,))
            locker = cur.fetchone()
            if not locker:
                return db_utils.format_response(404, {'message': 'No tienes locker para cancelar'})

            # Liberar locker (Reset completo)
            sql = """
                UPDATE lockers 
                SET status='available', current_user_id=NULL, assigned_at=NULL, expires_at=NULL, 
                    current_otp_hash=NULL, otp_salt=NULL, otp_valid_until=NULL, color_hex=NULL
                WHERE id=%s
            """
            cur.execute(sql, (locker['id'],))
            conn.commit()

        return db_utils.format_response(200, {'message': 'Locker liberado exitosamente'})
    except Exception as e:
        logger.error(str(e))
        return db_utils.format_response(500, {'error': str(e)})
    finally:
        if 'conn' in locals(): conn.close()

def request_time_change(event):
    """Crea una solicitud en locker_requests"""
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        days = body.get('days', 1)
        
        if not user_id: return db_utils.format_response(400, {'message': 'Falta user_id'})

        conn = db_utils.get_db_connection()
        with conn.cursor() as cur:
            # Obtener el locker ID
            cur.execute("SELECT id FROM lockers WHERE current_user_id = %s", (user_id,))
            locker = cur.fetchone()
            if not locker:
                return db_utils.format_response(404, {'message': 'No tienes locker'})

            # Insertar solicitud
            sql = """
                INSERT INTO locker_requests (locker_id, user_id, request_type, status, notes, created_at)
                VALUES (%s, %s, 'change_time', 'pending', %s, NOW())
            """
            note = f"Solicitud de extensión por {days} días adicionales"
            cur.execute(sql, (locker['id'], user_id, note))
            conn.commit()

        return db_utils.format_response(200, {'message': 'Solicitud enviada al administrador'})
    except Exception as e:
        logger.error(str(e))
        return db_utils.format_response(500, {'error': str(e)})
    finally:
        if 'conn' in locals(): conn.close()

def refresh_otp(event):
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        if not user_id: return db_utils.format_response(400, {'message': 'Falta user_id'})
        otp_plain, salt, otp_hash = generate_otp()
        conn = db_utils.get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM lockers WHERE current_user_id = %s", (user_id,))
            locker = cur.fetchone()
            if not locker: return db_utils.format_response(404, {'message': 'No tienes locker'})
            sql = "UPDATE lockers SET current_otp_hash=%s, otp_salt=%s, otp_valid_until=DATE_ADD(NOW(), INTERVAL 15 SECOND) WHERE id=%s"
            cur.execute(sql, (otp_hash, salt, locker['id']))
            conn.commit()
        return db_utils.format_response(200, {'otp': otp_plain})
    except Exception as e:
        return db_utils.format_response(500, {'error': str(e)})
    finally:
        if 'conn' in locals(): conn.close()

def get_available_lockers():
    conn = db_utils.get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, code, status FROM lockers WHERE status = 'available'")
            lockers = cur.fetchall()
        return db_utils.format_response(200, lockers)
    except Exception as e: return db_utils.format_response(500, {'error': str(e)})
    finally: conn.close()

def assign_locker(event):
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        locker_id = body.get('locker_id')
        days = int(body.get('days', 1))
        color = body.get('color', '#000000')
        if not user_id or not locker_id: return db_utils.format_response(400, {'message': 'Faltan datos'})
        conn = db_utils.get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM lockers WHERE current_user_id = %s", (user_id,))
            if cur.fetchone(): return db_utils.format_response(409, {'message': 'Ya tienes locker'})
            cur.execute("SELECT status FROM lockers WHERE id = %s", (locker_id,))
            locker = cur.fetchone()
            if not locker or locker['status'] != 'available': return db_utils.format_response(409, {'message': 'Locker no disponible'})
            otp_plain, salt, otp_hash = generate_otp()
            sql = "UPDATE lockers SET status='occupied', current_user_id=%s, assigned_at=NOW(), expires_at=DATE_ADD(NOW(), INTERVAL %s DAY), current_otp_hash=%s, otp_salt=%s, otp_valid_until=DATE_ADD(NOW(), INTERVAL 15 MINUTE), color_hex=%s WHERE id=%s"
            cur.execute(sql, (user_id, days, otp_hash, salt, color, locker_id))
            conn.commit()
            return db_utils.format_response(200, {'message': 'Asignado', 'initial_otp': otp_plain})
    except Exception as e: return db_utils.format_response(500, {'error': str(e)})
    finally: 
        if 'conn' in locals(): conn.close()

def get_my_locker(event):
    try:
        params = event.get('queryStringParameters', {}) or {}
        user_id = params.get('user_id')
        if not user_id: return db_utils.format_response(400, {'message': 'Falta user_id'})
        conn = db_utils.get_db_connection()
        with conn.cursor() as cur:
            sql = "SELECT id, code, status, expires_at, color_hex FROM lockers WHERE current_user_id = %s"
            cur.execute(sql, (user_id,))
            locker = cur.fetchone()
            if not locker: return db_utils.format_response(404, {'message': 'Sin locker'})
            return db_utils.format_response(200, locker)
    except Exception as e: return db_utils.format_response(500, {'error': str(e)})
    finally: 
        if 'conn' in locals(): conn.close()