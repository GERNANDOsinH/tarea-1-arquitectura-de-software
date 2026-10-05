from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from datetime import datetime

class Sismo(BaseModel):
    id: int
    magnitude: float
    depth: float
    location: str
    datetime: datetime
    latitude: float
    longitude: float

DATA: list[Sismo] = []

# Función que se ejecuta antes de levantar la API (usando lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    archivo_path = "sismos.txt"    
    try:
        with open(archivo_path, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue

                partes = linea.split(",")
                if len(partes) == 7:
                    sismo = Sismo(
                        id=int(partes[0]),
                        magnitude=float(partes[1]),
                        depth=float(partes[2]),
                        location=partes[3],
                        datetime=datetime.fromisoformat(partes[4]),
                        latitude=float(partes[5]),
                        longitude=float(partes[6])
                    )
                    DATA.append(sismo)
        print(f"¡Se cargaron {len(DATA)} sismos exitosamente!")
    except FileNotFoundError:
        print(f"Aviso: El archivo '{archivo_path}' no fue encontrado. La lista DATA iniciará vacía.")
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")

    yield
    
    DATA.clear()

app = FastAPI(lifespan=lifespan)

@app.get("/{id}")
def get(id: int):
    if id < 0 or len(DATA) <= id:
        return {
            "status": "failure",
            "description": "Ingrese un identificador dentro de un rango válido."
        }

    elem = DATA[id]

    return {
        "status": "success",
        "data": {
            "id": elem.id,
            "magnitude": f"{elem.magnitude:.1f}",
            "depth": f"{elem.depth:.1f} km",
            "location": elem.location,
            "datetime": elem.datetime,
            "latitude": f"{elem.latitude:.1f}",
            "longitude": f"{elem.longitude:.1f}",
        }
    }