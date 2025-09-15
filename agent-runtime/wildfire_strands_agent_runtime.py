"""
Wildfire Early-Warning & Triage AI Agent for Amazon Bedrock AgentCore Runtime
This version uses the Strands Agent framework for NASA FIRMS data integration
"""
import os
import json
import logging
import requests
import asyncio
from dotenv import load_dotenv
import utils
import access_token

# Import Strands Agents SDK
from strands import Agent
from strands.models import BedrockModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Load environment variables
load_dotenv()

# Initialize the AgentCore Runtime App
app = BedrockAgentCoreApp()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Set logging level for specific libraries
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('mcp').setLevel(logging.INFO)
logging.getLogger('strands').setLevel(logging.INFO)

# MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
logger.info(f"MCP_SERVER_URL set to: {MCP_SERVER_URL}")

# Configure conversation management for production
conversation_manager = SlidingWindowConversationManager(
    window_size=25,  # Limit history size
)

# Function to check if MCP server is running
def check_mcp_server():
    try:
        # Get the bearer token
        jwt_token = os.getenv("BEARER_TOKEN")
        
        logger.info(f"Checking MCP server at URL: {MCP_SERVER_URL}")
        
        # If no bearer token, try to get one from Cognito
        if not jwt_token:
            logger.info("No bearer token available, trying to get one from Cognito...")
            try:
                jwt_token = access_token.get_gateway_access_token()
                logger.info(f"Retrieved token: {jwt_token}")
                logger.info(f"Cognito token obtained: {'Yes' if jwt_token else 'No'}")
            except Exception as e:
                logger.error(f"Error getting Cognito token: {str(e)}", exc_info=True)
        
        if jwt_token:
            headers = {"Authorization": f"Bearer {jwt_token}", "Content-Type": "application/json"}
            payload = {
                "jsonrpc": "2.0",
                "id": "test",
                "method": "tools/list",
                "params": {}
            }
            
            try:
                response = requests.post(f"{MCP_SERVER_URL}/mcp", headers=headers, json=payload, timeout=10)
                logger.info(f"MCP server response status: {response.status_code}")
                
                has_tools = "tools" in response.text
                return has_tools
            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception when checking MCP server: {str(e)}")
                return False
        else:
            # Try without token for local testing
            logger.info("No bearer token available, trying health endpoint")
            try:
                response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
                logger.info(f"Health endpoint response status: {response.status_code}")
                
                return response.status_code == 200
            except requests.exceptions.RequestException as e:
                logger.error(f"Health endpoint request exception: {str(e)}")
                return False
    except Exception as e:
        logger.error(f"Error checking MCP server: {str(e)}", exc_info=True)
        return False

# Initialize Strands Agent with MCP tools
def initialize_agent():
    try:
        # Get OAuth token for authentication
        logger.info("Starting agent initialization...")
        
        # First try to get token from environment variable (for Docker)
        jwt_token = os.getenv("BEARER_TOKEN")
        
        # If not available in environment, try to get from Cognito
        if not jwt_token:
            logger.info("No token in environment, trying Cognito...")
            try:
                jwt_token = access_token.get_gateway_access_token()
                logger.info(f"Retrieved token: {jwt_token}")
            except Exception as e:
                logger.error(f"Error getting Cognito token: {str(e)}", exc_info=True)
        
        # Create MCP client with authentication headers
        gateway_endpoint = os.getenv("gateway_endpoint", MCP_SERVER_URL)
        logger.info(f"Using gateway endpoint: {gateway_endpoint}")
        
        # Try to resolve the hostname to check network connectivity
        try:
            import socket
            hostname = gateway_endpoint.split("://")[1].split("/")[0]
            ip_address = socket.gethostbyname(hostname)
            logger.info(f"Hostname resolved to IP: {ip_address}")
        except Exception as e:
            logger.error(f"Error resolving hostname: {str(e)}")
        
        headers = {"Authorization": f"Bearer {jwt_token}"} if jwt_token else {}
        
        try:
            logger.info("Creating MCP client...")
            
            # Create the MCP client
            mcp_client = MCPClient(lambda: streamablehttp_client(
                url = f"{gateway_endpoint}/mcp",
                headers=headers
            ))
            logger.info("MCP Client setup complete")
            
            # Enter the context manager
            mcp_client.__enter__()
            
            # Get the tools from the MCP server
            logger.info("Listing tools from MCP server...")
            tools = mcp_client.list_tools_sync()
            logger.info(f"Loaded {len(tools)} tools from MCP server")
            
            # Log available tools
            if tools and len(tools) > 0:
                # Try to access the tool name using the correct attribute
                tool_names = []
                for tool in tools:
                    # Check if the tool has a 'schema' attribute that might contain the name
                    if hasattr(tool, 'schema') and hasattr(tool.schema, 'name'):
                        tool_names.append(tool.schema.name)
                    # Or if it has a direct attribute that contains the name
                    elif hasattr(tool, 'tool_name'):
                        tool_names.append(tool.tool_name)
                    # Or if it's in the __dict__
                    elif '_name' in vars(tool):
                        tool_names.append(vars(tool)['_name'])
                    else:
                        # If we can't find the name, use a placeholder
                        tool_names.append(f"Tool-{id(tool)}")
                
                logger.info(f"Available tools: {', '.join(tool_names)}")
            
        except Exception as e:
            logger.error(f"Error setting up MCP client: {str(e)}", exc_info=True)
            return None, None
        
        # Create an agent with these tools
        try:
            logger.info("Creating Strands Agent with tools...")
            model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"  # Using Claude Sonnet
            model = BedrockModel(model_id=model_id)
            
            agent = Agent(
                model=model,
                tools=tools,
                conversation_manager=conversation_manager,
                system_prompt="""
                You are an AI assistant for Wildfire Early-Warning & Triage. You help emergency managers, fire departments, 
                and land management agencies monitor wildfire threats and coordinate response efforts.
                
                You have access to real-time NASA satellite data and tools for wildfire detection and threat assessment:
                
                Available tools:
                - fetch_firms_hotspots: Get latest MODIS/VIIRS fire detections from NASA FIRMS
                - assess_threat_level: Analyze wildfire threat to specific locations or protected areas
                - generate_fire_map: Create interactive maps showing current fire activity
                - draft_ics_update: Generate Incident Command System (ICS-213) reports
                - check_aoi_intersections: Check if fires intersect with Areas of Interest (protected areas)
                
                Key capabilities:
                1. **Real-time Fire Detection**: Monitor NASA satellite data for new fire hotspots
                2. **Threat Assessment**: Evaluate fire proximity to critical infrastructure and protected areas
                3. **Automated Alerting**: Identify high-priority situations requiring immediate attention
                4. **Map Generation**: Create visual fire maps with overlays for situational awareness
                5. **ICS Integration**: Generate standardized incident reports for emergency response
                
                When helping users:
                - Prioritize safety and provide actionable information
                - Use official terminology (ICS standards when applicable)
                - Explain confidence levels and data sources
                - Suggest appropriate response actions based on threat levels
                - Always mention data limitations and recommend ground verification
                
                Remember: This system provides early warning intelligence but should not replace 
                official fire department notifications or emergency response protocols.
                """
            )
            logger.info("Agent created successfully")
            
            return agent, mcp_client
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}", exc_info=True)
            return None, None
    except Exception as e:
        logger.error(f"Error initializing agent: {str(e)}", exc_info=True)
        return None, None

# Initialize the agent if MCP server is running
agent = None
mcp_client = None
if check_mcp_server():
    agent, mcp_client = initialize_agent()
    if agent:
        logger.info("Wildfire Agent initialized successfully")
    else:
        logger.warning("Failed to initialize wildfire agent")
else:
    logger.warning("MCP server is not running. Wildfire agent initialization skipped.")

# Function to format response for wildfire data
def format_response(text):
    """Format the response for better display of wildfire data"""
    if not isinstance(text, str):
        text = str(text)
        
    # Check if the response contains JSON data
    json_start = text.find('{')
    json_end = text.rfind('}')
    if json_start >= 0 and json_end > json_start:
        try:
            json_str = text[json_start:json_end+1]
            json_data = json.loads(json_str)
            
            # Format based on the type of wildfire data
            if isinstance(json_data, dict):
                # Check for hotspots data
                if 'hotspots' in json_data and 'total_hotspots' in json_data:
                    formatted_text = format_hotspots_data(json_data)
                    return text[:json_start] + formatted_text + text[json_end+1:]
                # Check for threat assessment
                elif 'threat_assessment' in json_data:
                    formatted_text = format_threat_assessment(json_data)
                    return text[:json_start] + formatted_text + text[json_end+1:]
                # Check for map configuration
                elif 'center' in json_data and 'base_map_url' in json_data:
                    formatted_text = format_map_config(json_data)
                    return text[:json_start] + formatted_text + text[json_end+1:]
                # Check for ICS update
                elif 'ics_update' in json_data:
                    formatted_text = format_ics_update(json_data)
                    return text[:json_start] + formatted_text + text[json_end+1:]
                # Check for intersection analysis
                elif 'intersections' in json_data and 'total_intersections' in json_data:
                    formatted_text = format_intersections(json_data)
                    return text[:json_start] + formatted_text + text[json_end+1:]
                # Generic object formatting
                else:
                    formatted_text = format_generic_wildfire_object(json_data)
                    return text[:json_start] + formatted_text + text[json_end+1:]
                    
        except Exception as e:
            logger.debug(f"Error formatting wildfire JSON: {str(e)}")
    
    # If no JSON formatting was applied, return the original text
    return text

def format_hotspots_data(data):
    """Format hotspots data for display"""
    if not data or 'hotspots' not in data:
        return "No hotspot data available."
    
    hotspots = data['hotspots']
    total = data.get('total_hotspots', len(hotspots))
    source = data.get('source', 'Unknown')
    
    result = f"🔥 WILDFIRE HOTSPOT DETECTION REPORT\n"
    result += f"{'='*50}\n\n"
    result += f"Data Source: NASA FIRMS ({source})\n"
    result += f"Total Hotspots: {total}\n"
    result += f"New Hotspots Stored: {data.get('new_hotspots_stored', 'N/A')}\n\n"
    
    if not hotspots:
        result += "No active hotspots detected.\n"
        return result
    
    # Show high-priority hotspots first
    high_priority = [h for h in hotspots if h.get('threat_assessment', {}).get('threat_level') in ['CRITICAL', 'HIGH']]
    
    if high_priority:
        result += "🚨 HIGH PRIORITY DETECTIONS:\n"
        result += f"{'='*30}\n"
        
        for hotspot in high_priority[:10]:  # Limit to top 10
            lat = hotspot.get('latitude', 'N/A')
            lon = hotspot.get('longitude', 'N/A')
            confidence = hotspot.get('confidence', 'N/A')
            threat = hotspot.get('threat_assessment', {})
            threat_level = threat.get('threat_level', 'UNKNOWN')
            min_distance = threat.get('min_distance_km', float('inf'))
            
            result += f"📍 Location: {lat}, {lon}\n"
            result += f"   Confidence: {confidence}%\n"
            result += f"   Threat Level: {threat_level}\n"
            if min_distance != float('inf'):
                result += f"   Distance to Protected Area: {min_distance:.1f} km\n"
            
            # Show affected areas
            affected_areas = threat.get('affected_areas', [])
            if affected_areas:
                result += f"   Affected Areas: {', '.join([area.get('name', 'Unknown') for area in affected_areas[:3]])}\n"
            
            result += "\n"
    
    # Summary statistics
    threat_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for hotspot in hotspots:
        threat_level = hotspot.get('threat_assessment', {}).get('threat_level', 'LOW')
        threat_counts[threat_level] = threat_counts.get(threat_level, 0) + 1
    
    result += "📊 THREAT LEVEL SUMMARY:\n"
    result += f"Critical: {threat_counts['CRITICAL']} | High: {threat_counts['HIGH']} | "
    result += f"Medium: {threat_counts['MEDIUM']} | Low: {threat_counts['LOW']}\n\n"
    
    result += "💡 RECOMMENDATIONS:\n"
    if threat_counts['CRITICAL'] > 0:
        result += "• Immediate ground verification required for critical threats\n"
        result += "• Consider activating emergency response protocols\n"
    if threat_counts['HIGH'] > 0:
        result += "• Monitor high-threat areas closely\n"
        result += "• Pre-position resources if conditions warrant\n"
    
    result += "• Verify detections through multiple sources\n"
    result += "• Monitor weather conditions for fire behavior changes\n"
    
    return result

def format_threat_assessment(data):
    """Format threat assessment data"""
    if not data or 'threat_assessment' not in data:
        return "No threat assessment available."
    
    location = data.get('location', {})
    assessment = data['threat_assessment']
    
    result = f"🎯 THREAT ASSESSMENT REPORT\n"
    result += f"{'='*35}\n\n"
    result += f"Location: {location.get('latitude', 'N/A')}, {location.get('longitude', 'N/A')}\n"
    result += f"Threat Level: {assessment.get('threat_level', 'UNKNOWN')}\n"
    result += f"Minimum Distance to Protected Area: {assessment.get('min_distance_km', 'N/A')} km\n"
    result += f"Confidence Factor: {assessment.get('confidence_factor', 0):.2f}\n\n"
    
    affected_areas = assessment.get('affected_areas', [])
    if affected_areas:
        result += "🏛️ AFFECTED PROTECTED AREAS:\n"
        for area in affected_areas:
            result += f"• {area.get('name', 'Unknown')} (Priority: {area.get('priority', 'N/A')})\n"
            if 'distance_km' in area:
                result += f"  Distance: {area['distance_km']:.1f} km\n"
    else:
        result += "✅ No protected areas directly threatened.\n"
    
    return result

def format_map_config(data):
    """Format map configuration data"""
    if not data:
        return "No map configuration available."
    
    center = data.get('center', {})
    hotspots = data.get('hotspots', [])
    
    result = f"🗺️ FIRE MAP CONFIGURATION\n"
    result += f"{'='*30}\n\n"
    result += f"Map Center: {center.get('latitude', 'N/A')}, {center.get('longitude', 'N/A')}\n"
    result += f"Zoom Level: {data.get('zoom', 'N/A')}\n"
    result += f"Active Hotspots in View: {len(hotspots)}\n\n"
    
    if data.get('base_map_url'):
        result += "🌍 Base Map: NASA GIBS True Color\n"
    if data.get('fire_overlay_url'):
        result += "🔥 Fire Overlay: MODIS Active Fires\n"
    
    # Legend
    legend = data.get('legend', {})
    if legend:
        result += "\n📋 LEGEND:\n"
        for color, description in legend.items():
            result += f"• {color.upper()}: {description}\n"
    
    return result

def format_ics_update(data):
    """Format ICS update data"""
    if not data or 'ics_update' not in data:
        return "No ICS update available."
    
    result = f"📋 ICS-213 REPORT GENERATED\n"
    result += f"{'='*35}\n\n"
    result += f"Incident ID: {data.get('incident_id', 'N/A')}\n"
    result += f"Generated: {data.get('generated_at', 'N/A')}\n"
    result += f"Hotspots Analyzed: {data.get('hotspot_count', 'N/A')}\n\n"
    
    result += "📄 ICS-213 CONTENT:\n"
    result += f"{'-'*20}\n"
    result += data.get('ics_update', 'No content available')
    
    return result

def format_intersections(data):
    """Format intersection analysis data"""
    if not data:
        return "No intersection data available."
    
    intersections = data.get('intersections', [])
    total = data.get('total_intersections', len(intersections))
    
    result = f"🎯 AOI INTERSECTION ANALYSIS\n"
    result += f"{'='*35}\n\n"
    result += f"Total Intersections Found: {total}\n"
    result += f"Analysis Time: {data.get('analysis_timestamp', 'N/A')}\n\n"
    
    if not intersections:
        result += "✅ No hotspots intersecting with protected areas.\n"
        return result
    
    # Group by intersection type
    direct = [i for i in intersections if i.get('intersection_type') == 'DIRECT']
    proximity = [i for i in intersections if i.get('intersection_type') == 'PROXIMITY']
    
    if direct:
        result += f"🚨 DIRECT INTERSECTIONS ({len(direct)}):\n"
        for intersection in direct[:5]:  # Limit display
            hotspot = intersection.get('hotspot', {})
            area = intersection.get('area', {})
            result += f"• {area.get('name', 'Unknown')} (Priority: {area.get('priority', 'N/A')})\n"
            result += f"  Hotspot: {hotspot.get('latitude', 'N/A')}, {hotspot.get('longitude', 'N/A')}\n"
            result += f"  Confidence: {hotspot.get('confidence', 'N/A')}%\n\n"
    
    if proximity:
        result += f"⚠️ PROXIMITY THREATS ({len(proximity)}):\n"
        for intersection in proximity[:5]:  # Limit display
            hotspot = intersection.get('hotspot', {})
            area = intersection.get('area', {})
            distance = intersection.get('distance_km', 'N/A')
            result += f"• {area.get('name', 'Unknown')} (Distance: {distance} km)\n"
            result += f"  Hotspot: {hotspot.get('latitude', 'N/A')}, {hotspot.get('longitude', 'N/A')}\n"
            result += f"  Confidence: {hotspot.get('confidence', 'N/A')}%\n\n"
    
    return result

def format_generic_wildfire_object(obj):
    """Format generic wildfire object data"""
    if not obj or not isinstance(obj, dict):
        return "No data available."
    
    if 'error' in obj:
        return f"❌ Error: {obj['error']}"
    
    result = "🔥 WILDFIRE SYSTEM RESPONSE\n"
    result += f"{'='*35}\n\n"
    
    # Get the maximum key length for alignment
    max_key_length = max([len(key) for key in obj.keys()]) if obj.keys() else 0
    
    for key, value in sorted(obj.items()):
        if isinstance(value, dict):
            # Nested object
            result += f"{key.replace('_', ' ').title()}:\n"
            result += f"{'-' * len(key)}\n"
            
            for k, v in sorted(value.items()):
                result += f"  {k.replace('_', ' ').title()}: {v}\n"
            result += "\n"
        elif isinstance(value, list) and value:
            # List of values
            result += f"{key.replace('_', ' ').title()}:\n"
            result += f"{'-' * len(key)}\n"
            
            for i, item in enumerate(value[:5], 1):  # Limit to 5 items
                if isinstance(item, dict):
                    result += f"  {i}. "
                    for k, v in sorted(item.items()):
                        result += f"{k}: {v}, "
                    result = result[:-2] + "\n"  # Remove trailing comma
                else:
                    result += f"  {i}. {item}\n"
            
            if len(value) > 5:
                result += f"  ... and {len(value) - 5} more items\n"
            result += "\n"
        else:
            # Simple value
            formatted_key = key.replace('_', ' ').title()
            result += f"{formatted_key.ljust(max_key_length + 2)}: {value}\n"
    
    return result

@app.entrypoint
async def process_request(payload):
    """
    Process requests from AgentCore Runtime with streaming support
    This is the entry point for the Wildfire AgentCore Runtime
    """
    global agent, mcp_client
    try:
        # Extract the user message from the payload
        user_message = payload.get("prompt", "No prompt found in input, please provide a message")
        logger.info(f"Received wildfire query: {user_message}")
        
        # Check if agent is initialized
        if not agent:
            logger.info("Wildfire agent not initialized, checking MCP server status...")
            # Try to initialize the agent if MCP server is running
            if check_mcp_server():
                logger.info("MCP server is running, attempting to initialize wildfire agent...")
                agent, mcp_client = initialize_agent()
                if not agent:
                    error_msg = "Failed to initialize wildfire agent. Please ensure MCP server is running correctly."
                    logger.error(error_msg)
                    yield {"error": error_msg}
                    return
                logger.info("Wildfire agent initialized successfully")
            else:
                error_msg = "Wildfire agent is not initialized. Please ensure MCP server is running."
                logger.error(error_msg)
                yield {"error": error_msg}
                return
        
        # Use Strands Agent to process the message with streaming
        logger.info("Processing wildfire query with Strands Agent (streaming)...")
        try:
            # Stream response using agent.stream_async
            stream = agent.stream_async(user_message)
            async for event in stream:
                logger.debug(f"Streaming event: {event}")
                
                # Process different event types
                if "data" in event:
                    # Text chunk from the model
                    chunk = event["data"]
                    formatted_chunk = format_response(chunk)
                    yield {
                        "type": "chunk",
                        "data": chunk,
                        "formatted": formatted_chunk
                    }
                elif "current_tool_use" in event:
                    # Tool use information
                    tool_info = event["current_tool_use"]
                    yield {
                        "type": "tool_use",
                        "tool_name": tool_info.get("name", "Unknown tool"),
                        "tool_input": tool_info.get("input", {}),
                        "tool_id": tool_info.get("toolUseId", "")
                    }
                elif "reasoning" in event and event["reasoning"]:
                    # Reasoning information
                    yield {
                        "type": "reasoning",
                        "reasoning_text": event.get("reasoningText", "")
                    }
                elif "result" in event:
                    # Final result
                    result = event["result"]
                    if hasattr(result, 'message') and hasattr(result.message, 'content'):
                        if isinstance(result.message.content, list) and len(result.message.content) > 0:
                            final_response = result.message.content[0].get('text', '')
                        else:
                            final_response = str(result.message.content)
                    else:
                        final_response = str(result)
                    
                    yield {
                        "type": "complete",
                        "final_response": format_response(final_response)
                    }
                else:
                    # Pass through other events
                    yield event
                
        except Exception as e:
            logger.error(f"Error in streaming mode: {str(e)}", exc_info=True)
            yield {"error": f"Error processing wildfire request with agent (streaming): {str(e)}"}
        
    except Exception as e:
        error_msg = f"Error processing wildfire request: {str(e)}"
        logger.error(error_msg, exc_info=True)
        yield {"error": error_msg}

if __name__ == "__main__":
    # Test MCP server connection at startup
    logger.info("Testing wildfire MCP server connection at startup...")
    try:
        jwt_token = access_token.get_gateway_access_token()
        headers = {"Authorization": f"Bearer {jwt_token}", "Content-Type": "application/json"} if jwt_token else {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "id": "startup-test",
            "method": "tools/list",
            "params": {}
        }
        response = requests.post(f"{MCP_SERVER_URL}/mcp", headers=headers, json=payload, timeout=10)
        logger.info(f"Direct test response status: {response.status_code}")
    except Exception as e:
        logger.error(f"Error in direct test: {str(e)}", exc_info=True)
    
    # Run the AgentCore Runtime App
    app.run()
