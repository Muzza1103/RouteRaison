# RouteRaison

RouteRaison is a demonstration-oriented web application integrating argumentation-based decision making into a route planning workflow.

The system separates:
1. Context construction
2. Argumentation-based decision
3. Route computation and visualization

It is designed as an educational prototype highlighting explainability in routing strategies.

---

## Project Structure

- `backend/` – FastAPI application (context building, ai-raison integration, ORS routing)
- `frontend/` – React application (interactive map and UI)

---

## Prerequisites

- Python 3.10+
- Node.js (>=18 recommended)
- npm
- API keys for:
  - OpenRouteService
  - TomTom
  - OpenWeather (if enabled)

---

## Environment Configuration

1. Copy `.env.example` to `.env` and insert your own API keys and AI_RAISON app ID: 

```
OPENWEATHER_API_KEY=xxxxx
ORS_API_KEY=xxxxx
TOMTOM_API_KEY=xxxxx
AI_RAISON_API_KEY=xxxxx
AI_RAISON_APP_ID=xxxxx
```

Make sure all required keys are properly set before running the backend.

---

## Running the Backend

From the `backend/` directory:

``` bash
python main.py
```

The FastAPI server will start automatically (by default:
http://127.0.0.1:8000).

You can verify it is running by visiting:

http://127.0.0.1:8000/health

---

## Running the Frontend

From the `frontend/` directory:

``` bash
npm install
npm run dev
```

The development server will start and provide a local URL (usually
http://localhost:5173).

---

## How It Works

1.  The frontend sends a `/plan` request.
2.  The backend builds contextual scenarios.
3.  The ai-raison engine selects routing strategy(ies).
4.  The selected strategy is compiled into ORS parameters.
5.  The route is returned as GeoJSON and displayed on the map.

---

## Notes

-   Traffic enrichment depends on the availability of the TomTom API.
-   This project was developed as part of an academic coursework exploring argumentation-based decision making in route planning.
-   External API availability may affect runtime behavior.
