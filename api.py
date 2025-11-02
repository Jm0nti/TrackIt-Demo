# API.py - Simula una API que otorga datos de envíos para el posterior procesamiento de TrackIt

from module_integration.models import TrackItShipment
from fastapi.middleware.cors import CORSMiddleware
from module_integration.normalizer import ShipmentNormalizer
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import time
import random
from typing import Dict, Any

app = FastAPI()

# --- CONFIGURACIÓN DE CORS (SOLUCIÓN AL ERROR 'Failed to fetch') ---
# Esto permite que tu index.html local (origen "file://") acceda a la API
origins = ["*"] # Permitir cualquier origen (ideal para desarrollo)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"], # Permitir todos los headers
)



normalizer = ShipmentNormalizer() # Instancia del normalizador

# --- ALMACENES DE DATOS EN MEMORIA (No Persistentes) ---

# Simula la base de datos de las logísticas (Datos Crudos, Externos)
MOCK_EXTERNAL_DATABASE: Dict[str, Dict[str, Any]] = {} 

# Simula la base de datos de TrackIt (Datos Normalizados, Internos)
TRACKIT_STANDARD_DATABASE: Dict[str, TrackItShipment] = {} 

# --- Lógica de Inicialización de Datos ---

def generate_mock_shipments(count: int = 100):
    """Genera una base de datos inicial de envíos simulados en formatos A y B."""
    statuses_a = ["DELIVERED", "IN_TRANSIT", "AT_WAREHOUSE"]
    statuses_b = ["Entregado", "En Tránsito", "En Almacén"]
    
    for i in range(1, count + 1):
        tracking_id = f"TRACK{i:04d}"
        
        if i % 2 == 0:
            # Simulación A (Formato con códigos de estado en inglés y lat/lng separados)
            raw_data = {
                "tracking_number": tracking_id,
                "status_code": random.choice(statuses_a),
                "progress_details": f"Paquete en el área metropolitana {i}.",
                "location_lat": random.uniform(30.0, 40.0),
                "location_lng": random.uniform(-100.0, -80.0),
                "carrier_format": "Simulación A"
            }
        else:
            # Simulación B (Formato con códigos de estado en español y ubicación anidada)
            raw_data = {
                "id_seguimiento": tracking_id,
                "estado": random.choice(statuses_b),
                "detalles": f"El pedido está siendo procesado en la bodega {i}.",
                "ubicacion": {
                    "latitud": random.uniform(30.0, 40.0),
                    "longitud": random.uniform(-100.0, -80.0),
                },
                "carrier_format": "Simulación B"
            }
        
        MOCK_EXTERNAL_DATABASE[tracking_id] = raw_data

# Generar datos al iniciar
generate_mock_shipments()

# --- Lógica de Simulación de Tiempo Real y Latencia ---

async def simulate_time_and_latency():
    """Simula latencia intencional y actualiza algunos envíos de forma simple."""
    # Simulación de Latencia (10% de probabilidad de 1.5 segundos)
    if random.random() < 0.10: 
        time.sleep(1.5)

    # Simulación de Actualización de Ubicación/Estado (Movimiento)
    if random.random() < 0.05: 
        tracking_id = random.choice(list(MOCK_EXTERNAL_DATABASE.keys()))
        data = MOCK_EXTERNAL_DATABASE[tracking_id]

        if data["carrier_format"] == "Simulación A":
            if data["status_code"] == "AT_WAREHOUSE":
                data["status_code"] = "IN_TRANSIT"
            data["location_lat"] += random.uniform(-0.01, 0.01)
            data["location_lng"] += random.uniform(-0.01, 0.01)
        
        elif data["carrier_format"] == "Simulación B":
            if data["estado"] == "En Almacén":
                data["estado"] = "En Tránsito"
            data["ubicacion"]["latitud"] += random.uniform(-0.01, 0.01)
            data["ubicacion"]["longitud"] += random.uniform(-0.01, 0.01)


# --- Lógica de Rate Limiting ---

REQUEST_COUNTS: Dict[str, int] = {}
RATE_LIMIT = 50 

# Limpia el contador de solicitudes cada minuto (para simular el límite por minuto)
@app.on_event("startup")
async def startup_event():
    import asyncio
    async def reset_counts():
        while True:
            await asyncio.sleep(60) # Espera 60 segundos
            REQUEST_COUNTS.clear()
            
    asyncio.create_task(reset_counts())


# -----------------------------------------------------------
# IV. ENDPOINTS (Simulando la interacción)
# -----------------------------------------------------------
@app.get("/")
def read_root():
    """Confirma que el servicio TrackIt Mock API está en funcionamiento."""
    return {"message": "TrackIt Mock API is running successfully. Use /api/v1/track/{id} for shipment tracking."}

@app.get("/api/v1/track/{tracking_id}")
async def get_shipment_status(tracking_id: str, request: Request):
    """
    Simula la consulta a una API externa, aplica Normalización
    y almacena el resultado en la 'BD' de TrackIt.
    """
    
    # 1. Simulación de Error: Rate Limiting
    client_ip = request.client.host
    REQUEST_COUNTS[client_ip] = REQUEST_COUNTS.get(client_ip, 0) + 1
    if REQUEST_COUNTS[client_ip] > RATE_LIMIT:
        raise HTTPException(status_code=429, detail="429 Too Many Requests: Límite de consultas excedido.")
    
    # 2. Simulación de Tiempo Real y Latencia
    await simulate_time_and_latency()

    # 3. Obtener datos crudos de la simulación externa (Simulación de Llamada a API Externa)
    if tracking_id not in MOCK_EXTERNAL_DATABASE:
        # Simulación de Error: 404
        raise HTTPException(status_code=404, detail=f"404 Not Found: El ID {tracking_id} no existe en la logística.")

    # Copiamos para no modificar accidentalmente la BD externa con pop
    raw_data = MOCK_EXTERNAL_DATABASE[tracking_id].copy() 
    carrier_format = raw_data.pop("carrier_format") 
    
    # 4. PROCESO DE NORMALIZACIÓN (El corazón de tu módulo de integración)
    try:
        # Pydantic valida los datos y la clase Normalizer los mapea al estándar TrackIt
        standard_shipment = normalizer.normalize(raw_data, carrier_format)
        
    except Exception as e:
        # Simulación de Error: 500 (Fallo en procesamiento de datos)
        print(f"ERROR FATAL EN NORMALIZACIÓN para ID {tracking_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo crítico al procesar datos externos: {type(e).__name__} - {str(e)}")
        
    # 5. Almacenamiento Interno (Simulación de Base de Datos de TrackIt)
    TRACKIT_STANDARD_DATABASE[tracking_id] = standard_shipment
    
    # Devolver el objeto estandarizado
    return standard_shipment


@app.get("/api/trackit/standard/{tracking_id}")
async def get_normalized_shipment(tracking_id: str):
    """
    Endpoint interno para consultar el estado del envío YA NORMALIZADO 
    (Simula la consulta que haría el frontend/otros módulos de TrackIt).
    """
    if tracking_id not in TRACKIT_STANDARD_DATABASE:
        raise HTTPException(status_code=404, detail="El envío no ha sido consultado o no existe en el almacén de TrackIt.")
    
    return TRACKIT_STANDARD_DATABASE[tracking_id]


@app.post("/api/v1/webhook_simulator")
async def simulate_webhook_push(data: Dict[str, Any]):
    """
    Simula la recepción de un Webhook por parte de TU módulo de integración.
    En un entorno real, tu módulo aquí desencadenaría una normalización y notificación.
    """
    if "tracking_id" in data and "new_status" in data:
        # En este punto, tu módulo de integración debería tomar la data, normalizarla y 
        # actualizar TRACKIT_STANDARD_DATABASE
        return {"message": "Webhook recibido. Tu módulo de integración procesaría estos datos asíncronamente."}
    
    raise HTTPException(status_code=400, detail="Faltan datos de seguimiento en el payload del webhook.")