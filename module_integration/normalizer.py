from .models import TrackItShipment, StandardLocation
from .adapters import AdapterShipmentA, AdapterShipmentB
from typing import Any, Dict
import time


class ShipmentNormalizer:
    
    # Mapeo de estados externos a un estándar interno (clave para la calidad)
    STATUS_MAP = {
        "EN_ALMACEN": "AT_WAREHOUSE",
        "EN_TRANSITO": "IN_TRANSIT",
        "INTENTO_DE_ENTREGA_FALLIDO": "DELIVERY_ATTEMPT_FAILED",
        "ENTREGADO": "DELIVERED",
        # Incluir otros estados...
    }

    def normalize(self, raw_data: Dict[str, Any], carrier: str) -> TrackItShipment:
        """
        Toma el payload JSON crudo, lo valida contra el adaptador correcto
        y lo convierte al modelo TrackItShipment estándar.
        """
        
        if carrier == "Simulación A":
            # 1. Validar y Adaptar (Pydantic valida el formato y los tipos)
            adapted_data = AdapterShipmentA(**raw_data)
            
            # 2. Normalizar la estructura al modelo TrackIt
            return TrackItShipment(
                tracking_id=adapted_data.tracking_number,
                carrier_name=carrier,
                normalized_status=self._map_status(adapted_data.status_code),
                friendly_status=adapted_data.status_code.replace("_", " ").title(), # Asumiendo que el código es legible
                current_location=StandardLocation(
                    latitude=adapted_data.location_lat,
                    longitude=adapted_data.location_lng
                ),
                last_update=time.time(), # Usar el timestamp de recepción
                origin=adapted_data.origin,
                destination=adapted_data.destination
            )
            
        elif carrier == "Simulación B":
            # 1. Validar y Adaptar
            adapted_data = AdapterShipmentB(**raw_data)
            
            # 2. Normalizar
            return TrackItShipment(
                tracking_id=adapted_data.id_seguimiento,
                carrier_name=carrier,
                normalized_status=self._map_status(adapted_data.estado),
                friendly_status=adapted_data.estado,
                current_location=StandardLocation(
                    latitude=adapted_data.ubicacion.latitud,
                    longitude=adapted_data.ubicacion.longitud
                ),
                last_update=time.time(),
                origin=adapted_data.ubicacion.origin if hasattr(adapted_data.ubicacion, 'origin') else None,
                destination=adapted_data.ubicacion.destination if hasattr(adapted_data.ubicacion, 'destination') else None
            )
        
        else:
            raise ValueError(f"Portador desconocido: {carrier}")

    def _map_status(self, external_status: str) -> str:
        """Helper para mapear el estado externo al estándar interno."""
        # Limpiar y convertir a mayúsculas para la búsqueda en el mapa
        key = external_status.upper().replace(" ", "_")
        return self.STATUS_MAP.get(key, "UNKNOWN")


# Ejemplo de uso:
# normalizer = ShipmentNormalizer()
# datos_a = {"tracking_number": "TRACK0001", "status_code": "EN_TRANSITO", "progress_details": "...", "location_lat": 34.0, "location_lng": -118.0}
# shipment_estandar = normalizer.normalize(datos_a, "Simulación A")
# print(shipment_estandar.json(indent=2))