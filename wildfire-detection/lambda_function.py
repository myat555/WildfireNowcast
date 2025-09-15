"""
AWS Lambda function for Wildfire Detection MCP Tools
Implements NASA FIRMS data integration and threat assessment
"""
import json
import os
import datetime
import uuid
import logging
import boto3
import requests
import math
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Helper function to convert datetime to ISO format string
def datetime_to_iso(dt):
    if isinstance(dt, datetime.datetime):
        return dt.isoformat()
    return dt

# Helper function to handle decimal serialization for DynamoDB
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def json_dumps(obj):
    return json.dumps(obj, cls=DecimalEncoder)

# Initialize DynamoDB resource
def get_dynamodb_resource():
    """Get DynamoDB resource based on environment"""
    aws_region = os.getenv('AWS_REGION', 'us-west-2')
    return boto3.resource('dynamodb', region_name=aws_region)

# Define table names
INCIDENTS_TABLE = 'WildfireIncidents'
HOTSPOTS_TABLE = 'FireHotspots'
PROTECTED_AREAS_TABLE = 'ProtectedAreas'
ALERTS_TABLE = 'FireAlerts'

# NASA API configuration
FIRMS_API_URL = os.getenv('FIRMS_API_URL', 'https://firms.modaps.eosdis.nasa.gov/api/')
NASA_API_KEY = os.getenv('NASA_API_KEY', '')
GIBS_API_URL = os.getenv('GIBS_API_URL', 'https://gibs.earthdata.nasa.gov/wmts/')

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371
    return c * r

def point_in_polygon(lat: float, lon: float, polygon: List[List[float]]) -> bool:
    """
    Check if a point is inside a polygon using ray casting algorithm
    """
    x, y = lon, lat
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

# NASA FIRMS API functions
def fetch_firms_hotspots(source: str = 'VIIRS', days: int = 1, area: Optional[Dict] = None) -> List[Dict]:
    """
    Fetch hotspots from NASA FIRMS API
    
    Args:
        source: Data source (VIIRS or MODIS)
        days: Number of days to look back
        area: Optional area filter {'lat': float, 'lon': float, 'radius_km': float}
    
    Returns:
        List of hotspot data
    """
    try:
        # Build API URL
        if area:
            # Area-based query
            url = f"{FIRMS_API_URL}area/csv/{NASA_API_KEY}/{source}/{area['lat']},{area['lon']},{area['radius_km']}/{days}"
        else:
            # Global query (limited to avoid large responses)
            url = f"{FIRMS_API_URL}country/csv/{NASA_API_KEY}/{source}/USA/{days}"
        
        logger.info(f"Fetching FIRMS data from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse CSV data
        lines = response.text.strip().split('\n')
        if len(lines) < 2:
            return []
        
        headers = lines[0].split(',')
        hotspots = []
        
        for line in lines[1:]:
            values = line.split(',')
            if len(values) >= len(headers):
                hotspot = dict(zip(headers, values))
                
                # Convert numeric fields
                try:
                    hotspot['latitude'] = float(hotspot['latitude'])
                    hotspot['longitude'] = float(hotspot['longitude'])
                    hotspot['confidence'] = int(hotspot['confidence']) if hotspot['confidence'].isdigit() else 0
                    hotspot['bright_ti4'] = float(hotspot['bright_ti4']) if hotspot['bright_ti4'] != '' else 0.0
                    hotspot['bright_ti5'] = float(hotspot['bright_ti5']) if hotspot['bright_ti5'] != '' else 0.0
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error parsing hotspot data: {e}")
                    continue
                
                hotspots.append(hotspot)
        
        logger.info(f"Retrieved {len(hotspots)} hotspots from FIRMS")
        return hotspots
    
    except Exception as e:
        logger.error(f"Error fetching FIRMS data: {str(e)}")
        return []

def store_hotspots(hotspots: List[Dict]) -> int:
    """
    Store hotspots in DynamoDB
    
    Returns:
        Number of hotspots stored
    """
    if not hotspots:
        return 0
    
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(HOTSPOTS_TABLE)
        
        stored_count = 0
        for hotspot in hotspots:
            # Generate unique ID
            hotspot_id = f"{hotspot['latitude']}_{hotspot['longitude']}_{hotspot['acq_date']}_{hotspot['acq_time']}"
            
            item = {
                'hotspot_id': hotspot_id,
                'latitude': Decimal(str(hotspot['latitude'])),
                'longitude': Decimal(str(hotspot['longitude'])),
                'confidence': hotspot['confidence'],
                'bright_ti4': Decimal(str(hotspot['bright_ti4'])),
                'bright_ti5': Decimal(str(hotspot['bright_ti5'])),
                'acq_date': hotspot['acq_date'],
                'acq_time': hotspot['acq_time'],
                'satellite': hotspot['satellite'],
                'instrument': hotspot['instrument'],
                'version': hotspot['version'],
                'track': Decimal(str(hotspot.get('track', 0))),
                'scan': Decimal(str(hotspot.get('scan', 0))),
                'created_at': datetime_to_iso(datetime.datetime.utcnow())
            }
            
            # Use put_item with condition to avoid duplicates
            try:
                table.put_item(
                    Item=item,
                    ConditionExpression='attribute_not_exists(hotspot_id)'
                )
                stored_count += 1
            except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
                # Hotspot already exists, skip
                pass
        
        logger.info(f"Stored {stored_count} new hotspots")
        return stored_count
    
    except Exception as e:
        logger.error(f"Error storing hotspots: {str(e)}")
        return 0

def get_protected_areas() -> List[Dict]:
    """
    Get all protected areas from DynamoDB
    """
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(PROTECTED_AREAS_TABLE)
        
        response = table.scan()
        return response.get('Items', [])
    
    except Exception as e:
        logger.error(f"Error retrieving protected areas: {str(e)}")
        return []

def assess_threat_level(hotspot: Dict, protected_areas: List[Dict]) -> Dict:
    """
    Assess threat level of a hotspot against protected areas
    
    Returns:
        Threat assessment with level, distance, and affected areas
    """
    threat_assessment = {
        'threat_level': 'LOW',
        'min_distance_km': float('inf'),
        'affected_areas': [],
        'confidence_factor': hotspot.get('confidence', 0) / 100.0
    }
    
    hotspot_lat = float(hotspot['latitude'])
    hotspot_lon = float(hotspot['longitude'])
    
    for area in protected_areas:
        # Check if hotspot is within area polygon
        if 'polygon' in area:
            polygon_coords = area['polygon']
            if point_in_polygon(hotspot_lat, hotspot_lon, polygon_coords):
                threat_assessment['affected_areas'].append({
                    'area_id': area['area_id'],
                    'name': area['name'],
                    'distance_km': 0,
                    'priority': area.get('priority', 'MEDIUM')
                })
                threat_assessment['min_distance_km'] = 0
                threat_assessment['threat_level'] = 'CRITICAL'
                continue
        
        # Calculate distance to area center
        area_lat = float(area.get('center_lat', 0))
        area_lon = float(area.get('center_lon', 0))
        distance = haversine_distance(hotspot_lat, hotspot_lon, area_lat, area_lon)
        
        if distance < threat_assessment['min_distance_km']:
            threat_assessment['min_distance_km'] = distance
        
        # Determine threat level based on distance and area priority
        area_priority = area.get('priority', 'MEDIUM')
        threat_radius = area.get('threat_radius_km', 10)
        
        if distance <= threat_radius:
            threat_assessment['affected_areas'].append({
                'area_id': area['area_id'],
                'name': area['name'],
                'distance_km': distance,
                'priority': area_priority
            })
            
            # Update threat level
            if area_priority == 'HIGH' and distance <= 5:
                threat_assessment['threat_level'] = 'CRITICAL'
            elif area_priority == 'HIGH' and distance <= threat_radius:
                if threat_assessment['threat_level'] not in ['CRITICAL']:
                    threat_assessment['threat_level'] = 'HIGH'
            elif distance <= threat_radius:
                if threat_assessment['threat_level'] not in ['CRITICAL', 'HIGH']:
                    threat_assessment['threat_level'] = 'MEDIUM'
    
    # Adjust threat level based on confidence
    if threat_assessment['confidence_factor'] < 0.3:
        if threat_assessment['threat_level'] == 'CRITICAL':
            threat_assessment['threat_level'] = 'HIGH'
        elif threat_assessment['threat_level'] == 'HIGH':
            threat_assessment['threat_level'] = 'MEDIUM'
    
    return threat_assessment

def generate_ics_update(incident_id: str, hotspots: List[Dict], threat_assessments: List[Dict]) -> str:
    """
    Generate ICS-213 style update for fire incident
    """
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    # Count hotspots by threat level
    threat_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for assessment in threat_assessments:
        threat_counts[assessment['threat_level']] += 1
    
    # Generate report
    report = f"""ICS-213 GENERAL MESSAGE
    
INCIDENT: {incident_id}
DATE/TIME: {timestamp}
FROM: Wildfire Detection System
TO: Incident Commander

SUBJECT: Automated Fire Detection Update

MESSAGE:
Current satellite detection summary:
- Total active hotspots: {len(hotspots)}
- Critical threats: {threat_counts['CRITICAL']}
- High threats: {threat_counts['HIGH']}
- Medium threats: {threat_counts['MEDIUM']}
- Low threats: {threat_counts['LOW']}

CRITICAL AREAS AFFECTED:
"""
    
    critical_areas = set()
    for assessment in threat_assessments:
        if assessment['threat_level'] == 'CRITICAL':
            for area in assessment['affected_areas']:
                critical_areas.add(area['name'])
    
    if critical_areas:
        for area in sorted(critical_areas):
            report += f"- {area}\n"
    else:
        report += "- None\n"
    
    report += f"""
RECOMMENDED ACTIONS:
- Verify critical detections through ground reconnaissance
- Consider pre-positioning resources near high-threat areas
- Monitor weather conditions for fire behavior changes
- Update evacuation plans for affected communities

NEXT UPDATE: {(datetime.datetime.utcnow() + datetime.timedelta(hours=2)).strftime("%H:%M UTC")}

Generated by: AWS Wildfire Detection Agent
Confidence: Based on NASA VIIRS/MODIS satellite data
"""
    
    return report

# MCP Tool implementations
def tool_fetch_firms_hotspots(source: str = 'VIIRS', days: int = 1, area: Optional[Dict] = None):
    """
    Fetch latest wildfire hotspots from NASA FIRMS
    
    Args:
        source: Data source (VIIRS or MODIS)
        days: Number of days to look back
        area: Optional area filter with lat, lon, radius_km
    
    Returns:
        Hotspot data with threat assessments
    """
    try:
        # Fetch hotspots from NASA FIRMS
        hotspots = fetch_firms_hotspots(source, days, area)
        
        if not hotspots:
            return {"message": "No active hotspots found", "hotspots": []}
        
        # Store hotspots in database
        stored_count = store_hotspots(hotspots)
        
        # Get protected areas for threat assessment
        protected_areas = get_protected_areas()
        
        # Assess threats for each hotspot
        assessed_hotspots = []
        for hotspot in hotspots:
            threat_assessment = assess_threat_level(hotspot, protected_areas)
            hotspot['threat_assessment'] = threat_assessment
            assessed_hotspots.append(hotspot)
        
        return {
            "total_hotspots": len(hotspots),
            "new_hotspots_stored": stored_count,
            "hotspots": assessed_hotspots,
            "source": source,
            "days_back": days
        }
    
    except Exception as e:
        logger.error(f"Error in fetch_firms_hotspots: {str(e)}")
        return {"error": str(e)}

def tool_assess_threat_level(latitude: float, longitude: float, confidence: int = 50):
    """
    Assess threat level for a specific location
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        confidence: Confidence level (0-100)
    
    Returns:
        Threat assessment for the location
    """
    try:
        # Create mock hotspot for assessment
        hotspot = {
            'latitude': latitude,
            'longitude': longitude,
            'confidence': confidence
        }
        
        # Get protected areas
        protected_areas = get_protected_areas()
        
        # Assess threat
        threat_assessment = assess_threat_level(hotspot, protected_areas)
        
        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "threat_assessment": threat_assessment
        }
    
    except Exception as e:
        logger.error(f"Error in assess_threat_level: {str(e)}")
        return {"error": str(e)}

def tool_generate_fire_map(center_lat: float, center_lon: float, zoom: int = 8, include_hotspots: bool = True):
    """
    Generate fire map URL with NASA GIBS tiles
    
    Args:
        center_lat: Center latitude for map
        center_lon: Center longitude for map  
        zoom: Zoom level (1-16)
        include_hotspots: Include fire hotspot overlay
    
    Returns:
        Map configuration and URLs
    """
    try:
        # Generate GIBS WMTS URLs
        base_map_url = f"{GIBS_API_URL}1.0.0/MODIS_Terra_CorrectedReflectance_TrueColor/default/{{time}}/GoogleMapsCompatible_Level9/{{z}}/{{x}}/{{y}}.jpg"
        
        fire_overlay_url = None
        if include_hotspots:
            fire_overlay_url = f"{GIBS_API_URL}1.0.0/MODIS_Fires_All/default/{{time}}/GoogleMapsCompatible_Level9/{{z}}/{{x}}/{{y}}.png"
        
        # Get recent hotspots for the area
        area_filter = {
            'lat': center_lat,
            'lon': center_lon,
            'radius_km': 100  # 100km radius for map context
        }
        
        recent_hotspots = fetch_firms_hotspots('VIIRS', 1, area_filter)
        
        map_config = {
            "center": {"latitude": center_lat, "longitude": center_lon},
            "zoom": zoom,
            "base_map_url": base_map_url,
            "fire_overlay_url": fire_overlay_url,
            "hotspots": recent_hotspots[:50],  # Limit for performance
            "legend": {
                "red": "High confidence fire detection",
                "orange": "Medium confidence fire detection", 
                "yellow": "Low confidence fire detection"
            }
        }
        
        return map_config
    
    except Exception as e:
        logger.error(f"Error in generate_fire_map: {str(e)}")
        return {"error": str(e)}

def tool_draft_ics_update(incident_id: str = None):
    """
    Draft ICS-213 update for current fire situation
    
    Args:
        incident_id: Optional incident identifier
    
    Returns:
        ICS-213 formatted update
    """
    try:
        if not incident_id:
            incident_id = f"WF-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M')}"
        
        # Get recent hotspots
        recent_hotspots = fetch_firms_hotspots('VIIRS', 1)
        
        # Get protected areas
        protected_areas = get_protected_areas()
        
        # Assess threats
        threat_assessments = []
        for hotspot in recent_hotspots:
            assessment = assess_threat_level(hotspot, protected_areas)
            threat_assessments.append(assessment)
        
        # Generate ICS update
        ics_update = generate_ics_update(incident_id, recent_hotspots, threat_assessments)
        
        return {
            "incident_id": incident_id,
            "ics_update": ics_update,
            "hotspot_count": len(recent_hotspots),
            "generated_at": datetime_to_iso(datetime.datetime.utcnow())
        }
    
    except Exception as e:
        logger.error(f"Error in draft_ics_update: {str(e)}")
        return {"error": str(e)}

def tool_check_aoi_intersections(hotspots_data: List[Dict] = None):
    """
    Check hotspot intersections with Areas of Interest
    
    Args:
        hotspots_data: Optional list of hotspots, if not provided fetches recent data
    
    Returns:
        Intersection analysis results
    """
    try:
        if not hotspots_data:
            hotspots_data = fetch_firms_hotspots('VIIRS', 1)
        
        protected_areas = get_protected_areas()
        
        intersections = []
        for hotspot in hotspots_data:
            for area in protected_areas:
                hotspot_lat = float(hotspot['latitude'])
                hotspot_lon = float(hotspot['longitude'])
                
                # Check polygon intersection
                if 'polygon' in area:
                    if point_in_polygon(hotspot_lat, hotspot_lon, area['polygon']):
                        intersections.append({
                            'hotspot': {
                                'latitude': hotspot_lat,
                                'longitude': hotspot_lon,
                                'confidence': hotspot.get('confidence', 0)
                            },
                            'area': {
                                'id': area['area_id'],
                                'name': area['name'],
                                'priority': area.get('priority', 'MEDIUM')
                            },
                            'intersection_type': 'DIRECT'
                        })
                
                # Check distance-based threat
                area_lat = float(area.get('center_lat', 0))
                area_lon = float(area.get('center_lon', 0))
                distance = haversine_distance(hotspot_lat, hotspot_lon, area_lat, area_lon)
                threat_radius = area.get('threat_radius_km', 10)
                
                if distance <= threat_radius:
                    intersections.append({
                        'hotspot': {
                            'latitude': hotspot_lat,
                            'longitude': hotspot_lon,
                            'confidence': hotspot.get('confidence', 0)
                        },
                        'area': {
                            'id': area['area_id'],
                            'name': area['name'],
                            'priority': area.get('priority', 'MEDIUM')
                        },
                        'intersection_type': 'PROXIMITY',
                        'distance_km': distance
                    })
        
        return {
            "total_intersections": len(intersections),
            "intersections": intersections,
            "analysis_timestamp": datetime_to_iso(datetime.datetime.utcnow())
        }
    
    except Exception as e:
        logger.error(f"Error in check_aoi_intersections: {str(e)}")
        return {"error": str(e)}

# Lambda handler
def lambda_handler(event, context):
    """
    AWS Lambda handler function for wildfire detection tools
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        tool_name = event['action_name']
        result = None
        
        if tool_name == 'fetch_firms_hotspots':
            source = event.get('source', 'VIIRS')
            days = event.get('days', 1)
            area = event.get('area')
            result = tool_fetch_firms_hotspots(source, days, area)
        
        elif tool_name == 'assess_threat_level':
            latitude = event['latitude']
            longitude = event['longitude']
            confidence = event.get('confidence', 50)
            result = tool_assess_threat_level(latitude, longitude, confidence)
        
        elif tool_name == 'generate_fire_map':
            center_lat = event['center_lat']
            center_lon = event['center_lon']
            zoom = event.get('zoom', 8)
            include_hotspots = event.get('include_hotspots', True)
            result = tool_generate_fire_map(center_lat, center_lon, zoom, include_hotspots)
        
        elif tool_name == 'draft_ics_update':
            incident_id = event.get('incident_id')
            result = tool_draft_ics_update(incident_id)
        
        elif tool_name == 'check_aoi_intersections':
            hotspots_data = event.get('hotspots_data')
            result = tool_check_aoi_intersections(hotspots_data)
        
        else:
            available_tools = [
                'fetch_firms_hotspots',
                'assess_threat_level', 
                'generate_fire_map',
                'draft_ics_update',
                'check_aoi_intersections'
            ]
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f"Unknown tool: {tool_name}",
                    'available_tools': available_tools
                })
            }
        
        return {
            'statusCode': 200,
            'body': json_dumps(result)
        }
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Internal server error: {str(e)}"
            })
        }
