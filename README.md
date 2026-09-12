# RoadPulse AI

**Predict. Explain. Prevent. Prioritize.**

RoadPulse AI is a road-safety intelligence application for analysing official Indian road-accident data at the geographic granularity actually supplied by the source. The production data path is official State/UT annual data from the Open Government Data Platform India. The application does not invent road names, coordinates, hourly patterns, causes, or road-user categories when the loaded source does not contain them.

## Data policy

Official mode is the default. The application refuses to load `data/demo_accidents.csv` unless `ALLOW_DEMO_DATA=true` is explicitly set. With no official file present, `/health` reports `data_unavailable`, `/api/data/status` explains the missing file, and analytics endpoints return HTTP 503 rather than silently showing synthetic results.

The official catalog currently configured is:

- [State/UT-wise Total Number of Road Accidents in India from 2016 to 2019](https://www.data.gov.in/resource/stateut-wise-total-number-road-accidents-india-2016-2019), Ministry of Road Transport and Highways, annual State/UT granularity.
- [Road Accidents in India 2019](https://www.data.gov.in/catalog/road-accidents-india-2019), Ministry of Road Transport and Highways.
- [ADSI 2023](https://www.data.gov.in/catalog/accidental-deaths-suicides-india-adsi-2023), National Crime Records Bureau.

Source metadata is stored in `data/metadata/sources.json`. Raw government files are never modified. Processed outputs include provenance columns such as `source_name`, `source_url`, `source_year`, and `source_granularity`.

## Load official data

Option A, manual download:

1. Download the official State/UT CSV from the MoRTH data.gov.in resource.
2. Save it as `data/raw/morth_accidents.csv`.
3. Run:

```powershell
.\.venv\Scripts\activate
python -m backend.data_pipeline.process_data
python -m backend.data_pipeline.inspect_data
```

Option B, configured API download:

```powershell
$env:DATA_GOV_API_KEY="your-key"
$env:DATA_GOV_RESOURCE_ACCIDENTS="resource-id-from-data.gov.in"
python -m backend.data_pipeline.download_data
python -m backend.data_pipeline.process_data
```

The API key and resource IDs are environment variables only. They are not committed. Cause and transport datasets can be configured with `DATA_GOV_RESOURCE_CAUSES` and `DATA_GOV_RESOURCE_TRANSPORT`; if they are absent, the UI reports those analyses as unavailable instead of fabricating them.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API documentation is at `http://localhost:8000/docs`.

## Pipeline

- `backend/data_pipeline/download_data.py` caches configured official data.gov.in API downloads and records retrieval status.
- `backend/data_pipeline/inspect_data.py` writes `data/metadata/data_profile.json` with rows, columns, types, missing values, and granularity.
- `backend/data_pipeline/normalize.py` handles common official column aliases and wide State/UT year tables.
- `backend/data_pipeline/validate.py` checks negative measures, invalid years, missing states, and duplicates.
- `backend/data_pipeline/process_data.py` writes `data/processed/state_year_summary.csv` without changing raw files.
- `backend/services/official_service.py` calculates State/UT risk and annual trend analytics from processed official data.

## Official-data API

- `GET /health`
- `GET /api/data/status`
- `GET /api/data/sources`
- `GET /api/dashboard/summary`
- `GET /api/regions` and `GET /api/locations` compatibility response
- `GET /api/regions/{id}/risk`, `/causes`, `/vulnerability`, `/trend`, `/prediction`, `/interventions`
- `GET /api/locations/{id}` compatibility response
- `POST /api/simulate`
- `GET /api/action-plan`
- `GET /api/model/metrics`

State-level official data is shown as State/UT intelligence. The application does not render road-segment markers when the source has no coordinates. If the source is annual, hourly and monthly views are omitted.

## Risk methodology

The State/UT score uses only available measurable fields. Available components include accident frequency, fatalities, injuries, fatality rate, and historical trend. Components are normalized across the loaded State/UT records and exposed in the API. Risk levels are Low `0-24`, Medium `25-49`, High `50-74`, and Critical `75-100`.

## Prediction and simulation

Prediction falls back to a clearly labelled `Historical Trend Forecast` when annual State/UT history is insufficient for chronological ML validation. No accuracy or causal claim is invented. Intervention effects are planning assumptions only. The simulator labels outputs `SCENARIO-BASED ESTIMATE` and separates observed official data from assumed effectiveness.

## Explicit demo mode

For local UI work only, synthetic data can be enabled explicitly:

```powershell
$env:ALLOW_DEMO_DATA="true"
uvicorn backend.main:app --reload --port 8000
```

Synthetic values must not be described as government data or used as official analysis.
