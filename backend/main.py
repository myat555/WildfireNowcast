"""
FastAPI Backend Server for WildfireNowcast Agent
Connects frontend to AWS Bedrock Agent and NASA APIs
"""

import os
import sys
import json
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
import boto3
from dotenv import load_dotenv
import logging
import aiohttp

# Add tools directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import NASA tools
try:
    from tools.improved_nasa_tools import (
        fetch_firms_hotspots_enhanced,
        fetch_gibs_map_image,
        fetch_eonet_events_enhanced,
        get_nasa_data_summary_enhanced
    )
    from tools.threat_tools import (
        assess_asset_threats,
        rank_fire_threats,
        calculate_evacuation_zones,
        generate_threat_summary
    )
    from tools.mapping_tools import (
        generate_fire_map,
        render_evacuation_map,
        create_progression_map,
        generate_threat_visualization
    )
    from tools.ics_tools import (
        draft_ics_situation_report,
        create_resource_recommendations
    )
    logger.info("Successfully imported all tools")
except Exception as e:
    logger.error(f"Error importing tools: {e}")
    raise

# Initialize FastAPI
app = FastAPI(
    title="WildfireNowcast API",
    description="Backend API for WildfireNowcast Agent",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS Clients
bedrock_agentcore_runtime = boto3.client('bedrock-agentcore', region_name=os.getenv('AWS_REGION', 'us-east-1'))

# Load agent configuration - Using AgentCore Runtime
RUNTIME_ID = os.getenv('BEDROCK_AGENTCORE_RUNTIME_ID')
SESSION_ID = os.getenv('SESSION_ID', 'default-session')

# Weather API Configuration
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Request/Response Models
class AgentQuery(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    enable_trace: Optional[bool] = False

class AgentResponse(BaseModel):
    response: str
    session_id: str
    trace: Optional[Dict] = None
    citations: Optional[List] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    agent_id: Optional[str] = None
    region: str

class NASAFIRMSRequest(BaseModel):
    area: str = "global"
    days_back: int = 1
    confidence: str = "nominal"
    satellite: str = "both"

class GIBSRequest(BaseModel):
    layer_name: str = "MODIS_Terra_CorrectedReflectance_TrueColor"
    bbox: str = "-180,-90,180,90"
    size: str = "1200,600"
    date: Optional[str] = None
    projection: str = "epsg4326"

class EONETRequest(BaseModel):
    category: str = "wildfires"
    days_back: int = 30
    status: str = "open"
    limit: int = 100
    source: Optional[str] = None

class WeatherRequest(BaseModel):
    latitude: float
    longitude: float

class WeatherResponse(BaseModel):
    temperature: float
    humidity: float
    wind_speed: float
    wind_direction: str
    pressure: float
    visibility: float
    description: str
    icon: str

# Helper Functions
def get_session_id() -> str:
    """Generate a unique session ID"""
    from uuid import uuid4
    return str(uuid4())

def degrees_to_direction(degrees: float) -> str:
    """Convert wind direction in degrees to cardinal direction"""
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    index = int((degrees + 11.25) / 22.5) % 16
    return directions[index]

async def fetch_weather_data(latitude: float, longitude: float) -> Dict[str, Any]:
    """Fetch real-time weather data from OpenWeatherMap API"""
    if not OPENWEATHER_API_KEY:
        logger.warning("OpenWeather API key not configured, returning mock data")
        return {
            "temperature": 75.0,
            "humidity": 20.0,
            "wind_speed": 15.0,
            "wind_direction": "NW",
            "pressure": 1013.25,
            "visibility": 10.0,
            "description": "Clear sky",
            "icon": "01d"
        }

    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": OPENWEATHER_API_KEY,
                "units": "imperial"  # Fahrenheit, mph
            }

            async with session.get(OPENWEATHER_BASE_URL, params=params) as response:
                if response.status != 200:
                    logger.error(f"Weather API error: {response.status}")
                    raise HTTPException(status_code=response.status, detail="Weather API error")

                data = await response.json()

                # Extract weather data
                return {
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
                    "wind_direction": degrees_to_direction(data["wind"].get("deg", 0)),
                    "pressure": data["main"]["pressure"],
                    "visibility": data.get("visibility", 10000) / 1609.34,  # Convert meters to miles
                    "description": data["weather"][0]["description"],
                    "icon": data["weather"][0]["icon"]
                }
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        # Return fallback data
        return {
            "temperature": 75.0,
            "humidity": 20.0,
            "wind_speed": 15.0,
            "wind_direction": "NW",
            "pressure": 1013.25,
            "visibility": 10.0,
            "description": "Data unavailable",
            "icon": "01d"
        }

async def invoke_bedrock_agentcore(prompt: str, session_id: str, enable_trace: bool = False) -> Dict:
    """Invoke Bedrock AgentCore Runtime and return response"""
    try:
        # TEMPORARY: Use local agent while debugging AgentCore deployment issues
        logger.info(f"Using local agent for session {session_id}")
        logger.warning("TEMPORARY: Using local agent instead of AgentCore runtime")

        # Import the local agent
        import sys
        sys.path.insert(0, '/Users/myatbhonesan/Desktop/Hackathon/WildfireNowcast')
        from wildfire_nowcast_agent import wildfire_agent

        # Invoke the agent directly using its async method
        response_text = await wildfire_agent.agent.invoke_async(prompt)

        return {
            'response': str(response_text),
            'session_id': session_id,
            'trace': None,
            'citations': None
        }

    except Exception as e:
        logger.error(f"Error invoking local agent: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return a helpful error message
        return {
            'response': f"I'm currently in demo mode. The agent said: Error - {str(e)}",
            'session_id': session_id,
            'trace': None,
            'citations': None
        }

async def stream_agent_response(prompt: str, session_id: str):
    """Stream agent response for real-time updates"""
    try:
        # Get account ID and region for ARN
        sts = boto3.client('sts', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        account_id = sts.get_caller_identity()['Account']
        region = os.getenv('AWS_REGION', 'us-east-1')

        runtime_arn = f"arn:aws:bedrock-agentcore:{region}:{account_id}:runtime/{RUNTIME_ID}"

        payload_dict = {'prompt': prompt, 'session_id': session_id}
        payload_bytes = json.dumps(payload_dict).encode('utf-8')

        response = bedrock_agentcore_runtime.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            payload=payload_bytes,
            contentType='application/json',
            accept='application/json'
        )

        response_body = response.get('payload', b'')
        if isinstance(response_body, bytes):
            response_body = response_body.decode('utf-8')

        try:
            response_data = json.loads(response_body)
            full_response = response_data if isinstance(response_data, str) else str(response_data)
        except json.JSONDecodeError:
            full_response = response_body

        yield f"data: {json.dumps({'type': 'chunk', 'content': full_response})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

# API Endpoints

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with API information"""
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": RUNTIME_ID,
        "region": os.getenv('AWS_REGION', 'us-east-1')
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": RUNTIME_ID,
        "region": os.getenv('AWS_REGION', 'us-east-1')
    }

@app.post("/api/agent-query", response_model=AgentResponse)
async def query_agent(query: AgentQuery):
    """Query the Bedrock agent"""
    session_id = query.session_id or get_session_id()

    result = await invoke_bedrock_agentcore(
        prompt=query.prompt,
        session_id=session_id,
        enable_trace=query.enable_trace
    )

    return result

@app.post("/api/agent-query-stream")
async def query_agent_stream(query: AgentQuery):
    """Stream agent responses in real-time"""
    session_id = query.session_id or get_session_id()

    return StreamingResponse(
        stream_agent_response(query.prompt, session_id),
        media_type="text/event-stream"
    )

@app.post("/api/firms-hotspots")
async def get_firms_hotspots(request: NASAFIRMSRequest):
    """Get NASA FIRMS fire hotspots"""
    try:
        logger.info(f"Fetching FIRMS hotspots: area={request.area}, days_back={request.days_back}")

        # Call the NASA FIRMS tool directly
        result_str = fetch_firms_hotspots_enhanced(
            area=request.area,
            days_back=request.days_back,
            confidence=request.confidence,
            satellite=request.satellite
        )

        result = json.loads(result_str)
        return result

    except Exception as e:
        logger.error(f"Error fetching FIRMS hotspots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gibs-map-image")
async def get_gibs_map(request: GIBSRequest):
    """Get NASA GIBS satellite imagery"""
    try:
        logger.info(f"Fetching GIBS imagery: layer={request.layer_name}, bbox={request.bbox}")

        # Call the NASA GIBS tool directly
        result_str = fetch_gibs_map_image(
            layer_name=request.layer_name,
            bbox=request.bbox,
            size=request.size,
            date=request.date,
            projection=request.projection
        )

        result = json.loads(result_str)
        return result

    except Exception as e:
        logger.error(f"Error fetching GIBS imagery: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/eonet-events")
async def get_eonet_events(request: EONETRequest):
    """Get NASA EONET wildfire events"""
    try:
        logger.info(f"Fetching EONET events: category={request.category}, days_back={request.days_back}")

        # Call the NASA EONET tool directly
        result_str = fetch_eonet_events_enhanced(
            category=request.category,
            days_back=request.days_back,
            status=request.status,
            limit=request.limit,
            source=request.source
        )

        result = json.loads(result_str)
        return result

    except Exception as e:
        logger.error(f"Error fetching EONET events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/threat-assessment")
async def assess_threats(data: Dict[str, Any]):
    """Assess threats to critical infrastructure"""
    try:
        logger.info("Performing threat assessment")

        hotspots_data = data.get("hotspots_data", {})
        assets_data = data.get("assets_data", {})

        # Call the threat assessment tool directly
        result_str = assess_asset_threats(
            hotspots_data=json.dumps(hotspots_data),
            assets_data=json.dumps(assets_data),
            max_distance_km=data.get("max_distance_km", 50.0)
        )

        result = json.loads(result_str)
        return result

    except Exception as e:
        logger.error(f"Error in threat assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fire-map")
async def create_fire_map(data: Dict[str, Any]):
    """Generate fire map visualization"""
    try:
        logger.info("Generating fire map")

        hotspots_data = data.get("hotspots_data", {})
        assets_data = data.get("assets_data")
        map_center = data.get("map_center", "39.8283,-98.5795")
        zoom_level = data.get("zoom_level", 6)

        # Call the fire map generation tool directly
        result_str = generate_fire_map(
            hotspots_data=json.dumps(hotspots_data),
            assets_data=json.dumps(assets_data) if assets_data else None,
            map_center=map_center,
            zoom_level=zoom_level,
            include_assets=bool(assets_data)
        )

        result = json.loads(result_str)
        return result

    except Exception as e:
        logger.error(f"Error generating fire map: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ics-report")
async def create_ics_report(data: Dict[str, Any]):
    """Generate ICS situation report"""
    try:
        logger.info("Generating ICS report")

        hotspots_data = data.get("hotspots_data", {})
        threat_data = data.get("threat_data", {})
        evacuation_data = data.get("evacuation_data", {})
        incident_name = data.get("incident_name", "Wildfire Incident")
        incident_number = data.get("incident_number")

        # Call the ICS report generation tool directly
        result_str = draft_ics_situation_report(
            hotspots_data=json.dumps(hotspots_data),
            threat_data=json.dumps(threat_data),
            evacuation_data=json.dumps(evacuation_data),
            incident_name=incident_name,
            incident_number=incident_number
        )

        result = json.loads(result_str)
        return result

    except Exception as e:
        logger.error(f"Error generating ICS report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evacuation-zones")
async def get_evacuation_zones(data: Dict[str, Any]):
    """Calculate evacuation zones around fire hotspots"""
    try:
        logger.info("Calculating evacuation zones")

        hotspots_data = data.get("hotspots_data", {})
        assets_data = data.get("assets_data", {})
        buffer_distance_km = data.get("buffer_distance_km", 5.0)

        # Call the evacuation zone calculation tool
        result_str = calculate_evacuation_zones(
            hotspots_data=json.dumps(hotspots_data),
            assets_data=json.dumps(assets_data),
            buffer_distance_km=buffer_distance_km
        )

        result = json.loads(result_str)
        return result

    except Exception as e:
        logger.error(f"Error calculating evacuation zones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rank-threats")
async def rank_threats(data: Dict[str, Any]):
    """Rank fire threats by various criteria"""
    try:
        logger.info("Ranking fire threats")

        hotspots_data = data.get("hotspots_data", {})
        criteria = data.get("criteria", "population_proximity")

        # Call the threat ranking tool
        result_str = rank_fire_threats(
            hotspots_data=json.dumps(hotspots_data),
            criteria=criteria
        )

        result = json.loads(result_str)
        return result

    except Exception as e:
        logger.error(f"Error ranking threats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evacuation-map")
async def get_evacuation_map(data: Dict[str, Any]):
    """Generate evacuation zone map"""
    try:
        logger.info("Generating evacuation map")

        hotspots_data = data.get("hotspots_data", {})
        assets_data = data.get("assets_data", {})
        evacuation_data = data.get("evacuation_data", {})
        map_center = data.get("map_center", "39.8283,-98.5795")
        zoom_level = data.get("zoom_level", 6)

        # Call the evacuation map rendering tool
        result_str = render_evacuation_map(
            hotspots_data=json.dumps(hotspots_data),
            assets_data=json.dumps(assets_data),
            evacuation_data=json.dumps(evacuation_data),
            map_center=map_center,
            zoom_level=zoom_level
        )

        result = json.loads(result_str)
        return result

    except Exception as e:
        logger.error(f"Error generating evacuation map: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/progression-map")
async def get_progression_map(data: Dict[str, Any]):
    """Generate fire progression map"""
    try:
        logger.info("Generating fire progression map")

        hotspots_data = data.get("hotspots_data", {})
        time_range_hours = data.get("time_range_hours", 24)
        map_center = data.get("map_center", "39.8283,-98.5795")
        zoom_level = data.get("zoom_level", 6)

        # Call the progression map tool
        result_str = create_progression_map(
            hotspots_data=json.dumps(hotspots_data),
            time_range_hours=time_range_hours,
            map_center=map_center,
            zoom_level=zoom_level
        )

        result = json.loads(result_str)
        return result

    except Exception as e:
        logger.error(f"Error generating progression map: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resource-recommendations")
async def get_resource_recommendations(data: Dict[str, Any]):
    """Generate resource allocation recommendations"""
    try:
        logger.info("Generating resource recommendations")

        threat_data = data.get("threat_data", {})
        evacuation_data = data.get("evacuation_data", {})
        resource_availability = data.get("resource_availability")

        # Call the resource recommendation tool
        result_str = create_resource_recommendations(
            threat_data=json.dumps(threat_data),
            evacuation_data=json.dumps(evacuation_data),
            resource_availability=json.dumps(resource_availability) if resource_availability else None
        )

        result = json.loads(result_str)
        return result

    except Exception as e:
        logger.error(f"Error generating resource recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nasa-summary")
async def get_nasa_summary(
    area: str = "usa",
    days_back: int = 1,
    include_gibs: bool = True,
    include_eonet: bool = True
):
    """Get comprehensive NASA data summary"""
    try:
        logger.info(f"Getting NASA data summary for {area}")

        # Call the NASA summary tool
        result_str = get_nasa_data_summary_enhanced(
            area=area,
            days_back=days_back,
            include_gibs=include_gibs,
            include_eonet=include_eonet
        )

        result = json.loads(result_str)
        return result

    except Exception as e:
        logger.error(f"Error getting NASA summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest):
    """Get real-time weather data for a specific location"""
    try:
        logger.info(f"Fetching weather for lat={request.latitude}, lon={request.longitude}")
        weather_data = await fetch_weather_data(request.latitude, request.longitude)
        return weather_data
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weather-by-coords")
async def get_weather_by_coords(lat: float, lon: float):
    """Get real-time weather data by coordinates (GET endpoint)"""
    try:
        logger.info(f"Fetching weather for lat={lat}, lon={lon}")
        weather_data = await fetch_weather_data(lat, lon)
        return weather_data
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time streaming
@app.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket):
    """WebSocket endpoint for real-time agent communication"""
    await websocket.accept()
    session_id = get_session_id()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            prompt = message.get('prompt', '')
            if not prompt:
                await websocket.send_json({'error': 'No prompt provided'})
                continue

            # Send acknowledgment
            await websocket.send_json({
                'type': 'start',
                'session_id': session_id
            })

            # Invoke AgentCore runtime
            try:
                sts = boto3.client('sts', region_name=os.getenv('AWS_REGION', 'us-east-1'))
                account_id = sts.get_caller_identity()['Account']
                region = os.getenv('AWS_REGION', 'us-east-1')

                runtime_arn = f"arn:aws:bedrock-agentcore:{region}:{account_id}:runtime/{RUNTIME_ID}"

                payload_dict = {'prompt': prompt, 'session_id': session_id}
                payload_bytes = json.dumps(payload_dict).encode('utf-8')

                response = bedrock_agentcore_runtime.invoke_agent_runtime(
                    agentRuntimeArn=runtime_arn,
                    payload=payload_bytes,
                    contentType='application/json',
                    accept='application/json'
                )

                response_body = response.get('payload', b'')
                if isinstance(response_body, bytes):
                    response_body = response_body.decode('utf-8')

                try:
                    response_data = json.loads(response_body)
                    full_text = response_data if isinstance(response_data, str) else str(response_data)
                except json.JSONDecodeError:
                    full_text = response_body

                # Send the full response
                await websocket.send_json({
                    'type': 'chunk',
                    'content': full_text
                })

                # Send completion
                await websocket.send_json({
                    'type': 'complete',
                    'session_id': session_id,
                    'full_response': full_text
                })

            except Exception as e:
                await websocket.send_json({
                    'type': 'error',
                    'message': str(e)
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
