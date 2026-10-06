# Contrato del mensaje (publisher ↔ subscribers ↔ API)

Los nombres de campo siguen los de la API (`api/main.py`), para que el mensaje y el detalle usen el mismo vocabulario.

## Mensajería

| Elemento | Valor |
|---|---|
| Broker | RabbitMQ (`amqp://guest:guest@localhost:5672/%2F`) |
| Exchange | `sismos`, tipo **fanout**, durable |
| Routing key | vacía (se ignora en fanout) |
| Cola | **la declara cada subscriber** (una por ciudad, p. ej. `sismos.arica`) y la enlaza al exchange `sismos` |
| Formato | JSON UTF‑8, `content_type: application/json`, mensaje persistente |

Fanout porque todos los subscribers reciben todos los sismos y cada uno filtra por distancia; el publisher no sabe quién escucha.
Si ninguna cola está enlazada cuando se publica, el mensaje se descarta (el publisher lo avisa con un warning), así que **levanten los subscribers antes de publicar**.

## Cuerpo del mensaje (información mínima)

```json
{"id": 2, "datetime": "2026-10-04T09:40:00", "latitude": -33.1, "longitude": -72.0}
```

| Campo | Tipo | Uso |
|---|---|---|
| `id` | entero | Identificador del sismo; es lo que el subscriber usa para pedir el detalle a la API |
| `datetime` | string ISO 8601 | Cuándo ocurrió (igual que en la API) |
| `latitude`, `longitude` | número, grados decimales | Lo único que necesita el subscriber para calcular distancia y decidir si le interesa (< 500 km) |

Se deja fuera a propósito magnitud, profundidad y ubicación: no intervienen en la decisión y se obtienen de la API (pull) solo si el sismo interesa.
