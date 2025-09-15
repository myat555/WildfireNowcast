"""
Notification System for Wildfire Detection
Handles email, SMS, and Slack notifications for critical wildfire threats
"""
import os
import json
import logging
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import boto3

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class NotificationSystem:
    def __init__(self):
        self.alert_email = os.getenv('ALERT_EMAIL')
        self.alert_phone = os.getenv('ALERT_PHONE')
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.aws_region = os.getenv('AWS_REGION', 'us-west-2')
        
        # Initialize AWS SNS client for SMS
        self.sns_client = boto3.client('sns', region_name=self.aws_region)
        
        # Initialize SES client for email
        self.ses_client = boto3.client('ses', region_name=self.aws_region)
    
    def send_critical_alert(self, hotspot_data, threat_assessment, affected_areas):
        """
        Send critical wildfire alert through multiple channels
        
        Args:
            hotspot_data: Dictionary containing hotspot information
            threat_assessment: Threat assessment results
            affected_areas: List of affected protected areas
        """
        try:
            alert_message = self._format_alert_message(hotspot_data, threat_assessment, affected_areas)
            
            # Send notifications through all configured channels
            results = {
                'email': False,
                'sms': False,
                'slack': False,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send email alert
            if self.alert_email:
                results['email'] = self._send_email_alert(alert_message, hotspot_data)
            
            # Send SMS alert
            if self.alert_phone:
                results['sms'] = self._send_sms_alert(alert_message, hotspot_data)
            
            # Send Slack alert
            if self.slack_webhook_url:
                results['slack'] = self._send_slack_alert(alert_message, hotspot_data, affected_areas)
            
            # Log notification results
            logger.info(f"Critical alert sent: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error sending critical alert: {str(e)}")
            return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    
    def send_high_priority_alert(self, hotspot_data, threat_assessment, affected_areas):
        """
        Send high priority wildfire alert (less urgent than critical)
        """
        try:
            alert_message = self._format_alert_message(hotspot_data, threat_assessment, affected_areas, priority='HIGH')
            
            results = {
                'email': False,
                'slack': False,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # For high priority, send email and Slack but not SMS
            if self.alert_email:
                results['email'] = self._send_email_alert(alert_message, hotspot_data, priority='HIGH')
            
            if self.slack_webhook_url:
                results['slack'] = self._send_slack_alert(alert_message, hotspot_data, affected_areas, priority='HIGH')
            
            logger.info(f"High priority alert sent: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error sending high priority alert: {str(e)}")
            return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    
    def _format_alert_message(self, hotspot_data, threat_assessment, affected_areas, priority='CRITICAL'):
        """Format alert message for notifications"""
        lat = hotspot_data.get('latitude', 'Unknown')
        lon = hotspot_data.get('longitude', 'Unknown')
        confidence = hotspot_data.get('confidence', 'Unknown')
        
        threat_level = threat_assessment.get('threat_level', 'Unknown')
        min_distance = threat_assessment.get('min_distance_km', 'Unknown')
        
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        message = f"""🔥 {priority} WILDFIRE ALERT 🔥

DETECTION DETAILS:
• Location: {lat}, {lon}
• Confidence: {confidence}%
• Threat Level: {threat_level}
• Distance to Protected Area: {min_distance} km
• Detection Time: {timestamp}

AFFECTED AREAS:"""
        
        if affected_areas:
            for area in affected_areas[:5]:  # Limit to top 5 areas
                area_name = area.get('name', 'Unknown')
                area_priority = area.get('priority', 'Unknown')
                distance = area.get('distance_km', 'Unknown')
                message += f"\n• {area_name} (Priority: {area_priority}, Distance: {distance} km)"
        else:
            message += "\n• No protected areas directly threatened"
        
        message += f"""

RECOMMENDED ACTIONS:
• Verify detection through ground reconnaissance
• Monitor weather conditions for fire behavior changes
• Consider pre-positioning resources near threatened areas
• Update evacuation plans if necessary

DATA SOURCE: NASA FIRMS (VIIRS/MODIS)
SYSTEM: Wildfire Early-Warning & Triage Agent

This is an automated alert from the AWS Wildfire Detection System.
For more information, access the dashboard or contact emergency management."""
        
        return message
    
    def _send_email_alert(self, message, hotspot_data, priority='CRITICAL'):
        """Send email alert using AWS SES"""
        try:
            subject = f"🔥 {priority} WILDFIRE ALERT - {hotspot_data.get('latitude', 'Unknown')}, {hotspot_data.get('longitude', 'Unknown')}"
            
            # Create HTML version of the message
            html_message = message.replace('\n', '<br>').replace('•', '&bull;')
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="background: linear-gradient(135deg, #dc3545, #fd7e14); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="margin: 0;">🔥 Wildfire Detection Alert</h2>
                    <p style="margin: 5px 0 0 0;">Automated alert from AWS Wildfire Early-Warning System</p>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545;">
                    <pre style="font-family: Arial, sans-serif; white-space: pre-wrap;">{html_message}</pre>
                </div>
                <div style="margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 8px;">
                    <p style="margin: 0; font-size: 14px; color: #6c757d;">
                        <strong>Dashboard:</strong> <a href="http://your-dashboard-url.com">Access Wildfire Dashboard</a><br>
                        <strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </p>
                </div>
            </body>
            </html>
            """
            
            response = self.ses_client.send_email(
                Source='wildfire-alerts@your-domain.com',  # Configure with your verified SES domain
                Destination={'ToAddresses': [self.alert_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': message, 'Charset': 'UTF-8'},
                        'Html': {'Data': html_message, 'Charset': 'UTF-8'}
                    }
                }
            )
            
            logger.info(f"Email alert sent successfully: {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}")
            return False
    
    def _send_sms_alert(self, message, hotspot_data):
        """Send SMS alert using AWS SNS"""
        try:
            # Truncate message for SMS (160 character limit)
            sms_message = f"🔥 CRITICAL WILDFIRE ALERT\n"
            sms_message += f"Location: {hotspot_data.get('latitude', 'Unknown')}, {hotspot_data.get('longitude', 'Unknown')}\n"
            sms_message += f"Confidence: {hotspot_data.get('confidence', 'Unknown')}%\n"
            sms_message += f"Time: {datetime.utcnow().strftime('%H:%M UTC')}\n"
            sms_message += "Check dashboard for details."
            
            response = self.sns_client.publish(
                PhoneNumber=self.alert_phone,
                Message=sms_message[:160]  # Ensure SMS limit
            )
            
            logger.info(f"SMS alert sent successfully: {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS alert: {str(e)}")
            return False
    
    def _send_slack_alert(self, message, hotspot_data, affected_areas, priority='CRITICAL'):
        """Send Slack alert using webhook"""
        try:
            # Format Slack message with rich formatting
            color = '#dc3545' if priority == 'CRITICAL' else '#fd7e14'
            
            slack_payload = {
                "username": "Wildfire Alert Bot",
                "icon_emoji": ":fire:",
                "attachments": [
                    {
                        "color": color,
                        "title": f"🔥 {priority} WILDFIRE ALERT",
                        "title_link": "http://your-dashboard-url.com",
                        "fields": [
                            {
                                "title": "Location",
                                "value": f"{hotspot_data.get('latitude', 'Unknown')}, {hotspot_data.get('longitude', 'Unknown')}",
                                "short": True
                            },
                            {
                                "title": "Confidence",
                                "value": f"{hotspot_data.get('confidence', 'Unknown')}%",
                                "short": True
                            },
                            {
                                "title": "Detection Time",
                                "value": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                                "short": True
                            },
                            {
                                "title": "Data Source",
                                "value": "NASA FIRMS (VIIRS/MODIS)",
                                "short": True
                            }
                        ],
                        "footer": "AWS Wildfire Detection System",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            # Add affected areas if any
            if affected_areas:
                areas_text = "\n".join([f"• {area.get('name', 'Unknown')} ({area.get('priority', 'Unknown')} priority)" for area in affected_areas[:3]])
                slack_payload["attachments"][0]["fields"].append({
                    "title": "Affected Protected Areas",
                    "value": areas_text,
                    "short": False
                })
            
            response = requests.post(
                self.slack_webhook_url,
                json=slack_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack alert sent successfully")
                return True
            else:
                logger.error(f"Slack alert failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack alert: {str(e)}")
            return False
    
    def test_notifications(self):
        """Test all notification channels"""
        test_hotspot = {
            'latitude': 34.0522,
            'longitude': -118.2437,
            'confidence': 85,
            'acq_date': datetime.utcnow().strftime('%Y-%m-%d'),
            'acq_time': datetime.utcnow().strftime('%H%M')
        }
        
        test_threat = {
            'threat_level': 'HIGH',
            'min_distance_km': 5.2,
            'confidence_factor': 0.85
        }
        
        test_areas = [
            {
                'name': 'Test Protected Area',
                'priority': 'HIGH',
                'distance_km': 5.2
            }
        ]
        
        logger.info("Testing notification system...")
        results = self.send_high_priority_alert(test_hotspot, test_threat, test_areas)
        logger.info(f"Test results: {results}")
        return results

def create_notification_lambda():
    """
    Create a Lambda function for processing notifications
    This can be triggered by DynamoDB streams or EventBridge
    """
    def lambda_handler(event, context):
        """
        Lambda handler for processing wildfire notifications
        """
        try:
            notification_system = NotificationSystem()
            
            # Process each record in the event
            results = []
            for record in event.get('Records', []):
                # Extract hotspot data from the event
                if 'dynamodb' in record and record['eventName'] in ['INSERT', 'MODIFY']:
                    # DynamoDB stream event
                    new_image = record['dynamodb'].get('NewImage', {})
                    hotspot_data = {
                        'latitude': float(new_image.get('latitude', {}).get('N', 0)),
                        'longitude': float(new_image.get('longitude', {}).get('N', 0)),
                        'confidence': int(new_image.get('confidence', {}).get('N', 0)),
                        'acq_date': new_image.get('acq_date', {}).get('S', ''),
                        'acq_time': new_image.get('acq_time', {}).get('S', '')
                    }
                    
                    # Determine if this requires notification
                    if hotspot_data['confidence'] >= 70:  # High confidence threshold
                        # Here you would call your threat assessment logic
                        # For now, we'll use dummy data
                        threat_assessment = {'threat_level': 'HIGH', 'min_distance_km': 10}
                        affected_areas = []
                        
                        if hotspot_data['confidence'] >= 85:
                            result = notification_system.send_critical_alert(
                                hotspot_data, threat_assessment, affected_areas
                            )
                        else:
                            result = notification_system.send_high_priority_alert(
                                hotspot_data, threat_assessment, affected_areas
                            )
                        
                        results.append(result)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Notifications processed successfully',
                    'results': results
                })
            }
            
        except Exception as e:
            logger.error(f"Error in notification Lambda: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': str(e)
                })
            }
    
    return lambda_handler

if __name__ == "__main__":
    # Test the notification system
    notification_system = NotificationSystem()
    notification_system.test_notifications()
