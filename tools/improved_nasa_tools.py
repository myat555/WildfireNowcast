"""
Improved NASA Data Integration Tools for Wildfire Nowcast Agent

This module provides enhanced tools for accessing NASA's Earth observation data sources
following NASA's official documentation and best practices.
"""

import requests
import json
import logging
import os
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from strands import tool
import pandas as pd
import numpy as np
from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# NASA API Configuration
FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api"
GIBS_WMS_BASE_URL = "https://gibs.earthdata.nasa.gov/wms"
GIBS_WMTS_BASE_URL = "https://gibs.earthdata.nasa.gov/wmts"
EONET_BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3"

class ImprovedNASAAPIClient:
    """Enhanced client for accessing NASA APIs with proper error handling"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('NASA_FIRMS_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WildfireNowcastAgent/2.0'
        })
    
    def _make_request(self, url: str, params: Dict = None, timeout: int = 30) -> Dict:
        """Make a request to NASA API with enhanced error handling"""
        try:
            if params is None:
                params = {}
            
            if self.api_key:
                params['api_key'] = self.api_key
            
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            
            # Handle different content types
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                return response.json()
            elif 'text/csv' in content_type:
                return self._parse_csv_response(response.text)
            else:
                return {"data": response.text, "content_type": content_type}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"NASA API request failed: {e}")
            raise Exception(f"Failed to fetch data from NASA API: {e}")
    
    def _parse_csv_response(self, csv_text: str) -> Dict:
        """Parse CSV response from FIRMS API"""
        lines = csv_text.strip().split('\n')
        if len(lines) < 2:
            return {"hotspots": [], "count": 0}
        
        headers = lines[0].split(',')
        hotspots = []
        
        for line in lines[1:]:
            if line.strip():
                values = line.split(',')
                hotspot = dict(zip(headers, values))
                hotspots.append(hotspot)
        
        return {"hotspots": hotspots, "count": len(hotspots)}

class GIBSClient:
    """Enhanced GIBS client following NASA documentation"""
    
    def __init__(self):
        self.wms_services = {}
        self.wmts_services = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize WMS and WMTS services for different projections"""
        projections = {
            'epsg4326': 'epsg4326/best',
            'epsg3857': 'epsg3857/best', 
            'epsg3413': 'epsg3413/best',  # Arctic
            'epsg3031': 'epsg3031/best'   # Antarctic
        }
        
        for proj, path in projections.items():
            try:
                wms_url = f"{GIBS_WMS_BASE_URL}/{path}/wms.cgi?"
                self.wms_services[proj] = WebMapService(wms_url, version='1.1.1')
                logger.info(f"Initialized WMS service for {proj}")
            except Exception as e:
                logger.warning(f"Failed to initialize WMS service for {proj}: {e}")
    
    def get_capabilities(self, projection: str = 'epsg4326') -> Dict:
        """Get WMS capabilities for a specific projection"""
        if projection not in self.wms_services:
            raise ValueError(f"Unsupported projection: {projection}")
        
        wms = self.wms_services[projection]
        capabilities = {
            'projection': projection,
            'layers': list(wms.contents.keys()),
            'formats': wms.getOperationByName('GetMap').formatOptions,
            'version': wms.version
        }
        
        return capabilities
    
    def get_layer_info(self, layer_name: str, projection: str = 'epsg4326') -> Dict:
        """Get detailed information about a specific layer"""
        if projection not in self.wms_services:
            raise ValueError(f"Unsupported projection: {projection}")
        
        wms = self.wms_services[projection]
        if layer_name not in wms.contents:
            raise ValueError(f"Layer not found: {layer_name}")
        
        layer = wms.contents[layer_name]
        return {
            'name': layer_name,
            'title': layer.title,
            'abstract': layer.abstract,
            'boundingBox': layer.boundingBox,
            'timeExtent': getattr(layer, 'timeExtent', None),
            'styles': list(layer.styles.keys()) if layer.styles else []
        }
    
    def get_map_image(self, 
                     layer_name: str,
                     bbox: Tuple[float, float, float, float],
                     size: Tuple[int, int] = (1200, 600),
                     date: str = None,
                     projection: str = 'epsg4326',
                     format: str = 'image/png') -> bytes:
        """Get map image from GIBS WMS following NASA documentation"""
        if projection not in self.wms_services:
            raise ValueError(f"Unsupported projection: {projection}")
        
        wms = self.wms_services[projection]
        
        # Set default date to today if not provided
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            img = wms.getmap(
                layers=[layer_name],
                srs=f'epsg:{projection.replace("epsg", "")}',
                bbox=bbox,
                size=size,
                time=date,
                format=format,
                transparent=True
            )
            return img.read()
        except Exception as e:
            logger.error(f"Error getting map image: {e}")
            raise

class EONETClient:
    """Enhanced EONET client with proper API usage"""
    
    def __init__(self):
        self.base_url = EONET_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WildfireNowcastAgent/2.0'
        })
    
    def get_events(self, 
                   category: str = "wildfires",
                   days_back: int = 30,
                   status: str = "open",
                   limit: int = 100,
                   source: str = None) -> Dict:
        """Get events from EONET with enhanced filtering"""
        url = f"{self.base_url}/events"
        
        params = {
            'category': category,
            'days': days_back,
            'status': status,
            'limit': limit
        }
        
        if source:
            params['source'] = source
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching EONET events: {e}")
            raise
    
    def get_event_details(self, event_id: str) -> Dict:
        """Get detailed information about a specific event"""
        url = f"{self.base_url}/events/{event_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching event details: {e}")
            raise
    
    def get_categories(self) -> Dict:
        """Get available event categories"""
        url = f"{self.base_url}/categories"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            raise
    
    def get_sources(self) -> Dict:
        """Get available data sources"""
        url = f"{self.base_url}/sources"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching sources: {e}")
            raise

# Initialize clients
nasa_client = ImprovedNASAAPIClient()
gibs_client = GIBSClient()
eonet_client = EONETClient()

@tool
def fetch_firms_hotspots_enhanced(
    area: str = "global",
    days_back: int = 1,
    confidence: str = "nominal",
    satellite: str = "both",
    format: str = "json"
) -> str:
    """
    Enhanced FIRMS hotspot retrieval with better error handling and data processing.
    
    Args:
        area: Geographic area ('global', 'usa', 'canada', 'australia', etc.)
        days_back: Number of days to look back (1-7)
        confidence: Confidence level ('nominal', 'low', 'high')
        satellite: Satellite source ('modis', 'viirs', 'both')
        format: Response format ('json', 'csv')
    
    Returns:
        JSON string containing enhanced hotspot data
    """
    try:
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
        
        # Build FIRMS API URL based on format
        if format == 'json' and nasa_client.api_key:
            url = f"{FIRMS_BASE_URL}/area/json/{nasa_client.api_key}/{satellite}/{area_code}/{days_back}"
        else:
            # Use CSV format (public access)
            url = f"{FIRMS_BASE_URL}/area/csv/public/{satellite}/{area_code}/{days_back}"
        
        data = nasa_client._make_request(url)
        
        # Enhanced data processing
        hotspots = data.get("hotspots", [])
        processed_hotspots = []
        
        for hotspot in hotspots:
            processed_hotspot = {
                "latitude": float(hotspot.get('latitude', 0)),
                "longitude": float(hotspot.get('longitude', 0)),
                "brightness": float(hotspot.get('brightness', 0)),
                "scan": float(hotspot.get('scan', 0)),
                "track": float(hotspot.get('track', 0)),
                "acq_date": hotspot.get('acq_date', ''),
                "acq_time": hotspot.get('acq_time', ''),
                "satellite": hotspot.get('satellite', ''),
                "confidence": hotspot.get('confidence', ''),
                "version": hotspot.get('version', ''),
                "bright_t31": float(hotspot.get('bright_t31', 0)),
                "frp": float(hotspot.get('frp', 0)),
                "daynight": hotspot.get('daynight', '')
            }
            processed_hotspots.append(processed_hotspot)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "area": area,
            "days_back": days_back,
            "satellite": satellite,
            "confidence": confidence,
            "format": format,
            "hotspot_count": len(processed_hotspots),
            "hotspots": processed_hotspots,
            "data_source": "NASA FIRMS",
            "api_version": "2.0"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error fetching FIRMS hotspots: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "hotspot_count": 0,
            "hotspots": [],
            "data_source": "NASA FIRMS"
        })

@tool
def get_gibs_capabilities(projection: str = "epsg4326") -> str:
    """
    Get GIBS WMS capabilities for available layers and services.
    
    Args:
        projection: Map projection ('epsg4326', 'epsg3857', 'epsg3413', 'epsg3031')
    
    Returns:
        JSON string containing GIBS capabilities information
    """
    try:
        capabilities = gibs_client.get_capabilities(projection)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "projection": projection,
            "service_type": "WMS",
            "capabilities": capabilities,
            "data_source": "NASA GIBS"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting GIBS capabilities: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "data_source": "NASA GIBS"
        })

@tool
def get_gibs_layer_info(layer_name: str, projection: str = "epsg4326") -> str:
    """
    Get detailed information about a specific GIBS layer.
    
    Args:
        layer_name: Name of the GIBS layer
        projection: Map projection ('epsg4326', 'epsg3857', 'epsg3413', 'epsg3031')
    
    Returns:
        JSON string containing layer information
    """
    try:
        layer_info = gibs_client.get_layer_info(layer_name, projection)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "layer_info": layer_info,
            "projection": projection,
            "data_source": "NASA GIBS"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting layer info: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "data_source": "NASA GIBS"
        })

@tool
def fetch_gibs_map_image(
    layer_name: str = "MODIS_Terra_CorrectedReflectance_TrueColor",
    bbox: str = "-180,-90,180,90",
    size: str = "1200,600",
    date: str = None,
    projection: str = "epsg4326",
    format: str = "image/png"
) -> str:
    """
    Fetch map image from GIBS WMS following NASA documentation best practices.
    
    Args:
        layer_name: GIBS layer identifier
        bbox: Bounding box as "west,south,east,north"
        size: Image size as "width,height"
        date: Date in YYYY-MM-DD format (default: today)
        projection: Map projection ('epsg4326', 'epsg3857', 'epsg3413', 'epsg3031')
        format: Image format ('image/png', 'image/jpeg', 'image/tiff')
    
    Returns:
        JSON string containing image metadata and base64 encoded image
    """
    try:
        # Parse parameters
        west, south, east, north = map(float, bbox.split(','))
        width, height = map(int, size.split(','))
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Get map image
        image_data = gibs_client.get_map_image(
            layer_name=layer_name,
            bbox=(west, south, east, north),
            size=(width, height),
            date=date,
            projection=projection,
            format=format
        )
        
        # Encode image as base64 for JSON transport
        import base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "layer_name": layer_name,
            "bbox": bbox,
            "size": size,
            "date": date,
            "projection": projection,
            "format": format,
            "image_data": image_b64,
            "image_size_bytes": len(image_data),
            "data_source": "NASA GIBS"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error fetching GIBS map image: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "data_source": "NASA GIBS"
        })

@tool
def fetch_eonet_events_enhanced(
    category: str = "wildfires",
    days_back: int = 30,
    status: str = "open",
    limit: int = 100,
    source: str = None
) -> str:
    """
    Enhanced EONET events retrieval with better filtering and data processing.
    
    Args:
        category: Event category ('wildfires', 'all', 'volcanoes', etc.)
        days_back: Number of days to look back
        status: Event status ('open', 'closed', 'all')
        limit: Maximum number of events to return
        source: Specific data source to filter by
    
    Returns:
        JSON string containing enhanced EONET event data
    """
    try:
        data = eonet_client.get_events(
            category=category,
            days_back=days_back,
            status=status,
            limit=limit,
            source=source
        )
        
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
                "sources": [src.get('id') for src in event.get('sources', [])],
                "geometry": event.get('geometry'),
                "date": event.get('date'),
                "status": event.get('status'),
                "closed": event.get('closed')
            }
            processed_events.append(processed_event)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "days_back": days_back,
            "status": status,
            "limit": limit,
            "source": source,
            "event_count": len(processed_events),
            "events": processed_events,
            "data_source": "NASA EONET"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error fetching EONET events: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "event_count": 0,
            "events": [],
            "data_source": "NASA EONET"
        })

@tool
def get_eonet_categories() -> str:
    """
    Get available EONET event categories.
    
    Returns:
        JSON string containing available categories
    """
    try:
        data = eonet_client.get_categories()
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "categories": data.get('categories', []),
            "data_source": "NASA EONET"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error fetching EONET categories: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "data_source": "NASA EONET"
        })

@tool
def get_eonet_sources() -> str:
    """
    Get available EONET data sources.
    
    Returns:
        JSON string containing available sources
    """
    try:
        data = eonet_client.get_sources()
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "sources": data.get('sources', []),
            "data_source": "NASA EONET"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error fetching EONET sources: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "data_source": "NASA EONET"
        })

@tool
def get_nasa_data_summary_enhanced(
    area: str = "usa",
    days_back: int = 1,
    include_gibs: bool = True,
    include_eonet: bool = True
) -> str:
    """
    Get comprehensive summary of NASA wildfire data from all sources with enhanced processing.
    
    Args:
        area: Geographic area to analyze
        days_back: Number of days to look back
        include_gibs: Whether to include GIBS capabilities info
        include_eonet: Whether to include EONET events
    
    Returns:
        JSON string containing integrated data summary
    """
    try:
        # Fetch FIRMS data
        firms_data = json.loads(fetch_firms_hotspots_enhanced(
            area=area, 
            days_back=days_back
        ))
        
        # Fetch EONET data if requested
        eonet_data = None
        if include_eonet:
            eonet_data = json.loads(fetch_eonet_events_enhanced(
                days_back=days_back
            ))
        
        # Get GIBS capabilities if requested
        gibs_capabilities = None
        if include_gibs:
            gibs_capabilities = json.loads(get_gibs_capabilities())
        
        # Create enhanced summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "area": area,
            "days_back": days_back,
            "data_sources": {
                "firms": {
                    "hotspot_count": firms_data.get("hotspot_count", 0),
                    "status": "success" if "error" not in firms_data else "error",
                    "error": firms_data.get("error"),
                    "api_version": firms_data.get("api_version", "1.0")
                }
            },
            "total_hotspots": firms_data.get("hotspot_count", 0),
            "data_freshness": "real-time" if days_back <= 1 else f"{days_back} days old"
        }
        
        if eonet_data:
            summary["data_sources"]["eonet"] = {
                "event_count": eonet_data.get("event_count", 0),
                "status": "success" if "error" not in eonet_data else "error",
                "error": eonet_data.get("error")
            }
            summary["total_events"] = eonet_data.get("event_count", 0)
        
        if gibs_capabilities:
            summary["data_sources"]["gibs"] = {
                "available_layers": len(gibs_capabilities.get("capabilities", {}).get("layers", [])),
                "status": "success" if "error" not in gibs_capabilities else "error",
                "error": gibs_capabilities.get("error")
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
