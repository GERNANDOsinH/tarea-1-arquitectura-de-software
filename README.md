# Tarea 1 Arquitectura de Software

## Integrantes:
- Fernando Hernández 202273056-0
- Martin Muñoz
- Martin

## Instrucciones Ejecución

### API

**Activación Entorno Virtual(opcional: en caso de querer aislar del resto del sistema)**
```bash
python -m venv venv
venv\Scripts\activate
```
**Instalación Dependencias**
```bash
pip install -r requirements.txt
```

**Ejecución API Rest**
```bash
uvicorn main:app --reload
```

### Subscriber

### Publisher

Requiere Docker (RabbitMQ) y Python 3.10+. Detalle en [publisher/README.md](publisher/README.md).
```bash
docker compose up -d rabbitmq
cd publisher
pip install -r requirements.txt
python publisher.py --todos
```