"""
Generate synthetic data for Wildfire Detection System
Creates sample protected areas and test data for development
"""
import boto3
import json
import logging
from decimal import Decimal
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_dynamodb_resource():
    """Get DynamoDB resource"""
    aws_region = os.getenv('AWS_REGION', 'us-west-2')
    return boto3.resource('dynamodb', region_name=aws_region)

def create_sample_protected_areas():
    """Create sample protected areas (AOI) data"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('ProtectedAreas')
    
    # Sample protected areas with real-world locations
    protected_areas = [
        {
            'area_id': 'yellowstone-np',
            'name': 'Yellowstone National Park',
            'priority': 'HIGH',
            'center_lat': Decimal('44.4280'),
            'center_lon': Decimal('-110.5885'),
            'threat_radius_km': Decimal('15'),
            'polygon': [
                [-111.15, 44.13], [-111.15, 45.02], [-109.83, 45.02], 
                [-109.83, 44.13], [-111.15, 44.13]
            ],
            'description': 'Yellowstone National Park - High priority protected area',
            'contact_email': 'yellowstone-alerts@nps.gov',
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'area_id': 'yosemite-np',
            'name': 'Yosemite National Park',
            'priority': 'HIGH',
            'center_lat': Decimal('37.8651'),
            'center_lon': Decimal('-119.5383'),
            'threat_radius_km': Decimal('12'),
            'polygon': [
                [-120.01, 37.49], [-120.01, 38.18], [-119.20, 38.18],
                [-119.20, 37.49], [-120.01, 37.49]
            ],
            'description': 'Yosemite National Park - High priority protected area',
            'contact_email': 'yosemite-alerts@nps.gov',
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'area_id': 'los-angeles-metro',
            'name': 'Los Angeles Metropolitan Area',
            'priority': 'CRITICAL',
            'center_lat': Decimal('34.0522'),
            'center_lon': Decimal('-118.2437'),
            'threat_radius_km': Decimal('25'),
            'polygon': [
                [-118.67, 33.70], [-118.67, 34.34], [-117.65, 34.34],
                [-117.65, 33.70], [-118.67, 33.70]
            ],
            'description': 'Los Angeles Metropolitan Area - Critical infrastructure',
            'contact_email': 'lafd-wildfire@lacity.org',
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'area_id': 'sequoia-nf',
            'name': 'Sequoia National Forest',
            'priority': 'MEDIUM',
            'center_lat': Decimal('35.7781'),
            'center_lon': Decimal('-118.5551'),
            'threat_radius_km': Decimal('20'),
            'polygon': [
                [-119.25, 35.30], [-119.25, 36.25], [-117.86, 36.25],
                [-117.86, 35.30], [-119.25, 35.30]
            ],
            'description': 'Sequoia National Forest - Medium priority forest area',
            'contact_email': 'sequoia-fire@usfs.gov',
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'area_id': 'san-francisco-bay',
            'name': 'San Francisco Bay Area',
            'priority': 'HIGH',
            'center_lat': Decimal('37.7749'),
            'center_lon': Decimal('-122.4194'),
            'threat_radius_km': Decimal('30'),
            'polygon': [
                [-122.75, 37.35], [-122.75, 38.20], [-121.75, 38.20],
                [-121.75, 37.35], [-122.75, 37.35]
            ],
            'description': 'San Francisco Bay Area - High priority urban area',
            'contact_email': 'bay-area-fire@calfire.ca.gov',
            'created_at': datetime.utcnow().isoformat()
        }
    ]
    
    logger.info("Creating sample protected areas...")
    for area in protected_areas:
        try:
            table.put_item(
                Item=area,
                ConditionExpression='attribute_not_exists(area_id)'
            )
            logger.info(f"Created protected area: {area['name']}")
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            logger.info(f"Protected area already exists: {area['name']}")
        except Exception as e:
            logger.error(f"Error creating protected area {area['name']}: {str(e)}")

def create_sample_incidents():
    """Create sample wildfire incidents"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('WildfireIncidents')
    
    # Sample incidents
    incidents = [
        {
            'incident_id': 'WF-2024-001',
            'name': 'Sample Fire Alpha',
            'status': 'ACTIVE',
            'created_date': (datetime.utcnow() - timedelta(days=2)).isoformat(),
            'location': {
                'latitude': Decimal('34.1234'),
                'longitude': Decimal('-118.3456')
            },
            'size_acres': Decimal('1250'),
            'containment_percent': Decimal('25'),
            'threat_level': 'HIGH',
            'description': 'Sample wildfire incident for testing',
            'resources_assigned': ['Engine 42', 'Hand Crew 15', 'Air Tanker 912'],
            'last_updated': datetime.utcnow().isoformat()
        },
        {
            'incident_id': 'WF-2024-002',
            'name': 'Sample Fire Bravo',
            'status': 'CONTAINED',
            'created_date': (datetime.utcnow() - timedelta(days=5)).isoformat(),
            'location': {
                'latitude': Decimal('37.8765'),
                'longitude': Decimal('-119.4321')
            },
            'size_acres': Decimal('850'),
            'containment_percent': Decimal('100'),
            'threat_level': 'MEDIUM',
            'description': 'Sample contained wildfire incident',
            'resources_assigned': ['Engine 23', 'Hand Crew 8'],
            'last_updated': datetime.utcnow().isoformat()
        }
    ]
    
    logger.info("Creating sample incidents...")
    for incident in incidents:
        try:
            table.put_item(
                Item=incident,
                ConditionExpression='attribute_not_exists(incident_id)'
            )
            logger.info(f"Created incident: {incident['name']}")
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            logger.info(f"Incident already exists: {incident['name']}")
        except Exception as e:
            logger.error(f"Error creating incident {incident['name']}: {str(e)}")

def create_sample_hotspots():
    """Create sample hotspot data"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('FireHotspots')
    
    # Generate sample hotspots around protected areas
    base_locations = [
        (34.0522, -118.2437),  # Los Angeles
        (37.7749, -122.4194),  # San Francisco
        (44.4280, -110.5885),  # Yellowstone
        (37.8651, -119.5383),  # Yosemite
    ]
    
    logger.info("Creating sample hotspots...")
    today = datetime.utcnow()
    
    for i, (base_lat, base_lon) in enumerate(base_locations):
        for j in range(5):  # 5 hotspots per location
            # Add some random variation
            lat_offset = random.uniform(-0.1, 0.1)
            lon_offset = random.uniform(-0.1, 0.1)
            
            hotspot_id = f"{base_lat + lat_offset}_{base_lon + lon_offset}_{today.strftime('%Y%m%d')}_{today.strftime('%H%M')}"
            
            hotspot = {
                'hotspot_id': hotspot_id,
                'latitude': Decimal(str(base_lat + lat_offset)),
                'longitude': Decimal(str(base_lon + lon_offset)),
                'confidence': random.randint(30, 95),
                'bright_ti4': Decimal(str(random.uniform(300.0, 400.0))),
                'bright_ti5': Decimal(str(random.uniform(280.0, 380.0))),
                'acq_date': today.strftime('%Y-%m-%d'),
                'acq_time': today.strftime('%H%M'),
                'satellite': 'N',  # NOAA
                'instrument': 'VIIRS',
                'version': '2.0NRT',
                'track': Decimal(str(random.uniform(1.0, 2.0))),
                'scan': Decimal(str(random.uniform(1.0, 2.0))),
                'created_at': datetime.utcnow().isoformat()
            }
            
            try:
                table.put_item(
                    Item=hotspot,
                    ConditionExpression='attribute_not_exists(hotspot_id)'
                )
                logger.info(f"Created hotspot: {hotspot_id[:50]}...")
            except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
                logger.info(f"Hotspot already exists: {hotspot_id[:50]}...")
            except Exception as e:
                logger.error(f"Error creating hotspot: {str(e)}")

def create_sample_alerts():
    """Create sample alert records"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('FireAlerts')
    
    alerts = [
        {
            'alert_id': f"ALERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-001",
            'alert_level': 'CRITICAL',
            'created_date': datetime.utcnow().isoformat(),
            'hotspot_location': {
                'latitude': Decimal('34.0522'),
                'longitude': Decimal('-118.2437')
            },
            'affected_areas': ['los-angeles-metro'],
            'message': 'Critical wildfire threat detected near Los Angeles metropolitan area',
            'status': 'SENT',
            'recipients': ['lafd-wildfire@lacity.org'],
            'notification_methods': ['email', 'sms']
        },
        {
            'alert_id': f"ALERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-002",
            'alert_level': 'HIGH',
            'created_date': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            'hotspot_location': {
                'latitude': Decimal('37.8651'),
                'longitude': Decimal('-119.5383')
            },
            'affected_areas': ['yosemite-np'],
            'message': 'High confidence fire detection in Yosemite National Park area',
            'status': 'ACKNOWLEDGED',
            'recipients': ['yosemite-alerts@nps.gov'],
            'notification_methods': ['email']
        }
    ]
    
    logger.info("Creating sample alerts...")
    for alert in alerts:
        try:
            table.put_item(
                Item=alert,
                ConditionExpression='attribute_not_exists(alert_id)'
            )
            logger.info(f"Created alert: {alert['alert_id']}")
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            logger.info(f"Alert already exists: {alert['alert_id']}")
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")

def main():
    """Main function to create all sample data"""
    try:
        logger.info("Starting synthetic data generation for Wildfire Detection System...")
        
        # Create sample data
        create_sample_protected_areas()
        create_sample_incidents()
        create_sample_hotspots()
        create_sample_alerts()
        
        logger.info("Synthetic data generation completed successfully!")
        
        # Print summary
        dynamodb = get_dynamodb_resource()
        
        tables_info = [
            ('ProtectedAreas', 'Protected areas (AOI) for threat assessment'),
            ('WildfireIncidents', 'Active and historical wildfire incidents'),
            ('FireHotspots', 'Satellite fire detections from NASA FIRMS'),
            ('FireAlerts', 'Alert notifications and response tracking')
        ]
        
        print("\n" + "="*60)
        print("WILDFIRE DETECTION SYSTEM - SAMPLE DATA SUMMARY")
        print("="*60)
        
        for table_name, description in tables_info:
            try:
                table = dynamodb.Table(table_name)
                response = table.scan(Select='COUNT')
                count = response.get('Count', 0)
                print(f"{table_name:<20}: {count:>3} items - {description}")
            except Exception as e:
                print(f"{table_name:<20}: ERROR - {str(e)}")
        
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("1. Test the Lambda function: python test_lambda.py")
        print("2. Deploy the gateway and agent runtime")
        print("3. Try sample queries:")
        print('   - "Show me active wildfires near Los Angeles"')
        print('   - "What is the threat level for Yellowstone?"')
        print('   - "Generate a fire map for California"')
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error generating synthetic data: {str(e)}")
        raise

if __name__ == "__main__":
    main()
