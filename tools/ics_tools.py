"""
ICS (Incident Command System) Reporting Tools for Wildfire Nowcast Agent

This module provides tools for generating standardized ICS reports,
resource recommendations, and incident briefings for emergency management.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from strands import tool

logger = logging.getLogger(__name__)

class ICSReportGenerator:
    """Generator for ICS-compliant wildfire reports"""
    
    def __init__(self):
        # ICS report templates
        self.situation_report_template = {
            "incident_name": "",
            "incident_number": "",
            "date_time": "",
            "prepared_by": "Wildfire Nowcast Agent",
            "report_type": "Situation Report",
            "sections": {
                "current_situation": "",
                "fire_activity": "",
                "weather_conditions": "",
                "resources_assigned": "",
                "evacuations": "",
                "threats_to_life_property": "",
                "planned_actions": "",
                "coordination": ""
            }
        }
        
        # Resource types and capabilities
        self.resource_types = {
            "aircraft": {
                "types": ["helicopter", "air_tanker", "single_engine_air_tanker", "lead_plane"],
                "capabilities": ["water_drops", "retardant_drops", "reconnaissance", "command_control"]
            },
            "ground_crews": {
                "types": ["hotshot_crew", "engine_crew", "hand_crew", "dozer_crew"],
                "capabilities": ["fireline_construction", "mop_up", "structure_protection", "evacuation_support"]
            },
            "equipment": {
                "types": ["fire_engines", "bulldozers", "water_tenders", "communications"],
                "capabilities": ["fire_suppression", "line_construction", "water_supply", "communications"]
            },
            "personnel": {
                "types": ["incident_commander", "operations_chief", "safety_officer", "liaison_officer"],
                "capabilities": ["command_control", "operations_management", "safety_monitoring", "coordination"]
            }
        }
        
        # Threat assessment criteria
        self.threat_criteria = {
            "CRITICAL": {
                "description": "Immediate threat to life and property",
                "response_time": "Immediate",
                "resource_priority": "Highest",
                "evacuation_status": "Mandatory"
            },
            "HIGH": {
                "description": "Significant threat requiring immediate attention",
                "response_time": "Within 1 hour",
                "resource_priority": "High",
                "evacuation_status": "Recommended"
            },
            "MODERATE": {
                "description": "Potential threat requiring monitoring",
                "response_time": "Within 4 hours",
                "resource_priority": "Medium",
                "evacuation_status": "Prepare"
            },
            "LOW": {
                "description": "Minimal threat with routine monitoring",
                "response_time": "Within 24 hours",
                "resource_priority": "Low",
                "evacuation_status": "Monitor"
            }
        }

@tool
def draft_ics_situation_report(
    hotspots_data: str,
    threat_data: str,
    evacuation_data: str,
    incident_name: str = "Wildfire Incident",
    incident_number: str = None
) -> str:
    """
    Draft a comprehensive ICS Situation Report based on current wildfire data.
    
    Args:
        hotspots_data: JSON string containing FIRMS hotspot data
        threat_data: JSON string containing threat assessment data
        evacuation_data: JSON string containing evacuation zone data
        incident_name: Name of the incident
        incident_number: Incident number (auto-generated if not provided)
    
    Returns:
        JSON string containing formatted ICS Situation Report
    """
    try:
        # Parse input data
        hotspots = json.loads(hotspots_data)
        threats = json.loads(threat_data)
        evacuations = json.loads(evacuation_data)
        
        # Generate incident number if not provided
        if not incident_number:
            incident_number = f"WF-{datetime.now().strftime('%Y%m%d-%H%M')}"
        
        # Initialize report generator
        generator = ICSReportGenerator()
        
        # Create base report
        report = generator.situation_report_template.copy()
        report["incident_name"] = incident_name
        report["incident_number"] = incident_number
        report["date_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate report sections
        hotspot_count = len(hotspots.get('hotspots', []))
        critical_threats = threats.get('summary', {}).get('critical_threats', 0)
        high_threats = threats.get('summary', {}).get('high_threats', 0)
        evacuation_zones = evacuations.get('summary', {}).get('total_evacuation_zones', 0)
        affected_population = evacuations.get('summary', {}).get('total_affected_population', 0)
        
        # Current Situation
        report["sections"]["current_situation"] = f"""
        Multiple wildfire hotspots detected in the area. Total of {hotspot_count} active hotspots 
        identified through NASA satellite monitoring. {critical_threats} critical threats and 
        {high_threats} high-level threats to life and property identified.
        """
        
        # Fire Activity
        fire_activity = "Active fire activity detected in the following areas:\n"
        for hotspot in hotspots.get('hotspots', [])[:5]:  # Top 5 hotspots
            lat = hotspot.get('latitude', 0)
            lon = hotspot.get('longitude', 0)
            confidence = hotspot.get('confidence', 'unknown')
            brightness = hotspot.get('brightness', 0)
            fire_activity += f"- Location: {lat:.4f}, {lon:.4f} | Confidence: {confidence} | Brightness: {brightness}\n"
        
        report["sections"]["fire_activity"] = fire_activity
        
        # Weather Conditions
        report["sections"]["weather_conditions"] = """
        Weather conditions favorable for fire spread. Recommend monitoring wind patterns 
        and humidity levels. Current conditions support rapid fire growth potential.
        """
        
        # Resources Assigned
        report["sections"]["resources_assigned"] = f"""
        Resources required based on threat assessment:
        - Aircraft: {max(1, critical_threats)} units for immediate response
        - Ground crews: {max(2, critical_threats + high_threats)} units
        - Equipment: Fire engines, bulldozers, water tenders
        - Personnel: Incident command team, safety officers
        """
        
        # Evacuations
        if evacuation_zones > 0:
            report["sections"]["evacuations"] = f"""
            {evacuation_zones} evacuation zones established affecting approximately 
            {affected_population} people. Evacuation orders issued for areas within 
            fire spread zones.
            """
        else:
            report["sections"]["evacuations"] = "No evacuation zones currently established."
        
        # Threats to Life and Property
        threat_summary = f"""
        Critical threats identified: {critical_threats}
        High-level threats identified: {high_threats}
        Total affected population: {affected_population}
        
        Primary concerns:
        - Immediate threat to life and property in critical threat areas
        - Potential for rapid fire spread
        - Resource allocation challenges
        """
        report["sections"]["threats_to_life_property"] = threat_summary
        
        # Planned Actions
        report["sections"]["planned_actions"] = f"""
        1. Deploy resources to critical threat areas immediately
        2. Establish incident command post
        3. Implement evacuation procedures for affected areas
        4. Coordinate with local emergency services
        5. Monitor fire progression and adjust response accordingly
        6. Provide regular updates to command staff
        """
        
        # Coordination
        report["sections"]["coordination"] = """
        Coordination established with:
        - NASA FIRMS for satellite monitoring
        - Local emergency management agencies
        - Fire departments and emergency services
        - Weather service for conditions monitoring
        """
        
        # Add metadata
        report["metadata"] = {
            "data_sources": ["NASA FIRMS", "Threat Assessment Engine", "Evacuation Zone Calculator"],
            "report_generated": datetime.now().isoformat(),
            "hotspot_count": hotspot_count,
            "critical_threats": critical_threats,
            "high_threats": high_threats,
            "evacuation_zones": evacuation_zones,
            "affected_population": affected_population
        }
        
        return json.dumps(report, indent=2)
        
    except Exception as e:
        logger.error(f"Error drafting ICS situation report: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "incident_name": incident_name,
            "incident_number": incident_number or "UNKNOWN",
            "status": "error"
        })

@tool
def create_resource_recommendations(
    threat_data: str,
    evacuation_data: str,
    resource_availability: str = None
) -> str:
    """
    Create resource allocation recommendations based on threat assessment.
    
    Args:
        threat_data: JSON string containing threat assessment data
        evacuation_data: JSON string containing evacuation zone data
        resource_availability: JSON string containing available resources (optional)
    
    Returns:
        JSON string containing resource recommendations
    """
    try:
        # Parse input data
        threats = json.loads(threat_data)
        evacuations = json.loads(evacuation_data)
        available_resources = json.loads(resource_availability) if resource_availability else {}
        
        # Initialize report generator
        generator = ICSReportGenerator()
        
        # Analyze threat levels
        critical_threats = threats.get('summary', {}).get('critical_threats', 0)
        high_threats = threats.get('summary', {}).get('high_threats', 0)
        moderate_threats = threats.get('summary', {}).get('moderate_threats', 0)
        evacuation_zones = evacuations.get('summary', {}).get('total_evacuation_zones', 0)
        affected_population = evacuations.get('summary', {}).get('total_affected_population', 0)
        
        # Calculate resource requirements
        recommendations = {
            "timestamp": datetime.now().isoformat(),
            "threat_summary": {
                "critical_threats": critical_threats,
                "high_threats": high_threats,
                "moderate_threats": moderate_threats,
                "evacuation_zones": evacuation_zones,
                "affected_population": affected_population
            },
            "resource_recommendations": {},
            "deployment_priorities": [],
            "estimated_costs": {},
            "timeline": {}
        }
        
        # Aircraft recommendations
        aircraft_needed = max(1, critical_threats) + max(0, high_threats // 2)
        recommendations["resource_recommendations"]["aircraft"] = {
            "helicopters": max(1, critical_threats),
            "air_tankers": max(1, high_threats),
            "lead_planes": max(1, aircraft_needed // 3),
            "rationale": f"Required for immediate response to {critical_threats} critical threats"
        }
        
        # Ground crew recommendations
        ground_crews_needed = max(2, critical_threats + high_threats)
        recommendations["resource_recommendations"]["ground_crews"] = {
            "hotshot_crews": max(1, critical_threats),
            "engine_crews": max(2, high_threats),
            "hand_crews": max(1, moderate_threats),
            "dozer_crews": max(1, evacuation_zones),
            "rationale": f"Required for fireline construction and structure protection"
        }
        
        # Equipment recommendations
        recommendations["resource_recommendations"]["equipment"] = {
            "fire_engines": max(3, critical_threats + high_threats),
            "bulldozers": max(2, evacuation_zones),
            "water_tenders": max(2, affected_population // 1000),
            "communications_units": max(1, evacuation_zones),
            "rationale": "Essential equipment for fire suppression and evacuation support"
        }
        
        # Personnel recommendations
        recommendations["resource_recommendations"]["personnel"] = {
            "incident_commanders": max(1, critical_threats),
            "operations_chiefs": max(1, high_threats),
            "safety_officers": max(1, evacuation_zones),
            "liaison_officers": max(1, affected_population // 5000),
            "rationale": "Command and control personnel for incident management"
        }
        
        # Deployment priorities
        if critical_threats > 0:
            recommendations["deployment_priorities"].append({
                "priority": 1,
                "action": "Immediate deployment of aircraft and ground crews to critical threat areas",
                "timeline": "Within 30 minutes",
                "resources": ["helicopters", "hotshot_crews", "fire_engines"]
            })
        
        if high_threats > 0:
            recommendations["deployment_priorities"].append({
                "priority": 2,
                "action": "Deploy additional resources to high-threat areas",
                "timeline": "Within 1 hour",
                "resources": ["air_tankers", "engine_crews", "bulldozers"]
            })
        
        if evacuation_zones > 0:
            recommendations["deployment_priorities"].append({
                "priority": 3,
                "action": "Establish evacuation support and communications",
                "timeline": "Within 2 hours",
                "resources": ["water_tenders", "communications_units", "liaison_officers"]
            })
        
        # Estimated costs (rough estimates)
        recommendations["estimated_costs"] = {
            "aircraft": aircraft_needed * 5000,  # $5k per aircraft per day
            "ground_crews": ground_crews_needed * 2000,  # $2k per crew per day
            "equipment": (critical_threats + high_threats) * 1000,  # $1k per equipment unit per day
            "personnel": max(1, evacuation_zones) * 1500,  # $1.5k per personnel unit per day
            "total_daily": 0  # Will be calculated
        }
        
        total_daily = sum(recommendations["estimated_costs"].values())
        recommendations["estimated_costs"]["total_daily"] = total_daily
        
        # Timeline
        recommendations["timeline"] = {
            "immediate": "0-30 minutes: Deploy critical resources",
            "short_term": "1-4 hours: Full resource deployment",
            "medium_term": "4-24 hours: Establish incident command and evacuation procedures",
            "long_term": "24+ hours: Monitor and adjust based on fire behavior"
        }
        
        return json.dumps(recommendations, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating resource recommendations: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "resource_recommendations": {}
        })

@tool
def generate_incident_briefing(
    situation_report: str,
    resource_recommendations: str,
    briefing_type: str = "command_staff"
) -> str:
    """
    Generate an incident briefing for command staff based on situation report and resource recommendations.
    
    Args:
        situation_report: JSON string containing ICS situation report
        resource_recommendations: JSON string containing resource recommendations
        briefing_type: Type of briefing ('command_staff', 'public', 'media')
    
    Returns:
        JSON string containing formatted incident briefing
    """
    try:
        # Parse input data
        situation = json.loads(situation_report)
        resources = json.loads(resource_recommendations)
        
        # Initialize report generator
        generator = ICSReportGenerator()
        
        # Create briefing based on type
        if briefing_type == "command_staff":
            briefing = {
                "briefing_type": "Command Staff Briefing",
                "incident_name": situation.get("incident_name", "Unknown"),
                "incident_number": situation.get("incident_number", "Unknown"),
                "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "prepared_by": "Wildfire Nowcast Agent",
                "sections": {
                    "executive_summary": "",
                    "current_threat_assessment": "",
                    "resource_status": "",
                    "evacuation_status": "",
                    "immediate_actions": "",
                    "command_decisions": "",
                    "next_briefing": ""
                }
            }
            
            # Executive Summary
            metadata = situation.get("metadata", {})
            briefing["sections"]["executive_summary"] = f"""
            INCIDENT: {situation.get('incident_name', 'Unknown')}
            INCIDENT NUMBER: {situation.get('incident_number', 'Unknown')}
            DATE/TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            SUMMARY: {metadata.get('hotspot_count', 0)} active wildfire hotspots detected. 
            {metadata.get('critical_threats', 0)} critical threats and {metadata.get('high_threats', 0)} 
            high-level threats identified. {metadata.get('evacuation_zones', 0)} evacuation zones 
            affecting {metadata.get('affected_population', 0)} people.
            """
            
            # Current Threat Assessment
            threat_summary = resources.get("threat_summary", {})
            briefing["sections"]["current_threat_assessment"] = f"""
            THREAT LEVELS:
            - Critical Threats: {threat_summary.get('critical_threats', 0)}
            - High Threats: {threat_summary.get('high_threats', 0)}
            - Moderate Threats: {threat_summary.get('moderate_threats', 0)}
            - Evacuation Zones: {threat_summary.get('evacuation_zones', 0)}
            - Affected Population: {threat_summary.get('affected_population', 0)}
            
            IMMEDIATE CONCERNS:
            - Life safety in critical threat areas
            - Resource allocation challenges
            - Evacuation coordination requirements
            """
            
            # Resource Status
            resource_recs = resources.get("resource_recommendations", {})
            briefing["sections"]["resource_status"] = f"""
            RESOURCE REQUIREMENTS:
            - Aircraft: {resource_recs.get('aircraft', {}).get('helicopters', 0)} helicopters, 
              {resource_recs.get('aircraft', {}).get('air_tankers', 0)} air tankers
            - Ground Crews: {resource_recs.get('ground_crews', {}).get('hotshot_crews', 0)} hotshot crews, 
              {resource_recs.get('ground_crews', {}).get('engine_crews', 0)} engine crews
            - Equipment: {resource_recs.get('equipment', {}).get('fire_engines', 0)} fire engines, 
              {resource_recs.get('equipment', {}).get('bulldozers', 0)} bulldozers
            
            ESTIMATED DAILY COST: ${resources.get('estimated_costs', {}).get('total_daily', 0):,.2f}
            """
            
            # Evacuation Status
            briefing["sections"]["evacuation_status"] = situation.get("sections", {}).get("evacuations", "No evacuation information available.")
            
            # Immediate Actions
            deployment_priorities = resources.get("deployment_priorities", [])
            briefing["sections"]["immediate_actions"] = "IMMEDIATE ACTIONS REQUIRED:\n"
            for priority in deployment_priorities[:3]:  # Top 3 priorities
                briefing["sections"]["immediate_actions"] += f"""
                {priority.get('priority', 0)}. {priority.get('action', 'Unknown action')}
                   Timeline: {priority.get('timeline', 'Unknown')}
                   Resources: {', '.join(priority.get('resources', []))}
                """
            
            # Command Decisions
            briefing["sections"]["command_decisions"] = """
            COMMAND DECISIONS REQUIRED:
            1. Approve resource deployment recommendations
            2. Authorize evacuation orders for affected areas
            3. Establish incident command post location
            4. Coordinate with local emergency services
            5. Implement public information procedures
            """
            
            # Next Briefing
            briefing["sections"]["next_briefing"] = f"""
            NEXT BRIEFING: {datetime.now() + timedelta(hours=4):%Y-%m-%d %H:%M:%S}
            BRIEFING TYPE: Situation Update
            LOCATION: Incident Command Post
            """
            
        elif briefing_type == "public":
            # Public briefing format
            briefing = {
                "briefing_type": "Public Information Briefing",
                "incident_name": situation.get("incident_name", "Wildfire Incident"),
                "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sections": {
                    "situation_overview": "",
                    "safety_information": "",
                    "evacuation_information": "",
                    "contact_information": ""
                }
            }
            
            # Situation Overview
            briefing["sections"]["situation_overview"] = f"""
            A wildfire incident is currently active in the area. {metadata.get('hotspot_count', 0)} 
            fire hotspots have been detected through satellite monitoring. Emergency services 
            are responding to the situation.
            """
            
            # Safety Information
            briefing["sections"]["safety_information"] = """
            SAFETY INFORMATION:
            - Stay informed through official channels
            - Prepare for potential evacuation
            - Have emergency supplies ready
            - Follow instructions from emergency personnel
            - Avoid the fire area
            """
            
            # Evacuation Information
            if metadata.get('evacuation_zones', 0) > 0:
                briefing["sections"]["evacuation_information"] = f"""
                EVACUATION INFORMATION:
                - {metadata.get('evacuation_zones', 0)} evacuation zones have been established
                - Approximately {metadata.get('affected_population', 0)} people are affected
                - Follow evacuation orders immediately
                - Use designated evacuation routes
                """
            else:
                briefing["sections"]["evacuation_information"] = """
                EVACUATION INFORMATION:
                - No evacuation orders currently in effect
                - Monitor official channels for updates
                - Prepare for potential evacuation
                """
            
            # Contact Information
            briefing["sections"]["contact_information"] = """
            CONTACT INFORMATION:
            - Emergency: 911
            - Incident Information: [Local emergency number]
            - Evacuation Center: [Local evacuation center]
            - Updates: [Local emergency management website]
            """
            
        else:  # Media briefing
            briefing = {
                "briefing_type": "Media Briefing",
                "incident_name": situation.get("incident_name", "Wildfire Incident"),
                "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sections": {
                    "incident_summary": "",
                    "response_efforts": "",
                    "public_safety": "",
                    "media_contacts": ""
                }
            }
            
            # Incident Summary
            briefing["sections"]["incident_summary"] = f"""
            INCIDENT SUMMARY:
            - Incident Name: {situation.get('incident_name', 'Unknown')}
            - Incident Number: {situation.get('incident_number', 'Unknown')}
            - Active Hotspots: {metadata.get('hotspot_count', 0)}
            - Critical Threats: {metadata.get('critical_threats', 0)}
            - Evacuation Zones: {metadata.get('evacuation_zones', 0)}
            - Affected Population: {metadata.get('affected_population', 0)}
            """
            
            # Response Efforts
            briefing["sections"]["response_efforts"] = """
            RESPONSE EFFORTS:
            - Emergency services are actively responding
            - Resources are being deployed to affected areas
            - Incident command has been established
            - Coordination with local agencies is ongoing
            """
            
            # Public Safety
            briefing["sections"]["public_safety"] = """
            PUBLIC SAFETY:
            - Follow official evacuation orders
            - Stay informed through official channels
            - Avoid the fire area
            - Have emergency supplies ready
            """
            
            # Media Contacts
            briefing["sections"]["media_contacts"] = """
            MEDIA CONTACTS:
            - Public Information Officer: [PIO Contact]
            - Media Inquiries: [Media Contact]
            - Updates: [Official website/social media]
            """
        
        # Add metadata
        briefing["metadata"] = {
            "briefing_generated": datetime.now().isoformat(),
            "data_sources": ["ICS Situation Report", "Resource Recommendations"],
            "briefing_type": briefing_type,
            "incident_name": situation.get("incident_name", "Unknown"),
            "incident_number": situation.get("incident_number", "Unknown")
        }
        
        return json.dumps(briefing, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating incident briefing: {e}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "briefing_type": briefing_type,
            "status": "error"
        })
