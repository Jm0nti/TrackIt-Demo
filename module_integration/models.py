from pydantic import BaseModel
from typing import List, Dict

# Modelo de Ubicación Estandarizado
class StandardLocation(BaseModel):
    latitude: float
    longitude: float

# Modelo de Envío Estandarizado para toda la aplicación TrackIt
class TrackItShipment(BaseModel):
    tracking_id: str
    normalized_status: str # Ejemplo: "DELIVERED", "IN_TRANSIT", "AT_WAREHOUSE"
    friendly_status: str   # Ejemplo: "Entregado", "En tránsito"
    current_location: StandardLocation
    carrier_name: str      # Para identificar la fuente (e.g., "Logística A", "Logística B")
    last_update: float     # Timestamp para control de tiempo real