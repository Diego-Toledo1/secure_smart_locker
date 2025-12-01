import json
import logging
import db_utils # Usaremos el helper compartido

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Ejecuta SQL arbitrario para depuración.
    Evento esperado: { "sql": "SELECT * FROM lockers" }
    """
    sql_query = event.get('sql')
    
    if not sql_query:
        return db_utils.format_response(400, {'message': 'Falta el campo "sql" en el evento'})

    logger.info(f"Ejecutando SQL: {sql_query}")

    conn = db_utils.get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql_query)
            # Si es SELECT, devolvemos datos
            if sql_query.strip().upper().startswith("SELECT"):
                result = cur.fetchall()
                # Convertir fechas a string para que JSON no falle (lo hace db_utils, pero por si acaso)
                return db_utils.format_response(200, result)
            else:
                # Si es UPDATE/INSERT/DELETE, confirmamos cambios
                conn.commit()
                return db_utils.format_response(200, {'message': 'Comando ejecutado', 'rows_affected': cur.rowcount})
                
    except Exception as e:
        logger.error(str(e))
        return db_utils.format_response(500, {'error': str(e)})
    finally:
        conn.close()