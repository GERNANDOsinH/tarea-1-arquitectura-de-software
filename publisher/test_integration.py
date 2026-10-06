"""Prueba contra un RabbitMQ real. Se omite si no hay broker disponible."""
import json

import pika
import pytest

import publisher as pub

EXCHANGE_TEST = "sismos_test"


@pytest.fixture
def conexion():
    try:
        c = pika.BlockingConnection(pika.URLParameters(pub.RABBITMQ_URL))
    except pika.exceptions.AMQPConnectionError:
        pytest.skip("RabbitMQ no disponible")
    yield c
    c.close()


def suscribir(conexion, exchange):
    """Simula un subscriber: cola propia exclusiva enlazada al exchange."""
    canal = conexion.channel()
    canal.exchange_declare(exchange=exchange, exchange_type="fanout", durable=True)
    cola = canal.queue_declare(queue="", exclusive=True).method.queue
    canal.queue_bind(queue=cola, exchange=exchange)
    return canal, cola


def test_todos_los_subscribers_reciben_el_mensaje_minimo(conexion):
    subs = [suscribir(conexion, EXCHANGE_TEST) for _ in range(5)]
    canal_pub = pub.abrir_canal(conexion, EXCHANGE_TEST)
    evento = pub.construir_evento(2, "2026-10-04T09:40:00", -33.1, -72.0)

    assert pub.publicar(canal_pub, evento, EXCHANGE_TEST) is True

    for canal, cola in subs:
        metodo, props, cuerpo = canal.basic_get(cola, auto_ack=True)
        assert metodo is not None, "el subscriber no recibió el sismo"
        assert json.loads(cuerpo) == evento
        assert props.content_type == "application/json"
    canal_pub.exchange_delete(EXCHANGE_TEST)


def test_sin_subscribers_se_detecta(conexion):
    canal_pub = pub.abrir_canal(conexion, "sismos_test_vacio")
    evento = pub.construir_evento(1, "2026-10-04T08:15:00", -20.2, -70.1)
    assert pub.publicar(canal_pub, evento, "sismos_test_vacio") is False
    canal_pub.exchange_delete("sismos_test_vacio")
