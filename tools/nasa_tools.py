"""
NASA Data Integration Tools for Wildfire Nowcast Agent

This module provides tools for accessing NASA's Earth observation data sources
including FIRMS (fire hotspots), GIBS (satellite imagery), and EONET (events).
"""

import requests
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from strands import tool
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# NASA API Configuration
FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api"
GIBS_BASE_URL = "https://gibs.earthdata.nasa.gov/wmts"
EONET_BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3"

class NASAAPIClient:
    """Client for accessing NASA APIs"""
    
    def __init__(self, api_key: Optional[str] = None):
        # Use provided API key or get from environment variables
        self.api_key = api_key or os.getenv('NASA_FIRMS_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WildfireNowcastAgent/1.0'
        })
    
    def _make_request(self, url: str, params: Dict = None) -> Dict:
        """Make a request to NASA API with error handling"""
        try:
            if params is None:
                params = {}
            
            if self.api_key:
                params['api_key'] = self.api_key
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"NASA API request failed: {e}")
            raise Exception(f"Failed to fetch data from NASA API: {e}")

@tool
def fetch_firms_hotspots(
    area: str = "global",
    days_back: int = 1,
    confidence: str = "nominal",
    satellite: str = "both"
) -> str:
    """
    Fetch near-real-time MODIS/VIIRS wildfire hotspots from NASA FIRMS.
    
    Args:
        area: Geographic area to search ('global', 'usa', 'canada', 'australia', etc.)
        days_back: Number of days to look back (1-7)
        confidence: Confidence level ('nominal', 'low', 'high')
        satellite: Satellite source ('modis', 'viirs', 'both')
    
    Returns:
        JSON string containing hotspot data with coordinates, confidence, and timestamps
    """
    try:
        client = NASAAPIClient()
        
        # Map area names to FIRMS area codes
        area_mapping = {
            'global': 'global',
            'usa': 'usa',
            'canada': 'canada', 
            'australia': 'australia',
            'europe': 'europe',
            'asia': 'asia',
            'africa': 'africa',
            'south_america': 'south_america'
        }
        
        area_code = area_mapping.get(area.lower(), 'global')
        
        # Build FIRMS API URL
        url = f"{FIRMS_BASE_URL}/area/csv/{client.api_key or 'public'}/{satellite}/{area_code}/{days_back}"
        
        # For CSV data, we need to handle it differently
        if client.api_key:
            # Use JSON API if we have an API key
            url = f"{FIRMS_BASE_URL}/area/json/{client.api_key}/{satellite}/{area_code}/{days_back}"
            data = client._make_request(url)
        else:
            # Use public CSV endpoint
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse CSV data
            csv_data = response.text
            lines = csv_data.strip().split('\n')
            
            if len(lines) < 2:
                return json.dumps({"hotspots": [], "count": 0, "message": "No hotspots found"})
            
            # Parse CSV headers and data
            headers = lines[0].split(',')
            hotspots = []
            
            for line in lines[1:]:
                if line.strip():
                    values = line.split(',')
                    hotspot = dict(zip(headers, values))
                    hotspots.append(hotspot)
            
            data = {"hotspots": hotspots, "count": len(hotspots)}
        
        # Process and format the data
        processed_data = {
            "timestamp": datetime.now().isoformat(),
            "area": area,
            "days_back": days_back,
            "satellite": satellite,
            "confidence": confidence,
            "hotspot_count": len(data.get("hotspots", [])),
            "hotspots": data.get("hotspots", [])
        }
        
        return json.dumps(processed_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error fetching FIRMS hotspots: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "hotspot_count": 0,
            "hotspots": []
        })

@tool
def fetch_gibs_tiles(
    layer: str = "MODIS_Terra_Aqua_CorrectedReflectance_Bands721",
    date: str = None,
    zoom_level: int = 6,
    bbox: str = None
) -> str:
    """
    Fetch GIBS WMTS tiles for wildfire mapping and visualization.
    
    Args:
        layer: GIBS layer identifier (default: MODIS corrected reflectance)
        date: Date in YYYY-MM-DD format (default: today)
        zoom_level: Zoom level for tiles (1-8)
        bbox: Bounding box as "west,south,east,north" (default: global)
    
    Returns:
        JSON string containing tile information and URLs
    """
    try:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if bbox is None:
            bbox = "-180,-90,180,90"  # Global coverage
        
        # Parse bounding box
        west, south, east, north = map(float, bbox.split(','))
        
        # Calculate tile coordinates for the given zoom level
        def deg2num(lat_deg, lon_deg, zoom):
            import math
            lat_rad = math.radians(lat_deg)
            n = 2.0 ** zoom
            xtile = int((lon_deg + 180.0) / 360.0 * n)
            ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
            return (xtile, ytile)
        
        # Get tile bounds
        x_min, y_max = deg2num(north, west, zoom_level)
        x_max, y_min = deg2num(south, east, zoom_level)
        
        tiles = []
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                tile_url = f"{GIBS_BASE_URL}/{layer}/default/{date}/EPSG4326_1km/{zoom_level}/{y}/{x}.jpg"
                tiles.append({
                    "x": x,
                    "y": y,
                    "url": tile_url,
                    "zoom_level": zoom_level
                })
        
        tile_data = {
            "timestamp": datetime.now().isoformat(),
            "layer": layer,
            "date": date,
            "zoom_level": zoom_level,
            "bbox": bbox,
            "tile_count": len(tiles),
            "tiles": tiles
        }
        
        return json.dumps(tile_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error fetching GIBS tiles: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "tile_count": 0,
            "tiles": []
        })

@tool
def fetch_eonet_events(
    category: str = "wildfires",
    days_back: int = 30,
    status: str = "open"
) -> str:
    """
    Fetch wildfire events from NASA EONET for additional context.
    
    Args:
        category: Event category ('wildfires', 'all')
        days_back: Number of days to look back
        status: Event status ('open', 'closed', 'all')
    
    Returns:
        JSON string containing EONET event data
    """
    try:
        client = NASAAPIClient()
        
        # Build EONET API URL
        url = f"{EONET_BASE_URL}/events"
        
        params = {
            'category': category,
            'days': days_back,
            'status': status,
            'limit': 100
        }
        
        data = client._make_request(url, params)
        
        # Process events data
        events = data.get('events', [])
        processed_events = []
        
        for event in events:
            processed_event = {
                "id": event.get('id'),
                "title": event.get('title'),
                "description": event.get('description'),
                "link": event.get('link'),
                "categories": [cat.get('title') for cat in event.get('categories', [])],
                "geometry": event.get('geometry'),
                "date": event.get('date'),
                "status": event.get('status')
            }
            processed_events.append(processed_event)
        
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "days_back": days_back,
            "status": status,
            "event_count": len(processed_events),
            "events": processed_events
        }
        
        return json.dumps(event_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error fetching EONET events: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "event_count": 0,
            "events": []
        })

@tool
def get_nasa_data_summary(
    area: str = "usa",
    days_back: int = 1
) -> str:
    """
    Get a comprehensive summary of NASA wildfire data from all sources.
    
    Args:
        area: Geographic area to analyze
        days_back: Number of days to look back
    
    Returns:
        JSON string containing integrated data summary
    """
    try:
        # Fetch data from all sources
        firms_data = json.loads(fetch_firms_hotspots(area=area, days_back=days_back))
        eonet_data = json.loads(fetch_eonet_events(days_back=days_back))
        
        # Create summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "area": area,
            "days_back": days_back,
            "data_sources": {
                "firms": {
                    "hotspot_count": firms_data.get("hotspot_count", 0),
                    "status": "success" if "error" not in firms_data else "error",
                    "error": firms_data.get("error")
                },
                "eonet": {
                    "event_count": eonet_data.get("event_count", 0),
                    "status": "success" if "error" not in eonet_data else "error",
                    "error": eonet_data.get("error")
                }
            },
            "total_hotspots": firms_data.get("hotspot_count", 0),
            "total_events": eonet_data.get("event_count", 0),
            "data_freshness": "real-time" if days_back <= 1 else f"{days_back} days old"
        }
        
        return json.dumps(summary, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating NASA data summary: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "total_hotspots": 0,
            "total_events": 0
        })
