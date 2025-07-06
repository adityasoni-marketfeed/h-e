# API Usage Examples

## Base URL
```
http://localhost:8000/api/v1
```

## 1. Build Index

Construct the equal-weighted index for a date range.

### Request
```bash
curl -X POST http://localhost:8000/api/v1/build-index \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }'
```

### Response
```json
{
  "success": true,
  "message": "Index built successfully for 21 trading days",
  "dates_processed": 21,
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

## 2. Get Index Performance

Retrieve performance data for a date range.

### Request
```bash
curl -X GET "http://localhost:8000/api/v1/index-performance?start_date=2024-01-01&end_date=2024-01-31"
```

### Response
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "total_days": 21,
  "performance_data": [
    {
      "date": "2024-01-01",
      "value": 1000.0,
      "daily_return": 0.0,
      "cumulative_return": 0.0
    },
    {
      "date": "2024-01-02",
      "value": 1005.23,
      "daily_return": 0.523,
      "cumulative_return": 0.523
    }
    // ... more days
  ],
  "summary": {
    "total_return": 2.45,
    "average_daily_return": 0.117,
    "volatility": 0.89,
    "max_daily_return": 1.23,
    "min_daily_return": -0.98,
    "sharpe_ratio": 1.65
  }
}
```

## 3. Get Index Composition

Get the 100 stocks that comprise the index on a specific date.

### Request
```bash
curl -X GET "http://localhost:8000/api/v1/index-composition?date=2024-01-15"
```

### Response
```json
{
  "date": "2024-01-15",
  "total_stocks": 100,
  "compositions": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "weight": 0.01,
      "market_cap": 2950000000000,
      "sector": "Technology",
      "industry": "Consumer Electronics"
    },
    {
      "ticker": "MSFT",
      "name": "Microsoft Corporation",
      "weight": 0.01,
      "market_cap": 2850000000000,
      "sector": "Technology",
      "industry": "Software—Infrastructure"
    }
    // ... 98 more stocks
  ]
}
```

## 4. Get Composition Changes

Track when stocks enter or exit the index.

### Request
```bash
curl -X GET "http://localhost:8000/api/v1/composition-changes?start_date=2024-01-01&end_date=2024-01-31"
```

### Response
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "total_change_dates": 3,
  "changes": [
    {
      "date": "2024-01-08",
      "stocks_added": [
        {
          "ticker": "NVDA",
          "name": "NVIDIA Corporation",
          "action": "added",
          "market_cap": 1200000000000
        }
      ],
      "stocks_removed": [
        {
          "ticker": "WBA",
          "name": "Walgreens Boots Alliance",
          "action": "removed",
          "market_cap": 25000000000
        }
      ],
      "total_changes": 2
    }
    // ... more change dates
  ]
}
```

## 5. Export Data to Excel

Generate a comprehensive Excel report.

### Request
```bash
curl -X POST http://localhost:8000/api/v1/export-data \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }'
```

### Response
```json
{
  "success": true,
  "file_path": "exports/index_data_2024-01-01_2024-01-31.xlsx",
  "file_size_mb": 2.45
}
```

### Download the Excel file
```bash
curl -O http://localhost:8000/api/v1/export-data/download/index_data_2024-01-01_2024-01-31.xlsx
```

## 6. Health Check

Check if the service is running.

### Request
```bash
curl -X GET http://localhost:8000/api/v1/health
```

### Response
```json
{
  "status": "healthy",
  "service": "index-tracker"
}
```

## Python Client Example

```python
import requests
from datetime import date

BASE_URL = "http://localhost:8000/api/v1"

# Build index
response = requests.post(
    f"{BASE_URL}/build-index",
    json={
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    }
)
print(f"Index built: {response.json()}")

# Get performance
response = requests.get(
    f"{BASE_URL}/index-performance",
    params={
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    }
)
performance = response.json()
print(f"Total return: {performance['summary']['total_return']}%")

# Get composition
response = requests.get(
    f"{BASE_URL}/index-composition",
    params={"date": "2024-01-15"}
)
composition = response.json()
print(f"Top stock: {composition['compositions'][0]['ticker']}")
```

## Postman Collection

Import this collection into Postman:

```json
{
  "info": {
    "name": "Equal-Weighted Index Tracker",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Build Index",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"start_date\": \"2024-01-01\",\n  \"end_date\": \"2024-01-31\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/build-index",
          "host": ["{{base_url}}"],
          "path": ["build-index"]
        }
      }
    },
    {
      "name": "Get Performance",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{base_url}}/index-performance?start_date=2024-01-01&end_date=2024-01-31",
          "host": ["{{base_url}}"],
          "path": ["index-performance"],
          "query": [
            {
              "key": "start_date",
              "value": "2024-01-01"
            },
            {
              "key": "end_date",
              "value": "2024-01-31"
            }
          ]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000/api/v1"
    }
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "detail": "end_date must be greater than or equal to start_date"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "detail": "No performance data available for date range 2024-01-01 to 2024-01-31"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "detail": "An unexpected error occurred"
}
```

## Rate Limiting

The API currently does not implement rate limiting, but in production, you might encounter:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Performance Tips

1. **Use Caching**: Results are cached for 1 hour by default
2. **Batch Requests**: Build index for longer periods to reduce API calls
3. **Date Ranges**: Query specific date ranges instead of entire history
4. **Parallel Requests**: Use async/await for multiple API calls

## WebSocket Support (Future)

Future versions may support WebSocket connections for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Index update:', data);
};