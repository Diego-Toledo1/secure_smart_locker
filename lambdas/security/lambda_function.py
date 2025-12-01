import json
import logging
import hashlib
import os
import boto3 # Cliente AWS para DynamoDB
from datetime import datetime
import db_utils # Helper compartido

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cliente DynamoDB (se inicializa fuera del handler para reuso)
dynamodb = boto3.resource('dynamodb')
AUDIT_TABLE_NAME = 'SmartLocker_AuditLogs' # Asegurarse de que coincida con la que cree

def lambda_handler(event, context):
    path = event.get('path', '') or event.get('rawPath', '')
    http_method = event.get('httpMethod', '') or event.get('requestContext', {}).get('http', {}).get('method')
    
    logger.info(f"Security Request: {http_method} {path}")

    if http_method == 'OPTIONS':
        return db_utils.format_response(200, {})

    # Esperamos ruta: /security/lockers/{lockerId}/access-attempt
    if 'access-attempt' in path and http_method == 'POST':
        return validate_access(event, path)
    
    return db_utils.format_response(404, {'message': 'Ruta de seguridad no encontrada'})

def log_attempt_dynamodb(locker_id, status, reason):
    """Escribe el intento en DynamoDB via VPC Endpoint"""
    try:
        table = dynamodb.Table(AUDIT_TABLE_NAME)
        timestamp = datetime.now().isoformat()
        
        item = {
            'locker_id': str(locker_id),
            'timestamp': timestamp,
            'status': status, # 'SUCCESS', 'FAILED', 'EXPIRED'
            'reason': reason
        }
        table.put_item(Item=item)
        logger.info(f"Audit log guardado: {item}")
    except Exception as e:
        # No fallamos la petición si falla el log, pero lo reportamos
        logger.error(f"Error escribiendo en DynamoDB: {str(e)}")

def validate_access(event, path):
    try:
        # 1. Obtener Locker ID del path (hack rápido)
        # .../lockers/1/access-attempt
        parts = path.split('/')
        if 'access-attempt' not in parts: return db_utils.format_response(400, {'message': 'URL invalida'})
        idx = parts.index('access-attempt')
        locker_id = parts[idx - 1]

        # 2. Obtener OTP del body
        body = json.loads(event.get('body', '{}'))
        input_otp = body.get('otp')

        if not input_otp:
            log_attempt_dynamodb(locker_id, 'FAILED', 'Missing OTP')
            return db_utils.format_response(400, {'message': 'Falta el OTP'})

        # 3. Consultar la "Verdad" en MySQL
        conn = db_utils.get_db_connection()
        locker_data = None
        with conn.cursor() as cur:
            sql = "SELECT current_otp_hash, otp_salt, otp_valid_until, status FROM lockers WHERE id = %s"
            cur.execute(sql, (locker_id,))
            locker_data = cur.fetchone()
        conn.close()

        if not locker_data:
            log_attempt_dynamodb(locker_id, 'FAILED', 'Locker not found')
            return db_utils.format_response(404, {'message': 'Locker no encontrado'})

        # 4. Validaciones de Negocio
        if locker_data['status'] != 'occupied':
            log_attempt_dynamodb(locker_id, 'FAILED', 'Locker not occupied')
            return db_utils.format_response(403, {'message': 'El locker no está en uso'})

        stored_hash = locker_data['current_otp_hash']
        salt = locker_data['otp_salt']
        valid_until = locker_data['otp_valid_until']

        # Checar expiración de tiempo
        if not valid_until or datetime.now() > valid_until:
            log_attempt_dynamodb(locker_id, 'EXPIRED', 'OTP Expired')
            return db_utils.format_response(403, {'message': 'El código ha expirado'})

        # 5. Validar Hash (SHA-256)
        check_hash = hashlib.sha256((input_otp + salt).encode('utf-8')).hexdigest()

        if check_hash == stored_hash:
            # ¡BINGO!
            log_attempt_dynamodb(locker_id, 'SUCCESS', 'Access Granted')
            return db_utils.format_response(200, {'message': 'Acceso Concedido', 'door_open': True})
        else:
            # Fallo
            log_attempt_dynamodb(locker_id, 'FAILED', 'Invalid OTP')
            return db_utils.format_response(401, {'message': 'Código Incorrecto'})

    except Exception as e:
        logger.error(str(e))
        return db_utils.format_response(500, {'error': str(e)})