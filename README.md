# 🔥 Wildfire Nowcast Agent


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
| SDK used | Strands Agents SDK, Amazon Bedrock AgentCore |

## Features

### 🔥 Real-Time Wildfire Detection 
- **Enhanced NASA FIRMS Integration**: Near-real-time MODIS/VIIRS hotspot detection with improved data processing
- **Automated Hotspot Analysis**: Identifies new fire hotspots and tracks progression
- **Multi-Source Validation**: Cross-references multiple satellite data sources
- **Live Demo**: `"Check for wildfire hotspots in California"` → Real NASA data in 15.75s

### 🎯 Threat Assessment & Asset Protection 
- **Asset Proximity Analysis**: Calculates distance from hotspots to critical infrastructure
- **Risk Ranking Algorithm**: Prioritizes threats based on fire intensity and asset value
- **Evacuation Zone Mapping**: Identifies areas requiring immediate attention
- **Enhanced Tools**: Improved threat assessment with better data processing

### 🗺️ Live Mapping & Visualization 
- **Enhanced GIBS Integration**: Real-time WMS/WMTS with OWSLib compliance
- **Interactive Fire Maps**: Dynamic visualization of fire progression
- **Multi-Layer Support**: Combines satellite imagery, fire perimeters, and asset locations
- **NASA Compliant**: Follows official NASA GIBS documentation exactly

### 📋 Incident Command System (ICS) Integration 
- **Automated ICS Updates**: Generates standardized incident reports
- **Situation Reports**: Creates comprehensive status updates for command staff
- **Resource Allocation**: Recommends resource deployment based on threat analysis

### 🧠 Advanced Memory Management
- **Multi-Strategy Memory**: Semantic + Summary strategies active
- **Incident Tracking**: Maintains persistent memory of ongoing wildfires
- **Historical Analysis**: Learns from past incidents to improve predictions
- **Memory ID**: `WildfireNowcastAgentMultiStrategy-XXXXXXXXXX`

## NASA Data Sources

### FIRMS (Fire Information for Resource Management System)
- **MODIS Hotspots**: Terra and Aqua satellite fire detection
- **VIIRS Hotspots**: Suomi NPP and NOAA-20 satellite data
- **Update Frequency**: Near-real-time (3-6 hour delay)
- **Coverage**: Global wildfire monitoring

### GIBS (Global Imagery Browse Services)
- **WMTS Tiles**: Web Map Tile Service for basemaps
- **MODIS Corrected Reflectance**: True-color and false-color imagery
- **VIIRS Day/Night Band**: Nighttime fire detection
- **Landsat Imagery**: High-resolution satellite data

### EONET (Earth Observatory Natural Event Tracker)
- **Event Context**: Additional wildfire event information
- **Historical Events**: Past wildfire data for comparison
- **Event Classification**: Categorizes fire events by type and severity

### Getting NASA API Keys

**Only FIRMS requires an API key** - GIBS and EONET are publicly accessible:

1. **FIRMS API Key** (Required): 
   - Visit: https://firms.modaps.eosdis.nasa.gov/api/map_key
   - Register for a free account
   - Generate your API key
   - Add to `.env` file as `NASA_FIRMS_API_KEY`

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



3. **Configure Environment Variables**
```bash
# Option A: Interactive setup (recommended)
uv run python setup_env.py

# Option B: Manual setup
cp .env.template .env
# Edit .env and add your NASA API keys
# Required: NASA_FIRMS_API_KEY
# Note: GIBS and EONET are publicly accessible - no API keys needed
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

6. **Test the Agent**
```bash
# Test specific query
uv run python test_agent.py --query "Check for wildfire hotspots in California"

# Test NASA integration
uv run python test_agent.py --test-type nasa

# Test threat assessment
uv run python test_agent.py --test-type threat

# Run all tests
uv run python test_agent.py
```

## 🎯 **Live Demo**

The agent is currently operational and processing real queries:

```bash
# Example: Real-time wildfire detection
uv run python test_agent.py --query "Check for wildfire hotspots in California"

# Output: Real NASA FIRMS data showing current fire status
# Response time: ~15 seconds with live satellite data
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

**Enhanced NASA Data Integration** (`tools/improved_nasa_tools.py`):
- `fetch_firms_hotspots_enhanced()`:  Enhanced MODIS/VIIRS hotspot data with better processing
- `get_gibs_capabilities()`:  Get GIBS WMS capabilities and available layers
- `get_gibs_layer_info()`:  Get detailed information about specific GIBS layers
- `fetch_gibs_map_image()`:  Fetch map images from GIBS WMS (NASA compliant)
- `fetch_eonet_events_enhanced()`:  Enhanced EONET events with advanced filtering
- `get_eonet_categories()`:  Get available EONET event categories
- `get_eonet_sources()`:  Get available EONET data sources
- `get_nasa_data_summary_enhanced()`:  Comprehensive NASA data summary

**Threat Assessment** (`tools/threat_tools.py`):
- `assess_asset_threats()`:  Analyze threats to critical infrastructure
- `rank_fire_threats()`:  Prioritize fires by threat level
- `calculate_evacuation_zones()`:  Determine evacuation areas
- `generate_threat_summary()`:  Generate comprehensive threat assessment

**Mapping & Visualization** (`tools/mapping_tools.py`):
- `generate_fire_map()`:  Create live fire maps with overlays
- `render_evacuation_map()`:  Generate evacuation zone maps
- `create_progression_map()`:  Show fire progression over time
- `generate_threat_visualization()`:  Create data visualizations

**ICS Reporting** (`tools/ics_tools.py`):
- `draft_ics_situation_report()`:  Generate standardized ICS reports
- `create_resource_recommendations()`:  Recommend resource allocation
- `generate_incident_briefing()`:  Create command staff briefings

**Memory & Incident Management** (`tools/memory_tools.py`):
- `create_wildfire_memory()`:  Create multi-strategy memory system
- `create_memory_tools()`:  Generate memory management tools
- Memory strategies:  Semantic + Summary (active)

## 🚀 **Accessing Your Deployed Agent**

### Option 1: AWS Bedrock Console (Recommended)
1. Go to [AWS Bedrock AgentCore Console](https://console.aws.amazon.com/bedrock-agentcore/agents)
2. Select region: **us-east-1**
3. Navigate to **AgentCore** section
4. Find runtime: `wildfire_nowcast_agent_runtime-XXXXXXXXXX`
5. Use the built-in agent sandbox to test queries

### Option 2: Local Testing (Working)
```bash
# Test specific queries
uv run python test_agent.py --query "Check for wildfire hotspots in California"
uv run python test_agent.py --query "Generate a fire map for the Pacific Northwest"
uv run python test_agent.py --query "Assess threats to critical infrastructure"

# Test different capabilities
uv run python test_agent.py --test-type nasa
uv run python test_agent.py --test-type threat
uv run python test_agent.py --test-type mapping
```

### Option 3: Direct AgentCore API
```bash
# Use AWS CLI to invoke the agent
aws bedrock-agentcore invoke-agent-runtime \
  --runtime-id wildfire_nowcast_agent_runtime-XXXXXXXXXX \
  --input '{"prompt": "Check for wildfire hotspots in California"}'
```

## Monitoring

### CloudWatch Logs
Monitor your deployed agent:
```bash
# View logs for your runtime
aws logs tail /aws/bedrock-agentcore/runtimes/wildfire_nowcast_agent_runtime-XXXXXXXXXX-DEFAULT --follow

# View memory logs
aws logs tail /aws/bedrock-agentcore/memory/WildfireNowcastAgentMultiStrategy-XXXXXXXXXX --follow
```

### Health Checks
-  Agent runtime: Active and responding
-  Memory system: Multi-strategy memory operational
-  NASA API connectivity: Real-time data access confirmed
-  Response times: ~15 seconds for complex queries

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
-  AgentCore Runtime instances
-  AgentCore Memory instances  
-  ECR repositories and container images
-  CodeBuild projects
-  S3 build artifacts
-  SSM parameters
-  IAM roles and policies (unless `--skip-iam`)
-  Local deployment files

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

- **NASA FIRMS** for wildfire hotspot data
- **NASA GIBS** for satellite imagery services  
- **NASA EONET** for event tracking
- **Amazon Bedrock** for AI/ML capabilities
- **Strands Agents** for the agent framework
- **OWSLib** for NASA-compliant geospatial data access
