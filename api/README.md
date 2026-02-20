# Personal Hub - API

FastAPI backend for Personal Hub.

## 🏗️ Status: Template

This directory is intentionally minimal. You should implement:

- `main.py` - FastAPI application entry point
- `models/` - SQLAlchemy database models
- `routers/` - API route handlers
- `collectors/` - Data source collectors
- `requirements.txt` - Python dependencies

## 📚 Example Structure

```
api/
├── main.py                 # FastAPI app
├── requirements.txt        # Dependencies
├── alembic.ini            # Database migrations config
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── health_data.py
│   └── data_item.py
├── routers/
│   ├── __init__.py
│   ├── health.py
│   ├── intel.py
│   └── auth.py
├── collectors/
│   ├── __init__.py
│   ├── base.py           # Base collector class
│   ├── whoop.py          # Whoop integration
│   ├── apple_health.py   # Apple Health webhook
│   ├── withings.py       # Withings integration
│   └── slack.py          # Slack integration
└── migrations/           # Alembic migrations
    └── versions/
```

## 🚀 Getting Started

See the full Personal Hub repository for a complete implementation example.

## 📖 Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
