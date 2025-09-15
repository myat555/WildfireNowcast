"""
Wildfire Detection Web Interface
Flask application for interacting with the Wildfire Early-Warning & Triage Agent
"""
import os
import json
import requests
import asyncio
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, stream_template
from dotenv import load_dotenv
import logging
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'wildfire-detection-secret-key-change-in-production')

# Configuration
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'https://your-gateway.bedrock-agentcore.amazonaws.com')
COGNITO_DOMAIN = os.getenv('COGNITO_DOMAIN', '')
COGNITO_CLIENT_ID = os.getenv('COGNITO_CLIENT_ID', '')
BEARER_TOKEN = os.getenv('BEARER_TOKEN', '')

# Sample protected areas for the map display
PROTECTED_AREAS = [
    {
        'id': 'yellowstone-np',
        'name': 'Yellowstone National Park',
        'center': [44.4280, -110.5885],
        'priority': 'HIGH'
    },
    {
        'id': 'yosemite-np', 
        'name': 'Yosemite National Park',
        'center': [37.8651, -119.5383],
        'priority': 'HIGH'
    },
    {
        'id': 'los-angeles-metro',
        'name': 'Los Angeles Metropolitan Area',
        'center': [34.0522, -118.2437],
        'priority': 'CRITICAL'
    },
    {
        'id': 'san-francisco-bay',
        'name': 'San Francisco Bay Area',
        'center': [37.7749, -122.4194],
        'priority': 'HIGH'
    }
]

def get_bearer_token():
    """Get bearer token for authentication"""
    if BEARER_TOKEN:
        return BEARER_TOKEN
    
    # Try to get token from Cognito if configured
    if COGNITO_DOMAIN and COGNITO_CLIENT_ID:
        try:
            # This would need proper OAuth2 implementation
            # For now, return None to use simple auth
            pass
        except Exception as e:
            logger.error(f"Error getting Cognito token: {e}")
    
    return None

def send_message_to_agent(message, conversation_id=None):
    """Send message to the wildfire agent and get streaming response"""
    try:
        token = get_bearer_token()
        headers = {
            'Content-Type': 'application/json'
        }
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        payload = {
            "jsonrpc": "2.0",
            "id": conversation_id or str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "chat",
                "arguments": {
                    "prompt": message
                }
            }
        }
        
        logger.info(f"Sending request to: {MCP_SERVER_URL}/mcp")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response content: {response.text[:500]}...")
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"HTTP {response.status_code}: {response.text}",
                "status_code": response.status_code
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception: {str(e)}")
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

@app.route('/')
def index():
    """Main page with wildfire monitoring interface"""
    return render_template('wildfire_dashboard.html', 
                         protected_areas=PROTECTED_AREAS,
                         mcp_server_url=MCP_SERVER_URL)

@app.route('/chat')
def chat():
    """Chat interface for interacting with the wildfire agent"""
    return render_template('wildfire_chat.html')

@app.route('/map')
def fire_map():
    """Interactive fire map interface"""
    return render_template('fire_map.html', protected_areas=PROTECTED_AREAS)

@app.route('/alerts')
def alerts():
    """Alert management interface"""
    return render_template('alert_dashboard.html')

@app.route('/api/send_message', methods=['POST'])
def api_send_message():
    """API endpoint to send message to wildfire agent"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        conversation_id = data.get('conversation_id')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Add timestamp to message for context
        timestamped_message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}] {message}"
        
        response = send_message_to_agent(timestamped_message, conversation_id)
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/quick_query/<query_type>')
def api_quick_query(query_type):
    """API endpoint for quick wildfire queries"""
    try:
        queries = {
            'hotspots_california': 'Show me active wildfire hotspots in California from the last 24 hours',
            'threat_yellowstone': 'What is the current wildfire threat level for Yellowstone National Park?',
            'map_west_coast': 'Generate a fire map for the West Coast showing current hotspots',
            'ics_update': 'Draft an ICS-213 update for current wildfire activity',
            'protected_areas': 'Check if any fires are currently threatening protected areas',
            'high_confidence': 'Show me only high confidence fire detections from NASA satellites'
        }
        
        message = queries.get(query_type)
        if not message:
            return jsonify({"error": "Invalid query type"}), 400
        
        response = send_message_to_agent(message)
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in quick_query: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/system_status')
def api_system_status():
    """API endpoint to check system status"""
    try:
        # Test connection to MCP server
        token = get_bearer_token()
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        test_payload = {
            "jsonrpc": "2.0",
            "id": "health-check",
            "method": "tools/list",
            "params": {}
        }
        
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        status = {
            "mcp_server": {
                "url": MCP_SERVER_URL,
                "status": "connected" if response.status_code == 200 else "error",
                "response_time": response.elapsed.total_seconds() if response else None
            },
            "authentication": {
                "method": "bearer_token" if token else "none",
                "status": "configured" if token else "not_configured"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error checking system status: {str(e)}")
        return jsonify({
            "mcp_server": {"status": "error", "error": str(e)},
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/login')
def login():
    """Login page"""
    if COGNITO_DOMAIN:
        return render_template('cognito_login.html', 
                             cognito_domain=COGNITO_DOMAIN,
                             client_id=COGNITO_CLIENT_ID)
    else:
        return render_template('simple_login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """Simple login API (for demo purposes)"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Simple demo authentication
        if username and password:
            session['user'] = username
            session['authenticated'] = True
            return jsonify({"success": True, "message": "Login successful"})
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"success": False, "message": "Login failed"}), 500

@app.route('/logout')
def logout():
    """Logout endpoint"""
    session.clear()
    return redirect(url_for('login'))

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('error.html', 
                         error_code=404,
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('error.html',
                         error_code=500, 
                         error_message="Internal server error"), 500

if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Wildfire Detection Web Interface on port {port}")
    logger.info(f"MCP Server URL: {MCP_SERVER_URL}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
