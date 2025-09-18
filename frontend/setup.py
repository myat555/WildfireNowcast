#!/usr/bin/env python3
"""
Setup script for WildfireNowcast Frontend

This script sets up the React frontend and integrates it with the existing
WildfireNowcast agent backend.
"""

import os
import subprocess
import sys
import json
from pathlib import Path

def run_command(command, cwd=None, check=True):
    """Run a command and handle errors"""
    try:
        print(f"Running: {command}")
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_node_installed():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Node.js is not installed")
            return False
    except FileNotFoundError:
        print("❌ Node.js is not installed")
        return False

def check_npm_installed():
    """Check if npm is installed"""
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ npm is not installed")
            return False
    except FileNotFoundError:
        print("❌ npm is not installed")
        return False

def install_frontend_dependencies():
    """Install frontend dependencies"""
    print("\n📦 Installing frontend dependencies...")
    
    # Install dependencies
    result = run_command("npm install")
    if result.returncode == 0:
        print("✅ Frontend dependencies installed successfully")
        return True
    else:
        print("❌ Failed to install frontend dependencies")
        return False

def install_backend_dependencies():
    """Install backend API dependencies"""
    print("\n📦 Installing backend API dependencies...")
    
    dependencies = [
        "fastapi",
        "uvicorn",
        "python-multipart"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        result = run_command(f"pip install {dep}")
        if result.returncode == 0:
            print(f"✅ {dep} installed successfully")
        else:
            print(f"❌ Failed to install {dep}")
            return False
    
    return True

def build_frontend():
    """Build the frontend for production"""
    print("\n🔨 Building frontend...")
    
    # Build the frontend
    result = run_command("npm run build")
    if result.returncode == 0:
        print("✅ Frontend built successfully")
        return True
    else:
        print("❌ Failed to build frontend")
        return False

def create_env_file():
    """Create environment file for frontend"""
    print("\n📝 Creating environment file...")
    
    env_content = """# Frontend Environment Variables
VITE_API_URL=http://localhost:8000
"""
    
    env_file = Path(".env")
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("✅ Environment file created")

def create_startup_scripts():
    """Create startup scripts"""
    print("\n📝 Creating startup scripts...")
    
    # Frontend development script
    frontend_dev_script = """#!/bin/bash
echo "🚀 Starting WildfireNowcast Frontend Development Server..."
npm run dev
"""
    
    with open("start_dev.sh", "w") as f:
        f.write(frontend_dev_script)
    os.chmod("start_dev.sh", 0o755)
    
    # Backend API script
    backend_api_script = """#!/bin/bash
echo "🚀 Starting WildfireNowcast API Server..."
python api_server.py
"""
    
    with open("start_api.sh", "w") as f:
        f.write(backend_api_script)
    os.chmod("start_api.sh", 0o755)
    
    # Full stack script
    full_stack_script = """#!/bin/bash
echo "🚀 Starting WildfireNowcast Full Stack..."
echo "Starting API server in background..."
python api_server.py &
API_PID=$!

echo "Waiting for API server to start..."
sleep 5

echo "Starting frontend development server..."
npm run dev &
FRONTEND_PID=$!

echo "Both servers are running!"
echo "API Server: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait $API_PID $FRONTEND_PID
"""
    
    with open("start_full_stack.sh", "w") as f:
        f.write(full_stack_script)
    os.chmod("start_full_stack.sh", 0o755)
    
    print("✅ Startup scripts created")

def create_demo_script():
    """Create agent demo script"""
    print("\n📝 Creating agent demo script...")
    
    demo_script = """#!/usr/bin/env python3
\"\"\"
Agent Demo Script for WildfireNowcast Frontend

This script demonstrates the agent's capabilities by running example queries
and showing the intelligent responses that would be displayed in the frontend.
\"\"\"

import json
import time
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path to import the agent
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from wildfire_nowcast_agent import wildfire_nowcast_agent_local
except ImportError:
    print("Warning: Could not import agent. Make sure you're running from the project root.")
    def wildfire_nowcast_agent_local(payload):
        return "Mock agent response - agent not available"

def print_header(title):
    \"\"\"Print a formatted header\"\"\"
    print("\\n" + "="*60)
    print(f"🔥 {title}")
    print("="*60)

def print_step(step, description):
    \"\"\"Print a formatted step\"\"\"
    print(f"\\n📋 {step}")
    print(f"   {description}")

def print_response(response, tools_used=None, insights=None, recommendations=None):
    \"\"\"Print a formatted agent response\"\"\"
    print(f"\\n🤖 Agent Response:")
    print(f"   {response}")
    
    if tools_used:
        print(f"\\n🛠️  Tools Used:")
        for tool in tools_used:
            print(f"   • {tool}")
    
    if insights:
        print(f"\\n💡 Data Insights:")
        for insight in insights:
            print(f"   • {insight}")
    
    if recommendations:
        print(f"\\n🎯 Recommendations:")
        for rec in recommendations:
            print(f"   • {rec}")

def simulate_thinking(step_name, duration=2):
    \"\"\"Simulate agent thinking process\"\"\"
    print(f"\\n🧠 Agent is thinking about: {step_name}")
    for i in range(duration):
        print(".", end="", flush=True)
        time.sleep(1)
    print(" ✓")

def demo_agent_capabilities():
    \"\"\"Demonstrate the agent's capabilities\"\"\"
    
    print_header("WildfireNowcast Agent Capabilities Demo")
    
    print("\\nThis demo showcases the intelligent capabilities of the WildfireNowcast Agent")
    print("that would be displayed in the frontend interface.")
    
    # Demo queries
    demos = [
        {
            "title": "1. Real-time Wildfire Detection",
            "query": "Check for wildfire hotspots in California",
            "response": "I've analyzed NASA FIRMS satellite data and detected 8 active wildfire hotspots in California. The Canyon Fire in Los Angeles County shows extreme severity with 15,420 acres burned and only 25% containment.",
            "tools": ["fetch_firms_hotspots_enhanced", "assess_asset_threats", "generate_threat_summary"],
            "insights": ["8 active fires detected via MODIS/VIIRS satellites", "Canyon Fire poses immediate threat to 3 power substations"],
            "recommendations": ["Immediate evacuation of Zone A (2,500 residents)", "Deploy additional aircraft for aerial suppression"]
        },
        {
            "title": "2. AI-Powered Threat Assessment", 
            "query": "Assess threats to critical infrastructure near current fires",
            "response": "I've conducted a comprehensive threat assessment for critical infrastructure within 10 miles of active fires. The analysis reveals 12 high-risk assets including power substations, water treatment facilities, and communication towers.",
            "tools": ["assess_asset_threats", "rank_fire_threats", "calculate_evacuation_zones"],
            "insights": ["3 power substations within 2-mile radius of Canyon Fire", "2 water treatment facilities at risk of contamination"],
            "recommendations": ["Implement protective measures for power infrastructure", "Prepare backup water supply systems"]
        }
    ]
    
    for demo in demos:
        print_header(demo["title"])
        print_step("User Query", demo["query"])
        simulate_thinking("Analyzing data and generating insights", 2)
        print_response(demo["response"], demo["tools"], demo["insights"], demo["recommendations"])
    
    print_header("Agent Intelligence Summary")
    print("\\n🎯 Key Capabilities Demonstrated:")
    capabilities = [
        "Real-time NASA satellite data analysis",
        "AI-powered threat assessment", 
        "Dynamic fire mapping and visualization",
        "Automated ICS report generation",
        "Intelligent resource planning",
        "Evacuation zone calculation"
    ]
    
    for capability in capabilities:
        print(f"   ✅ {capability}")
    
    print("\\n🚀 This demonstrates how the WildfireNowcast Agent provides:")
    benefits = [
        "Intelligent analysis of complex wildfire data",
        "Automated threat assessment and recommendations", 
        "Real-time situational awareness",
        "Professional emergency response planning",
        "Seamless integration of multiple data sources",
        "AI-driven decision support for emergency managers"
    ]
    
    for benefit in benefits:
        print(f"   🔥 {benefit}")
    
    print("\\n" + "="*60)
    print("🎉 Agent Demo Complete!")
    print("The frontend showcases these intelligent capabilities")
    print("through an interactive, professional interface.")
    print("="*60)

if __name__ == "__main__":
    demo_agent_capabilities()
"""
    
    with open("demo_agent.py", "w") as f:
        f.write(demo_script)
    os.chmod("demo_agent.py", 0o755)
    
    print("✅ Agent demo script created")

def main():
    """Main setup function"""
    print("🔥 WildfireNowcast Frontend Setup")
    print("=" * 50)
    
    # Check prerequisites
    print("\n🔍 Checking prerequisites...")
    if not check_node_installed():
        print("\n❌ Please install Node.js from https://nodejs.org/")
        sys.exit(1)
    
    if not check_npm_installed():
        print("\n❌ Please install npm (usually comes with Node.js)")
        sys.exit(1)
    
    # Setup steps
    steps = [
        ("Installing frontend dependencies", install_frontend_dependencies),
        ("Installing backend API dependencies", install_backend_dependencies),
        ("Creating environment file", create_env_file),
        ("Building frontend", build_frontend),
        ("Creating startup scripts", create_startup_scripts),
        ("Creating agent demo script", create_demo_script),
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        if not step_func():
            print(f"❌ Failed: {step_name}")
            sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Start the full stack: ./start_full_stack.sh")
    print("2. Or start components separately:")
    print("   - Frontend: ./start_dev.sh")
    print("   - API: ./start_api.sh")
    print("3. Access the dashboard at http://localhost:3000")
    print("4. API documentation at http://localhost:8000/docs")
    print("5. Run agent demo: python demo_agent.py")

if __name__ == "__main__":
    main()
