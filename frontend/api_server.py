#!/usr/bin/env python3
"""
API Server for WildfireNowcast Frontend

This server provides REST API endpoints for the React frontend to interact
with the WildfireNowcast agent and NASA data sources.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directory to path to import the agent
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from fastapi import FastAPI, HTTPException, Query, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    import uvicorn
except ImportError:
    print("Installing FastAPI dependencies...")
    os.system("pip install fastapi uvicorn python-multipart")
    from fastapi import FastAPI, HTTPException, Query, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    import uvicorn

# Import your existing agent and tools
try:
    from wildfire_nowcast_agent import wildfire_nowcast_agent_local
    from tools.improved_nasa_tools import (
        fetch_firms_hotspots_enhanced,
        fetch_gibs_map_image,
        fetch_eonet_events_enhanced,
        get_nasa_data_summary_enhanced
    )
    from tools.threat_tools import assess_asset_threats, generate_threat_summary
    from tools.mapping_tools import generate_fire_map
    from tools.ics_tools import draft_ics_situation_report
except ImportError as e:
    print(f"Warning: Could not import agent modules: {e}")
    print("Make sure you're running this from the WildfireNowcast project root")
    # Create mock functions for development
    def wildfire_nowcast_agent_local(payload):
        return "Mock agent response - agent not available"
    
    def fetch_firms_hotspots_enhanced(*args, **kwargs):
        return json.dumps({"hotspots": [], "error": "Agent not available"})
    
    def fetch_gibs_map_image(*args, **kwargs):
        return json.dumps({"error": "Agent not available"})
    
    def fetch_eonet_events_enhanced(*args, **kwargs):
        return json.dumps({"events": [], "error": "Agent not available"})
    
    def get_nasa_data_summary_enhanced(*args, **kwargs):
        return json.dumps({"error": "Agent not available"})
    
    def assess_asset_threats(*args, **kwargs):
        return json.dumps({"error": "Agent not available"})
    
    def generate_threat_summary(*args, **kwargs):
        return json.dumps({"error": "Agent not available"})
    
    def generate_fire_map(*args, **kwargs):
        return json.dumps({"error": "Agent not available"})
    
    def draft_ics_situation_report(*args, **kwargs):
        return json.dumps({"error": "Agent not available"})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="WildfireNowcast Frontend API",
    description="REST API for WildfireNowcast Frontend",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from frontend build
if os.path.exists("dist"):
    app.mount("/static", StaticFiles(directory="dist"), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the React frontend"""
    if os.path.exists("dist/index.html"):
        return FileResponse("dist/index.html")
    else:
        return {"message": "Frontend not built. Run 'npm run build' in the frontend directory."}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "WildfireNowcast Frontend API"
    }

@app.get("/api/firms-hotspots")
async def get_firms_hotspots(
    area: str = Query("global", description="Geographic area"),
    days_back: int = Query(1, description="Days to look back"),
    confidence: str = Query("nominal", description="Confidence level"),
    satellite: str = Query("both", description="Satellite source")
):
    """Get FIRMS hotspot data"""
    try:
        result = fetch_firms_hotspots_enhanced(
            area=area,
            days_back=days_back,
            confidence=confidence,
            satellite=satellite,
            format="json"
        )
        return json.loads(result)
    except Exception as e:
        logger.error(f"Error fetching FIRMS hotspots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gibs-map-image")
async def get_gibs_map_image(
    layer_name: str = Query("MODIS_Terra_CorrectedReflectance_TrueColor", description="GIBS layer"),
    bbox: str = Query("-180,-90,180,90", description="Bounding box"),
    size: str = Query("1200,600", description="Image size"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    projection: str = Query("epsg4326", description="Map projection")
):
    """Get GIBS map image"""
    try:
        result = fetch_gibs_map_image(
            layer_name=layer_name,
            bbox=bbox,
            size=size,
            date=date,
            projection=projection,
            format="image/png"
        )
        return json.loads(result)
    except Exception as e:
        logger.error(f"Error fetching GIBS map image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/eonet-events")
async def get_eonet_events(
    category: str = Query("wildfires", description="Event category"),
    days_back: int = Query(30, description="Days to look back"),
    status: str = Query("open", description="Event status"),
    limit: int = Query(100, description="Maximum events"),
    source: Optional[str] = Query(None, description="Data source")
):
    """Get EONET events"""
    try:
        result = fetch_eonet_events_enhanced(
            category=category,
            days_back=days_back,
            status=status,
            limit=limit,
            source=source
        )
        return json.loads(result)
    except Exception as e:
        logger.error(f"Error fetching EONET events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/threat-assessment")
async def get_threat_assessment(request: Request):
    """Get threat assessment for hotspots"""
    try:
        data = await request.json()
        hotspots_data = data.get("hotspots_data", {})
        assets_data = data.get("assets_data", {})
        
        # Use your existing threat assessment tools
        result = assess_asset_threats(
            hotspots_data=hotspots_data,
            assets_data=assets_data,
            max_distance_km=50
        )
        return json.loads(result)
    except Exception as e:
        logger.error(f"Error assessing threats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fire-map")
async def generate_fire_map_endpoint(request: Request):
    """Generate fire map"""
    try:
        data = await request.json()
        hotspots_data = data.get("hotspots_data", {})
        assets_data = data.get("assets_data", {})
        map_center = data.get("map_center", [34.0522, -118.2437])
        zoom_level = data.get("zoom_level", 8)
        
        result = generate_fire_map(
            hotspots_data=hotspots_data,
            assets_data=assets_data,
            map_center=map_center,
            zoom_level=zoom_level,
            include_assets=True
        )
        return json.loads(result)
    except Exception as e:
        logger.error(f"Error generating fire map: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ics-report")
async def generate_ics_report(request: Request):
    """Generate ICS situation report"""
    try:
        data = await request.json()
        hotspots_data = data.get("hotspots_data", {})
        threat_data = data.get("threat_data", {})
        evacuation_data = data.get("evacuation_data", {})
        incident_name = data.get("incident_name", "Wildfire Incident")
        incident_number = data.get("incident_number", "WF-001")
        
        result = draft_ics_situation_report(
            hotspots_data=hotspots_data,
            threat_data=threat_data,
            evacuation_data=evacuation_data,
            incident_name=incident_name,
            incident_number=incident_number
        )
        return json.loads(result)
    except Exception as e:
        logger.error(f"Error generating ICS report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agent-query")
async def query_agent(request: Request):
    """Query the WildfireNowcast agent"""
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Use your existing agent
        response = wildfire_nowcast_agent_local({"prompt": prompt})
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "query": prompt
        }
    except Exception as e:
        logger.error(f"Error querying agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nasa-summary")
async def get_nasa_summary(
    area: str = Query("usa", description="Geographic area"),
    days_back: int = Query(1, description="Days to look back"),
    include_gibs: bool = Query(True, description="Include GIBS data"),
    include_eonet: bool = Query(True, description="Include EONET data")
):
    """Get comprehensive NASA data summary"""
    try:
        result = get_nasa_data_summary_enhanced(
            area=area,
            days_back=days_back,
            include_gibs=include_gibs,
            include_eonet=include_eonet
        )
        return json.loads(result)
    except Exception as e:
        logger.error(f"Error getting NASA summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
