"""
Deployment script for Wildfire Nowcast Agent

This script deploys the wildfire detection and response agent to Amazon Bedrock AgentCore
using the Strands Agent framework.
"""

import argparse
import boto3
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WildfireAgentDeployer:
    """Deployer for the Wildfire Nowcast Agent"""
    
    def __init__(self, agent_name: str, region: str, role_name: str):
        self.agent_name = agent_name
        self.region = region
        self.role_name = role_name
        
        # Initialize AWS clients
        self.bedrock_client = boto3.client('bedrock-agentcore', region_name=region)
        self.bedrock_control_client = boto3.client('bedrock-agentcore-control', region_name=region)
        self.ecr_client = boto3.client('ecr', region_name=region)
        self.codebuild_client = boto3.client('codebuild', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.ssm_client = boto3.client('ssm', region_name=region)
        
        # Project paths
        self.project_root = Path(__file__).parent
        self.dockerfile_path = self.project_root / "Dockerfile"
        self.agent_file = self.project_root / "wildfire_nowcast_agent.py"
        
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        logger.info("Checking prerequisites...")
        
        # Check if .env file exists and has required NASA API keys
        self.check_env_file()
        
        # Check if Docker is running
        try:
            subprocess.run(['docker', '--version'], check=True, capture_output=True)
            logger.info("✅ Docker is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ Docker is not available. Please install and start Docker.")
            sys.exit(1)
        
        # Check if AWS CLI is configured
        try:
            subprocess.run(['aws', 'sts', 'get-caller-identity'], check=True, capture_output=True)
            logger.info("✅ AWS CLI is configured")
        except subprocess.CalledProcessError:
            logger.error("❌ AWS CLI is not configured. Please run 'aws configure'.")
            sys.exit(1)
        
        # Check if required files exist
        if not self.agent_file.exists():
            logger.error(f"❌ Agent file not found: {self.agent_file}")
            sys.exit(1)
        
        logger.info("✅ All prerequisites met")
    
    def check_env_file(self):
        """Check if .env file exists and contains required NASA API keys"""
        env_file = self.project_root / ".env"
        template_file = self.project_root / ".env.template"
        
        if not env_file.exists():
            logger.error("❌ .env file not found!")
            logger.error("📋 Please create a .env file with your NASA API keys:")
            logger.error("   1. Copy .env.template to .env:")
            logger.error("      cp .env.template .env")
            logger.error("   2. Edit .env and add your NASA API keys")
            logger.error("   3. Get free NASA API keys from:")
            logger.error("      - FIRMS: https://firms.modaps.eosdis.nasa.gov/api/")
            logger.error("      - GIBS: https://earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/gibs")
            logger.error("      - EONET: https://eonet.gsfc.nasa.gov/api/v3/")
            sys.exit(1)
        
        # Load environment variables
        load_dotenv(env_file)
        
        # Check for required NASA API keys
        required_keys = {
            'NASA_FIRMS_API_KEY': 'NASA FIRMS API key (required for fire hotspot data)'
        }
        
        # Optional NASA API keys (not required - services are publicly accessible)
        optional_keys = {}
        
        missing_keys = []
        for key, description in required_keys.items():
            value = os.getenv(key)
            if not value or value == f"your_{key.lower()}_here":
                missing_keys.append(f"  - {key}: {description}")
        
        if missing_keys:
            logger.error("❌ Missing or invalid NASA API keys in .env file:")
            for key in missing_keys:
                logger.error(key)
            logger.error("\n📋 Please update your .env file with valid NASA API keys.")
            logger.error("   Get free API keys from:")
            logger.error("   - FIRMS: https://firms.modaps.eosdis.nasa.gov/api/")
            logger.error("   Note: GIBS and EONET are publicly accessible without API keys")
            sys.exit(1)
        
        # GIBS and EONET are publicly accessible - no API keys needed
        
        logger.info("✅ NASA API keys found in .env file")
    
    def create_dockerfile(self):
        """Create Dockerfile for the agent"""
        logger.info("Creating Dockerfile...")
        
        # Load environment variables from .env file
        env_file = self.project_root / ".env"
        load_dotenv(env_file)
        
        # Get NASA API keys from environment (only FIRMS required)
        nasa_firms_key = os.getenv('NASA_FIRMS_API_KEY', '')
        
        dockerfile_content = f"""FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies
RUN yum update -y && \\
    yum install -y gcc gcc-c++ make && \\
    yum clean all

# Copy requirements and install Python dependencies
COPY requirements.txt ${{LAMBDA_TASK_ROOT}}/
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY wildfire_nowcast_agent.py ${{LAMBDA_TASK_ROOT}}/
COPY tools/ ${{LAMBDA_TASK_ROOT}}/tools/

# Set environment variables (NASA API keys will be passed at runtime)
ENV AWS_REGION={self.region}
ENV PYTHONPATH=${{LAMBDA_TASK_ROOT}}

# Set the CMD to your handler
CMD ["wildfire_nowcast_agent.wildfire_nowcast_agent_runtime"]
"""
        
        with open(self.dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        logger.info("✅ Dockerfile created (NASA API keys will be passed at runtime)")
    
    def create_iam_role(self):
        """Create IAM role for the agent"""
        logger.info(f"Creating IAM role: {self.role_name}")
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock-agentcore.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock-agentcore:*",
                        "ecr:*",
                        "xray:*",
                        "logs:*",
                        "s3:*",
                        "ssm:*"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            # Create role
            self.iam_client.create_role(
                RoleName=self.role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"IAM role for {self.agent_name}"
            )
            
            # Attach permissions policy
            self.iam_client.put_role_policy(
                RoleName=self.role_name,
                PolicyName=f"{self.role_name}Policy",
                PolicyDocument=json.dumps(permissions_policy)
            )
            
            logger.info("✅ IAM role created")
            
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            logger.info("✅ IAM role already exists")
        except Exception as e:
            logger.error(f"❌ Error creating IAM role: {e}")
            raise
    
    def create_ecr_repository(self):
        """Create ECR repository for the agent"""
        logger.info(f"Creating ECR repository: {self.agent_name}")
        
        try:
            self.ecr_client.create_repository(
                repositoryName=self.agent_name,
                imageTagMutability='MUTABLE',
                imageScanningConfiguration={
                    'scanOnPush': True
                }
            )
            logger.info("✅ ECR repository created")
        except self.ecr_client.exceptions.RepositoryAlreadyExistsException:
            logger.info("✅ ECR repository already exists")
        except Exception as e:
            logger.error(f"❌ Error creating ECR repository: {e}")
            raise
    
    def build_and_push_image(self):
        """Build and push Docker image to ECR"""
        logger.info("Building and pushing Docker image...")
        
        # Get ECR login token
        login_response = self.ecr_client.get_authorization_token()
        token = login_response['authorizationData'][0]['authorizationToken']
        endpoint = login_response['authorizationData'][0]['proxyEndpoint']
        
        # Login to ECR with better error handling
        try:
            login_result = subprocess.run([
                'docker', 'login', '--username', 'AWS', '--password-stdin', endpoint
            ], input=token, check=True, text=True, capture_output=True)
            logger.info("✅ Docker ECR login successful")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Docker ECR login failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            # Try alternative login method
            logger.info("Trying alternative ECR login method...")
            try:
                subprocess.run([
                    'aws', 'ecr', 'get-login-password', '--region', self.region
                ], check=True, capture_output=True)
                subprocess.run([
                    'docker', 'login', '--username', 'AWS', '--password-stdin', endpoint
                ], input=subprocess.run([
                    'aws', 'ecr', 'get-login-password', '--region', self.region
                ], capture_output=True, text=True).stdout, check=True, text=True)
                logger.info("✅ Alternative ECR login successful")
            except Exception as alt_e:
                logger.error(f"❌ Alternative ECR login also failed: {alt_e}")
                raise
        
        # Build image for ARM64 architecture (required by Bedrock AgentCore)
        image_tag = f"{endpoint.replace('https://', '')}/{self.agent_name}:latest"
        subprocess.run([
            'docker', 'build', '--platform', 'linux/arm64', '-t', image_tag, '.'
        ], cwd=self.project_root, check=True)
        
        # Push image
        subprocess.run(['docker', 'push', image_tag], check=True)
        
        logger.info("✅ Docker image built and pushed")
        return image_tag
    
    def create_agentcore_runtime(self, image_uri: str):
        """Create AgentCore Runtime"""
        logger.info("Creating AgentCore Runtime...")
        
        try:
            response = self.bedrock_control_client.create_agent_runtime(
                agentRuntimeName=f"{self.agent_name.replace('-', '_')}_runtime",
                description=f"Runtime for {self.agent_name}",
                agentRuntimeArtifact={
                    'containerConfiguration': {
                        'containerUri': image_uri
                    }
                },
                roleArn=f"arn:aws:iam::{self._get_account_id()}:role/{self.role_name}",
                networkConfiguration={
                    'networkMode': 'PUBLIC'
                },
                protocolConfiguration={
                    'serverProtocol': 'HTTP'
                },
                environmentVariables={
                    'AWS_REGION': self.region,
                    'NASA_FIRMS_API_KEY': os.getenv('NASA_FIRMS_API_KEY', '')
                }
            )
            
            runtime_id = response['agentRuntimeId']
            logger.info(f"✅ AgentCore Runtime created: {runtime_id}")
            logger.info(f"   Runtime ARN: {response['agentRuntimeArn']}")
            logger.info(f"   Runtime Version: {response['agentRuntimeVersion']}")
            return runtime_id
            
        except Exception as e:
            logger.error(f"❌ Error creating AgentCore Runtime: {e}")
            raise
    
    def _get_account_id(self):
        """Get AWS account ID"""
        sts_client = boto3.client('sts', region_name=self.region)
        return sts_client.get_caller_identity()['Account']
    
    def save_deployment_info(self, runtime_id: str, image_uri: str):
        """Save deployment information to files"""
        deployment_info = {
            'agent_name': self.agent_name,
            'runtime_id': runtime_id,
            'image_uri': image_uri,
            'region': self.region,
            'role_name': self.role_name,
            'deployment_time': datetime.now().isoformat()
        }
        
        # Save to JSON file
        with open('.deployment_info', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        # Save runtime ID to separate file for easy access
        with open('.runtime_id', 'w') as f:
            f.write(runtime_id)
        
        logger.info("✅ Deployment information saved")
    
    def deploy(self):
        """Deploy the wildfire agent"""
        logger.info(f"🚀 Deploying {self.agent_name} to {self.region}")
        
        try:
            # Check prerequisites
            self.check_prerequisites()
            
            # Create Dockerfile
            self.create_dockerfile()
            
            # Create IAM role
            self.create_iam_role()
            
            # Create ECR repository
            self.create_ecr_repository()
            
            # Build and push image
            image_uri = self.build_and_push_image()
            
            # Create AgentCore Runtime
            runtime_id = self.create_agentcore_runtime(image_uri)
            
            # Save deployment info
            self.save_deployment_info(runtime_id, image_uri)
            
            logger.info("🎉 Deployment completed successfully!")
            logger.info(f"Runtime ID: {runtime_id}")
            logger.info(f"Image URI: {image_uri}")
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Deploy Wildfire Nowcast Agent')
    parser.add_argument('--agent-name', default='wildfire-nowcast-agent', 
                       help='Name for the agent (default: wildfire-nowcast-agent)')
    parser.add_argument('--role-name', default='WildfireNowcastAgentRole',
                       help='IAM role name (default: WildfireNowcastAgentRole)')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--skip-checks', action='store_true',
                       help='Skip prerequisite validation')
    
    args = parser.parse_args()
    
    deployer = WildfireAgentDeployer(
        agent_name=args.agent_name,
        region=args.region,
        role_name=args.role_name
    )
    
    if not args.skip_checks:
        deployer.check_prerequisites()
    
    deployer.deploy()

if __name__ == "__main__":
    main()
