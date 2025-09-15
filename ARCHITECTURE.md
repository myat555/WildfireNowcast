# Wildfire Early-Warning & Triage Agent - Architecture

## System Overview

The Wildfire Early-Warning & Triage Agent is an autonomous AI system that monitors real-time NASA satellite data to detect wildfire threats and coordinate emergency response. Built on AWS using the Strands Agent framework, it demonstrates the power of combining earth observation data with AI reasoning for public safety.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    WILDFIRE NOWCAST SYSTEM                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │   NASA      │    │   AWS        │    │   Emergency     │    │
│  │   FIRMS     │───▶│   Lambda     │───▶│   Response      │    │
│  │   GIBS      │    │   Functions  │    │   Teams         │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
│         │                   │                      │           │
│         │                   ▼                      │           │
│         │          ┌─────────────────┐             │           │
│         │          │   DynamoDB      │             │           │
│         │          │   - Hotspots    │             │           │
│         │          │   - Incidents   │             │           │
│         │          │   - Areas (AOI) │             │           │
│         │          │   - Alerts      │             │           │
│         │          └─────────────────┘             │           │
│         │                   │                      │           │
│         ▼                   ▼                      ▼           │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │  Bedrock    │    │   Strands    │    │  Notification   │    │
│  │  AgentCore  │◀──▶│   Agent      │───▶│  System         │    │
│  │  Gateway    │    │   Runtime    │    │  - Email        │    │
│  └─────────────┘    └──────────────┘    │  - SMS          │    │
│         │                   │           │  - Slack        │    │
│         │                   │           └─────────────────┘    │
│         ▼                   ▼                                  │
│  ┌─────────────┐    ┌──────────────┐                          │
│  │  Web        │    │  Mobile      │                          │
│  │  Dashboard  │    │  App (Future)│                          │
│  └─────────────┘    └──────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Data Ingestion Layer

#### NASA FIRMS API Integration
- **Purpose**: Real-time wildfire hotspot detection
- **Data Sources**: 
  - MODIS (1km resolution, 4x daily)
  - VIIRS (375m resolution, 2x daily)
- **Format**: CSV/JSON with lat/lon, confidence, brightness temperature
- **Update Frequency**: Every 15 minutes (configurable)

#### NASA GIBS Integration
- **Purpose**: Satellite imagery and map tile services
- **Services**: WMTS (Web Map Tile Service)
- **Layers**: True color imagery, fire overlays, burn scars
- **Usage**: Interactive map generation and visualization

### 2. Processing Layer

#### Lambda Functions
```python
# Main processing functions
wildfire-detection/
├── lambda_function.py       # MCP tool implementations
├── dynamodb_models.py       # Database schema and setup
├── notification_system.py   # Alert notifications
├── alert_processor.py       # Alert logic and suppression
└── synthetic_data.py        # Test data generation
```

**Key Functions:**
- `fetch_firms_hotspots`: Retrieve and process NASA satellite data
- `assess_threat_level`: AI-powered threat assessment
- `generate_fire_map`: Create interactive fire maps
- `draft_ics_update`: Generate ICS-213 incident reports
- `check_aoi_intersections`: Protected area intersection analysis

### 3. AI Agent Layer

#### Strands Agent Runtime
```python
# Agent implementation
agent-runtime/
├── wildfire_strands_agent_runtime.py    # Main agent logic
├── wildfire_strands_agent_runtime_deploy.py  # Deployment
├── access_token.py                       # Authentication
├── utils.py                             # Utilities
└── requirements-runtime.txt             # Dependencies
```

**Features:**
- **Model**: Claude Sonnet 3.5 via Amazon Bedrock
- **Conversation Management**: Sliding window with context retention
- **Tool Integration**: Real-time NASA data access
- **Streaming Responses**: Real-time chat with formatted output
- **Specialized Prompts**: Emergency management terminology and protocols

### 4. Data Storage Layer

#### DynamoDB Tables

```sql
-- Hotspot detections from NASA FIRMS
WildfireIncidents:
  - incident_id (PK)
  - name, status, location
  - size_acres, containment_percent
  - threat_level, resources_assigned

-- Individual satellite fire detections  
FireHotspots:
  - hotspot_id (PK)
  - latitude, longitude, confidence
  - acq_date, acq_time, satellite, instrument
  - GSI: DateIndex (acq_date, confidence)

-- Protected areas and assets
ProtectedAreas:
  - area_id (PK)
  - name, priority, center_lat, center_lon
  - polygon (coordinates), threat_radius_km
  - GSI: PriorityIndex (priority, name)

-- Alert history and notifications
FireAlerts:
  - alert_id (PK)
  - alert_level, created_date
  - hotspot_location, affected_areas
  - notification_results, status
  - GSI: AlertLevelIndex (alert_level, created_date)
```

### 5. Gateway Layer

#### Bedrock AgentCore Gateway
```python
# Gateway configuration
gateway/
├── create_gateway.py              # Gateway setup
├── wildfire-detection-target.py   # Lambda target configuration
└── gateway_observability.py       # Monitoring setup
```

**Configuration:**
- **Protocol**: MCP (Model Context Protocol)
- **Authentication**: Cognito JWT tokens
- **Tools**: 5 specialized wildfire detection tools
- **Observability**: CloudWatch Logs, X-Ray tracing

### 6. User Interface Layer

#### Web Dashboard
```python
# Frontend application
frontend/
├── main.py                    # Flask application
├── templates/
│   ├── wildfire_dashboard.html    # Main dashboard
│   ├── wildfire_chat.html         # AI chat interface
│   └── fire_map.html             # Interactive map
└── static/css/wildfire.css       # Custom styling
```

**Features:**
- **Real-time Dashboard**: Live fire activity monitoring
- **AI Chat Interface**: Natural language queries
- **Interactive Maps**: NASA GIBS tile integration
- **Alert Management**: Notification history and status
- **Responsive Design**: Mobile and desktop optimized

### 7. Notification System

#### Multi-channel Alerting
```python
# Alert processing
notification_system.py:
  - Email alerts via AWS SES
  - SMS alerts via AWS SNS  
  - Slack notifications via webhooks
  - Alert suppression and rate limiting
```

**Alert Levels:**
- **CRITICAL**: Immediate threat to life/property (all channels)
- **HIGH**: Significant threat requiring attention (email + Slack)
- **MEDIUM**: Monitoring required (logged only)
- **LOW**: Informational (logged only)

## Data Flow

### 1. Detection Flow
```
NASA FIRMS → Lambda Function → Threat Assessment → DynamoDB Storage
     ↓              ↓                 ↓                ↓
  Hotspot Data → AI Analysis → Risk Calculation → Alert Generation
```

### 2. User Interaction Flow
```
User Query → Web Interface → AgentCore Gateway → Strands Agent
     ↓             ↓              ↓                 ↓
  Natural Lang. → MCP Protocol → Tool Selection → NASA API Call
     ↓             ↓              ↓                 ↓  
  Response ← Formatted Output ← Processing ← Real Data
```

### 3. Alert Flow
```
High Confidence Detection → Threat Assessment → Alert Processor
           ↓                        ↓                ↓
    AOI Intersection → Risk Calculation → Notification System
           ↓                        ↓                ↓
    Protected Areas → Alert Level → Multi-channel Alerts
```

## Security & Compliance

### Authentication & Authorization
- **Cognito Integration**: JWT token-based authentication
- **IAM Roles**: Least-privilege access patterns
- **API Security**: Rate limiting and input validation

### Data Privacy
- **No PII Storage**: Only geospatial and system data
- **Encryption**: At-rest and in-transit encryption
- **Audit Logging**: Complete activity trails

### Emergency Response Compliance
- **ICS Standards**: Incident Command System compatibility
- **NWCG Guidelines**: National Wildland Coordinating Group protocols
- **NASA Attribution**: Proper data source acknowledgment

## Scalability & Performance

### Horizontal Scaling
- **Lambda Functions**: Auto-scaling based on demand
- **DynamoDB**: On-demand billing with burst capacity
- **Gateway**: Multi-AZ deployment with load balancing

### Performance Optimizations
- **Caching**: DynamoDB DAX for sub-millisecond responses
- **Connection Pooling**: Reusable database connections
- **Batch Processing**: Efficient bulk operations

### Monitoring & Observability
- **CloudWatch Metrics**: Custom performance metrics
- **X-Ray Tracing**: End-to-end request tracking
- **Log Aggregation**: Centralized logging with search
- **Alerting**: System health notifications

## Deployment Architecture

### Infrastructure as Code
```bash
# Deployment components
deploy_all.sh                    # Master deployment script
├── wildfire-detection/deploy.sh    # Lambda deployment
├── gateway/create_gateway.py       # Gateway setup
└── agent-runtime/deploy.py         # Agent deployment
```

### Environment Management
- **Development**: Local testing with mock data
- **Staging**: AWS deployment with test notifications
- **Production**: Full monitoring with real alerts

### CI/CD Pipeline (Recommended)
```yaml
# GitHub Actions workflow
Deploy Pipeline:
  - Code Quality Checks
  - Unit Tests
  - Integration Tests  
  - Security Scanning
  - Infrastructure Deployment
  - Smoke Tests
  - Production Deployment
```

## Cost Optimization

### AWS Service Usage
- **Lambda**: Pay-per-invocation model
- **DynamoDB**: On-demand pricing for variable workloads
- **Bedrock**: Token-based LLM pricing
- **S3**: Intelligent tiering for map tiles

### Estimated Monthly Costs (1000 queries/day)
- **Lambda Functions**: ~$5-10
- **DynamoDB**: ~$10-20  
- **Bedrock (Claude)**: ~$50-100
- **Gateway**: ~$20-30
- **Notifications**: ~$5-15
- **Total**: ~$90-175/month

## Future Enhancements

### Planned Features
1. **Mobile Application**: Native iOS/Android apps
2. **Weather Integration**: Wind/humidity data for fire behavior
3. **Predictive Modeling**: ML-based fire spread prediction
4. **Drone Integration**: Real-time aerial reconnaissance
5. **Multi-language Support**: International deployment

### Technical Improvements
1. **GraphQL API**: More efficient data fetching
2. **Real-time Streaming**: WebSocket-based live updates
3. **Edge Computing**: Regional data processing
4. **Blockchain Logging**: Immutable audit trails
5. **AR Visualization**: Augmented reality fire mapping

This architecture provides a robust, scalable, and compliant foundation for wildfire early-warning systems while demonstrating advanced AI agent capabilities using AWS services.
