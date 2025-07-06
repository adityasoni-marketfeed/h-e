# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the API does not require authentication. This will be added in future versions.

## Response Format
All responses are in JSON format with appropriate HTTP status codes.

### Success Response
```json
{
  "data": { ... },
  "success": true,
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Endpoints

### 1. Health Check
Check the health status of the service.

**Endpoint:** `GET /api/v1/health`

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

**Response:**
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
Build the equal-weighted index for a specified date range.

**Endpoint:** `POST /api/v1/build-index`

**Request Body:**
```json
{
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/build-index" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-06-01",
    "end_date": "2025-07-03"
  }'
```

**Response:**
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
Retrieve index performance metrics for a date range.

**Endpoint:** `GET /api/v1/index-performance`

**Query Parameters:**
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/index-performance?start_date=2025-06-01&end_date=2025-07-03"
```

**Response:**
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
    {
      "date": "2025-06-03",
      "value": 1005.2019,
      "daily_return": 0.520192,
      "cumulative_return": 0.520192
    }
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
Get the composition of the index for a specific date.

**Endpoint:** `GET /api/v1/index-composition`

**Query Parameters:**
- `date` (required): Date in YYYY-MM-DD format

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/index-composition?date=2025-07-03"
```

**Response:**
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
    {
      "ticker": "MSFT",
      "name": "Microsoft Corporation",
      "weight": 0.01,
      "market_cap": 3707648306195.62,
      "sector": "Technology",
      "industry": "Software - Infrastructure"
    }
  ]
}
```

### 5. Get Composition Changes
Track changes in index composition between two dates.

**Endpoint:** `GET /api/v1/composition-changes`

**Query Parameters:**
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/composition-changes?start_date=2025-06-01&end_date=2025-07-03"
```

**Response:**
```json
{
  "start_date": "2025-06-01",
  "end_date": "2025-07-03",
  "changes": {
    "added": ["TICKER1", "TICKER2"],
    "removed": ["TICKER3", "TICKER4"],
    "consistent": ["AAPL", "MSFT", "GOOGL", ...]
  },
  "summary": {
    "total_added": 2,
    "total_removed": 2,
    "total_consistent": 98
  }
}
```

### 6. Export Data
Export index data in various formats.

**Endpoint:** `POST /api/v1/export`

**Request Body:**
```json
{
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "format": "csv|json",
  "include_composition": true|false
}
```

**cURL Examples:**

**Export as CSV:**
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

**Export as JSON:**
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

**Response Headers (CSV):**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="index_data_2025-06-01_2025-07-03.csv"
```

**Response Headers (JSON):**
```
Content-Type: application/json
Content-Disposition: attachment; filename="index_data_2025-06-01_2025-07-03.json"
```

## Complete Testing Workflow

Here's a complete workflow to test all endpoints:

```bash
# 1. Check service health
curl -X GET "http://localhost:8000/api/v1/health"

# 2. Fetch stock data (run this in a separate terminal)
cd /path/to/project
source venv/bin/activate
python -m data_acquisition.fetch_data

# 3. Build the index
curl -X POST "http://localhost:8000/api/v1/build-index" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-06-01",
    "end_date": "2025-07-03"
  }'

# 4. Get performance data
curl -X GET "http://localhost:8000/api/v1/index-performance?start_date=2025-06-01&end_date=2025-07-03" | python -m json.tool

# 5. Get latest composition
curl -X GET "http://localhost:8000/api/v1/index-composition?date=2025-07-03" | python -m json.tool

# 6. Check composition changes
curl -X GET "http://localhost:8000/api/v1/composition-changes?start_date=2025-06-01&end_date=2025-07-03" | python -m json.tool

# 7. Export data as CSV
curl -X POST "http://localhost:8000/api/v1/export" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-06-01",
    "end_date": "2025-07-03",
    "format": "csv",
    "include_composition": true
  }' \
  -o index_data.csv

# 8. Export data as JSON
curl -X POST "http://localhost:8000/api/v1/export" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-06-01",
    "end_date": "2025-07-03",
    "format": "json",
    "include_composition": false
  }' \
  -o index_performance.json

# 9. Pretty print any JSON response
curl -X GET "http://localhost:8000/api/v1/index-composition?date=2025-07-03" | python -m json.tool

# 10. Save response to file with headers
curl -X GET "http://localhost:8000/api/v1/index-performance?start_date=2025-06-01&end_date=2025-07-03" \
  -H "Accept: application/json" \
  -o performance.json \
  -D headers.txt
```

## Error Handling

### Common Error Responses

**400 Bad Request**
```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD"
}
```

**404 Not Found**
```json
{
  "detail": "No data found for the specified date range"
}
```

**422 Unprocessable Entity**
```json
{
  "detail": [
    {
      "loc": ["body", "start_date"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

## Performance Tips

1. **Use date ranges wisely**: Requesting large date ranges will take longer to process
2. **Cache is your friend**: Repeated requests for the same data will be served from cache
3. **Build incrementally**: Build the index for smaller date ranges first
4. **Monitor the logs**: Check server logs for detailed error information

## Rate Limits

Currently, there are no rate limits implemented. In production, the following limits would apply:
- 100 requests per minute per IP
- 1000 requests per hour per IP
- 10,000 requests per day per API key

## Webhooks (Future)

Future versions will support webhooks for:
- Daily index updates
- Composition changes
- Performance alerts

## WebSocket Support (Future)

Future versions will support WebSocket connections for:
- Real-time index values
- Live performance updates
- Composition change notifications

## SDK Support (Future)

Official SDKs will be provided for:
- Python
- JavaScript/TypeScript
- Go
- Java

## Additional Resources

- [Architecture Documentation](ARCHITECTURE.md)
- [Production Deployment Guide](PRODUCTION_IMPROVEMENTS.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [API Changelog](CHANGELOG.md)