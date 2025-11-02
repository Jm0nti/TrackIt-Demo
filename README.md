# TrackIt - Demo

Proyecto demo que simula un módulo de integración para seguimiento de envíos (TrackIt). Incluye una API simulada (FastAPI) que normaliza payloads de distintos carriers y un frontend simple (HTML + JS) que consume la API y muestra el estado normalizado.

## Estructura del repositorio

- `API.py` — Servidor FastAPI que genera datos mock, normaliza usando `module_integration` y expone endpoints para consulta.
- `requirements.txt` — Dependencias Python (pydantic, fastapi, uvicorn, python-multipart).
- `module_integration/`
  - `adapters.py` — Modelos Pydantic para validar formatos externos (Simulación Carriers A y B).
  - `models.py` — Modelos internos estandarizados (`TrackItShipment`, `StandardLocation`).
  - `normalizer.py` — Lógica para convertir payloads externos a `TrackItShipment`.
- `client/`
  - `index.html` — Frontend estático (Tailwind via CDN) y tarjeta de resultados.
  - `trackit.js` — Lógica del cliente: consulta la API, renderiza resultados y maneja polling.
  - `styles.css` — Estilos personalizados.

## Objetivo

Permitir a desarrolladores y QA explorar y probar la normalización de datos de envíos. La API genera envíos mock (100 por defecto) en dos formatos distintos, asigna aleatoriamente `origin` y `destination`, y entrega un modelo normalizado que el frontend consume.

## Requisitos

- Python 3.8+
- (Opcional) Navegador moderno para abrir `client/index.html`.

Instalar dependencias:

PowerShell:

```powershell
python -m venv .venv
..venv\Scripts\Activate.ps1 # Windows PowerShell
python -m pip install -r requirements.txt
```

## Cómo ejecutar el backend

Desde la raíz del proyecto (donde está `api.py`):

PowerShell:

```powershell
# Inicia FastAPI con Uvicorn
uvicorn api:app --reload
```

Por defecto la app se servirá en `http://127.0.0.1:8000`.

Notas:
- CORS está configurado para permitir cualquier origen (útil para abrir `client/index.html` desde `file://` durante desarrollo).
- La API simula latencia y actualizaciones aleatorias; puede devolver códigos 404, 429 o 500 para probar manejo de errores en el frontend.

## Endpoints principales

- `GET /api/v1/track/{tracking_id}`
  - Simula la consulta a un carrier, normaliza el resultado con `ShipmentNormalizer` y devuelve un objeto `TrackItShipment`.
  - Respuestas de ejemplo: 200 (objeto normalizado), 404 (no existe), 429 (rate limit) o 500 (error en normalización).

- `GET /api/trackit/standard/{tracking_id}`
  - Devuelve el envío ya normalizado y almacenado internamente si fue consultado previamente.

- `POST /api/v1/webhook_simulator`
  - Endpoint de ejemplo que simula recibir un webhook (no procesa en este demo, responde con mensaje).

## Forma del objeto normalizado (`TrackItShipment`)

Campos relevantes (JSON retornado):

- `tracking_id` (string)
- `normalized_status` (string) — Ej: `DELIVERED`, `IN_TRANSIT`, `AT_WAREHOUSE`, `UNKNOWN`.
- `friendly_status` (string) — Texto legible por humanos.
- `current_location` (object) — `{ "latitude": float, "longitude": float }`.
- `carrier_name` (string)
- `last_update` (float) — timestamp (segundos desde epoch).
- `origin` (string | null) — ciudad de origen si disponible.
- `destination` (string | null) — ciudad destino si disponible.

El frontend ya consume estos campos y muestra `origin` y `destination` en la tarjeta.

## Frontend

- Abrir `client/index.html` en el navegador. Si prefieres servirlo por HTTP, puedes usar un servidor ligero (p. ej. `python -m http.server 8080` desde la carpeta `client/`).
- Ingresar un ID de seguimiento (por ejemplo `TRACK0001`) y presionar "Buscar Envío". Después de la primera búsqueda exitosa, el cliente inicia polling cada 5s para actualizaciones.

PowerShell (servir carpeta client):

```powershell
cd client
python -m http.server 8080
# Luego abrir http://localhost:8080
```

## Pruebas sugeridas (para equipo de QA / devs)

Ideas de pruebas unitarias e integración:

1. Normalizer unit tests
   - Casos para `ShipmentNormalizer.normalize` con payloads A y B (validos y con campos faltantes).
   - Verificar que `origin`/`destination` se mapean correctamente.
2. Adapter validation
   - Probar `AdapterShipmentA` y `AdapterShipmentB` con datos mal formateados (tipos incorrectos) y esperar excepciones de Pydantic.
3. Endpoint tests (con `TestClient` de FastAPI)
   - Llamar a `/api/v1/track/{id}` y comprobar 200 y contenido esperado.
   - Forzar condiciones de error (por ejemplo, simular múltiples requests desde la misma IP para 429).