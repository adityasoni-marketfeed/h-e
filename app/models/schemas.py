"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, Field, validator
from datetime import date
from typing import List, Optional, Dict
from decimal import Decimal


class BuildIndexRequest(BaseModel):
    """Request model for building index."""
    start_date: date = Field(..., description="Start date for index construction")
    end_date: Optional[date] = Field(None, description="End date for index construction (optional)")
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if v and 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be greater than or equal to start_date')
        return v


class ExportDataRequest(BaseModel):
    """Request model for exporting data."""
    start_date: date = Field(..., description="Start date for data export")
    end_date: date = Field(..., description="End date for data export")
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be greater than or equal to start_date')
        return v


class StockComposition(BaseModel):
    """Stock composition in the index."""
    ticker: str
    name: str
    weight: float = Field(..., ge=0, le=1, description="Weight in the index (0-1)")
    market_cap: float = Field(..., description="Market capitalization in USD")
    sector: Optional[str] = None
    industry: Optional[str] = None


class IndexCompositionResponse(BaseModel):
    """Response model for index composition."""
    date: date
    total_stocks: int
    compositions: List[StockComposition]


class PerformanceData(BaseModel):
    """Daily performance data."""
    date: date
    value: float = Field(..., description="Index value")
    daily_return: Optional[float] = Field(None, description="Daily return percentage")
    cumulative_return: Optional[float] = Field(None, description="Cumulative return percentage")


class IndexPerformanceResponse(BaseModel):
    """Response model for index performance."""
    start_date: date
    end_date: date
    total_days: int
    performance_data: List[PerformanceData]
    summary: Dict[str, float] = Field(..., description="Performance summary statistics")


class CompositionChange(BaseModel):
    """Composition change details."""
    ticker: str
    name: str
    action: str = Field(..., description="'added' or 'removed'")
    market_cap: float


class CompositionChangeDate(BaseModel):
    """Composition changes for a specific date."""
    date: date
    stocks_added: List[CompositionChange]
    stocks_removed: List[CompositionChange]
    total_changes: int


class CompositionChangesResponse(BaseModel):
    """Response model for composition changes."""
    start_date: date
    end_date: date
    total_change_dates: int
    changes: List[CompositionChangeDate]


class BuildIndexResponse(BaseModel):
    """Response model for build index operation."""
    success: bool
    message: str
    dates_processed: int
    start_date: date
    end_date: date


class ExportDataResponse(BaseModel):
    """Response model for export data operation."""
    success: bool
    file_path: str
    file_size_mb: float


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    status_code: int