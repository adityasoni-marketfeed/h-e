# Changelog

All notable changes to the Equal-Weighted Stock Index Tracker project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-07-06

### Added
- Comprehensive documentation including:
  - Detailed README with setup instructions and cURL examples
  - API_DOCUMENTATION.md with complete endpoint documentation
  - Updated ARCHITECTURE.md with current implementation details
  - Enhanced PRODUCTION_IMPROVEMENTS.md with deployment checklist
- Configurable index size via INDEX_SIZE environment variable
- Batch downloading for Yahoo Finance data to avoid rate limits
- Composite primary keys (date, ticker) for better database performance
- Improved error handling in cache and export services

### Changed
- Database backend from SQLite to DuckDB for better analytical performance
- Database file name from `stocks.db` to `hedgineer.db`
- SQL queries updated for DuckDB compatibility (ON CONFLICT syntax)
- Default stock count from 10 to 100 (configurable)
- Stock list expanded to include top 100 US stocks by market cap
- Error handling in cache service (JSONEncodeError → ValueError, TypeError)

### Fixed
- Missing database import in export service
- SQL syntax compatibility issues with DuckDB
- Yahoo Finance rate limiting issues with batch download implementation
- Cache error handling for non-existent exception types

### Technical Details
- **Database Migration**: Moved from SQLite `INSERT OR REPLACE` to DuckDB `ON CONFLICT` syntax
- **Performance**: Batch inserts now handle 1000+ records/second
- **Caching**: Redis integration with 1-hour TTL for expensive queries
- **API**: FastAPI with automatic OpenAPI documentation

## [1.0.0] - 2025-07-05

### Initial Release
- Core index tracking functionality
- FastAPI-based REST API
- DuckDB for data storage
- Redis caching layer
- Yahoo Finance integration for market data
- Docker containerization
- Basic API endpoints:
  - Health check
  - Build index
  - Get performance
  - Get composition
  - Track composition changes
  - Export data (CSV/JSON)

### Features
- Equal-weighted index calculation
- Daily rebalancing logic
- Performance metrics (returns, volatility, Sharpe ratio)
- Historical data storage
- Automated data fetching
- API documentation via Swagger/ReDoc

### Technical Stack
- Python 3.11+
- FastAPI 0.104.1
- DuckDB 0.9.2
- Redis (optional)
- yfinance 0.2.64
- Polars for data processing
- Docker for containerization

## Future Releases

### [1.2.0] - Planned
- Authentication and authorization (JWT tokens)
- API rate limiting
- Database connection pooling
- Prometheus metrics integration
- Enhanced data validation

### [1.3.0] - Planned
- WebSocket support for real-time updates
- Background task processing with Celery
- Multi-index support
- International markets
- GraphQL API endpoint

### [2.0.0] - Planned
- Machine learning integration
- Predictive analytics
- Custom index creation
- Advanced risk metrics
- Multi-currency support

## Migration Guide

### From 1.0.0 to 1.1.0

1. **Database Migration**:
   ```bash
   # Backup existing database
   cp data/stocks.db data/stocks.db.backup
   
   # Update .env file
   # Change DATABASE_PATH from "data/stocks.db" to "data/hedgineer.db"
   
   # Re-initialize database
   python -m app.db.init_db
   
   # Re-fetch data
   python -m data_acquisition.fetch_data
   ```

2. **Configuration Changes**:
   ```bash
   # Add to .env file
   INDEX_SIZE=100  # or your preferred number
   ```

3. **Code Updates**:
   - No API changes required
   - All endpoints remain backward compatible

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the [API Documentation](API_DOCUMENTATION.md)
- Review the [Architecture Guide](ARCHITECTURE.md)
- See [Production Deployment Guide](PRODUCTION_IMPROVEMENTS.md)