# Architecture Documentation

## System Overview

The Equal-Weighted Stock Index Tracker is a high-performance backend service designed to track and manage an equal-weighted stock index comprising the top 100 US stocks by daily market capitalization. The system fetches real-time market data, calculates index performance, and provides RESTful APIs for data access.

## Key Design Decisions

### 1. Database Choice: DuckDB

**Why DuckDB?**
- **OLAP Optimized**: Perfect for analytical queries on financial time-series data
- **Embedded**: No separate database server required
- **Columnar Storage**: Efficient for aggregations and calculations
- **SQL Compatible**: Familiar interface with advanced analytical functions

**Schema Design:**
- **Composite Primary Keys**: Using (date, ticker) as primary key instead of auto-increment IDs
- **Denormalized Structure**: Optimized for read performance over write efficiency
- **Indexed Columns**: Date and ticker columns for fast lookups

### 2. Caching Strategy: Redis

**Implementation:**
- **Cache-aside pattern**: Check cache first, fallback to database
- **TTL-based expiration**: Default 1-hour TTL for all cached data
- **Key structure**: `index_tracker:{operation}:{params_hash}`
- **Graceful degradation**: Service works without Redis, just slower

### 3. Data Acquisition: Yahoo Finance

**Strategy:**
- **Batch downloads**: Using `yf.download()` for multiple tickers at once
- **Rate limiting protection**: Delays between individual ticker info requests
- **Error handling**: Continues processing even if some tickers fail
- **Data validation**: Ensures data integrity before storage

### 4. API Framework: FastAPI

**Benefits:**
- **Async support**: Non-blocking I/O operations
- **Automatic documentation**: OpenAPI/Swagger integration
- **Type validation**: Pydantic models for request/response validation
- **High performance**: Built on Starlette and Pydantic

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Yahoo Finance  │────▶│ Data Acquisition│────▶│     DuckDB      │
│      API        │     │    Service      │     │    Database     │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   REST Client   │◀────│   FastAPI App   │◀────│  Index Service  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                         │
                                ▼                         ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │                 │     │                 │
                        │  Redis Cache    │     │ Export Service  │
                        │                 │     │                 │
                        └─────────────────┘     └─────────────────┘
```

## Data Flow

### 1. Data Acquisition Flow
```
1. Scheduled job triggers fetch_data.py
2. Fetch list of 100 tickers (hardcoded or from config)
3. Batch download stock info and historical data
4. Validate and clean data
5. Bulk insert into DuckDB tables
```

### 2. Index Building Flow
```
1. API receives build request with date range
2. Query historical data for all tickers in range
3. For each date:
   - Calculate market caps
   - Select top 100 by market cap
   - Assign equal weights (1/100)
   - Calculate returns
4. Store compositions and performance data
5. Invalidate relevant cache entries
```

### 3. Data Retrieval Flow
```
1. API receives request
2. Generate cache key from parameters
3. Check Redis cache
4. If miss, query DuckDB
5. Process and format results
6. Store in cache with TTL
7. Return response
```

## Database Schema

### Tables

#### 1. stock_info
```sql
CREATE TABLE stock_info (
    ticker VARCHAR PRIMARY KEY,
    name VARCHAR,
    sector VARCHAR,
    industry VARCHAR,
    market_cap DOUBLE,
    last_updated TIMESTAMP
)
```

#### 2. stock_data
```sql
CREATE TABLE stock_data (
    date DATE,
    ticker VARCHAR,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    adjusted_close DOUBLE,
    PRIMARY KEY (date, ticker)
)
```

#### 3. index_compositions
```sql
CREATE TABLE index_compositions (
    date DATE,
    ticker VARCHAR,
    weight DOUBLE,
    market_cap DOUBLE,
    PRIMARY KEY (date, ticker)
)
```

#### 4. index_performance
```sql
CREATE TABLE index_performance (
    date DATE PRIMARY KEY,
    value DOUBLE,
    daily_return DOUBLE,
    cumulative_return DOUBLE
)
```

## API Endpoints

### Core Endpoints

1. **POST /api/v1/build-index**
   - Builds index for specified date range
   - Calculates compositions and performance
   - Stores results in database

2. **GET /api/v1/index-performance**
   - Returns performance metrics for date range
   - Includes daily and cumulative returns
   - Calculates risk metrics (volatility, Sharpe ratio)

3. **GET /api/v1/index-composition**
   - Returns index composition for specific date
   - Shows all 100 stocks with weights
   - Includes market cap and sector information

4. **GET /api/v1/composition-changes**
   - Tracks changes in index composition
   - Shows stocks added/removed between dates
   - Useful for rebalancing analysis

5. **POST /api/v1/export**
   - Exports data in CSV or JSON format
   - Supports performance and composition data
   - Configurable date ranges

6. **GET /api/v1/health**
   - System health check
   - Database and cache connectivity
   - Version information

## Performance Optimizations

### 1. Database Optimizations
- **Composite indexes** on (date, ticker) for fast lookups
- **Bulk inserts** for data loading (1000+ records/second)
- **Connection pooling** to reuse database connections
- **Query optimization** using DuckDB's columnar engine

### 2. Caching Strategy
- **Aggressive caching** of expensive calculations
- **Partial invalidation** on data updates
- **Compression** for large cached objects
- **Pipeline operations** for Redis efficiency

### 3. API Optimizations
- **Async handlers** for non-blocking operations
- **Response streaming** for large exports
- **Pagination** for composition endpoints
- **Field filtering** to reduce payload size

## Error Handling

### 1. Data Acquisition Errors
- **Rate limiting**: Exponential backoff with retry
- **Network failures**: Graceful degradation
- **Invalid data**: Validation and logging
- **Partial failures**: Continue with available data

### 2. API Errors
- **Validation errors**: 400 with detailed messages
- **Not found**: 404 with resource information
- **Server errors**: 500 with correlation ID
- **Rate limiting**: 429 with retry-after header

### 3. Database Errors
- **Connection failures**: Circuit breaker pattern
- **Query timeouts**: Configurable limits
- **Data integrity**: Transaction rollbacks
- **Disk space**: Monitoring and alerts

## Security Considerations

### 1. API Security
- **CORS configuration**: Restrictive by default
- **Input validation**: Pydantic models
- **SQL injection**: Parameterized queries
- **Rate limiting**: Per-IP limits (future)

### 2. Data Security
- **Encryption at rest**: File system encryption
- **Encryption in transit**: HTTPS only
- **Access control**: API key authentication (future)
- **Audit logging**: All data modifications

## Monitoring and Observability

### 1. Logging
- **Structured logging**: JSON format
- **Log levels**: Configurable per module
- **Correlation IDs**: Request tracking
- **Performance metrics**: Response times

### 2. Metrics (Future)
- **API metrics**: Request count, latency, errors
- **Database metrics**: Query performance, connection pool
- **Cache metrics**: Hit rate, evictions
- **Business metrics**: Index calculations, data freshness

### 3. Health Checks
- **Liveness probe**: Basic application health
- **Readiness probe**: Database and cache connectivity
- **Dependency checks**: External API availability

## Scalability Considerations

### 1. Horizontal Scaling
- **Stateless design**: Multiple API instances
- **Shared cache**: Redis cluster
- **Database replication**: Read replicas (future)
- **Load balancing**: Round-robin or least-connections

### 2. Vertical Scaling
- **Memory optimization**: Efficient data structures
- **CPU optimization**: Parallel processing
- **I/O optimization**: Async operations
- **Query optimization**: Materialized views

### 3. Data Scaling
- **Partitioning**: By date for historical data
- **Archival**: Old data to cold storage
- **Compression**: For historical records
- **Incremental updates**: Only process changes

## Future Enhancements

### 1. Real-time Updates
- WebSocket support for live data
- Streaming index calculations
- Push notifications for changes

### 2. Advanced Analytics
- Factor analysis
- Risk attribution
- Performance attribution
- Backtesting framework

### 3. Multi-index Support
- Custom index definitions
- Sector-based indices
- International markets
- Different weighting schemes

### 4. Machine Learning
- Predictive analytics
- Anomaly detection
- Automated rebalancing
- Market regime detection

## Development Workflow

### 1. Local Development
```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database
python -m app.db.init_db

# Data fetch
python -m data_acquisition.fetch_data

# Run server
uvicorn app.main:app --reload
```

### 2. Testing
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Load tests
locust -f tests/load/locustfile.py
```

### 3. Deployment
```bash
# Docker build
docker build -t stock-index-tracker .

# Docker run
docker-compose up -d

# Health check
curl http://localhost:8000/api/v1/health
```

## Configuration Management

### Environment Variables
- **API_VERSION**: API version string
- **DATABASE_PATH**: DuckDB file location
- **REDIS_HOST**: Redis server address
- **INDEX_SIZE**: Number of stocks (default: 100)
- **CACHE_TTL**: Cache expiration in seconds
- **LOG_LEVEL**: Logging verbosity

### Configuration Hierarchy
1. Environment variables (highest priority)
2. .env file
3. Default values in config.py

## Conclusion

This architecture provides a solid foundation for a high-performance stock index tracking system. The modular design allows for easy extension and modification, while the performance optimizations ensure scalability. The use of modern tools like FastAPI, DuckDB, and Redis provides both developer productivity and system efficiency.