# Wildfire Nowcast Agent - Quick Start Guide

## Overview

This guide will help you quickly deploy and test the Wildfire Nowcast Agent, a sophisticated AI-powered system for wildfire detection and emergency response using NASA Earth observation data.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **AWS CLI** configured with appropriate credentials
- **Docker** installed and running
- **Access to Amazon Bedrock AgentCore**
- **NASA API keys** (optional, for enhanced data access)

## Quick Deployment (5 Minutes)

### 1. Install Dependencies

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### 2. Deploy the Agent

```bash
# Simple deployment
uv run python deploy.py

# Or with custom configuration
uv run python deploy.py \
  --agent-name "my-wildfire-agent" \
  --region "us-west-2" \
  --role-name "MyCustomRole"
```

### 3. Test the Agent

```bash
# Run comprehensive tests
uv run python test_agent.py

# Or test specific functionality
uv run python test_agent.py --test-type nasa
uv run python test_agent.py --test-type threat
uv run python test_agent.py --test-type mapping
```

## Quick Usage Examples

### 🔥 Wildfire Detection

```python
# Check for new hotspots
query = "Check for new wildfire hotspots in California"
response = wildfire_nowcast_agent_local({"prompt": query})
```

### 🎯 Threat Assessment

```python
# Assess threats to infrastructure
query = "Assess wildfire threats to critical infrastructure in California"
response = wildfire_nowcast_agent_local({"prompt": query})
```

### 🗺️ Live Mapping

```python
# Generate fire map
query = "Generate a live map of current fire activity"
response = wildfire_nowcast_agent_local({"prompt": query})
```

### 📋 ICS Reporting

```python
# Draft situation report
query = "Draft an ICS situation report for current fires"
response = wildfire_nowcast_agent_local({"prompt": query})
```

## Sample Data

The project includes sample asset data for testing:

```bash
# View sample assets
cat sample_assets.json
```

This includes:
- Los Angeles International Airport
- UCLA Medical Center
- Griffith Observatory
- Beverly Hills Residential Area
- And more...

## Common Use Cases

### 1. Real-Time Monitoring

```python
# Monitor specific area
query = "Monitor wildfire activity in the Pacific Northwest"
response = wildfire_nowcast_agent_local({"prompt": query})
```

### 2. Threat Analysis

```python
# Analyze threats to populated areas
query = "Analyze threats to populated areas near current fires"
response = wildfire_nowcast_agent_local({"prompt": query})
```

### 3. Evacuation Planning

```python
# Calculate evacuation zones
query = "Calculate evacuation zones for active fires"
response = wildfire_nowcast_agent_local({"prompt": query})
```

### 4. Resource Allocation

```python
# Recommend resources
query = "Recommend resource allocation for current threats"
response = wildfire_nowcast_agent_local({"prompt": query})
```

## Interactive Testing

### Command Line Interface

```bash
# Start interactive session
python -c "
import boto3, json
client = boto3.client('bedrock-agentcore', region_name='us-east-1')
with open('.agent_arn', 'r') as f: arn = f.read().strip()
print('🔥 Wildfire Nowcast Agent Chat (type \"quit\" to exit)')
while True:
    try:
        msg = input('\n🤖 You: ')
        if msg.lower() in ['quit', 'exit']: break
        resp = client.invoke_agent_runtime(agentRuntimeArn=arn, payload=json.dumps({'prompt': msg}))
        print('🔥 Agent:', resp['response'].read().decode('utf-8'))
    except KeyboardInterrupt: break
"
```

### Python Script Testing

```python
from wildfire_nowcast_agent import wildfire_nowcast_agent_local

# Test queries
queries = [
    "Check for new wildfire hotspots in California",
    "Assess threats to critical infrastructure",
    "Generate a live fire map",
    "Draft an ICS situation report"
]

for query in queries:
    print(f"\nQuery: {query}")
    response = wildfire_nowcast_agent_local({"prompt": query})
    print(f"Response: {response[:200]}...")
```

## Monitoring and Logs

### View Logs

```bash
# View agent logs
aws logs tail /aws/bedrock-agentcore/runtimes/{agent-id}-DEFAULT --follow
```

### Health Checks

The agent includes built-in health check endpoints and monitoring capabilities.

## Cleanup

When you're done testing:

```bash
# Complete cleanup
uv run python cleanup.py

# Preview cleanup (dry run)
uv run python cleanup.py --dry-run

# Keep IAM roles
uv run python cleanup.py --skip-iam
```

## Troubleshooting

### Common Issues

1. **Docker not running**
   ```bash
   # Start Docker
   sudo systemctl start docker
   ```

2. **AWS credentials not configured**
   ```bash
   # Configure AWS CLI
   aws configure
   ```

3. **Memory issues**
   ```bash
   # Clean up duplicate memories
   uv run python cleanup.py
   ```

4. **Permission errors**
   - Ensure IAM role has required permissions
   - Check AWS region configuration
   - Verify Bedrock access

### Debug Mode

```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
uv run python test_agent.py
```

## Next Steps

1. **Customize Configuration**
   - Modify `pyproject.toml` for dependencies
   - Update `sample_assets.json` with your assets
   - Configure NASA API keys for enhanced access

2. **Extend Functionality**
   - Add custom threat assessment algorithms
   - Integrate additional data sources
   - Create custom visualization tools

3. **Production Deployment**
   - Set up monitoring and alerting
   - Configure backup and recovery
   - Implement security best practices

## Support

For issues and questions:

1. Check the logs for error messages
2. Review the architecture documentation
3. Test individual components
4. Verify AWS permissions and configuration

## Resources

- [README.md](README.md) - Complete documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [NASA FIRMS API](https://firms.modaps.eosdis.nasa.gov/api/) - Fire data
- [NASA GIBS](https://gibs.earthdata.nasa.gov/) - Imagery service
- [Strands Agents](https://strandsagents.com/) - Agent framework
- [Amazon Bedrock](https://aws.amazon.com/bedrock/) - AI/ML platform
