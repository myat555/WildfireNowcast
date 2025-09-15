#!/bin/bash

# Deployment workflow script for Wildfire Detection System
# This script deploys all components in the correct order

set -e  # Exit on error

# Function to display section headers
section() {
  echo ""
  echo "=========================================="
  echo "  $1"
  echo "=========================================="
  echo ""
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
section "Checking prerequisites"

# Check for AWS CLI
if ! command_exists aws; then
  echo "Error: AWS CLI is not installed. Please install it first."
  exit 1
fi

# Check for Python
if ! command_exists python; then
  echo "Error: Python is not installed. Please install Python 3.8 or higher."
  exit 1
fi

# Check for pip
if ! command_exists pip; then
  echo "Error: pip is not installed. Please install it first."
  exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "Error: AWS credentials not configured or invalid. Please run 'aws configure'."
  exit 1
fi

echo "All prerequisites satisfied."

# Step 1: Deploy Wildfire Detection Lambda
section "Step 1: Deploying Wildfire Detection Lambda"

cd wildfire-detection
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Deploying Lambda function..."
chmod +x deploy.sh
./deploy.sh

# Get the Lambda ARN from the output file or AWS CLI
if [ -f lambda_arn.txt ]; then
  LAMBDA_ARN=$(grep LAMBDA_ARN lambda_arn.txt | cut -d= -f2)
  echo "Lambda ARN: $LAMBDA_ARN"
else
  # Fallback: get Lambda ARN directly from AWS
  LAMBDA_FUNCTION_NAME=${LAMBDA_FUNCTION_NAME:-"WildfireDetectionLambda"}
  LAMBDA_ARN=$(aws lambda get-function --function-name "$LAMBDA_FUNCTION_NAME" --region us-west-2 --query 'Configuration.FunctionArn' --output text 2>/dev/null)
  if [ -z "$LAMBDA_ARN" ]; then
    echo "Error: Lambda ARN not found. Please ensure the Lambda function was deployed successfully."
    exit 1
  fi
  echo "Lambda ARN (from AWS): $LAMBDA_ARN"
fi

cd ..

# Step 2: Create Gateway
section "Step 2: Creating Wildfire Gateway"

cd gateway

# Check if .env file exists, if not create it
if [ ! -f .env ]; then
  echo "Creating .env file for gateway..."
  
  # Create basic .env file structure
  cat > .env << EOF
# AWS and endpoint configuration
AWS_REGION=us-west-2
ENDPOINT_URL=https://bedrock-agentcore-control.us-west-2.amazonaws.com

# Lambda configuration (from wildfire-detection module)
LAMBDA_ARN=$LAMBDA_ARN

# Target configuration
GATEWAY_IDENTIFIER=your-gateway-identifier
TARGET_NAME=wildfire-detection-target
TARGET_DESCRIPTION=Wildfire Detection and Threat Assessment Target

# Gateway creation configuration
GATEWAY_NAME=Wildfire-Detection-Gateway
GATEWAY_DESCRIPTION=Wildfire Early-Warning and Triage Gateway

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
EOF
  
  echo "Please edit the gateway/.env file to set your Cognito details and other required values."
  echo "Then run this script again."
  exit 0
else
  # Update existing .env file with Lambda ARN
  echo "Updating existing .env file with Lambda ARN..."
  if grep -q "^LAMBDA_ARN=" .env; then
    # Update existing LAMBDA_ARN line
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "s|^LAMBDA_ARN=.*|LAMBDA_ARN=$LAMBDA_ARN|g" .env
    else
      sed -i "s|^LAMBDA_ARN=.*|LAMBDA_ARN=$LAMBDA_ARN|g" .env
    fi
  else
    # Add LAMBDA_ARN to the file
    echo "" >> .env
    echo "# Lambda configuration (from wildfire-detection module)" >> .env
    echo "LAMBDA_ARN=$LAMBDA_ARN" >> .env
  fi
fi

echo "Creating wildfire gateway..."
python create_gateway.py

# Get the Gateway ID from the output
GATEWAY_NAME=$(grep GATEWAY_NAME .env | cut -d= -f2)
GATEWAY_ID=$(aws bedrock-agentcore list-gateways --query "gateways[?name=='$GATEWAY_NAME'].gatewayId" --output text)

if [ -z "$GATEWAY_ID" ]; then
  echo "Error: Failed to get Gateway ID."
  exit 1
fi

echo "Gateway ID: $GATEWAY_ID"

# Update the .env file with the Gateway ID
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' "s|GATEWAY_IDENTIFIER=.*|GATEWAY_IDENTIFIER=$GATEWAY_ID|g" .env
else
  sed -i "s|GATEWAY_IDENTIFIER=.*|GATEWAY_IDENTIFIER=$GATEWAY_ID|g" .env
fi

echo "Creating wildfire gateway target..."
python wildfire-detection-target.py

# Update .env with Gateway ARN and ID for observability
GATEWAY_ARN=$(aws bedrock-agentcore list-gateways --query "gateways[?gatewayId=='$GATEWAY_ID'].gatewayArn" --output text)
if ! grep -q "^GATEWAY_ARN=" .env; then
  echo "GATEWAY_ARN=$GATEWAY_ARN" >> .env
fi
if ! grep -q "^GATEWAY_ID=" .env; then
  echo "GATEWAY_ID=$GATEWAY_ID" >> .env
fi

cd ..

# Step 3: Deploy Strands Agent Runtime
section "Step 3: Deploying Wildfire Strands Agent Runtime"

cd agent-runtime

# Check if .env file exists, if not create it
if [ ! -f .env ]; then
  echo "Creating .env file for agent runtime..."
  
  # Create basic .env file structure
  cat > .env << EOF
# AWS and endpoint configuration
AWS_REGION=us-west-2
ENDPOINT_URL=https://bedrock-agentcore-control.us-west-2.amazonaws.com

# Gateway configuration
GATEWAY_ID=$GATEWAY_ID
MCP_SERVER_URL=https://$GATEWAY_ID.gateway.bedrock-agentcore.us-west-2.amazonaws.com

# Agent configuration
AGENT_NAME=wildfire-detection-agent
AGENT_DESCRIPTION=Wildfire Early-Warning and Triage Agent
BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0

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
EOF
  
  echo "Please edit the agent-runtime/.env file to set your Cognito details and other required values."
  echo "Then run this script again."
  exit 0
fi

echo "Installing Python dependencies for agent runtime..."
pip install -r requirements-runtime.txt

echo "Deploying wildfire strands agent runtime..."
python wildfire_strands_agent_runtime_deploy.py --gateway_id "$GATEWAY_ID"

cd ..

# Step 4: Update frontend configuration
section "Step 4: Updating frontend configuration"

# Get the Gateway URL
GATEWAY_URL="https://$GATEWAY_ID.gateway.bedrock-agentcore.us-west-2.amazonaws.com"
echo "Gateway URL: $GATEWAY_URL"

# Create .env file for frontend if it doesn't exist
if [ ! -f frontend/.env ]; then
  echo "Creating .env file for frontend..."
  echo "MCP_SERVER_URL=$GATEWAY_URL" > frontend/.env
  echo "GATEWAY_ID=$GATEWAY_ID" >> frontend/.env
  echo "AGENT_TYPE=wildfire-detection" >> frontend/.env
  
  echo "Please complete the frontend/.env file with any missing values."
fi

section "Deployment completed successfully!"
echo "Next steps:"
echo "1. Set up protected areas data: Add your Areas of Interest (AOI) to DynamoDB"
echo "2. Configure NASA API access: Set your NASA_API_KEY in the .env files"
echo "3. Set up alerting: Configure email, phone, and Slack webhook URLs"
echo "4. Test the system: Use the Q CLI or chat application to query wildfire data"
echo "5. Monitor the system: Check CloudWatch Logs and X-Ray traces"
echo ""
echo "Gateway URL: $GATEWAY_URL"
echo ""
echo "Sample queries to try:"
echo '- "Show me active wildfires in California"'
echo '- "What is the threat level at coordinates 34.0522, -118.2437?"'
echo '- "Generate a fire map centered on Yellowstone National Park"'
echo '- "Draft an ICS update for current fire activity"'
echo '- "Check if any fires are threatening protected areas"'
echo ""
echo "Observability Information:"
echo "- CloudWatch Log Group: /aws/bedrock-agentcore/wildfire-detection-agent"
echo "- X-Ray Traces: Enabled for the agent runtime"
echo "- Metrics: Available in CloudWatch Metrics under the 'wildfire-detection-agent' namespace"
echo ""
echo "To view logs: https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups"
echo "To view traces: https://console.aws.amazon.com/xray/home?region=us-west-2#/traces"
