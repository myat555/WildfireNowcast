#!/bin/bash

# Setup and run script for Wildfire Detection Frontend

set -e  # Exit on error

# Function to display section headers
section() {
  echo ""
  echo "=========================================="
  echo "  $1"
  echo "=========================================="
  echo ""
}

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

section "Setting up Wildfire Detection Frontend"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || {
    echo "Error: Could not activate virtual environment"
    exit 1
}

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Flask Configuration
FLASK_DEBUG=false
SECRET_KEY=wildfire-detection-secret-key-change-in-production
PORT=5001

# MCP Server Configuration
MCP_SERVER_URL=https://your-gateway-id.gateway.bedrock-agentcore.us-west-2.amazonaws.com

# Cognito Configuration (optional)
COGNITO_DOMAIN=your-cognito-domain.auth.us-west-2.amazoncognito.com
COGNITO_CLIENT_ID=your-cognito-client-id

# Bearer Token (if available)
BEARER_TOKEN=your-bearer-token-here
EOF
    
    echo ""
    echo "Please edit the .env file to configure your settings:"
    echo "- Set MCP_SERVER_URL to your gateway endpoint"
    echo "- Configure Cognito settings if using authentication"
    echo "- Set BEARER_TOKEN if you have one"
    echo ""
    read -p "Press Enter to continue after editing .env file..."
fi

section "Starting Wildfire Detection Frontend"

echo "Starting Flask application on port 5001..."
echo "Open your browser to: http://localhost:5001"
echo ""
echo "Available endpoints:"
echo "  - /                : Main dashboard"
echo "  - /chat            : AI Assistant chat interface"
echo "  - /map             : Interactive fire map"
echo "  - /alerts          : Alert management"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the Flask application
python main.py
