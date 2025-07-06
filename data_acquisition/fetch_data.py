"""Background job for fetching stock market data."""

import yfinance as yf
import polars as pl
from datetime import datetime, timedelta
import sys
import os
import time
import random
from typing import List, Dict, Tuple
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import db
from app.config import get_settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


class StockDataFetcher:
    """Fetches and stores stock market data."""
    
    def __init__(self):
        self.min_trading_days = settings.min_trading_days
        # Top 100 US stocks by market cap (as of 2024)
        self.stock_universe = [
            # Top 10
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
            'META', 'TSLA', 'BRK-B', 'JPM', 'JNJ',
            # 11-20
            'V', 'UNH', 'XOM', 'LLY', 'PG',
            'MA', 'HD', 'CVX', 'MRK', 'ABBV',
            # 21-30
            'PEP', 'AVGO', 'KO', 'COST', 'ADBE',
            'WMT', 'MCD', 'CSCO', 'CRM', 'ACN',
            # 31-40
            'BAC', 'NFLX', 'AMD', 'TMO', 'LIN',
            'CMCSA', 'PFE', 'DIS', 'ABT', 'ORCL',
            # 41-50
            'NKE', 'DHR', 'TXN', 'VZ', 'INTC',
            'PM', 'INTU', 'COP', 'WFC', 'UNP',
            # 51-60
            'NEE', 'RTX', 'QCOM', 'CAT', 'BMY',
            'SPGI', 'GE', 'HON', 'BA', 'LOW',
            # 61-70
            'AMGN', 'ELV', 'IBM', 'DE', 'AMAT',
            'GS', 'SBUX', 'LMT', 'BLK', 'GILD',
            # 71-80
            'MDT', 'AXP', 'TJX', 'SYK', 'ADI',
            'VRTX', 'CVS', 'ISRG', 'MDLZ', 'REGN',
            # 81-90
            'PLD', 'ETN', 'SCHW', 'CI', 'ZTS',
            'SO', 'LRCX', 'BSX', 'BDX', 'TMUS',
            # 91-100
            'MU', 'SNPS', 'CB', 'C', 'PGR',
            'AON', 'KLAC', 'CME', 'MO', 'DUK'
        ]
    
    def fetch_stock_info(self, tickers: List[str]) -> Dict[str, Dict]:
        """Fetch stock information (name, sector, industry) with rate limiting."""
        logger.info(f"Fetching stock info for {len(tickers)} tickers")
        stock_info = {}
        
        # Use batch download for better performance and to avoid rate limiting
        tickers_str = ' '.join(tickers)
        
        try:
            # Download all tickers at once
            data = yf.download(tickers_str, period='1d', group_by='ticker', progress=False)
            
            for ticker in tickers:
                try:
                    # Get ticker info separately with delay
                    if len(stock_info) > 0:
                        time.sleep(random.uniform(0.5, 1.0))
                    
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    # Extract relevant information
                    stock_info[ticker] = {
                        'name': info.get('longName', info.get('shortName', ticker)),
                        'sector': info.get('sector', 'Unknown'),
                        'industry': info.get('industry', 'Unknown'),
                        'market_cap': info.get('marketCap', 0)
                    }
                    
                    logger.info(f"Successfully fetched info for {ticker}")
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch info for {ticker}: {e}")
                    # Use default values if fetch fails
                    stock_info[ticker] = {
                        'name': ticker,
                        'sector': 'Unknown',
                        'industry': 'Unknown',
                        'market_cap': 0
                    }
                    
        except Exception as e:
            logger.error(f"Failed to download ticker data: {e}")
            # Fallback to individual ticker fetching
            for ticker in tickers:
                stock_info[ticker] = {
                    'name': ticker,
                    'sector': 'Unknown',
                    'industry': 'Unknown',
                    'market_cap': 0
                }
        
        return stock_info
    
    def fetch_historical_data(self, tickers: List[str]) -> pl.DataFrame:
        """Fetch historical price data for multiple tickers using batch download."""
        logger.info(f"Fetching historical data for {len(tickers)} tickers")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 2)  # 2 years of data
        
        all_data = []
        
        try:
            # Download all tickers at once - much more efficient and avoids rate limiting
            tickers_str = ' '.join(tickers)
            logger.info(f"Downloading data for: {tickers_str}")
            
            data = yf.download(
                tickers_str,
                start=start_date,
                end=end_date,
                interval='1d',
                group_by='ticker',
                auto_adjust=True,
                progress=False,
                threads=False  # Avoid threading issues
            )
            
            if data.empty:
                raise ValueError("No data returned from yfinance")
            
            # Process data for each ticker
            for ticker in tickers:
                try:
                    if len(tickers) == 1:
                        # Single ticker download has different structure
                        ticker_data = data
                    else:
                        # Multiple tickers are grouped by ticker
                        ticker_data = data[ticker]
                    
                    # Skip if no data for this ticker
                    if ticker_data.empty or ticker_data['Close'].isna().all():
                        logger.warning(f"No valid data for {ticker}")
                        continue
                    
                    # Get shares outstanding
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    shares_outstanding = info.get('sharesOutstanding', info.get('impliedSharesOutstanding', 0))
                    
                    if shares_outstanding == 0:
                        # Estimate from market cap
                        market_cap = info.get('marketCap', 0)
                        if market_cap > 0:
                            latest_price = ticker_data['Close'].iloc[-1]
                            shares_outstanding = market_cap / latest_price
                    
                    # Create dataframe - convert dates to datetime first
                    dates = [d.strftime('%Y-%m-%d') for d in ticker_data.index.date]
                    df = pl.DataFrame({
                        'ticker': ticker,
                        'date': dates,
                        'open_price': ticker_data['Open'].values,
                        'close_price': ticker_data['Close'].values,
                        'volume': ticker_data['Volume'].values,
                        'market_cap': ticker_data['Close'].values * shares_outstanding
                    })
                    # Convert date string to date type
                    df = df.with_columns(
                        pl.col('date').str.strptime(pl.Date, '%Y-%m-%d')
                    )
                    
                    # Remove any rows with null values
                    df = df.filter(
                        pl.col('close_price').is_not_null() & 
                        pl.col('open_price').is_not_null() &
                        pl.col('volume').is_not_null()
                    )
                    
                    if len(df) > 0:
                        all_data.append(df)
                        logger.info(f"Successfully processed {len(df)} records for {ticker}")
                    
                except Exception as e:
                    logger.error(f"Error processing data for {ticker}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error downloading data: {e}")
            # Try individual downloads as fallback
            for ticker in tickers:
                try:
                    logger.info(f"Attempting individual download for {ticker}")
                    time.sleep(random.uniform(1.0, 2.0))  # Rate limiting
                    
                    stock = yf.Ticker(ticker)
                    hist = stock.history(start=start_date, end=end_date, interval='1d')
                    
                    if hist.empty:
                        logger.warning(f"No data for {ticker}")
                        continue
                    
                    info = stock.info
                    shares_outstanding = info.get('sharesOutstanding', info.get('impliedSharesOutstanding', 0))
                    
                    if shares_outstanding == 0:
                        market_cap = info.get('marketCap', 0)
                        if market_cap > 0 and len(hist) > 0:
                            latest_price = hist['Close'].iloc[-1]
                            shares_outstanding = market_cap / latest_price
                    
                    # Create dataframe - convert dates to datetime first
                    dates = [d.strftime('%Y-%m-%d') for d in hist.index.date]
                    df = pl.DataFrame({
                        'ticker': ticker,
                        'date': dates,
                        'open_price': hist['Open'].values,
                        'close_price': hist['Close'].values,
                        'volume': hist['Volume'].values,
                        'market_cap': hist['Close'].values * shares_outstanding
                    })
                    # Convert date string to date type
                    df = df.with_columns(
                        pl.col('date').str.strptime(pl.Date, '%Y-%m-%d')
                    )
                    
                    all_data.append(df)
                    logger.info(f"Successfully fetched {len(df)} records for {ticker}")
                    
                except Exception as e:
                    logger.error(f"Failed to fetch {ticker}: {e}")
                    continue
        
        if not all_data:
            raise ValueError("No data fetched for any ticker")
        
        # Combine all data
        combined_df = pl.concat(all_data)
        
        # Filter to ensure we have at least min_trading_days
        date_counts = combined_df.group_by('date').agg(pl.count().alias('count'))
        # For 10 stocks, require at least 5 stocks per day
        valid_dates_df = date_counts.filter(pl.col('count') >= 5)
        valid_dates_list = valid_dates_df['date'].to_list()
        combined_df = combined_df.filter(pl.col('date').is_in(valid_dates_list))
        
        # Sort by date and ticker
        combined_df = combined_df.sort(['date', 'ticker'])
        
        # Keep only the most recent days
        unique_dates = combined_df.select('date').unique().sort('date')
        if len(unique_dates) > self.min_trading_days:
            # Get the cutoff date
            all_dates = unique_dates['date'].to_list()
            cutoff_date = all_dates[-self.min_trading_days]
            combined_df = combined_df.filter(pl.col('date') >= cutoff_date)
        
        return combined_df
    
    def store_stock_info(self, stock_info: Dict[str, Dict]):
        """Store stock information in database."""
        logger.info("Storing stock information in database")
        
        with db.get_connection() as conn:
            for ticker, info in stock_info.items():
                conn.execute("""
                    INSERT OR REPLACE INTO stocks (ticker, name, sector, industry)
                    VALUES (?, ?, ?, ?)
                """, (ticker, info['name'], info['sector'], info['industry']))
            
            conn.commit()
    
    def store_historical_data(self, df: pl.DataFrame):
        """Store historical data in database."""
        logger.info(f"Storing {len(df)} historical data records in database")
        
        # Select only the columns that exist in the database table
        df_to_store = df.select([
            'ticker', 'date', 'open_price', 'close_price', 'volume', 'market_cap'
        ])
        
        with db.get_connection() as conn:
            # Clear existing data
            conn.execute("DELETE FROM daily_stock_data")
            
            # Convert to list of tuples for batch insert
            records = []
            for row in df_to_store.iter_rows():
                records.append(row)
            
            # Batch insert using DuckDB's native method
            conn.executemany("""
                INSERT INTO daily_stock_data (ticker, date, open_price, close_price, volume, market_cap)
                VALUES (?, ?, ?, ?, ?, ?)
            """, records)
            
            conn.commit()
    
    def run(self):
        """Run the data fetching job."""
        logger.info("Starting data fetching job")
        
        try:
            # Initialize database
            db.init_tables()
            
            # Fetch stock info
            stock_info = self.fetch_stock_info(self.stock_universe)
            self.store_stock_info(stock_info)
            
            # Fetch historical data
            historical_data = self.fetch_historical_data(self.stock_universe)
            self.store_historical_data(historical_data)
            
            # Log summary
            unique_dates = historical_data.select('date').unique()
            logger.info(f"Data fetching completed successfully")
            logger.info(f"Total records: {len(historical_data)}")
            logger.info(f"Date range: {unique_dates['date'].min()} to {unique_dates['date'].max()}")
            logger.info(f"Total trading days: {len(unique_dates)}")
            
        except Exception as e:
            logger.error(f"Data fetching failed: {e}")
            raise


def main():
    """Main entry point for the data fetching job."""
    fetcher = StockDataFetcher()
    fetcher.run()


if __name__ == "__main__":
    main()