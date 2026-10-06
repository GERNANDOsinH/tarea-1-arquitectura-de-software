"""Publisher de sismos (Notificador Sismos).

Publica eventos con información mínima en un exchange fanout de RabbitMQ.
No conoce a los subscribers: cada uno decide si el sismo le interesa y,
si es así, pide el detalle al servicio http (modelo pull).

Lee los sismos en el mismo formato que la API (api/sismos.txt):
    id,magnitude,depth,location,datetime,latitude,longitude

Contrato del mensaje: ver ../contrato_mensaje.md
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pika
from pika.exceptions import AMQPConnectionError, UnroutableError

EXCHANGE = os.getenv("SISMOS_EXCHANGE", "sismos")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")
CAMPOS_MENSAJE = ("id", "datetime", "latitude", "longitude")
ARCHIVO_API = Path(__file__).resolve().parent.parent / "api" / "sismos.txt"
ARCHIVO_PRUEBA = Path(__file__).with_name("sismos_prueba.txt")

log = logging.getLogger("publisher")


def construir_evento(id_sismo, fecha, latitude, longitude):
    """Arma el mensaje mínimo: id, datetime (ISO 8601), latitude, longitude."""
    latitude, longitude = float(latitude), float(longitude)
    if not -90 <= latitude <= 90:
        raise ValueError(f"latitude fuera de rango: {latitude}")
    if not -180 <= longitude <= 180:
        raise ValueError(f"longitude fuera de rango: {longitude}")
    return {
        "id": int(id_sismo),
        "datetime": datetime.fromisoformat(str(fecha)).isoformat(),
        "latitude": latitude,
        "longitude": longitude,
    }


def cargar_sismos(ruta):
    """Lee un archivo con el formato de api/sismos.txt y devuelve los mensajes mínimos."""
    eventos = []
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            p = linea.split(",")
            if len(p) != 7:
                raise ValueError(f"Línea inválida (se esperan 7 campos): {linea!r}")
            eventos.append(construir_evento(p[0], p[4], p[5], p[6]))
    return eventos


def serializar(evento):
    return json.dumps(evento, separators=(",", ":"), ensure_ascii=False).encode()


def conectar(url, intentos=10, espera=2.0):
    """Conecta a RabbitMQ reintentando (el broker puede estar arrancando)."""
    for i in range(1, intentos + 1):
        try:
            return pika.BlockingConnection(pika.URLParameters(url))
        except AMQPConnectionError:
            log.warning("RabbitMQ no disponible (intento %d/%d)", i, intentos)
            time.sleep(espera)
    raise ConnectionError(f"No se pudo conectar a RabbitMQ en {url}")


def abrir_canal(conexion, exchange=EXCHANGE):
    canal = conexion.channel()
    canal.exchange_declare(exchange=exchange, exchange_type="fanout", durable=True)
    canal.confirm_delivery()
    return canal


def publicar(canal, evento, exchange=EXCHANGE):
    """Publica un evento. Devuelve False si no había ningún subscriber enlazado."""
    try:
        canal.basic_publish(
            exchange=exchange,
            routing_key="",
            body=serializar(evento),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=pika.DeliveryMode.Persistent,
                message_id=str(evento["id"]),
            ),
            mandatory=True,
        )
    except UnroutableError:
        log.warning("Sismo %s sin destinatarios: no hay subscribers enlazados", evento["id"])
        return False
    log.info("Publicado %s", serializar(evento).decode())
    return True


def parsear_args(argv=None):
    p = argparse.ArgumentParser(description="Publica sismos en RabbitMQ (fanout).")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--todos", action="store_true", help="publica todos los sismos del archivo")
    g.add_argument("--id", type=int, help="publica solo el sismo con este id del archivo")
    g.add_argument("--lat", type=float, help="sismo manual: latitud (requiere --lon y --id-manual)")
    p.add_argument("--lon", type=float, help="sismo manual: longitud")
    p.add_argument("--id-manual", type=int, help="sismo manual: id (debe existir en la API)")
    p.add_argument("--archivo", default=str(ARCHIVO_API),
                   help="sismos en formato api/sismos.txt (por defecto el de la API)")
    p.add_argument("--prueba", action="store_true", help="usa publisher/sismos_prueba.txt")
    p.add_argument("--intervalo", type=float, default=1.0, help="segundos entre sismos")
    p.add_argument("--url", default=RABBITMQ_URL, help="URL AMQP (o variable RABBITMQ_URL)")
    p.add_argument("--exchange", default=EXCHANGE)
    args = p.parse_args(argv)
    if args.lat is not None and (args.lon is None or args.id_manual is None):
        p.error("--lat requiere --lon y --id-manual")
    if args.prueba:
        args.archivo = str(ARCHIVO_PRUEBA)
    return args


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parsear_args(argv)

    if args.lat is not None:
        eventos = [construir_evento(args.id_manual, datetime.now().isoformat(timespec="seconds"),
                                    args.lat, args.lon)]
    else:
        eventos = cargar_sismos(args.archivo)
        if args.id is not None:
            eventos = [e for e in eventos if e["id"] == args.id]
            if not eventos:
                sys.exit(f"No existe el sismo {args.id} en {args.archivo}")

    conexion = conectar(args.url)
    try:
        canal = abrir_canal(conexion, args.exchange)
        for i, evento in enumerate(eventos):
            if i:
                time.sleep(args.intervalo)
            publicar(canal, evento, args.exchange)
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
