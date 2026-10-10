# Tarea 1 Arquitectura de Software

## Integrantes:
- Fernando Hernández 202273056-0
- Martin Muñoz 202273100-1
- Martin Chacon 202023012-9

## Instrucciones Ejecución

### 1. Preparación del Entorno y API
En una terminal, encontrándonos en la carpeta raíz:
```bash
python -m venv venv
docker compose up -d rabbitmq

venv\Scripts\activate           # Para Windows (cmd/PowerShell)
source venv/Scripts/activate    # Para Windows con Git Bash
source venv/bin/activate        # Para Linux/Mac

pip install -r requirements.txt
cd api
uvicorn main:app --reload
```
*Nota: La API carga `api/sismos.txt` al arrancar (ruta relativa), por eso `uvicorn` debe ejecutarse estando dentro de `api/`. Queda escuchando en `http://localhost:8000`.*

### 2. Iniciar Subscribers (Ciudades)
En otra ventana de la terminal, encontrándonos en la carpeta raíz se debe iniciar la escucha de las ciudades:
```bash
venv\Scripts\activate           # Para Windows (cmd/PowerShell)
source venv/Scripts/activate    # Para Windows con Git Bash
source venv/bin/activate        # Para Linux/Mac

bash iniciar_ciudades.sh        # Para Git Bash / WSL en Windows
./iniciar_ciudades.sh           # Para Linux
```

### 3. Publicar Sismos
Finalmente (encontrándonos en la carpeta raíz nuevamente), en una tercera ventana de la terminal, para realizar la publicación de los sismos debemos hacer:
```bash
venv\Scripts\activate           # Para Windows (cmd/PowerShell)
source venv/Scripts/activate    # Para Windows con Git Bash
source venv/bin/activate        # Para Linux/Mac

cd publisher
python publisher.py --todos     # esta linea lee todos los sismos que se encuentran en api/sismos.txt
```
En caso de solo leer un sismo en particular se puede usar (esto se puede leer en profundidad en el README dentro del directorio publisher):
```bash
python publisher.py --id 2      # esta linea solamente lee el sismo con id 2
```

## Consideraciones de la implementación

- Mensajería: exchange `sismos` tipo **fanout** en RabbitMQ; el publisher no conoce a los subscribers y cada subscriber decide si el sismo le interesa (< 500 km, haversine) antes de pedir el detalle a la API. Contrato completo del mensaje en [contrato_mensaje.md](contrato_mensaje.md).
- La API mantiene los sismos **en memoria**, cargados desde `api/sismos.txt` al iniciar (sin base de datos, según lo permitido por el enunciado).
- Orden de arranque recomendado: RabbitMQ → API → subscribers → publisher (si un subscriber no está levantado y enlazado al exchange cuando se publica, pierde ese mensaje).
- Solo RabbitMQ corre en Docker ([docker-compose.yml](docker-compose.yml)); API, subscribers y publisher corren como procesos Python locales.