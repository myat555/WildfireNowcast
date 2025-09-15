import boto3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
GATEWAY_IDENTIFIER = os.getenv('GATEWAY_IDENTIFIER')
TARGET_NAME = os.getenv('TARGET_NAME', 'wildfire-detection-target')
TARGET_DESCRIPTION = os.getenv('TARGET_DESCRIPTION', 'Wildfire Detection and Threat Assessment Target')
LAMBDA_ARN = os.getenv('LAMBDA_ARN')

print(f"AWS Region: {AWS_REGION}")
print(f"Gateway Identifier: {GATEWAY_IDENTIFIER}")
print(f"Target Name: {TARGET_NAME}")
print(f"Lambda ARN: {LAMBDA_ARN}")

# Initialize the Bedrock Agent Core Control client
bedrock_agent_core_client = boto3.client(
    'bedrock-agentcore-control', 
    region_name=AWS_REGION
)

# Define the MCP tools for wildfire detection
tools = [
    {
        "name": "fetch_firms_hotspots",
        "description": "Fetch latest wildfire hotspots from NASA FIRMS (MODIS/VIIRS satellite data)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Data source (VIIRS or MODIS)",
                    "enum": ["VIIRS", "MODIS"],
                    "default": "VIIRS"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back (1-10)",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 1
                },
                "area": {
                    "type": "object",
                    "description": "Optional area filter",
                    "properties": {
                        "lat": {"type": "number", "description": "Center latitude"},
                        "lon": {"type": "number", "description": "Center longitude"},
                        "radius_km": {"type": "number", "description": "Radius in kilometers"}
                    }
                }
            }
        }
    },
    {
        "name": "assess_threat_level",
        "description": "Assess wildfire threat level for a specific location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": "Latitude of the location to assess"
                },
                "longitude": {
                    "type": "number", 
                    "description": "Longitude of the location to assess"
                },
                "confidence": {
                    "type": "integer",
                    "description": "Confidence level (0-100)",
                    "minimum": 0,
                    "maximum": 100,
                    "default": 50
                }
            },
            "required": ["latitude", "longitude"]
        }
    },
    {
        "name": "generate_fire_map",
        "description": "Generate interactive fire map with NASA GIBS tiles and hotspot overlays",
        "inputSchema": {
            "type": "object",
            "properties": {
                "center_lat": {
                    "type": "number",
                    "description": "Center latitude for the map"
                },
                "center_lon": {
                    "type": "number",
                    "description": "Center longitude for the map"
                },
                "zoom": {
                    "type": "integer",
                    "description": "Zoom level (1-16)",
                    "minimum": 1,
                    "maximum": 16,
                    "default": 8
                },
                "include_hotspots": {
                    "type": "boolean",
                    "description": "Include fire hotspot overlay",
                    "default": true
                }
            },
            "required": ["center_lat", "center_lon"]
        }
    },
    {
        "name": "draft_ics_update",
        "description": "Draft ICS-213 incident command system update for current fire situation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                    "description": "Optional incident identifier, will auto-generate if not provided"
                }
            }
        }
    },
    {
        "name": "check_aoi_intersections",
        "description": "Check if hotspots intersect with Areas of Interest (protected areas)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "hotspots_data": {
                    "type": "array",
                    "description": "Optional list of hotspots to check, will fetch recent data if not provided",
                    "items": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"},
                            "confidence": {"type": "integer"}
                        }
                    }
                }
            }
        }
    }
]

# Create the gateway target
try:
    create_target_response = bedrock_agent_core_client.create_gateway_target(
        gatewayIdentifier=GATEWAY_IDENTIFIER,
        name=TARGET_NAME,
        description=TARGET_DESCRIPTION,
        targetType='LAMBDA',
        targetConfiguration={
            'lambdaConfiguration': {
                'lambdaArn': LAMBDA_ARN
            }
        },
        tools=tools
    )

    print(f"Wildfire Gateway Target created successfully!")
    print(f"Target Name: {create_target_response.get('name')}")
    print(f"Target Type: {create_target_response.get('targetType')}")
    print(f"Creation Time: {create_target_response.get('creationTime')}")
    print(f"Number of Tools: {len(tools)}")
    
    # List the tools that were created
    print("\nTools created:")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")

except Exception as e:
    print(f"Error creating wildfire gateway target: {e}")
    exit(1)
