"""API endpoints for the index tracker."""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from datetime import date
from typing import Optional
import logging

from app.models.schemas import (
    BuildIndexRequest,
    BuildIndexResponse,
    ExportDataRequest,
    ExportDataResponse,
    IndexPerformanceResponse,
    IndexCompositionResponse,
    CompositionChangesResponse,
    ErrorResponse
)
from app.services.index_service import index_service
from app.services.export_service import export_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/build-index", response_model=BuildIndexResponse)
async def build_index(request: BuildIndexRequest):
    """
    Build the equal-weighted index for the specified date range.
    
    This endpoint constructs the index dynamically by:
    - Selecting the top 100 stocks by market cap for each trading day
    - Assigning equal weights (1/100) to each stock
    - Calculating daily returns and cumulative performance
    - Storing the results in the database and caching them
    """
    try:
        result = index_service.build_index(request.start_date, request.end_date)
        return BuildIndexResponse(**result)
    except ValueError as e:
        logger.error(f"Error building index: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error building index: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/index-performance", response_model=IndexPerformanceResponse)
async def get_index_performance(
    start_date: date = Query(..., description="Start date for performance data"),
    end_date: date = Query(..., description="End date for performance data")
):
    """
    Get index performance data for the specified date range.
    
    Returns:
    - Daily index values
    - Daily returns (percentage)
    - Cumulative returns (percentage)
    - Summary statistics (total return, volatility, Sharpe ratio, etc.)
    
    Results are cached for improved performance.
    """
    if end_date < start_date:
        raise HTTPException(
            status_code=400, 
            detail="end_date must be greater than or equal to start_date"
        )
    
    try:
        result = index_service.get_performance(start_date, end_date)
        return IndexPerformanceResponse(**result)
    except ValueError as e:
        logger.error(f"Error getting performance: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/index-composition", response_model=IndexCompositionResponse)
async def get_index_composition(
    date: date = Query(..., description="Date for which to get the index composition")
):
    """
    Get the index composition for a specific date.
    
    Returns the 100 stocks that comprise the index on the given date,
    including their weights, market caps, and sector information.
    
    Results are cached for improved performance.
    """
    try:
        result = index_service.get_composition(date)
        return IndexCompositionResponse(**result)
    except ValueError as e:
        logger.error(f"Error getting composition: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting composition: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/composition-changes", response_model=CompositionChangesResponse)
async def get_composition_changes(
    start_date: date = Query(..., description="Start date for composition changes"),
    end_date: date = Query(..., description="End date for composition changes")
):
    """
    Get composition changes between the specified dates.
    
    Returns all dates where the index composition changed, showing:
    - Stocks that were added to the index
    - Stocks that were removed from the index
    - Market cap information for context
    
    Results are cached for improved performance.
    """
    if end_date < start_date:
        raise HTTPException(
            status_code=400, 
            detail="end_date must be greater than or equal to start_date"
        )
    
    try:
        result = index_service.get_composition_changes(start_date, end_date)
        return CompositionChangesResponse(**result)
    except ValueError as e:
        logger.error(f"Error getting composition changes: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting composition changes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/export-data", response_model=ExportDataResponse)
async def export_data(request: ExportDataRequest):
    """
    Export index data to an Excel file.
    
    Creates a comprehensive Excel workbook containing:
    - Summary sheet with key metrics
    - Daily performance data
    - Daily index compositions
    - Composition changes over time
    
    The file is saved to the exports directory and can be downloaded.
    """
    try:
        result = export_service.export_to_excel(request.start_date, request.end_date)
        return ExportDataResponse(**result)
    except ValueError as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error exporting data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/export-data/download/{filename}")
async def download_export(filename: str):
    """
    Download an exported Excel file.
    
    This endpoint allows downloading of previously exported files.
    """
    import os
    from app.config import get_settings
    
    settings = get_settings()
    file_path = os.path.join(settings.export_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "index-tracker"}