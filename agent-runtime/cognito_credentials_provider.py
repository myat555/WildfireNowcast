"""
Cognito Credentials Provider for Wildfire Detection Agent
"""
import os
import boto3
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class CognitoCredentialsProvider:
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-west-2')
        self.user_pool_id = os.getenv('COGNITO_USERPOOL_ID')
        self.client_id = os.getenv('COGNITO_CLIENT_ID')
        self.client_secret = os.getenv('COGNITO_CLIENT_SECRET')
        
        if not all([self.user_pool_id, self.client_id, self.client_secret]):
            raise ValueError("Missing required Cognito configuration")
        
        self.cognito_client = boto3.client('cognito-idp', region_name=self.region)
    
    def get_access_token(self):
        """Get access token using client credentials flow"""
        try:
            response = self.cognito_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': 'wildfire-agent',
                    'PASSWORD': 'temp-password',
                    'SECRET_HASH': self._calculate_secret_hash('wildfire-agent')
                }
            )
            
            return response['AuthenticationResult']['AccessToken']
        except Exception as e:
            logger.error(f"Error getting Cognito access token: {str(e)}")
            return None
    
    def _calculate_secret_hash(self, username):
        """Calculate secret hash for Cognito authentication"""
        import hmac
        import hashlib
        import base64
        
        message = bytes(username + self.client_id, 'utf-8')
        key = bytes(self.client_secret, 'utf-8')
        secret_hash = base64.b64encode(hmac.new(key, message, digestmod=hashlib.sha256).digest()).decode()
        
        return secret_hash
