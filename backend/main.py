"""
FastAPI Backend Server for WildfireNowcast Agent
Connects frontend to AWS Bedrock Agent and NASA APIs
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import boto3
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Helper Functions
def get_session_id() -> str:
    """Generate a unique session ID"""
    from uuid import uuid4
    return str(uuid4())

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
    """Get NASA FIRMS fire hotspots via agent"""
    prompt = f"""Fetch fire hotspots using NASA FIRMS API with parameters:
    - Area: {request.area}
    - Days back: {request.days_back}
    - Confidence: {request.confidence}
    - Satellite: {request.satellite}

    Provide detailed hotspot data and analysis."""

    session_id = get_session_id()
    result = await invoke_bedrock_agentcore(prompt, session_id)

    return result

@app.post("/api/gibs-map-image")
async def get_gibs_map(request: GIBSRequest):
    """Get NASA GIBS satellite imagery via agent"""
    prompt = f"""Fetch satellite imagery from NASA GIBS with parameters:
    - Layer: {request.layer_name}
    - Bounding box: {request.bbox}
    - Size: {request.size}
    - Date: {request.date or 'latest'}
    - Projection: {request.projection}

    Provide the map image and metadata."""

    session_id = get_session_id()
    result = await invoke_bedrock_agentcore(prompt, session_id)

    return result

@app.post("/api/eonet-events")
async def get_eonet_events(request: EONETRequest):
    """Get NASA EONET wildfire events via agent"""
    prompt = f"""Fetch wildfire events from NASA EONET with parameters:
    - Category: {request.category}
    - Days back: {request.days_back}
    - Status: {request.status}
    - Limit: {request.limit}
    {f'- Source: {request.source}' if request.source else ''}

    Provide event details and analysis."""

    session_id = get_session_id()
    result = await invoke_bedrock_agentcore(prompt, session_id)

    return result

@app.post("/api/threat-assessment")
async def assess_threats(data: Dict[str, Any]):
    """Assess threats to critical infrastructure"""
    prompt = f"""Perform threat assessment for the following fire data:
    {json.dumps(data, indent=2)}

    Analyze threats to critical infrastructure, population centers, and provide recommendations."""

    session_id = get_session_id()
    result = await invoke_bedrock_agentcore(prompt, session_id)

    return result

@app.post("/api/fire-map")
async def generate_fire_map(data: Dict[str, Any]):
    """Generate fire map visualization"""
    prompt = f"""Generate a fire map with the following data:
    {json.dumps(data, indent=2)}

    Create an interactive map showing fire locations, progression, and threat zones."""

    session_id = get_session_id()
    result = await invoke_bedrock_agentcore(prompt, session_id)

    return result

@app.post("/api/ics-report")
async def generate_ics_report(data: Dict[str, Any]):
    """Generate ICS situation report"""
    prompt = f"""Generate an ICS (Incident Command System) situation report with:
    {json.dumps(data, indent=2)}

    Include incident overview, current status, resource deployment, and action items."""

    session_id = get_session_id()
    result = await invoke_bedrock_agentcore(prompt, session_id)

    return result

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
