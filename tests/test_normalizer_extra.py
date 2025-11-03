from module_integration.normalizer import ShipmentNormalizer

def test_normalizer_simulacion_a_y_b():
    norm = ShipmentNormalizer()
    raw_a = {
        "tracking_number": "TRACKA",
        "status_code": "EN_TRANSITO",
        "progress_details": "...",
        "location_lat": 10.0, "location_lng": -75.0,
        "origin": "Medellín", "destination": "Bogotá",
    }
    a = norm.normalize(raw_a, "Simulación A")
    assert a.tracking_id == "TRACKA"
    assert a.current_location.latitude == 10.0

    raw_b = {
        "id_seguimiento": "TRACKB",
        "estado": "Entregado",
        "detalles": "...",
        "ubicacion": {"latitud": 6.3, "longitud": -75.6, "origin": "Cali", "destination": "Barranquilla"},
    }
    b = norm.normalize(raw_b, "Simulación B")
    assert b.tracking_id == "TRACKB"
    assert b.current_location.longitude == -75.6

def test_normalizer_carrier_desconocido():
    norm = ShipmentNormalizer()
    try:
        norm.normalize({"foo": "bar"}, "X-Carrier")
        assert False, "Debe lanzar ValueError"
    except ValueError:
        assert True
