# Wildfire Early-Warning & Triage Agent

## Overview

This project implements a comprehensive Wildfire Early-Warning & Triage System using Amazon Bedrock AgentCore. It provides real-time wildfire detection, threat assessment, and automated alerting using NASA satellite data through natural language interactions.

| Information | Details |
|-------------|---------|
| Use case type | Autonomous monitoring and alerting |
| Agent type | Single agent with multiple data sources |
| Use case components | Tools, Gateway, NASA APIs, Mapping |
| Use case vertical | Emergency Management / Earth Observation |
| Example complexity | Advanced |
| SDK used | Amazon Bedrock AgentCore SDK, boto3, NASA APIs |

## Use case Architecture

![Wildfire Detection Architecture](./images/wildfire-detection-architecture.png)

### Process Flow

1. **Data Ingestion**: The system continuously monitors NASA FIRMS (Fire Information for Resource Management System) for near-real-time MODIS/VIIRS hotspot data.

2. **Threat Assessment**:
   - New hotspots are detected and analyzed
   - Intersection with protected Areas of Interest (AOI) is calculated
   - Threat levels are assigned based on proximity to assets
   - Historical fire behavior and weather data are considered

3. **Autonomous Decision Making**:
   - AgentCore processes hotspot data using LLM reasoning
   - Critical threats trigger automated alert workflows
   - ICS (Incident Command System) updates are drafted automatically

4. **Visualization & Mapping**:
   - Live maps are rendered using NASA GIBS WMTS tiles
   - Worldview-style interactive maps show current fire activity
   - Protected areas and assets are overlaid for context

5. **Alert System**:
   - On-call personnel are automatically paged for critical threats
   - Alert fatigue is minimized through intelligent filtering
   - Response teams receive actionable information

6. **Data Storage**:
   - DynamoDB stores incident records, hotspot history, and AOI definitions
   - S3 caches map tiles and stores generated reports
   - Lambda functions buffer and union AOI queries for efficiency

## Key Features

The Wildfire Early-Warning & Triage System provides:

- **Real-time Hotspot Detection**: Continuous monitoring of NASA FIRMS data
- **Intelligent Threat Ranking**: AI-powered assessment of wildfire threats to protected assets
- **Automated Alerting**: Smart notification system with minimal false positives
- **Interactive Mapping**: Live fire maps with protected area overlays
- **ICS Integration**: Automated generation of Incident Command System updates
- **Historical Analysis**: Trend analysis and fire behavior prediction
- **Multi-source Data**: Integration of MODIS, VIIRS, and optional EONET event data

## Demo Metrics

- **Detection→Notification Latency**: Target <5 minutes from satellite detection to alert
- **Actionable Alerts/Day**: Filtered high-priority alerts requiring human attention
- **False Positive Rate**: <10% of alerts result in no action required
- **Coverage Area**: Configurable AOI monitoring with polygon-based definitions

## Prerequisites

- Python 3.10+
- AWS account with appropriate permissions
- boto3 and Amazon Bedrock AgentCore SDK
- Cognito User Pool with configured app client
- IAM Role for Bedrock Agent Core Gateway
- NASA Earthdata account (optional, for enhanced data access)

## NASA Data Sources

### FIRMS (Fire Information for Resource Management System)
- **MODIS**: 1km resolution, 4x daily coverage
- **VIIRS**: 375m resolution, 2x daily coverage
- **Data Format**: CSV/JSON with lat/lon, confidence, brightness temperature
- **API Endpoints**: Near-real-time and historical data access

### GIBS (Global Imagery Browse Services)
- **Base Maps**: Natural color, terrain, and satellite imagery
- **Fire Overlays**: Active fire detections and burn scars
- **WMTS Protocol**: Web Map Tile Service for interactive mapping

### EONET (Earth Observatory Natural Event Tracker) - Optional
- **Event Context**: Large-scale wildfire event boundaries
- **Historical Data**: Multi-day fire progression tracking

## Installation & Setup

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
# AWS and endpoint configuration
AWS_REGION=us-west-2
ENDPOINT_URL=https://bedrock-agentcore-control.us-west-2.amazonaws.com

# Lambda configuration
LAMBDA_FUNCTION_NAME=WildfireDetectionLambda
LAMBDA_ARN=arn:aws:lambda:us-west-2:your-account-id:function:WildfireDetectionLambda

# Gateway configuration
GATEWAY_IDENTIFIER=your-gateway-identifier
GATEWAY_NAME=Wildfire-Detection-Gateway
GATEWAY_DESCRIPTION=Wildfire Early-Warning and Triage Gateway
ROLE_ARN=arn:aws:iam::your-account-id:role/YourGatewayRole

# NASA API configuration
NASA_API_KEY=your-nasa-api-key
FIRMS_API_URL=https://firms.modaps.eosdis.nasa.gov/api/
GIBS_API_URL=https://gibs.earthdata.nasa.gov/wmts/

# Alert configuration
ALERT_EMAIL=alerts@your-organization.com
ALERT_PHONE=+1234567890
SLACK_WEBHOOK_URL=your-slack-webhook-url

# Monitoring configuration
DETECTION_INTERVAL_MINUTES=15
THREAT_RADIUS_KM=10
```

### 2. Automated Deployment

Deploy all components using the deployment script:

```bash
chmod +x deploy_all.sh
./deploy_all.sh
```

### 3. Manual Deployment (Alternative)

Deploy components individually:

```bash
# Deploy Lambda functions
cd wildfire-detection
./deploy.sh

# Create Gateway
cd ../gateway
python create_gateway.py
python wildfire-detection-target.py
python gateway_observability.py

# Setup Agent Runtime
cd ../agent-runtime
./setup.sh

# Setup Frontend
cd ../frontend
./setup_and_run.sh
```

## Sample Prompts

1. "Show me all active wildfires within 50km of protected areas"
2. "What's the current threat level for the Yellowstone region?"
3. "Generate an ICS-213 update for the latest fire activity"
4. "Create a map showing fire progression over the last 24 hours"
5. "Alert me if any new hotspots appear near critical infrastructure"
6. "What's the confidence level of the fire detection at coordinates 45.123, -110.456?"

## Technical Implementation

### MCP Tools

- `fetch_firms_hotspots`: Retrieve latest MODIS/VIIRS fire detections
- `assess_threat_level`: Analyze hotspot proximity to protected areas
- `generate_fire_map`: Create interactive maps with fire overlays
- `draft_ics_update`: Generate Incident Command System reports
- `check_aoi_intersections`: Test hotspot intersection with Areas of Interest
- `send_alert`: Trigger notifications for critical threats
- `get_fire_history`: Retrieve historical fire data for analysis

### Data Models

- **Incidents**: Fire event records with metadata and progression
- **Hotspots**: Individual satellite detections with confidence scores
- **ProtectedAreas**: Polygon definitions of Areas of Interest (AOI)
- **Alerts**: Notification history and response tracking
- **MapTiles**: Cached imagery for faster map rendering

## Compliance & Standards

- **ICS (Incident Command System)**: Standard emergency response protocols
- **NWCG Standards**: National Wildland Coordinating Group guidelines
- **NASA Data Usage**: Compliant with Earthdata terms of service
- **AWS Security**: Implements least-privilege access and encryption

## Monitoring & Observability

- **CloudWatch Logs**: Detailed logging for all detection events
- **X-Ray Traces**: End-to-end request tracking
- **Custom Metrics**: Detection latency, alert accuracy, system health
- **Dashboards**: Real-time monitoring of fire activity and system status

## License

This project is for demonstration purposes in the AWS AI Agent Hackathon. Use appropriate NASA data attribution and comply with all relevant terms of service.

## Disclaimer

This system is for experimental and educational purposes. For production wildfire monitoring, integrate with official emergency response systems and validate all alerts through proper channels.
