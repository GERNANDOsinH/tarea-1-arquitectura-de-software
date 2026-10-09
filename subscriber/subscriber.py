import pika
import json
import requests
import math
import os
import time

SUBSCRIBER_NAME = os.getenv("NAME", "Valparaíso")
SUBSCRIBER_LAT = float(os.getenv("LAT", -33.036))
SUBSCRIBER_LON = float(os.getenv("LON", -71.62963))
API_URL = os.getenv("API_URL", "http://host.docker.internal:8000/sismos")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371  
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def callback(ch, method, properties, body):
    mensaje = json.loads(body.decode('utf-8'))
    sismo_id = mensaje.get("id")
    sismo_lat = mensaje.get("latitude")
    sismo_lon = mensaje.get("longitude")

    distancia = calcular_distancia(SUBSCRIBER_LAT, SUBSCRIBER_LON, sismo_lat, sismo_lon)

    if distancia < 500:
        # Aviso inmediato de recepción y cálculo
        print(f" ***** [{SUBSCRIBER_NAME}] Sismo detectado, [ID: {sismo_id}] (Distancia: {distancia:.1f} km)")
        
        try:
            respuesta = requests.get(f"{API_URL}/{sismo_id}")
            
            if respuesta.status_code == 200:
                json_resp = respuesta.json()
                if json_resp.get("status") == "success":
                    datos = json_resp.get("data", {})
                    mag = datos.get("magnitude", "N/A")
                    prof = datos.get("depth", "N/A")
                    ubicacion = datos.get("location", "N/A")
                    
                    # Aviso de detalles repitiendo el contexto (ID y Ciudad)
                    print(f"[{SUBSCRIBER_NAME}] +++++ Detalles sismo [id: {sismo_id}] detectado en {SUBSCRIBER_NAME} -> Mag: {mag} | Prof: {prof} | Origen: {ubicacion}")
                else:
                    print(f"[{SUBSCRIBER_NAME}] Detalles sismo id: {sismo_id} -> Error API: {json_resp.get('description')}")
            else:
                print(f"[{SUBSCRIBER_NAME}] Detalles sismo id: {sismo_id} -> Error HTTP: {respuesta.status_code}")
        except Exception as e:
            print(f"[{SUBSCRIBER_NAME}] Detalles sismo id: {sismo_id} -> Error de conexión: {e}")
            
    else:
        # Línea para los sismos ignorados
        print(f" ----- [{SUBSCRIBER_NAME}] Sismo id: {sismo_id} ignorado")
        


def iniciar_consumidor():
    credenciales = pika.PlainCredentials('guest', 'guest')
    parametros = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credenciales)
    
    # Ciclo de reintentos para evitar crasheos si RabbitMQ demora en despertar
    connection = None
    for i in range(10):
        try:
            connection = pika.BlockingConnection(parametros)
            break
        except pika.exceptions.AMQPConnectionError:
            print(f"[{SUBSCRIBER_NAME}] Esperando a que RabbitMQ acepte conexiones (intento {i+1}/10)...")
            time.sleep(3)
            
    if not connection:
        print(f"[{SUBSCRIBER_NAME}] Error fatal: No se pudo conectar a RabbitMQ tras varios intentos.")
        return

    channel = connection.channel()
    channel.exchange_declare(exchange='sismos', exchange_type='fanout', durable=True)
    
    nombre_cola = f"sismos.{SUBSCRIBER_NAME.lower().replace('í', 'i').replace(' ', '_')}"
    channel.queue_declare(queue=nombre_cola, durable=True)
    channel.queue_bind(exchange='sismos', queue=nombre_cola)

    print(f"[{SUBSCRIBER_NAME}] Escuchando eventos en la cola '{nombre_cola}'...")
    channel.basic_consume(queue=nombre_cola, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    iniciar_consumidor()