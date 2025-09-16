"""
Wildfire Nowcast Agent Tools

This package contains all tools for the wildfire detection and response agent,
including NASA data integration, threat assessment, mapping, and ICS reporting.
"""

from .improved_nasa_tools import (
    fetch_firms_hotspots_enhanced,
    get_gibs_capabilities,
    get_gibs_layer_info,
    fetch_gibs_map_image,
    fetch_eonet_events_enhanced,
    get_eonet_categories,
    get_eonet_sources,
    get_nasa_data_summary_enhanced
)

from .threat_tools import (
    assess_asset_threats,
    rank_fire_threats,
    calculate_evacuation_zones,
    generate_threat_summary
)

from .mapping_tools import (
    generate_fire_map,
    render_evacuation_map,
    create_progression_map,
    generate_threat_visualization
)

from .ics_tools import (
    draft_ics_situation_report,
    create_resource_recommendations,
    generate_incident_briefing
)

from .memory_tools import (
    create_wildfire_memory,
    create_memory_tools
)

__all__ = [
    # NASA Data Tools (Enhanced)
    "fetch_firms_hotspots_enhanced",
    "get_gibs_capabilities",
    "get_gibs_layer_info",
    "fetch_gibs_map_image",
    "fetch_eonet_events_enhanced",
    "get_eonet_categories",
    "get_eonet_sources",
    "get_nasa_data_summary_enhanced",
    
    # Threat Assessment Tools
    "assess_asset_threats",
    "rank_fire_threats",
    "calculate_evacuation_zones",
    "generate_threat_summary",
    
    # Mapping Tools
    "generate_fire_map",
    "render_evacuation_map",
    "create_progression_map",
    "generate_threat_visualization",
    
    # ICS Reporting Tools
    "draft_ics_situation_report",
    "create_resource_recommendations",
    "generate_incident_briefing",
    
    # Memory Tools
    "create_wildfire_memory",
    "create_memory_tools"
]
