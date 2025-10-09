# WildfireNowcast Backend API

FastAPI backend server that connects the frontend to AWS Bedrock Agent and NASA APIs.

## Features

- ✅ Real-time agent communication via REST and WebSocket
- ✅ Streaming responses for live updates
- ✅ NASA FIRMS, GIBS, and EONET API integration
- ✅ **Real-time weather data integration (OpenWeather API)**
- ✅ Threat assessment and ICS reporting
- ✅ Session management
- ✅ CORS support for frontend integration

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your AWS credentials and agent ID
```

**Required variables:**
- `AWS_REGION` - AWS region (e.g., us-east-1)
- `BEDROCK_AGENT_ID` - Your Bedrock Agent ID from deployment
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `NASA_FIRMS_API_KEY` - NASA FIRMS API key for fire data

**Optional variables:**
- `OPENWEATHER_API_KEY` - OpenWeather API key for real-time weather (see [WEATHER_INTEGRATION.md](../WEATHER_INTEGRATION.md))

**Get your Agent ID:**
```bash
# After deploying the agent, find the ID in:
cat ../.deployment_info
# Or from AWS Console: Amazon Bedrock → Agents
```

### 3. Run the Server

```bash
# Development mode (with auto-reload)
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

### 4. Test the API

**Health check:**
```bash
curl http://localhost:8000/health
```

**Query the agent:**
```bash
curl -X POST http://localhost:8000/api/agent-query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Check for wildfire hotspots in California"}'
```

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with API info |
| GET | `/health` | Health check |
| POST | `/api/agent-query` | Query agent (JSON response) |
| POST | `/api/agent-query-stream` | Query agent (streaming SSE) |
| WS | `/ws/agent` | WebSocket connection |

### NASA Data Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/firms-hotspots` | Get FIRMS fire hotspots |
| POST | `/api/gibs-map-image` | Get GIBS satellite imagery |
| POST | `/api/eonet-events` | Get EONET wildfire events |

### Analysis Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/threat-assessment` | Assess infrastructure threats |
| POST | `/api/rank-threats` | Rank fire threats by criteria |
| POST | `/api/evacuation-zones` | Calculate evacuation zones |
| POST | `/api/fire-map` | Generate fire map |
| POST | `/api/evacuation-map` | Generate evacuation map |
| POST | `/api/progression-map` | Generate fire progression map |
| POST | `/api/ics-report` | Generate ICS report |
| POST | `/api/resource-recommendations` | Get resource recommendations |
| GET | `/api/nasa-summary` | Get comprehensive NASA data summary |

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage Examples

### Basic Agent Query
```python
import requests

response = requests.post(
    "http://localhost:8000/api/agent-query",
    json={
        "prompt": "What are the current wildfire threats in California?",
        "enable_trace": False
    }
)

print(response.json())
```

### Streaming Response
```python
import requests

response = requests.post(
    "http://localhost:8000/api/agent-query-stream",
    json={"prompt": "Analyze current fire conditions"},
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/agent');

ws.onopen = () => {
    ws.send(JSON.stringify({
        prompt: "Check for wildfire hotspots"
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
};
```

### NASA FIRMS Hotspots
```python
response = requests.post(
    "http://localhost:8000/api/firms-hotspots",
    json={
        "area": "California",
        "days_back": 1,
        "confidence": "nominal",
        "satellite": "both"
    }
)
```

## Frontend Integration

Update your frontend environment variable:

```bash
# frontend/.env
VITE_API_URL=http://localhost:8000/api
```

The frontend will automatically use this endpoint for all API calls.

## Deployment

### Option 1: AWS Lambda + API Gateway

```bash
# Install serverless framework
npm install -g serverless

# Deploy
serverless deploy
```

### Option 2: AWS ECS/Fargate

```bash
# Build Docker image
docker build -t wildfire-backend .

# Push to ECR and deploy
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag wildfire-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/wildfire-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/wildfire-backend:latest
```

### Option 3: EC2

```bash
# SSH to EC2
ssh -i key.pem ec2-user@<instance-ip>

# Install dependencies
sudo yum install python3-pip
pip3 install -r requirements.txt

# Run with systemd or screen
screen -S backend
python3 main.py
```

## Configuration

### CORS Settings

By default, CORS allows all origins. For production:

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Session Management

Sessions are automatically managed with UUID-based session IDs. Each conversation maintains context within the same session.

## Troubleshooting

### "Agent ID not configured"
- Ensure `BEDROCK_AGENT_ID` is set in `.env`
- Get ID from deployment: `cat ../.deployment_info | grep agentRuntimeId`

### "Unable to locate credentials"
- Set AWS credentials in `.env` or use AWS CLI configured profile
- Ensure IAM permissions for Bedrock Agent Runtime

### CORS errors
- Add your frontend URL to `ALLOWED_ORIGINS` in `.env`
- Check browser console for specific CORS issues

### Connection timeout
- Increase timeout in uvicorn: `--timeout-keep-alive 300`
- Check AWS region matches agent deployment

## Development

### Add New Endpoint

```python
@app.post("/api/my-endpoint")
async def my_endpoint(data: MyModel):
    prompt = f"Custom prompt with {data}"
    session_id = get_session_id()
    result = await invoke_bedrock_agent(prompt, session_id)
    return result
```

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

MIT
