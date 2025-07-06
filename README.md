# Equal-Weighted Stock Index Tracker

A high-performance backend service for tracking and managing an equal-weighted stock index comprising the top 100 US stocks by daily market capitalization.

## Features

- **Dynamic Index Construction**: Automatically selects top 100 stocks by market cap daily
- **Equal Weighting**: Each stock receives 1% weight in the index
- **Performance Tracking**: Calculates daily returns, cumulative performance, and risk metrics
- **RESTful API**: FastAPI-based endpoints for all operations
- **High Performance**: DuckDB for analytics, Redis for caching
- **Data Export**: Export index data in CSV or JSON formats
- **Automated Data Fetching**: Yahoo Finance integration for real-time market data

## Architecture

- **FastAPI**: Modern Python web framework with automatic API documentation
- **DuckDB**: Analytical database optimized for OLAP queries
- **Redis**: In-memory cache for performance optimization
- **yfinance**: Yahoo Finance data integration
- **Polars**: Fast DataFrame library for data processing
- **Docker**: Containerized deployment

## Prerequisites

- Python 3.11+
- Redis server (optional, for caching)
- Git

## Local Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd hedgineer
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# API Configuration
API_VERSION=v1
API_TITLE=Equal-Weighted Stock Index Tracker
API_DESCRIPTION=Backend service for tracking equal-weighted stock indices

# Database Configuration
DATABASE_PATH=data/hedgineer.db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CACHE_TTL=3600

# Index Configuration
INDEX_SIZE=100
INDEX_NAME=Equal-Weighted Top 100 Index

# Logging
LOG_LEVEL=INFO
```

### 5. Initialize the Database

The database will be automatically initialized when you start the server, but you can also run:

```bash
python -m app.db.init_db
```

### 6. Fetch Initial Stock Data

```bash
python -m data_acquisition.fetch_data
```

This will fetch historical data for all 100 stocks in the index.

### 7. Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

## API Endpoints & cURL Examples

### 1. Health Check

Check if the service is running:

```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-06T12:00:00.000000",
  "version": "v1",
  "database": "connected",
  "cache": "connected"
}
```

### 2. Build Index

Build the index for a specific date range:

```bash
curl -X POST "http://localhost:8000/api/v1/build-index" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-06-01",
    "end_date": "2025-07-03"
  }'
```

Expected response:
```json
{
  "success": true,
  "message": "Index built successfully for 23 trading days",
  "dates_processed": 23,
  "start_date": "2025-06-01",
  "end_date": "2025-07-03"
}
```

### 3. Get Index Performance

Retrieve index performance data:

```bash
curl -X GET "http://localhost:8000/api/v1/index-performance?start_date=2025-06-01&end_date=2025-07-03"
```

Expected response:
```json
{
  "start_date": "2025-06-01",
  "end_date": "2025-07-03",
  "total_days": 23,
  "performance_data": [
    {
      "date": "2025-06-02",
      "value": 1000.0,
      "daily_return": null,
      "cumulative_return": null
    },
    ...
  ],
  "summary": {
    "total_return": 6.505487,
    "average_daily_return": 0.2755509565217391,
    "volatility": 0.490125327576759,
    "max_daily_return": 1.112528,
    "min_daily_return": -0.9937,
    "sharpe_ratio": 8.922158679166413
  }
}
```

### 4. Get Index Composition

Get the index composition for a specific date:

```bash
curl -X GET "http://localhost:8000/api/v1/index-composition?date=2025-07-03"
```

Expected response:
```json
{
  "date": "2025-07-03",
  "total_stocks": 100,
  "compositions": [
    {
      "ticker": "NVDA",
      "name": "NVIDIA Corporation",
      "weight": 0.01,
      "market_cap": 3885920155876.5,
      "sector": "Technology",
      "industry": "Semiconductors"
    },
    ...
  ]
}
```

### 5. Get Composition Changes

Track changes in index composition between dates:

```bash
curl -X GET "http://localhost:8000/api/v1/composition-changes?start_date=2025-06-01&end_date=2025-07-03"
```

### 6. Export Data

Export index data in different formats:

#### Export as CSV:
```bash
curl -X POST "http://localhost:8000/api/v1/export" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-06-01",
    "end_date": "2025-07-03",
    "format": "csv",
    "include_composition": true
  }' \
  -o index_data.csv
```

#### Export as JSON:
```bash
curl -X POST "http://localhost:8000/api/v1/export" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-06-01",
    "end_date": "2025-07-03",
    "format": "json",
    "include_composition": true
  }' \
  -o index_data.json
```

## Docker Deployment

### Using Docker Compose

1. Build and start the services:
```bash
docker-compose up --build
```

2. The API will be available at `http://localhost:8000`

### Using Docker Directly

1. Build the image:
```bash
docker build -t stock-index-tracker .
```

2. Run the container:
```bash
docker run -p 8000:8000 -v $(pwd)/data:/app/data stock-index-tracker
```

## Project Structure

```
hedgineer/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py      # API endpoint definitions
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py       # DuckDB connection management
│   │   ├── cache.py          # Redis cache implementation
│   │   └── init_db.py        # Database initialization
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py        # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── index_service.py  # Index calculation logic
│   │   └── export_service.py # Data export functionality
│   ├── utils/
│   │   └── __init__.py
│   ├── __init__.py
│   ├── config.py             # Configuration management
│   └── main.py               # FastAPI application
├── data_acquisition/
│   ├── __init__.py
│   └── fetch_data.py         # Yahoo Finance data fetcher
├── data/                     # Data directory (created automatically)
├── tests/                    # Test suite
├── .env.example              # Environment variables template
├── .gitignore
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker Compose configuration
├── requirements.txt          # Python dependencies
├── setup.sh                  # Setup script
├── ARCHITECTURE.md           # Architecture documentation
├── PRODUCTION_IMPROVEMENTS.md # Production deployment guide
└── README.md                 # This file
```

## Key Changes from Initial Implementation

1. **Database Path**: Changed from `data/stocks.db` to `data/hedgineer.db`
2. **Stock Count**: Configurable via `INDEX_SIZE` environment variable (default: 100)
3. **SQL Compatibility**: Updated queries from SQLite syntax to DuckDB syntax
4. **Error Handling**: Improved error handling in cache and export services
5. **Rate Limiting**: Implemented batch downloads to avoid Yahoo Finance rate limits
6. **Composite Keys**: Using composite primary keys (date, ticker) instead of auto-increment IDs

## Performance Considerations

- **Caching**: Redis caching reduces database queries by ~90%
- **Batch Processing**: Bulk inserts for efficient data loading
- **Indexed Queries**: Database indexes on date and ticker columns
- **Connection Pooling**: Reused database connections

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Ensure Redis is running: `redis-cli ping`
   - Check Redis configuration in `.env`
   - The app will work without Redis but with reduced performance

2. **Yahoo Finance Rate Limiting**
   - The fetcher implements delays between requests
   - If you get 429 errors, wait a few minutes before retrying

3. **Database Errors**
   - Ensure the `data/` directory exists and is writable
   - Check database path in `.env`

4. **Import Errors**
   - Ensure you're in the virtual environment
   - Reinstall dependencies: `pip install -r requirements.txt`

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black app/ data_acquisition/ tests/
isort app/ data_acquisition/ tests/
```

### Type Checking

```bash
mypy app/
```

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]
