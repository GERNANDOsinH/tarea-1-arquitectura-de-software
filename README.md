# Tarea 1 Arquitectura de Software

## Integrantes:
- Fernando Hernández 202273056-0
- Martin Muñoz
- Martin Chacon 202023012-9

## Instrucciones Ejecución

### API

```bash
cd api
python -m venv venv
source .venv/Scripts/activate          # opcional: aísla las dependencias del resto del sistema
pip install -r requirements.txt
uvicorn main:app --reload
```
La API carga `api/sismos.txt` al arrancar (ruta relativa), por eso `uvicorn` debe ejecutarse estando dentro de `api/`. Queda escuchando en `http://localhost:8000`.

### Subscriber

Requiere RabbitMQ (`docker compose up -d rabbitmq`) y la API corriendo (ver arriba).

```bash
cd subscriber
pip install -r requirements.txt
```

Para levantar los 5 subscribers (Arica, Coquimbo, Valparaíso, Concepción, Punta Arenas) con sus coordenadas reales, desde la raíz del repo:
```bash
bash iniciar_ciudades.sh    # Git Bash / WSL en Windows
```
Para levantar uno solo manualmente (ejemplo Valparaíso), en PowerShell:
```powershell
$env:NAME="Valparaíso"; $env:LAT="-33.036"; $env:LON="-71.62963"
$env:RABBITMQ_HOST="localhost"; $env:API_URL="http://localhost:8000"
python subscriber.py
```

### Publisher

Requiere Docker (RabbitMQ) y Python 3.10+. Detalle en [publisher/README.md](publisher/README.md).
```bash
docker compose up -d rabbitmq
cd publisher
pip install -r requirements.txt
python publisher.py --todos
```

## Consideraciones de la implementación

- Mensajería: exchange `sismos` tipo **fanout** en RabbitMQ; el publisher no conoce a los subscribers y cada subscriber decide si el sismo le interesa (< 500 km, haversine) antes de pedir el detalle a la API. Contrato completo del mensaje en [contrato_mensaje.md](contrato_mensaje.md).
- La API mantiene los sismos **en memoria**, cargados desde `api/sismos.txt` al iniciar (sin base de datos, según lo permitido por el enunciado).
- Orden de arranque recomendado: RabbitMQ → API → subscribers → publisher (si un subscriber no está levantado y enlazado al exchange cuando se publica, pierde ese mensaje).
- Solo RabbitMQ corre en Docker ([docker-compose.yml](docker-compose.yml)); API, subscribers y publisher corren como procesos Python locales.
