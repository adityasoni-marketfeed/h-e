"""Initialize the database."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize the database with tables."""
    logger.info("Initializing database...")
    
    try:
        db.init_tables()
        logger.info("Database initialized successfully!")
        
        # Test connection
        with db.get_connection() as conn:
            result = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            tables = [row[0] for row in result]
            logger.info(f"Created tables: {', '.join(tables)}")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


if __name__ == "__main__":
    init_database()