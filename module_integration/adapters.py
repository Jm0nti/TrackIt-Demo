from pydantic import BaseModel, Field

# --- Adaptador para "Simulación A" ---
# Formato: {"location_lat": ..., "location_lng": ...}
class AdapterShipmentA(BaseModel):
    tracking_number: str = Field(alias="tracking_number") # Usamos Field(alias) si la clave es diferente en la fuente
    status_code: str
    progress_details: str
    location_lat: float
    location_lng: float

# --- Adaptador para "Simulación B" ---
# Formato: {"ubicacion": {"latitud": ..., "longitud": ...}}
class UbicacionB(BaseModel):
    latitud: float
    longitud: float
    
class AdapterShipmentB(BaseModel):
    id_seguimiento: str
    estado: str
    detalles: str
    ubicacion: UbicacionB