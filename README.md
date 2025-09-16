# Wildfire Early-Warning & Triage Agent

## Overview

This project implements an intelligent wildfire detection and response agent using Amazon Bedrock AgentCore with the Strands Agent framework. The agent provides real-time wildfire monitoring, threat assessment, live mapping, and Incident Command System (ICS) update generation using NASA Earth observation data.

## Use Case Architecture

![Wildfire Agent Architecture](generated-diagrams/diagram_b6c65408.png)

| Information | Details |
|-------------|---------|
| Use case type | Earth Observation & Emergency Response |
| Agent type | Multi-Agent Orchestration |
| Use case components | NASA Data Integration, Threat Assessment, Live Mapping, ICS Reporting |
| Use case vertical | Emergency Management & Environmental Monitoring |
| Example complexity | Advanced |
| SDK used | Strands Agents SDK, Amazon Bedrock AgentCore |

## Features

### 🔥 Real-Time Wildfire Detection
- **NASA FIRMS Integration**: Near-real-time MODIS/VIIRS hotspot detection
- **Automated Hotspot Analysis**: Identifies new fire hotspots and tracks progression
- **Multi-Source Validation**: Cross-references multiple satellite data sources

### 🎯 Threat Assessment & Asset Protection
- **Asset Proximity Analysis**: Calculates distance from hotspots to critical infrastructure
- **Risk Ranking Algorithm**: Prioritizes threats based on fire intensity and asset value
- **Evacuation Zone Mapping**: Identifies areas requiring immediate attention

### 🗺️ Live Mapping & Visualization
- **GIBS WMTS Integration**: Real-time basemap and overlay rendering
- **Interactive Fire Maps**: Dynamic visualization of fire progression
- **Multi-Layer Support**: Combines satellite imagery, fire perimeters, and asset locations

### 📋 Incident Command System (ICS) Integration
- **Automated ICS Updates**: Generates standardized incident reports
- **Situation Reports**: Creates comprehensive status updates for command staff
- **Resource Allocation**: Recommends resource deployment based on threat analysis

### 🧠 Advanced Memory Management
- **Incident Tracking**: Maintains persistent memory of ongoing wildfires
- **Historical Analysis**: Learns from past incidents to improve predictions
- **Multi-Strategy Memory**: Uses both incident-specific and semantic memory strategies

## NASA Data Sources

### FIRMS (Fire Information for Resource Management System)
- **MODIS Hotspots**: Terra and Aqua satellite fire detection
- **VIIRS Hotspots**: Suomi NPP and NOAA-20 satellite data
- **Update Frequency**: Near-real-time (3-6 hour delay)
- **Coverage**: Global wildfire monitoring
- **API Key Required**: ✅ **Yes** (free registration at https://firms.modaps.eosdis.nasa.gov/api/map_key)

### GIBS (Global Imagery Browse Services)
- **WMTS Tiles**: Web Map Tile Service for basemaps
- **MODIS Corrected Reflectance**: True-color and false-color imagery
- **VIIRS Day/Night Band**: Nighttime fire detection
- **Landsat Imagery**: High-resolution satellite data
- **API Key Required**: ❌ **No** (publicly accessible - see [NASA GIBS documentation](https://nasa-gibs.github.io/gibs-api-docs/python-usage))

### EONET (Earth Observatory Natural Event Tracker)
- **Event Context**: Additional wildfire event information
- **Historical Events**: Past wildfire data for comparison
- **Event Classification**: Categorizes fire events by type and severity
- **API Key Required**: ❌ **No** (publicly accessible - see [EONET API documentation](https://eonet.gsfc.nasa.gov/docs/v3))

### Getting NASA API Keys

**Only FIRMS requires an API key** - GIBS and EONET are publicly accessible:

1. **FIRMS API Key** (✅ Required): 
   - Visit: https://firms.modaps.eosdis.nasa.gov/api/
   - Register for a free account
   - Generate your API key
   - Add to `.env` file as `NASA_FIRMS_API_KEY`

2. **GIBS API Key** (❌ Optional - Not Required):
   - GIBS is publicly accessible without authentication
   - See [NASA GIBS documentation](https://nasa-gibs.github.io/gibs-api-docs/python-usage) for direct access examples
   - If you have an Earthdata account, you can optionally add `NASA_GIBS_API_KEY` to `.env`

3. **EONET API Key** (❌ Optional - Not Required):
   - EONET API is publicly accessible without authentication
   - See [EONET API documentation](https://eonet.gsfc.nasa.gov/docs/v3) for direct access
   - If you have an account, you can optionally add `NASA_EONET_API_KEY` to `.env`

## Quick Start

### Prerequisites
- Python 3.10+
- AWS CLI configured with appropriate credentials
- Docker or Podman installed and running
- Access to Amazon Bedrock AgentCore
- **NASA API keys (required for deployment)**

### Installation & Deployment

1. **Install uv** (if not already installed)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

2. **Get NASA FIRMS API Key** (Required)
```bash
# Only FIRMS requires an API key - get it from:
# https://firms.modaps.eosdis.nasa.gov/api/
# 
# GIBS and EONET are publicly accessible without API keys
```

3. **Configure Environment Variables**
```bash
# Option A: Interactive setup (recommended)
uv run python setup_env.py

# Option B: Manual setup
cp .env.template .env
# Edit .env and add your NASA API keys
# Required: NASA_FIRMS_API_KEY
# Optional: NASA_GIBS_API_KEY, NASA_EONET_API_KEY (not required - publicly accessible)
```

4. **Install Dependencies**
```bash
uv sync
```

5. **Deploy the Agent** (One Command!)
```bash
# Simple deployment
uv run python deploy.py

# Custom configuration (optional)
uv run python deploy.py \
  --agent-name "my-wildfire-agent" \
  --region "us-west-2" \
  --role-name "MyCustomRole"
```

**Available Options:**
- `--agent-name`: Name for the agent (default: wildfire_nowcast_agent)
- `--role-name`: IAM role name (default: WildfireNowcastAgentRole)
- `--region`: AWS region (default: us-east-1)
- `--skip-checks`: Skip prerequisite validation

4. **Test the Agent**
```bash
uv run python test_agent.py
```

## Usage Examples

### 🔥 Wildfire Detection Query
```
"Check for new wildfire hotspots in California"
"Monitor fire activity in the Pacific Northwest"
"Detect any fires within 50 miles of Los Angeles"
```

### 🎯 Threat Assessment
```
"Assess threat level to critical infrastructure near current fires"
"Rank fire threats by proximity to populated areas"
"Identify evacuation zones for active fires"
```

### 🗺️ Live Mapping
```
"Generate a live map of current fire activity"
"Show fire progression over the last 24 hours"
"Create evacuation zone map for active incidents"
```

### 📋 ICS Reporting
```
"Draft an ICS situation report for current fires"
"Generate resource allocation recommendations"
"Create incident briefing for command staff"
```

## Architecture

### Multi-Agent System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    Wildfire Nowcast Agent                       │
├─────────────────────────────────────────────────────────────────┤
│  Strands Agent Framework                                        │
│  ├── Orchestrator Agent (Claude Sonnet 4)                      │
│  ├── Data Ingestion Agent                                      │
│  ├── Threat Analysis Agent                                      │
│  ├── Mapping Agent                                             │
│  └── ICS Reporting Agent                                       │
├─────────────────────────────────────────────────────────────────┤
│  AgentCore Multi-Strategy Memory                                │
│  ├── INCIDENT_TRACKING: Active wildfire incidents              │
│  └── SEMANTIC: Fire behavior patterns & historical data        │
├─────────────────────────────────────────────────────────────────┤
│  NASA Data Sources                                              │
│  ├── FIRMS API (MODIS/VIIRS hotspots)                          │
│  ├── GIBS WMTS (Basemaps & overlays)                           │
│  └── EONET API (Event context)                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Memory Strategies
- **INCIDENT_TRACKING**: Captures active wildfire incidents, asset locations, and threat assessments
- **SEMANTIC**: Stores fire behavior patterns, historical data, and response strategies

### Available Tools

**NASA Data Integration** (`tools/nasa_tools.py`):
- `fetch_firms_hotspots()`: Retrieve near-real-time MODIS/VIIRS hotspot data
- `fetch_gibs_tiles()`: Get GIBS WMTS tiles for mapping
- `fetch_eonet_events()`: Retrieve wildfire event context from EONET

**Threat Assessment** (`tools/threat_tools.py`):
- `assess_asset_threats()`: Analyze threats to critical infrastructure
- `rank_fire_threats()`: Prioritize fires by threat level
- `calculate_evacuation_zones()`: Determine evacuation areas

**Mapping & Visualization** (`tools/mapping_tools.py`):
- `generate_fire_map()`: Create live fire maps with overlays
- `render_evacuation_map()`: Generate evacuation zone maps
- `create_progression_map()`: Show fire progression over time

**ICS Reporting** (`tools/ics_tools.py`):
- `draft_ics_situation_report()`: Generate standardized ICS reports
- `create_resource_recommendations()`: Recommend resource allocation
- `generate_incident_briefing()`: Create command staff briefings

**Memory & Incident Management** (`tools/memory_tools.py`):
- `track_active_incidents()`: Monitor ongoing wildfire incidents
- `get_incident_history()`: Retrieve historical incident data
- `update_incident_status()`: Update incident status and progress

## Monitoring

### CloudWatch Logs
After deployment, monitor your agent:
```bash
# View logs (replace with your agent ID)
aws logs tail /aws/bedrock-agentcore/runtimes/{agent-id}-DEFAULT --follow
```

### Health Checks
- Built-in health check endpoints
- Monitor agent availability and response times
- Track NASA API connectivity and data freshness

## Cleanup

### Complete Resource Cleanup
When you're done with the agent, use the cleanup script to remove all AWS resources:

```bash
# Complete cleanup (removes everything)
uv run python cleanup.py

# Preview what would be deleted (dry run)
uv run python cleanup.py --dry-run

# Keep IAM roles (useful if shared with other projects)
uv run python cleanup.py --skip-iam

# Cleanup in different region
uv run python cleanup.py --region us-west-2
```

**What gets cleaned up:**
- ✅ AgentCore Runtime instances
- ✅ AgentCore Memory instances  
- ✅ ECR repositories and container images
- ✅ CodeBuild projects
- ✅ S3 build artifacts
- ✅ SSM parameters
- ✅ IAM roles and policies (unless `--skip-iam`)
- ✅ Local deployment files

## Security

### IAM Permissions
The deployment script automatically creates a role with:
- `bedrock:InvokeModel` (for Claude Sonnet)
- `bedrock-agentcore:*` (for memory and runtime operations)
- `ecr:*` (for container registry access)
- `xray:*` (for tracing)
- `logs:*` (for CloudWatch logging)
- `s3:*` (for map tile storage)

### Data Privacy
- Incident data is stored securely in Bedrock AgentCore Memory
- No sensitive location data is logged or exposed
- All communications are encrypted in transit
- NASA data is publicly available and properly attributed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NASA FIRMS for wildfire hotspot data
- NASA GIBS for satellite imagery services
- NASA EONET for event tracking
- Amazon Bedrock for AI/ML capabilities
- Strands Agents for the agent framework