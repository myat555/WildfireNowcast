"""
Wildfire Nowcast Agent - Main Agent Implementation

This module implements the main wildfire detection and response agent using
the Strands Agent framework with Amazon Bedrock AgentCore.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tools import (
    # NASA Data Tools (Enhanced)
    fetch_firms_hotspots_enhanced,
    get_gibs_capabilities,
    get_gibs_layer_info,
    fetch_gibs_map_image,
    fetch_eonet_events_enhanced,
    get_eonet_categories,
    get_eonet_sources,
    get_nasa_data_summary_enhanced,
    
    # Threat Assessment Tools
    assess_asset_threats,
    rank_fire_threats,
    calculate_evacuation_zones,
    generate_threat_summary,
    
    # Mapping Tools
    generate_fire_map,
    render_evacuation_map,
    create_progression_map,
    generate_threat_visualization,
    
    # ICS Reporting Tools
    draft_ics_situation_report,
    create_resource_recommendations,
    generate_incident_briefing,
    
    # Memory Tools
    create_wildfire_memory,
    create_memory_tools
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bedrock AgentCore App
app = BedrockAgentCoreApp()

class WildfireNowcastAgent:
    """Main Wildfire Nowcast Agent using Strands framework"""
    
    def __init__(self):
        self.memory_client = None
        self.memory_id = None
        self.session_id = f"wildfire-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.default_actor_id = "wildfire-operator"
        
        # Initialize memory
        self._initialize_memory()
        
        # Create memory tools
        self.memory_tools = create_memory_tools(
            self.memory_client, 
            self.memory_id, 
            self.session_id, 
            self.default_actor_id
        )
        
        # Initialize Strands Agent
        self.agent = self._create_agent()
    
    def _initialize_memory(self):
        """Initialize AgentCore Memory for the wildfire agent"""
        try:
            self.memory_client, self.memory_id = create_wildfire_memory()
            logger.info(f"Memory initialized with ID: {self.memory_id}")
        except Exception as e:
            logger.error(f"Error initializing memory: {e}")
            raise
    
    def _create_agent(self) -> Agent:
        """Create the main Strands Agent with all tools"""
        
        # Define all available tools
        tools = [
            # NASA Data Tools (Enhanced)
            fetch_firms_hotspots_enhanced,
            get_gibs_capabilities,
            get_gibs_layer_info,
            fetch_gibs_map_image,
            fetch_eonet_events_enhanced,
            get_eonet_categories,
            get_eonet_sources,
            get_nasa_data_summary_enhanced,
            
            # Threat Assessment Tools
            assess_asset_threats,
            rank_fire_threats,
            calculate_evacuation_zones,
            generate_threat_summary,
            
            # Mapping Tools
            generate_fire_map,
            render_evacuation_map,
            create_progression_map,
            generate_threat_visualization,
            
            # ICS Reporting Tools
            draft_ics_situation_report,
            create_resource_recommendations,
            generate_incident_briefing,
            
            # Memory Tools
            *self.memory_tools
        ]
        
        # Create Strands Agent with tools
        agent = Agent(
            name="WildfireNowcastAgent",
            description="Intelligent wildfire detection and response agent",
            tools=tools,
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            system_prompt=self._get_system_prompt()
        )
        
        return agent
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the wildfire agent"""
        return """You are an expert wildfire detection and response agent with advanced capabilities in Earth observation data analysis, threat assessment, and emergency management. You have access to NASA's real-time wildfire data and can provide comprehensive wildfire monitoring and response services.

PURPOSE:
- Detect and monitor wildfire hotspots using NASA satellite data
- Assess threats to life, property, and critical infrastructure
- Generate live maps and visualizations for situational awareness
- Draft Incident Command System (ICS) reports and briefings
- Provide real-time wildfire intelligence and response recommendations

AVAILABLE TOOLS:

NASA Data Integration (Enhanced):
- fetch_firms_hotspots_enhanced(area, days_back, confidence, satellite, format): Enhanced FIRMS hotspot retrieval with better data processing
- get_gibs_capabilities(projection): Get GIBS WMS capabilities for available layers and services
- get_gibs_layer_info(layer_name, projection): Get detailed information about specific GIBS layers
- fetch_gibs_map_image(layer_name, bbox, size, date, projection, format): Fetch map images from GIBS WMS following NASA documentation
- fetch_eonet_events_enhanced(category, days_back, status, limit, source): Enhanced EONET events with advanced filtering
- get_eonet_categories(): Get available EONET event categories
- get_eonet_sources(): Get available EONET data sources
- get_nasa_data_summary_enhanced(area, days_back, include_gibs, include_eonet): Enhanced comprehensive NASA data summary

Threat Assessment & Analysis:
- assess_asset_threats(hotspots_data, assets_data, max_distance_km): Analyze threats to critical assets
- rank_fire_threats(hotspots_data, criteria): Rank wildfire hotspots by threat level
- calculate_evacuation_zones(hotspots_data, assets_data, buffer_distance_km): Calculate evacuation zones
- generate_threat_summary(hotspots_data, assets_data): Generate comprehensive threat assessment

Mapping & Visualization:
- generate_fire_map(hotspots_data, assets_data, map_center, zoom_level, include_assets): Create interactive fire maps
- render_evacuation_map(hotspots_data, assets_data, evacuation_data, map_center, zoom_level): Generate evacuation zone maps
- create_progression_map(hotspots_data, time_range_hours, map_center, zoom_level): Show fire progression over time
- generate_threat_visualization(threat_data, visualization_type): Create data visualizations

ICS Reporting & Emergency Management:
- draft_ics_situation_report(hotspots_data, threat_data, evacuation_data, incident_name, incident_number): Generate ICS situation reports
- create_resource_recommendations(threat_data, evacuation_data, resource_availability): Recommend resource allocation
- generate_incident_briefing(situation_report, resource_recommendations, briefing_type): Create incident briefings

Memory & Incident Tracking:
- track_active_incidents(incident_data, actor_id_override): Track active wildfire incidents
- get_incident_history(incident_id, actor_id_override): Retrieve historical incident data
- update_incident_status(incident_id, status_update, actor_id_override): Update incident status
- store_threat_assessment(assessment_data, incident_id, actor_id_override): Store threat assessments
- retrieve_incident_patterns(incident_id, actor_id_override): Retrieve fire behavior patterns
- store_response_strategy(strategy_data, incident_id, actor_id_override): Store response strategies

WORKFLOW GUIDELINES:

1. **Wildfire Detection & Monitoring**:
   - Use fetch_firms_hotspots_enhanced() to get current wildfire data with enhanced processing
   - Analyze hotspot data for new fires and fire progression
   - Cross-reference with fetch_eonet_events_enhanced() for additional context
   - Use get_gibs_capabilities() to discover available imagery layers
   - Track active incidents using memory tools

2. **Threat Assessment**:
   - Assess threats to critical infrastructure and populated areas
   - Rank fires by threat level and potential impact
   - Calculate evacuation zones based on fire behavior
   - Generate comprehensive threat summaries

3. **Mapping & Visualization**:
   - Use get_gibs_layer_info() to get detailed layer information
   - Use fetch_gibs_map_image() to get high-quality satellite imagery
   - Create interactive maps showing fire locations and threats
   - Generate evacuation zone maps for emergency planning
   - Show fire progression over time
   - Create data visualizations for threat analysis

4. **Emergency Response**:
   - Draft ICS situation reports for command staff
   - Recommend resource allocation based on threat assessment
   - Generate incident briefings for different audiences
   - Provide real-time updates and recommendations

5. **Memory Management**:
   - Track all active incidents in memory
   - Store threat assessments and response strategies
   - Retrieve historical patterns for improved predictions
   - Maintain incident history for lessons learned

RESPONSE GUIDELINES:
- Always provide accurate, timely information based on NASA data
- Prioritize life safety and property protection in recommendations
- Use clear, professional language suitable for emergency management
- Include specific coordinates, threat levels, and recommended actions
- Reference data sources and update timestamps
- Provide actionable recommendations for emergency responders

CRITICAL: Always prioritize life safety and provide immediate actionable information for emergency response. Use the most current NASA data available and maintain situational awareness through continuous monitoring."""

    def process_query(self, query: str) -> str:
        """Process a user query using the Strands Agent"""
        try:
            # Use Strands Agent to process the query
            import asyncio
            response = asyncio.run(self.agent.invoke_async(query))
            return str(response)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"Error processing query: {e}"

# Initialize the agent
wildfire_agent = WildfireNowcastAgent()

@app.entrypoint
def wildfire_nowcast_agent_runtime(payload):
    """
    Invoke the wildfire nowcast agent with a payload for AgentCore Runtime
    """
    user_input = payload.get("prompt")
    
    # Process the query using the Strands Agent
    response = wildfire_agent.process_query(user_input)
    
    return response

def wildfire_nowcast_agent_local(payload):
    """
    Invoke the wildfire nowcast agent with a payload for local testing
    
    Args:
        payload (dict): Dictionary containing the user prompt
        
    Returns:
        str: The agent's response containing wildfire analysis and recommendations
    """
    user_input = payload.get("prompt")
    
    # Process the query using the Strands Agent
    response = wildfire_agent.process_query(user_input)
    
    return response

if __name__ == "__main__":
    app.run()
