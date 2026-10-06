# Publisher – Notificador Sismos

Publica sismos (mensaje mínimo `id, datetime, latitude, longitude`) en el exchange fanout `sismos` de RabbitMQ.
Lee los sismos del mismo archivo que usa la API (`api/sismos.txt`). Contrato: [../contrato_mensaje.md](../contrato_mensaje.md).

## Ejecución
```bash
# desde la raíz del repo
docker compose up -d rabbitmq
cd publisher
pip install -r requirements.txt

python publisher.py --todos                   # todos los sismos de api/sismos.txt
python publisher.py --id 2                    # solo el sismo 2
python publisher.py --todos --prueba          # los 6 sismos de publisher/sismos_prueba.txt
python publisher.py --lat -33.1 --lon -72.0 --id-manual 2   # sismo manual
```
Variables: `RABBITMQ_URL` (por defecto `amqp://guest:guest@localhost:5672/%2F`), `SISMOS_EXCHANGE`.
Consola de RabbitMQ: http://localhost:15672 (guest/guest).

## Tests
```bash
python -m pytest -q
```
Los tests de `test_integration.py` usan un RabbitMQ real (`docker compose up -d rabbitmq`); si no hay broker se omiten. También corren en GitHub Actions (`.github/workflows/publisher.yml`).

## Sismos de prueba y resultado esperado (radio 500 km, haversine R = 6371 km)
| id | Epicentro | Subscribers interesados |
|---|---|---|
| 1 | -20.2, -70.1 | Arica (193 km) |
| 2 | -33.1, -72.0 | Coquimbo (355), Valparaíso (35), Concepción (425) |
| 3 | -53.0, -71.0 | Punta Arenas (19) |
| 4 | -23.65, -70.4 | ninguno (Arica a 576 km) |
| 5 | -36.5, -73.2 | Valparaíso (411), Concepción (39) |
| 6 | -31.5, -71.5 | Coquimbo (173), Valparaíso (171) |
