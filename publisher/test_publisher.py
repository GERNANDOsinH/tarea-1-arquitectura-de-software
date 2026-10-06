import json

import pytest
from pika.exceptions import UnroutableError

import publisher as pub


def test_evento_tiene_solo_campos_minimos():
    e = pub.construir_evento(1, "2026-10-04T12:30:00", -33.04, -71.62)
    assert tuple(e) == pub.CAMPOS_MENSAJE
    assert e == {"id": 1, "datetime": "2026-10-04T12:30:00", "latitude": -33.04, "longitude": -71.62}


@pytest.mark.parametrize("lat,lon", [(91, 0), (-91, 0), (0, 181), (0, -181)])
def test_coordenadas_invalidas(lat, lon):
    with pytest.raises(ValueError):
        pub.construir_evento(1, "2026-10-04T12:30:00", lat, lon)


def test_archivo_de_la_api_se_reduce_a_mensaje_minimo():
    eventos = pub.cargar_sismos(pub.ARCHIVO_API)
    assert eventos
    assert all(tuple(e) == pub.CAMPOS_MENSAJE for e in eventos)


def test_archivo_de_prueba():
    eventos = pub.cargar_sismos(pub.ARCHIVO_PRUEBA)
    assert [e["id"] for e in eventos] == [1, 2, 3, 4, 5, 6]


def test_linea_invalida(tmp_path):
    f = tmp_path / "s.txt"
    f.write_text("1,5.0,10\n")
    with pytest.raises(ValueError):
        pub.cargar_sismos(f)


def test_serializacion_es_json_compacto():
    e = pub.construir_evento(7, "2026-01-01T00:00:00", -1.5, 2.5)
    assert json.loads(pub.serializar(e)) == e


class CanalFalso:
    def __init__(self, error=None):
        self.error, self.llamadas = error, []

    def basic_publish(self, **kw):
        if self.error:
            raise self.error
        self.llamadas.append(kw)


def test_publicar_usa_fanout_sin_routing_key():
    c = CanalFalso()
    e = pub.construir_evento(1, "2026-10-04T12:30:00", -1, 1)
    assert pub.publicar(c, e) is True
    kw = c.llamadas[0]
    assert kw["exchange"] == pub.EXCHANGE and kw["routing_key"] == ""
    assert kw["mandatory"] is True
    assert json.loads(kw["body"]) == e


def test_publicar_sin_subscribers_no_revienta():
    e = pub.construir_evento(1, "2026-10-04T12:30:00", -1, 1)
    assert pub.publicar(CanalFalso(UnroutableError([])), e) is False


def test_lat_sin_lon_es_error():
    with pytest.raises(SystemExit):
        pub.parsear_args(["--lat", "-30"])
