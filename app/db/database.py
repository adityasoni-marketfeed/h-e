"""Database connection and initialization."""

import duckdb
import os
from contextlib import contextmanager
from typing import Generator
from app.config import get_settings

settings = get_settings()


class Database:
    """Database connection manager."""
    
    def __init__(self):
        self.db_path = settings.database_path
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Get a database connection context manager."""
        conn = duckdb.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def init_tables(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            # Create stocks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stocks (
                    ticker TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    sector TEXT,
                    industry TEXT
                )
            """)
            
            # Create daily stock data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stock_data (
                    ticker TEXT NOT NULL,
                    date DATE NOT NULL,
                    open_price DECIMAL(10, 2),
                    close_price DECIMAL(10, 2) NOT NULL,
                    volume BIGINT,
                    market_cap DECIMAL(15, 2) NOT NULL,
                    PRIMARY KEY(ticker, date),
                    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
                )
            """)
            
            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_stock_date 
                ON daily_stock_data(date)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_stock_market_cap 
                ON daily_stock_data(date, market_cap DESC)
            """)
            
            # Create index compositions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS index_compositions (
                    date DATE NOT NULL,
                    ticker TEXT NOT NULL,
                    weight DECIMAL(6, 4) NOT NULL,
                    market_cap DECIMAL(15, 2) NOT NULL,
                    PRIMARY KEY(date, ticker),
                    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
                )
            """)
            
            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_composition_date 
                ON index_compositions(date)
            """)
            
            # Create index performance table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS index_performance (
                    date DATE PRIMARY KEY,
                    value DECIMAL(10, 4) NOT NULL,
                    daily_return DECIMAL(8, 6),
                    cumulative_return DECIMAL(8, 6)
                )
            """)
            
            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_performance_date 
                ON index_performance(date)
            """)
            
            conn.commit()
    
    def clear_tables(self):
        """Clear all tables (for testing purposes)."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM index_performance")
            conn.execute("DELETE FROM index_compositions")
            conn.execute("DELETE FROM daily_stock_data")
            conn.execute("DELETE FROM stocks")
            conn.commit()


# Global database instance
db = Database()