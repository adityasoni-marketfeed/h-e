"""Service for index construction and management."""

import polars as pl
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from app.db.database import db
from app.db.cache import cache, get_performance_cache_key, get_composition_cache_key, get_changes_cache_key
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class IndexService:
    """Service for managing equal-weighted stock index."""
    
    def __init__(self):
        # Force reload settings
        from app.config import get_settings
        fresh_settings = get_settings()
        self.index_size = fresh_settings.index_size
        self.base_value = 1000.0  # Base index value
        logger.info(f"IndexService initialized with index_size={self.index_size} (from settings: {fresh_settings.index_size})")
    
    def build_index(self, start_date: date, end_date: Optional[date] = None) -> Dict:
        """Build the equal-weighted index for the given date range."""
        logger.info(f"Building index from {start_date} to {end_date}")
        
        # If no end date, use the latest available date
        if not end_date:
            with db.get_connection() as conn:
                result = conn.execute("SELECT MAX(date) as max_date FROM daily_stock_data").fetchone()
                end_date = result[0] if result else start_date
        
        # Clear existing index data for the date range
        self._clear_index_data(start_date, end_date)
        
        # Get all trading dates in range
        trading_dates = self._get_trading_dates(start_date, end_date)
        
        if not trading_dates:
            raise ValueError(f"No trading data available for date range {start_date} to {end_date}")
        
        # Build index for each date
        previous_value = self.base_value
        dates_processed = 0
        
        for i, current_date in enumerate(trading_dates):
            # Get top stocks by market cap for this date
            top_stocks = self._get_top_stocks_by_market_cap(current_date)
            
            if len(top_stocks) < self.index_size:
                logger.warning(f"Only {len(top_stocks)} stocks available on {current_date} (need {self.index_size}), skipping")
                continue
            
            # Calculate equal weights
            weight = 1.0 / self.index_size
            
            # Store composition
            self._store_composition(current_date, top_stocks, weight)
            
            # Calculate performance
            if i == 0:
                # First day - set base value
                self._store_performance(current_date, self.base_value, 0.0, 0.0)
            else:
                # Calculate returns based on previous composition
                daily_return = self._calculate_daily_return(
                    trading_dates[i-1], 
                    current_date,
                    top_stocks
                )
                
                current_value = previous_value * (1 + daily_return)
                cumulative_return = (current_value / self.base_value - 1) * 100
                
                self._store_performance(
                    current_date, 
                    current_value, 
                    daily_return * 100,
                    cumulative_return
                )
                
                previous_value = current_value
            
            dates_processed += 1
        
        # Clear cache for affected date range
        self._invalidate_cache(start_date, end_date)
        
        return {
            "success": True,
            "message": f"Index built successfully for {dates_processed} trading days",
            "dates_processed": dates_processed,
            "start_date": start_date,
            "end_date": end_date
        }
    
    def get_performance(self, start_date: date, end_date: date) -> Dict:
        """Get index performance for date range."""
        # Check cache first
        cache_key = get_performance_cache_key(str(start_date), str(end_date))
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        with db.get_connection() as conn:
            df = conn.execute("""
                SELECT date, value, daily_return, cumulative_return
                FROM index_performance
                WHERE date >= ? AND date <= ?
                ORDER BY date
            """, (start_date, end_date)).pl()
            
            if df.is_empty():
                raise ValueError(f"No performance data available for date range {start_date} to {end_date}")
            
            # Calculate summary statistics
            summary = {
                "total_return": float(df['cumulative_return'].tail(1)[0]) if len(df) > 0 else 0.0,
                "average_daily_return": float(df['daily_return'].mean()) if len(df) > 1 else 0.0,
                "volatility": float(df['daily_return'].std()) if len(df) > 1 else 0.0,
                "max_daily_return": float(df['daily_return'].max()) if len(df) > 1 else 0.0,
                "min_daily_return": float(df['daily_return'].min()) if len(df) > 1 else 0.0,
                "sharpe_ratio": self._calculate_sharpe_ratio(df) if len(df) > 1 else 0.0
            }
            
            # Convert to response format
            performance_data = []
            for row in df.iter_rows(named=True):
                performance_data.append({
                    "date": row['date'],
                    "value": float(row['value']),
                    "daily_return": float(row['daily_return']) if row['daily_return'] else None,
                    "cumulative_return": float(row['cumulative_return']) if row['cumulative_return'] else None
                })
            
            result = {
                "start_date": start_date,
                "end_date": end_date,
                "total_days": len(performance_data),
                "performance_data": performance_data,
                "summary": summary
            }
            
            # Cache the result
            cache.set(cache_key, result)
            
            return result
    
    def get_composition(self, target_date: date) -> Dict:
        """Get index composition for a specific date."""
        # Check cache first
        cache_key = get_composition_cache_key(str(target_date))
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        with db.get_connection() as conn:
            df = conn.execute("""
                SELECT 
                    ic.ticker,
                    s.name,
                    ic.weight,
                    ic.market_cap,
                    s.sector,
                    s.industry
                FROM index_compositions ic
                JOIN stocks s ON ic.ticker = s.ticker
                WHERE ic.date = ?
                ORDER BY ic.market_cap DESC
            """, (target_date,)).pl()
            
            if df.is_empty():
                raise ValueError(f"No composition data available for date {target_date}")
            
            # Convert to response format
            compositions = []
            for row in df.iter_rows(named=True):
                compositions.append({
                    "ticker": row['ticker'],
                    "name": row['name'],
                    "weight": float(row['weight']),
                    "market_cap": float(row['market_cap']),
                    "sector": row['sector'],
                    "industry": row['industry']
                })
            
            result = {
                "date": target_date,
                "total_stocks": len(compositions),
                "compositions": compositions
            }
            
            # Cache the result
            cache.set(cache_key, result)
            
            return result
    
    def get_composition_changes(self, start_date: date, end_date: date) -> Dict:
        """Get composition changes between dates."""
        # Check cache first
        cache_key = get_changes_cache_key(str(start_date), str(end_date))
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        with db.get_connection() as conn:
            # Get all unique dates with compositions in range
            dates_df = conn.execute("""
                SELECT DISTINCT date 
                FROM index_compositions 
                WHERE date >= ? AND date <= ?
                ORDER BY date
            """, (start_date, end_date)).pl()
            
            if dates_df.is_empty():
                raise ValueError(f"No composition data available for date range {start_date} to {end_date}")
            
            dates = dates_df['date'].to_list()
            changes = []
            
            # Compare each date with the previous
            for i in range(1, len(dates)):
                prev_date = dates[i-1]
                curr_date = dates[i]
                
                # Get compositions for both dates
                prev_comp = conn.execute("""
                    SELECT ticker FROM index_compositions WHERE date = ?
                """, (prev_date,)).pl()['ticker'].to_list()
                
                curr_comp = conn.execute("""
                    SELECT ticker FROM index_compositions WHERE date = ?
                """, (curr_date,)).pl()['ticker'].to_list()
                
                # Find additions and removals
                added = set(curr_comp) - set(prev_comp)
                removed = set(prev_comp) - set(curr_comp)
                
                if added or removed:
                    # Get details for added stocks
                    stocks_added = []
                    if added:
                        added_df = conn.execute("""
                            SELECT ic.ticker, s.name, ic.market_cap
                            FROM index_compositions ic
                            JOIN stocks s ON ic.ticker = s.ticker
                            WHERE ic.date = ? AND ic.ticker IN ({})
                        """.format(','.join(['?'] * len(added))), 
                        (curr_date, *added)).pl()
                        
                        for row in added_df.iter_rows(named=True):
                            stocks_added.append({
                                "ticker": row['ticker'],
                                "name": row['name'],
                                "action": "added",
                                "market_cap": float(row['market_cap'])
                            })
                    
                    # Get details for removed stocks
                    stocks_removed = []
                    if removed:
                        removed_df = conn.execute("""
                            SELECT ic.ticker, s.name, ic.market_cap
                            FROM index_compositions ic
                            JOIN stocks s ON ic.ticker = s.ticker
                            WHERE ic.date = ? AND ic.ticker IN ({})
                        """.format(','.join(['?'] * len(removed))), 
                        (prev_date, *removed)).pl()
                        
                        for row in removed_df.iter_rows(named=True):
                            stocks_removed.append({
                                "ticker": row['ticker'],
                                "name": row['name'],
                                "action": "removed",
                                "market_cap": float(row['market_cap'])
                            })
                    
                    changes.append({
                        "date": curr_date,
                        "stocks_added": stocks_added,
                        "stocks_removed": stocks_removed,
                        "total_changes": len(stocks_added) + len(stocks_removed)
                    })
            
            result = {
                "start_date": start_date,
                "end_date": end_date,
                "total_change_dates": len(changes),
                "changes": changes
            }
            
            # Cache the result
            cache.set(cache_key, result)
            
            return result
    
    def _get_trading_dates(self, start_date: date, end_date: date) -> List[date]:
        """Get all trading dates in range."""
        with db.get_connection() as conn:
            df = conn.execute("""
                SELECT DISTINCT date 
                FROM daily_stock_data 
                WHERE date >= ? AND date <= ?
                ORDER BY date
            """, (start_date, end_date)).pl()
            
            return df['date'].to_list() if not df.is_empty() else []
    
    def _get_top_stocks_by_market_cap(self, target_date: date) -> List[Dict]:
        """Get top stocks by market cap for a specific date."""
        with db.get_connection() as conn:
            df = conn.execute("""
                SELECT ticker, market_cap
                FROM daily_stock_data
                WHERE date = ? AND market_cap > 0
                ORDER BY market_cap DESC
                LIMIT ?
            """, (target_date, self.index_size)).pl()
            
            return [
                {"ticker": row['ticker'], "market_cap": float(row['market_cap'])}
                for row in df.iter_rows(named=True)
            ]
    
    def _calculate_daily_return(self, prev_date: date, curr_date: date, current_stocks: List[Dict]) -> float:
        """Calculate daily return based on equal-weighted portfolio."""
        current_tickers = [stock['ticker'] for stock in current_stocks]
        
        with db.get_connection() as conn:
            # Get previous composition
            prev_comp_df = conn.execute("""
                SELECT ticker FROM index_compositions WHERE date = ?
            """, (prev_date,)).pl()
            
            if prev_comp_df.is_empty():
                return 0.0
            
            prev_tickers = prev_comp_df['ticker'].to_list()
            
            # Calculate returns for stocks that were in previous composition
            returns_df = conn.execute("""
                SELECT 
                    d1.ticker,
                    d1.close_price as prev_close,
                    d2.close_price as curr_close
                FROM daily_stock_data d1
                JOIN daily_stock_data d2 ON d1.ticker = d2.ticker
                WHERE d1.date = ? AND d2.date = ?
                AND d1.ticker IN ({})
            """.format(','.join(['?'] * len(prev_tickers))), 
            (prev_date, curr_date, *prev_tickers)).pl()
            
            if returns_df.is_empty():
                return 0.0
            
            # Calculate equal-weighted return
            returns_df = returns_df.with_columns(
                ((pl.col('curr_close') / pl.col('prev_close')) - 1).alias('return')
            )
            
            # Equal weight for each stock
            weight = 1.0 / len(prev_tickers)
            total_return = float(returns_df['return'].sum() * weight)
            
            return total_return
    
    def _store_composition(self, date: date, stocks: List[Dict], weight: float):
        """Store index composition for a date."""
        with db.get_connection() as conn:
            for stock in stocks:
                conn.execute("""
                    INSERT INTO index_compositions (date, ticker, weight, market_cap)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT (date, ticker) DO UPDATE SET
                        weight = EXCLUDED.weight,
                        market_cap = EXCLUDED.market_cap
                """, (date, stock['ticker'], weight, stock['market_cap']))
            conn.commit()
    
    def _store_performance(self, date: date, value: float, daily_return: float, cumulative_return: float):
        """Store index performance for a date."""
        with db.get_connection() as conn:
            conn.execute("""
                INSERT INTO index_performance (date, value, daily_return, cumulative_return)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (date) DO UPDATE SET
                    value = EXCLUDED.value,
                    daily_return = EXCLUDED.daily_return,
                    cumulative_return = EXCLUDED.cumulative_return
            """, (date, value, daily_return, cumulative_return))
            conn.commit()
    
    def _clear_index_data(self, start_date: date, end_date: date):
        """Clear existing index data for date range."""
        with db.get_connection() as conn:
            conn.execute("""
                DELETE FROM index_compositions WHERE date >= ? AND date <= ?
            """, (start_date, end_date))
            conn.execute("""
                DELETE FROM index_performance WHERE date >= ? AND date <= ?
            """, (start_date, end_date))
            conn.commit()
    
    def _invalidate_cache(self, start_date: date, end_date: date):
        """Invalidate cache entries affected by the date range."""
        # Clear performance cache entries that overlap with the date range
        cache.delete_pattern(f"index:performance:*")
        
        # Clear composition cache entries in the date range
        current = start_date
        while current <= end_date:
            cache.delete(get_composition_cache_key(str(current)))
            current += timedelta(days=1)
        
        # Clear all composition changes cache
        cache.delete_pattern(f"index:changes:*")
    
    def _calculate_sharpe_ratio(self, df: pl.DataFrame, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio (annualized)."""
        if len(df) < 2:
            return 0.0
        
        daily_returns = df['daily_return'].drop_nulls()
        if len(daily_returns) == 0:
            return 0.0
        
        avg_return = float(daily_returns.mean())
        std_return = float(daily_returns.std())
        
        if std_return == 0:
            return 0.0
        
        # Annualize (assuming 252 trading days)
        annual_return = avg_return * 252
        annual_std = std_return * (252 ** 0.5)
        
        sharpe = (annual_return - risk_free_rate) / annual_std
        return sharpe


# Global service instance
index_service = IndexService()