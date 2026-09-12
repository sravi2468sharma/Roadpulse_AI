# Road Safety Intelligence Network API

Transform roads from danger zones into safe, predictable infrastructure by creating a worldwide road safety intelligence network that prevents accidents before they occur through AI-powered predictive analytics.

## Product Vision

This application provides a comprehensive backend API for managing road safety incidents, performing predictive analytics, and generating safety reports. It serves traffic authority managers, urban planners, emergency response coordinators, and insurance companies.

## Target Audience

**Primary Users:**
- Traffic authority managers
- Urban planners
- Emergency response coordinators
- Insurance companies

**Secondary Users:**
- Commuters (through mobile applications)

## Core Features

- **Incident Management**: Create, read, update, and delete road incident reports
- **Analytics**: AI-powered risk analysis and predictive severity assessment
- **Safety Reports**: Generate comprehensive safety reports for specific areas and time periods

## Technology Stack

- **Framework**: FastAPI 0.104.1
- **Database**: SQLite (SQLAlchemy ORM)
- **Python**: 3.9+
- **Architecture**: Modular Monolith

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository** (or navigate to the project directory)

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - On Linux/Mac:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set your configuration values, especially:
   - `SECRET_KEY`: Generate a secure random string for production
   - `DATABASE_URL`: Database connection string (default: SQLite)

## Running the Application

### Development Mode

```bash
python -m backend.main
```

Or using uvicorn directly:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### Initialize Database

The database tables will be created automatically on first run. To manually initialize:

```python
from backend.database import init_db
init_db()
```

## API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

### Incidents
- `POST /api/v1/incidents/` - Create a new incident
- `GET /api/v1/incidents/` - List all incidents (with filters)
- `GET /api/v1/incidents/{incident_id}` - Get specific incident
- `PUT /api/v1/incidents/{incident_id}` - Update incident
- `DELETE /api/v1/incidents/{incident_id}` - Delete incident

### Analytics
- `POST /api/v1/analytics/` - Create analytics for an incident
- `GET /api/v1/analytics/incident/{incident_id}` - Get incident analytics
- `GET /api/v1/analytics/risk-analysis` - Get overall risk analysis
- `DELETE /api/v1/analytics/{analytics_id}` - Delete analytics

### Reports
- `POST /api/v1/reports/` - Create a safety report
- `GET /api/v1/reports/` - List all reports (with filters)
- `GET /api/v1/reports/{report_id}` - Get specific report
- `DELETE /api/v1/reports/{report_id}` - Delete report

## Project Structure

```
.
├── backend/
│   ├── main.py              # Main application entry point
│   ├── config.py            # Configuration management
│   ├── models.py            # Database models
│   ├── database.py          # Database connection and session
│   ├── requirements.txt     # Python dependencies
│   └── routers/
│       ├── incidents.py     # Incident management endpoints
│       ├── analytics.py     # Analytics endpoints
│       └── reports.py       # Report generation endpoints
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | Road Safety Intelligence Network |
| `DEBUG` | Debug mode | False |
| `HOST` | Server host | 0.0.0.0 |
| `PORT` | Server port | 8000 |
| `DATABASE_URL` | Database connection string | sqlite:///./road_safety.db |
| `SECRET_KEY` | Secret key for JWT tokens | (required) |
| `ALLOWED_ORIGINS` | CORS allowed origins | ["http://localhost:3000"] |

## Security

- JWT-based authentication ready (implement as needed)
- Password hashing with bcrypt
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention through SQLAlchemy ORM

## Development

### Adding New Features

1. Create new models in `backend/models.py`
2. Create new routers in `backend/routers/`
3. Register routers in `backend/main.py`
4. Update this README with new endpoints

### Database Migrations

For production, consider using Alembic for database migrations:

```bash
pip install alembic
alembic init alembic
```

## License

Proprietary - All rights reserved

## Support

For issues and questions, contact the development team.
