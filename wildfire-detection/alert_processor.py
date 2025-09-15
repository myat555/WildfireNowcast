"""
Alert Processor for Wildfire Detection System
Processes hotspot data and determines when to send alerts
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import boto3
from decimal import Decimal
from notification_system import NotificationSystem

# Configure logging
logger = logging.getLogger(__name__)

class AlertProcessor:
    def __init__(self):
        self.notification_system = NotificationSystem()
        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        self.alerts_table = self.dynamodb.Table('FireAlerts')
        
        # Alert thresholds
        self.CRITICAL_CONFIDENCE_THRESHOLD = 85
        self.HIGH_CONFIDENCE_THRESHOLD = 70
        self.CRITICAL_DISTANCE_THRESHOLD = 5  # km
        self.HIGH_DISTANCE_THRESHOLD = 15     # km
        
        # Alert suppression (to prevent spam)
        self.ALERT_SUPPRESSION_WINDOW = 30  # minutes
    
    def process_hotspot_for_alerts(self, hotspot_data: Dict, threat_assessment: Dict, affected_areas: List[Dict]) -> Dict:
        """
        Process a hotspot and determine if alerts should be sent
        
        Args:
            hotspot_data: Hotspot information from NASA FIRMS
            threat_assessment: Threat assessment results
            affected_areas: List of affected protected areas
            
        Returns:
            Alert processing results
        """
        try:
            # Determine alert level
            alert_level = self._determine_alert_level(hotspot_data, threat_assessment, affected_areas)
            
            if alert_level == 'NONE':
                return {'alert_level': 'NONE', 'message': 'No alert required'}
            
            # Check for recent similar alerts (suppression)
            if self._should_suppress_alert(hotspot_data, alert_level):
                return {
                    'alert_level': alert_level,
                    'suppressed': True,
                    'message': 'Alert suppressed due to recent similar alert'
                }
            
            # Send notifications
            notification_results = None
            if alert_level == 'CRITICAL':
                notification_results = self.notification_system.send_critical_alert(
                    hotspot_data, threat_assessment, affected_areas
                )
            elif alert_level == 'HIGH':
                notification_results = self.notification_system.send_high_priority_alert(
                    hotspot_data, threat_assessment, affected_areas
                )
            
            # Store alert record
            alert_record = self._create_alert_record(
                hotspot_data, threat_assessment, affected_areas, alert_level, notification_results
            )
            
            self._store_alert_record(alert_record)
            
            return {
                'alert_level': alert_level,
                'notification_results': notification_results,
                'alert_id': alert_record['alert_id'],
                'suppressed': False
            }
            
        except Exception as e:
            logger.error(f"Error processing hotspot for alerts: {str(e)}")
            return {'error': str(e)}
    
    def _determine_alert_level(self, hotspot_data: Dict, threat_assessment: Dict, affected_areas: List[Dict]) -> str:
        """
        Determine the appropriate alert level based on multiple factors
        """
        confidence = hotspot_data.get('confidence', 0)
        threat_level = threat_assessment.get('threat_level', 'LOW')
        min_distance = threat_assessment.get('min_distance_km', float('inf'))
        
        # Critical conditions
        critical_conditions = [
            confidence >= self.CRITICAL_CONFIDENCE_THRESHOLD and min_distance <= self.CRITICAL_DISTANCE_THRESHOLD,
            threat_level == 'CRITICAL',
            any(area.get('priority') == 'CRITICAL' and area.get('distance_km', float('inf')) <= self.CRITICAL_DISTANCE_THRESHOLD 
                for area in affected_areas),
            confidence >= 90 and min_distance <= 10  # Very high confidence close to protected areas
        ]
        
        if any(critical_conditions):
            return 'CRITICAL'
        
        # High priority conditions
        high_conditions = [
            confidence >= self.HIGH_CONFIDENCE_THRESHOLD and min_distance <= self.HIGH_DISTANCE_THRESHOLD,
            threat_level == 'HIGH',
            any(area.get('priority') in ['CRITICAL', 'HIGH'] and area.get('distance_km', float('inf')) <= self.HIGH_DISTANCE_THRESHOLD 
                for area in affected_areas),
            confidence >= 80 and min_distance <= 20  # High confidence moderately close
        ]
        
        if any(high_conditions):
            return 'HIGH'
        
        # Medium priority conditions (logged but no immediate alerts)
        medium_conditions = [
            confidence >= 60 and min_distance <= 30,
            threat_level == 'MEDIUM',
            len(affected_areas) > 0  # Any affected areas
        ]
        
        if any(medium_conditions):
            return 'MEDIUM'
        
        return 'NONE'
    
    def _should_suppress_alert(self, hotspot_data: Dict, alert_level: str) -> bool:
        """
        Check if we should suppress this alert due to recent similar alerts
        """
        try:
            lat = hotspot_data.get('latitude')
            lon = hotspot_data.get('longitude')
            
            # Look for recent alerts in the same area
            cutoff_time = datetime.utcnow() - timedelta(minutes=self.ALERT_SUPPRESSION_WINDOW)
            cutoff_time_str = cutoff_time.isoformat()
            
            response = self.alerts_table.query(
                IndexName='AlertLevelIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('alert_level').eq(alert_level),
                FilterExpression=boto3.dynamodb.conditions.Attr('created_date').gte(cutoff_time_str),
                Limit=50
            )
            
            # Check if any recent alerts are within 2km of this location
            for alert in response.get('Items', []):
                alert_lat = float(alert.get('hotspot_location', {}).get('latitude', 0))
                alert_lon = float(alert.get('hotspot_location', {}).get('longitude', 0))
                
                # Simple distance check (approximate)
                lat_diff = abs(lat - alert_lat)
                lon_diff = abs(lon - alert_lon)
                
                # Roughly 2km in degrees (very approximate)
                if lat_diff < 0.02 and lon_diff < 0.02:
                    logger.info(f"Suppressing {alert_level} alert - similar alert sent recently")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking alert suppression: {str(e)}")
            return False  # Don't suppress on error
    
    def _create_alert_record(self, hotspot_data: Dict, threat_assessment: Dict, 
                           affected_areas: List[Dict], alert_level: str, 
                           notification_results: Dict) -> Dict:
        """
        Create an alert record for storage
        """
        alert_id = f"ALERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{hotspot_data.get('latitude', 0):.4f}-{hotspot_data.get('longitude', 0):.4f}"
        
        return {
            'alert_id': alert_id,
            'alert_level': alert_level,
            'created_date': datetime.utcnow().isoformat(),
            'hotspot_location': {
                'latitude': Decimal(str(hotspot_data.get('latitude', 0))),
                'longitude': Decimal(str(hotspot_data.get('longitude', 0)))
            },
            'hotspot_data': {
                'confidence': hotspot_data.get('confidence', 0),
                'acq_date': hotspot_data.get('acq_date', ''),
                'acq_time': hotspot_data.get('acq_time', ''),
                'satellite': hotspot_data.get('satellite', ''),
                'instrument': hotspot_data.get('instrument', '')
            },
            'threat_assessment': {
                'threat_level': threat_assessment.get('threat_level', 'UNKNOWN'),
                'min_distance_km': Decimal(str(threat_assessment.get('min_distance_km', 0))),
                'confidence_factor': Decimal(str(threat_assessment.get('confidence_factor', 0)))
            },
            'affected_areas': [area.get('area_id', '') for area in affected_areas],
            'notification_results': notification_results or {},
            'status': 'SENT' if notification_results and not notification_results.get('error') else 'FAILED',
            'message': self._generate_alert_message(hotspot_data, threat_assessment, affected_areas, alert_level)
        }
    
    def _store_alert_record(self, alert_record: Dict):
        """
        Store alert record in DynamoDB
        """
        try:
            self.alerts_table.put_item(Item=alert_record)
            logger.info(f"Alert record stored: {alert_record['alert_id']}")
        except Exception as e:
            logger.error(f"Error storing alert record: {str(e)}")
    
    def _generate_alert_message(self, hotspot_data: Dict, threat_assessment: Dict, 
                              affected_areas: List[Dict], alert_level: str) -> str:
        """
        Generate a human-readable alert message
        """
        lat = hotspot_data.get('latitude', 'Unknown')
        lon = hotspot_data.get('longitude', 'Unknown')
        confidence = hotspot_data.get('confidence', 'Unknown')
        threat_level = threat_assessment.get('threat_level', 'Unknown')
        
        message = f"{alert_level} wildfire threat detected at {lat}, {lon} with {confidence}% confidence. "
        message += f"Threat level: {threat_level}. "
        
        if affected_areas:
            area_names = [area.get('name', 'Unknown') for area in affected_areas[:3]]
            message += f"Affected areas: {', '.join(area_names)}. "
        
        message += "Immediate verification recommended."
        
        return message
    
    def get_recent_alerts(self, hours: int = 24, alert_level: str = None) -> List[Dict]:
        """
        Get recent alerts from the database
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            cutoff_time_str = cutoff_time.isoformat()
            
            if alert_level:
                response = self.alerts_table.query(
                    IndexName='AlertLevelIndex',
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('alert_level').eq(alert_level),
                    FilterExpression=boto3.dynamodb.conditions.Attr('created_date').gte(cutoff_time_str),
                    ScanIndexForward=False  # Most recent first
                )
            else:
                response = self.alerts_table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr('created_date').gte(cutoff_time_str)
                )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}")
            return []
    
    def get_alert_statistics(self, days: int = 7) -> Dict:
        """
        Get alert statistics for the specified period
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            cutoff_time_str = cutoff_time.isoformat()
            
            response = self.alerts_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('created_date').gte(cutoff_time_str)
            )
            
            alerts = response.get('Items', [])
            
            stats = {
                'total_alerts': len(alerts),
                'critical_alerts': len([a for a in alerts if a.get('alert_level') == 'CRITICAL']),
                'high_alerts': len([a for a in alerts if a.get('alert_level') == 'HIGH']),
                'medium_alerts': len([a for a in alerts if a.get('alert_level') == 'MEDIUM']),
                'successful_notifications': len([a for a in alerts if a.get('status') == 'SENT']),
                'failed_notifications': len([a for a in alerts if a.get('status') == 'FAILED']),
                'period_days': days,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {str(e)}")
            return {'error': str(e)}

def lambda_handler(event, context):
    """
    Lambda handler for processing alerts from DynamoDB streams or scheduled events
    """
    try:
        alert_processor = AlertProcessor()
        results = []
        
        # Process DynamoDB stream records
        for record in event.get('Records', []):
            if record.get('eventSource') == 'aws:dynamodb' and record.get('eventName') in ['INSERT', 'MODIFY']:
                # Extract hotspot data from DynamoDB record
                new_image = record['dynamodb'].get('NewImage', {})
                
                hotspot_data = {
                    'latitude': float(new_image.get('latitude', {}).get('N', 0)),
                    'longitude': float(new_image.get('longitude', {}).get('N', 0)),
                    'confidence': int(new_image.get('confidence', {}).get('N', 0)),
                    'acq_date': new_image.get('acq_date', {}).get('S', ''),
                    'acq_time': new_image.get('acq_time', {}).get('S', ''),
                    'satellite': new_image.get('satellite', {}).get('S', ''),
                    'instrument': new_image.get('instrument', {}).get('S', '')
                }
                
                # Here you would normally call your threat assessment function
                # For this example, we'll use simplified logic
                threat_assessment = {
                    'threat_level': 'HIGH' if hotspot_data['confidence'] >= 80 else 'MEDIUM',
                    'min_distance_km': 10,  # This would come from actual assessment
                    'confidence_factor': hotspot_data['confidence'] / 100.0
                }
                
                affected_areas = []  # This would come from actual AOI intersection check
                
                # Process the alert
                result = alert_processor.process_hotspot_for_alerts(
                    hotspot_data, threat_assessment, affected_areas
                )
                results.append(result)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Alert processing completed',
                'processed_records': len(event.get('Records', [])),
                'results': results
            })
        }
        
    except Exception as e:
        logger.error(f"Error in alert processor Lambda: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

if __name__ == "__main__":
    # Test the alert processor
    alert_processor = AlertProcessor()
    
    # Test with sample data
    test_hotspot = {
        'latitude': 34.0522,
        'longitude': -118.2437,
        'confidence': 90,
        'acq_date': '2024-01-15',
        'acq_time': '1430'
    }
    
    test_threat = {
        'threat_level': 'CRITICAL',
        'min_distance_km': 3.5,
        'confidence_factor': 0.9
    }
    
    test_areas = [
        {
            'area_id': 'test-area-1',
            'name': 'Test Protected Area',
            'priority': 'HIGH',
            'distance_km': 3.5
        }
    ]
    
    result = alert_processor.process_hotspot_for_alerts(test_hotspot, test_threat, test_areas)
    print(f"Test result: {json.dumps(result, indent=2)}")
    
    # Get statistics
    stats = alert_processor.get_alert_statistics()
    print(f"Alert statistics: {json.dumps(stats, indent=2)}")
