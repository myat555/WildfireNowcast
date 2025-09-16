"""
Multi-Agent NASA Data Integration Architecture

This module implements a specialized multi-agent approach for NASA data sources,
where each agent is optimized for specific APIs and data types.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from strands import Agent, tool
from tools.improved_nasa_tools import (
    nasa_client, gibs_client, eonet_client,
    fetch_firms_hotspots_enhanced,
    get_gibs_capabilities,
    get_gibs_layer_info,
    fetch_gibs_map_image,
    fetch_eonet_events_enhanced,
    get_eonet_categories,
    get_eonet_sources
)

logger = logging.getLogger(__name__)

class FIRMSDataAgent:
    """Specialized agent for FIRMS fire hotspot data"""
    
    def __init__(self):
        self.agent = Agent(
            name="FIRMSDataAgent",
            description="Specialized agent for NASA FIRMS fire hotspot data analysis",
            tools=[fetch_firms_hotspots_enhanced],
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a specialized NASA FIRMS data analysis agent. Your expertise is in:

FIRE HOTSPOT DATA ANALYSIS:
- MODIS and VIIRS satellite fire detection
- Brightness temperature analysis
- Fire radiative power (FRP) calculations
- Confidence level assessment
- Temporal fire progression tracking

CAPABILITIES:
- Real-time hotspot detection and monitoring
- Fire intensity and size estimation
- Multi-satellite data fusion
- Geographic fire pattern analysis
- Historical fire trend analysis

RESPONSE GUIDELINES:
- Provide detailed fire hotspot analysis
- Include confidence levels and data quality metrics
- Explain satellite detection capabilities and limitations
- Focus on actionable fire intelligence
- Prioritize recent and high-confidence detections"""

    def analyze_hotspots(self, query: str) -> str:
        """Analyze fire hotspots based on user query"""
        return self.agent.run(query)

class GIBSImageryAgent:
    """Specialized agent for GIBS satellite imagery"""
    
    def __init__(self):
        self.agent = Agent(
            name="GIBSImageryAgent", 
            description="Specialized agent for NASA GIBS satellite imagery and mapping",
            tools=[get_gibs_capabilities, get_gibs_layer_info, fetch_gibs_map_image],
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a specialized NASA GIBS imagery analysis agent. Your expertise is in:

SATELLITE IMAGERY ANALYSIS:
- MODIS Terra/Aqua corrected reflectance
- VIIRS day/night band imagery
- Landsat high-resolution data
- Multi-spectral band analysis
- True-color and false-color composites

MAPPING CAPABILITIES:
- Web Map Service (WMS) integration
- Multiple projection support (EPSG:4326, EPSG:3857, etc.)
- Tile-based mapping systems
- Layer composition and overlay
- Temporal imagery analysis

RESPONSE GUIDELINES:
- Provide detailed imagery analysis
- Explain spectral characteristics and applications
- Recommend optimal layers for specific use cases
- Include technical specifications and limitations
- Focus on wildfire detection and monitoring applications"""

    def analyze_imagery(self, query: str) -> str:
        """Analyze satellite imagery based on user query"""
        return self.agent.run(query)

class EONETEventsAgent:
    """Specialized agent for EONET event data"""
    
    def __init__(self):
        self.agent = Agent(
            name="EONETEventsAgent",
            description="Specialized agent for NASA EONET natural event tracking",
            tools=[fetch_eonet_events_enhanced, get_eonet_categories, get_eonet_sources],
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a specialized NASA EONET events analysis agent. Your expertise is in:

NATURAL EVENT TRACKING:
- Wildfire event monitoring and classification
- Event lifecycle management (open/closed status)
- Multi-source event validation
- Historical event analysis
- Event categorization and tagging

DATA SOURCE INTEGRATION:
- Multiple data source coordination
- Event correlation and validation
- Source reliability assessment
- Event metadata analysis
- Cross-reference validation

RESPONSE GUIDELINES:
- Provide comprehensive event analysis
- Include event status and lifecycle information
- Explain data source reliability and validation
- Focus on wildfire-specific events
- Provide context for emergency response planning"""

    def analyze_events(self, query: str) -> str:
        """Analyze natural events based on user query"""
        return self.agent.run(query)

class NASAOrchestratorAgent:
    """Orchestrator agent that coordinates specialized NASA agents"""
    
    def __init__(self):
        self.firms_agent = FIRMSDataAgent()
        self.gibs_agent = GIBSImageryAgent()
        self.eonet_agent = EONETEventsAgent()
        
        self.agent = Agent(
            name="NASAOrchestratorAgent",
            description="Orchestrator for NASA data analysis agents",
            tools=[],  # No direct tools, coordinates other agents
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        return """You are the NASA Data Orchestrator Agent. You coordinate specialized agents for comprehensive wildfire analysis:

SPECIALIZED AGENTS:
1. FIRMSDataAgent - Fire hotspot detection and analysis
2. GIBSImageryAgent - Satellite imagery and mapping
3. EONETEventsAgent - Natural event tracking and validation

ORCHESTRATION CAPABILITIES:
- Route queries to appropriate specialized agents
- Combine results from multiple agents
- Provide integrated analysis across data sources
- Coordinate multi-source validation
- Synthesize comprehensive wildfire intelligence

WORKFLOW:
1. Analyze user query to determine required data sources
2. Route to appropriate specialized agents
3. Collect and synthesize results
4. Provide integrated analysis and recommendations

RESPONSE GUIDELINES:
- Always route queries to the most appropriate agent(s)
- Provide integrated analysis when multiple sources are needed
- Explain which agents were used and why
- Synthesize results into actionable intelligence
- Maintain context across multiple data sources"""

    def process_query(self, query: str) -> str:
        """Process query by routing to appropriate specialized agents"""
        try:
            # Analyze query to determine which agents to use
            agents_to_use = self._determine_agents(query)
            
            if len(agents_to_use) == 1:
                # Single agent query
                agent = agents_to_use[0]
                return agent.run(query)
            else:
                # Multi-agent query - use orchestrator
                return self._orchestrate_multi_agent_query(query, agents_to_use)
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"Error processing query: {e}"
    
    def _determine_agents(self, query: str) -> List[Any]:
        """Determine which agents should handle the query"""
        query_lower = query.lower()
        agents = []
        
        # Check for FIRMS-related keywords
        firms_keywords = ['hotspot', 'fire detection', 'modis', 'viirs', 'brightness', 'frp']
        if any(keyword in query_lower for keyword in firms_keywords):
            agents.append(self.firms_agent)
        
        # Check for GIBS-related keywords
        gibs_keywords = ['imagery', 'satellite image', 'map', 'visualization', 'layer', 'gibs']
        if any(keyword in query_lower for keyword in gibs_keywords):
            agents.append(self.gibs_agent)
        
        # Check for EONET-related keywords
        eonet_keywords = ['event', 'eonet', 'natural event', 'tracking', 'status']
        if any(keyword in query_lower for keyword in eonet_keywords):
            agents.append(self.eonet_agent)
        
        # If no specific keywords, use all agents for comprehensive analysis
        if not agents:
            agents = [self.firms_agent, self.gibs_agent, self.eonet_agent]
        
        return agents
    
    def _orchestrate_multi_agent_query(self, query: str, agents: List[Any]) -> str:
        """Orchestrate multi-agent query processing"""
        results = {}
        
        # Get results from each agent
        for agent in agents:
            try:
                agent_name = agent.agent.name
                result = agent.run(query)
                results[agent_name] = result
            except Exception as e:
                logger.error(f"Error with agent {agent.agent.name}: {e}")
                results[agent.agent.name] = f"Error: {e}"
        
        # Synthesize results
        synthesis = self._synthesize_results(query, results)
        return synthesis
    
    def _synthesize_results(self, query: str, results: Dict[str, str]) -> str:
        """Synthesize results from multiple agents"""
        synthesis_prompt = f"""
        Original Query: {query}
        
        Agent Results:
        {json.dumps(results, indent=2)}
        
        Please synthesize these results into a comprehensive analysis that:
        1. Integrates information from all relevant data sources
        2. Identifies correlations and patterns across sources
        3. Provides actionable recommendations
        4. Highlights any conflicting or complementary information
        5. Maintains focus on wildfire detection and response
        """
        
        return self.agent.run(synthesis_prompt)

# Initialize the orchestrator
nasa_orchestrator = NASAOrchestratorAgent()

@tool
def process_nasa_query_multi_agent(query: str) -> str:
    """
    Process NASA data query using multi-agent architecture.
    
    Args:
        query: User query about NASA data
    
    Returns:
        Comprehensive analysis from appropriate specialized agents
    """
    return nasa_orchestrator.process_query(query)

@tool
def get_nasa_agent_capabilities() -> str:
    """
    Get capabilities of all NASA specialized agents.
    
    Returns:
        JSON string containing agent capabilities
    """
    capabilities = {
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "FIRMSDataAgent": {
                "description": "Specialized agent for NASA FIRMS fire hotspot data analysis",
                "capabilities": [
                    "Real-time hotspot detection",
                    "MODIS/VIIRS data analysis", 
                    "Fire intensity assessment",
                    "Temporal progression tracking",
                    "Confidence level analysis"
                ],
                "tools": ["fetch_firms_hotspots_enhanced"]
            },
            "GIBSImageryAgent": {
                "description": "Specialized agent for NASA GIBS satellite imagery and mapping",
                "capabilities": [
                    "Satellite imagery analysis",
                    "Multi-spectral band processing",
                    "Map generation and visualization",
                    "Layer composition",
                    "Temporal imagery analysis"
                ],
                "tools": ["get_gibs_capabilities", "get_gibs_layer_info", "fetch_gibs_map_image"]
            },
            "EONETEventsAgent": {
                "description": "Specialized agent for NASA EONET natural event tracking",
                "capabilities": [
                    "Natural event monitoring",
                    "Event lifecycle management",
                    "Multi-source validation",
                    "Event categorization",
                    "Historical analysis"
                ],
                "tools": ["fetch_eonet_events_enhanced", "get_eonet_categories", "get_eonet_sources"]
            },
            "NASAOrchestratorAgent": {
                "description": "Orchestrator for coordinating specialized NASA agents",
                "capabilities": [
                    "Multi-agent coordination",
                    "Query routing",
                    "Result synthesis",
                    "Integrated analysis",
                    "Cross-source validation"
                ],
                "tools": []
            }
        }
    }
    
    return json.dumps(capabilities, indent=2)
