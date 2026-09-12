# RoadPulse AI

RoadPulse AI is a road-safety intelligence dashboard for analysing accident data in India. It combines a FastAPI backend, a React/Vite frontend, official government datasets, a risk-scoring service, prediction support, intervention recommendations, and scenario simulation.

The application helps users answer four questions:

1. Which State/UT or road location has the highest risk?
2. Which measurable factors contribute to that risk?
3. What does the historical or model-based outlook look like?
4. Which safety actions should be prioritised, and what could their estimated effect be?

> **Important:** Scenario results are planning estimates, not guaranteed causal effects. A risk score is not an accident probability.

## What Is Included

### Backend

- FastAPI REST API
- Official-data and demo-data loading modes
- CSV upload and column normalization
- Risk scoring and risk-level classification
- Historical trend prediction and prototype Random Forest support
- Intervention recommendations
- What-if intervention simulation
- Priority action-plan generation
- Official data processing and validation pipeline

### Frontend

The React dashboard contains these views:

- **Overview:** headline statistics, risk distribution, trend, and decision summary
- **Risk Map:** map markers when coordinates exist, otherwise a State/UT risk ranking
- **Road Intelligence:** detailed risk factors, causes, vulnerable users, and trend
- **Prediction:** future risk estimate and model signals
- **Interventions:** ranked safety recommendations
- **What-if Simulator:** estimated risk after selecting interventions
- **Priority Action Plan:** ranked actions with print and CSV download options
- **Data Upload:** preview and process a user-provided CSV
- **Model Insights:** model type, metrics, and feature importance

## Project Structure

```text
Roadpulse_AI/
├── backend/
│   ├── main.py                    # FastAPI application and API routes
│   ├── config.py                  # Environment-backed application settings
│   ├── requirements.txt           # Python dependencies
│   ├── data_pipeline/             # Download, normalize, process, and validate data
│   ├── ml/                        # Features, model service, model file, and metrics
│   ├── routers/                   # Additional route modules
│   ├── services/                  # Data, risk, official, national, and MVP services
│   └── schemas/                   # API schema package
├── data/
│   ├── raw/                       # Original source CSV files
│   ├── processed/                 # Generated analytics-ready files
│   ├── metadata/                  # Source, validation, and processing reports
│   ├── demo_accidents.csv         # Synthetic data for explicit local demo mode
│   └── intervention_library.json
├── frontend/
│   ├── src/main.jsx               # React application
│   ├── src/services/api.ts         # Frontend-to-backend API client
│   ├── src/styles.css              # Dashboard styles
│   └── package.json
├── scripts/                       # Utility scripts
├── tests/                         # Backend tests
└── README.md
```

## Requirements

Install these tools before running the project:

- Python 3.11 or newer
- Node.js 18 or newer
- npm
- Git, if cloning the repository

## Installation

Open PowerShell in the project root, then create the Python environment and install backend dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

## Run The Application

The backend and frontend run as separate processes. Keep each command in its own terminal.

### Terminal 1: backend

From the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- Application: http://localhost:8000
- Health check: http://localhost:8000/health
- Interactive API documentation: http://localhost:8000/docs

### Terminal 2: frontend

From the repository root:

```powershell
cd frontend
npm run dev
```

The dashboard will be available at http://localhost:5173.

The frontend calls `http://localhost:8000` by default. To use another backend URL, set `VITE_API_URL` before starting Vite:

```powershell
$env:VITE_API_URL="http://localhost:8000"
npm run dev
```

## Data Modes

The backend reports its active mode through `/health` and `/api/data/status`.

### Official mode

Official mode is used automatically when `data/processed/state_year_summary.csv` exists. The current processed dataset contains State/UT annual accident records and supporting official files.

In official mode:

- Risk is reported at State/UT or source-provided geographic granularity.
- Annual trends are available.
- The official source may not contain road coordinates, hourly data, causes, or road-user categories.
- The interface shows a ranked geographic table when a map cannot be supported by the source.
- Cause and vulnerability information can be shown as national supporting context when the relevant processed files exist.

### Demo mode

Demo mode is intended for local UI development only. It must be enabled explicitly:

```powershell
$env:ALLOW_DEMO_DATA="true"
python -m uvicorn backend.main:app --reload --port 8000
```

The backend then loads `data/demo_accidents.csv` when no processed official dataset is available. Demo values must not be presented as official government data.

### Upload mode

The **Data Upload** page accepts a CSV file and sends it to `POST /api/data/upload`. The backend maps recognized column names, fills missing optional fields with defaults, removes duplicate rows, and refreshes the active analytics data in memory.

Useful recognized column names include:

```text
accidents, fatalities, injuries, state, district, city,
road_name, road_segment, latitude, longitude, year, month,
hour, road_category, cause, vehicle_type, road_user_type,
weather, road_condition, lighting_condition, traffic_level
```

Common aliases such as `deaths`, `killed`, `injured`, `road`, `corridor`, `lat`, and `lon` are also supported.

## Official Data Pipeline

The repository includes raw and processed data from official Open Government Data Platform India sources, including:

- Ministry of Road Transport and Highways State/UT accident totals
- Road Accidents in India 2019 resources
- NCRB ADSI 2023 cause and mode-of-transport resources

Source metadata is recorded in `data/metadata/sources.json`.

### Process existing raw files

Place compatible official CSV files in `data/raw/`, then run:

```powershell
python -m backend.data_pipeline.process_data
python -m backend.data_pipeline.inspect_data
```

The processing command can generate files such as:

- `data/processed/state_year_summary.csv`
- `data/processed/accident_master.csv`
- `data/processed/road_category_summary.csv`
- `data/processed/cause_analysis.csv`
- `data/processed/vulnerability_analysis.csv`
- `data/processed/validation_report.json`
- `data/metadata/data_profile.json`
- `data/metadata/processing_report.json`

### Download configured data.gov.in resources

The downloader only uses credentials and resource IDs supplied through environment variables. It does not commit secrets.

```powershell
$env:DATA_GOV_API_KEY="your-api-key"
$env:DATA_GOV_RESOURCE_ACCIDENTS="resource-id"
$env:DATA_GOV_RESOURCE_CAUSES="resource-id"
$env:DATA_GOV_RESOURCE_TRANSPORT="resource-id"
python -m backend.data_pipeline.download_data
python -m backend.data_pipeline.process_data
```

If a resource ID is not configured, the downloader reports that manual download is required. Retrieval results are written to `data/metadata/retrieval.json`.

## Risk And Prediction Methodology

Risk levels use the following score ranges:

|  Score | Level    |
| -----: | :------- |
|   0-24 | Low      |
|  25-49 | Medium   |
|  50-74 | High     |
| 75-100 | Critical |

The risk service uses fields available in the loaded dataset, such as accident frequency, fatalities, injuries, fatality rate, and historical trend. Components are normalized across the available records.

Prediction behavior depends on the loaded data:

- Official annual data uses a historical trend forecast when chronological ML validation is not sufficient.
- Demo or uploaded data can use the bundled Random Forest model and calculated feature signals.
- Model feature importance describes model behavior; it does not prove causation.

## API Reference

The complete interactive reference is available at `http://localhost:8000/docs`.

### Status and data

| Method | Route                 | Purpose                                   |
| :----- | :-------------------- | :---------------------------------------- |
| GET    | `/`                 | Application metadata and active data mode |
| GET    | `/health`           | Backend and data availability check       |
| GET    | `/api/data/status`  | Current dataset status and source summary |
| GET    | `/api/data/sources` | Discovered source files and profiles      |
| POST   | `/api/data/upload`  | Process a user-provided CSV               |

### Analytics

| Method | Route                                          | Purpose                                           |
| :----- | :--------------------------------------------- | :------------------------------------------------ |
| GET    | `/api/dashboard/summary`                     | Dashboard totals, distribution, and trend         |
| GET    | `/api/locations`                             | Risk-ranked locations or State/UT records         |
| GET    | `/api/risk-map`                              | Map data or geographic ranking data               |
| GET    | `/api/locations/{location_id}`               | Full location detail                              |
| GET    | `/api/locations/{location_id}/risk`          | Risk details only                                 |
| GET    | `/api/locations/{location_id}/causes`        | Cause information                                 |
| GET    | `/api/locations/{location_id}/vulnerability` | Vulnerable-user information                       |
| GET    | `/api/locations/{location_id}/temporal`      | Annual, monthly, or hourly trends where available |
| GET    | `/api/locations/{location_id}/prediction`    | Location prediction and outlook                   |
| GET    | `/api/locations/{location_id}/interventions` | Recommended interventions                         |
| GET    | `/api/national/causes`                       | National cause context                            |
| GET    | `/api/national/vulnerability`                | National vulnerability context                    |
| GET    | `/api/action-plan`                           | Ranked operational action plan                    |
| GET    | `/api/model/metrics`                         | Model type, metrics, and feature information      |
| POST   | `/api/simulate`                              | Calculate a bounded intervention scenario         |

Example health request:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/health
```

## Testing

Run backend tests from the repository root with the virtual environment active:

```powershell
pytest
```

The tests cover health and data-status behavior, risk-level thresholds, official wide-table normalization, and validation behavior.

## Troubleshooting

### The dashboard says the backend is unavailable

1. Confirm the backend terminal is still running.
2. Open http://localhost:8000/health.
3. Confirm the frontend is using the same backend URL through `VITE_API_URL`.
4. Restart Vite after changing environment variables.

### The API reports `data_unavailable`

Either place compatible official CSV files in `data/raw/` and run the processing pipeline, or explicitly enable demo mode for local development.

### The API reports `official_pending_processing`

Raw files were found, but processed output has not been generated. Run:

```powershell
python -m backend.data_pipeline.process_data
```

### The Risk Map shows a table instead of markers

This is expected for official annual State/UT data without coordinates. The frontend switches to a geographic risk ranking rather than inventing map points.

## Data And Usage Limitations

- The application does not invent road names, coordinates, causes, hourly patterns, or road-user categories that are absent from the loaded source.
- Official data can have different years and geographic granularity depending on the source file.
- Uploaded CSV data is normalized for application use and should be checked before making operational decisions.
- Intervention effectiveness values are assumptions for scenario planning.
- Prediction output is a prototype analytical aid, not a guarantee of future crashes or risk.
- Raw source files are kept separate from generated processed outputs.

## License And Source Attribution

Refer to the repository and the source metadata in `data/metadata/sources.json` for the current project status and government dataset references. Source data remains subject to the terms of its original provider.
