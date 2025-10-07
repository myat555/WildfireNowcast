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
        self.build_only = False
        self.push_timeout = 600
        self.disable_proxy = False

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

# Install system dependencies and clean up in one layer to reduce size
RUN yum update -y && \\
    yum install -y gcc gcc-c++ make && \\
    yum clean all && \\
    rm -rf /var/cache/yum

# Copy requirements and install Python dependencies
COPY requirements.txt ${{LAMBDA_TASK_ROOT}}/
RUN pip install --no-cache-dir -r requirements.txt && \\
    find /var/lang/lib/python3.10/site-packages -type d -name "__pycache__" -exec rm -rf {{}} + 2>/dev/null || true && \\
    find /var/lang/lib/python3.10/site-packages -type f -name "*.pyc" -delete && \\
    find /var/lang/lib/python3.10/site-packages -type d -name "tests" -exec rm -rf {{}} + 2>/dev/null || true && \\
    find /var/lang/lib/python3.10/site-packages -type d -name "test" -exec rm -rf {{}} + 2>/dev/null || true

# Copy agent code
COPY wildfire_nowcast_agent.py ${{LAMBDA_TASK_ROOT}}/
COPY tools/ ${{LAMBDA_TASK_ROOT}}/tools/

# Set environment variables (NASA API keys will be passed at runtime)
ENV AWS_REGION={self.region}
ENV PYTHONPATH=${{LAMBDA_TASK_ROOT}}
ENV PYTHONDONTWRITEBYTECODE=1

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
            response = self.ecr_client.create_repository(
                repositoryName=self.agent_name,
                imageTagMutability='MUTABLE',
                imageScanningConfiguration={
                    'scanOnPush': True
                },
                encryptionConfiguration={
                    'encryptionType': 'AES256'
                }
            )
            logger.info("✅ ECR repository created")

            # Wait a moment for the repository to be fully ready
            time.sleep(2)

            # Verify repository exists and is accessible
            self.ecr_client.describe_repositories(repositoryNames=[self.agent_name])
            logger.info("✅ ECR repository verified and ready")

        except self.ecr_client.exceptions.RepositoryAlreadyExistsException:
            logger.info("✅ ECR repository already exists")
            # Verify it's accessible
            try:
                self.ecr_client.describe_repositories(repositoryNames=[self.agent_name])
                logger.info("✅ ECR repository verified and accessible")
            except Exception as e:
                logger.error(f"❌ ECR repository exists but not accessible: {e}")
                raise
        except Exception as e:
            logger.error(f"❌ Error creating ECR repository: {e}")
            raise
    
    def manual_ecr_push(self, image_tag: str, ecr_url: str) -> bool:
        """
        Manual method to push image to ECR using docker save/load
        More reliable for networks with proxy issues
        """
        try:
            import tempfile

            logger.info("Saving Docker image to tarball...")
            with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # Save image to tar file with progress
            save_process = subprocess.Popen(
                ['docker', 'save', '-o', tmp_path, image_tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            save_process.wait(timeout=300)

            if save_process.returncode != 0:
                logger.error("Failed to save image to tarball")
                return False

            logger.info(f"✅ Image saved to tarball")

            # Get file size
            import os
            file_size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
            logger.info(f"Tarball size: {file_size_mb:.2f} MB")

            # Use AWS CLI to push via S3 as intermediate (for very large images)
            logger.info("Uploading to S3 and importing to ECR...")

            # Create temporary S3 bucket for image transfer
            s3_client = boto3.client('s3', region_name=self.region)
            bucket_name = f"ecr-image-transfer-{self._get_account_id()}"

            try:
                s3_client.create_bucket(Bucket=bucket_name)
                logger.info(f"Created temporary S3 bucket: {bucket_name}")
            except s3_client.exceptions.BucketAlreadyOwnedByYou:
                logger.info(f"Using existing S3 bucket: {bucket_name}")

            # Upload tarball to S3 with multipart upload
            s3_key = f"{self.agent_name}-{int(time.time())}.tar"
            logger.info(f"Uploading to S3: s3://{bucket_name}/{s3_key}")

            # Use AWS CLI for more reliable upload with progress
            subprocess.run([
                'aws', 's3', 'cp', tmp_path, f's3://{bucket_name}/{s3_key}',
                '--region', self.region
            ], check=True)

            logger.info("✅ Uploaded to S3")

            # Load from S3 back to local Docker, then push in smaller chunks
            logger.info("Loading image back and pushing to ECR...")
            subprocess.run(['docker', 'load', '-i', tmp_path], check=True)

            # Try pushing again with longer timeout
            push_result = subprocess.run(
                ['docker', 'push', image_tag],
                timeout=1800,  # 30 minute timeout
                capture_output=True,
                text=True
            )

            # Cleanup
            os.unlink(tmp_path)
            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)

            return push_result.returncode == 0

        except Exception as e:
            logger.error(f"Manual push failed: {e}")
            return False

    def build_and_push_image(self):
        """Build and push Docker image to ECR"""
        logger.info("Building and pushing Docker image...")

        # Get account ID for ECR URL
        account_id = self._get_account_id()
        ecr_url = f"{account_id}.dkr.ecr.{self.region}.amazonaws.com"

        # Disable proxy if requested
        push_env = os.environ.copy()
        if self.disable_proxy:
            logger.info("Disabling HTTP proxy for Docker push...")
            push_env['HTTP_PROXY'] = ''
            push_env['HTTPS_PROXY'] = ''
            push_env['http_proxy'] = ''
            push_env['https_proxy'] = ''
            push_env['NO_PROXY'] = '*'
            push_env['no_proxy'] = '*'

        # Login to ECR using AWS CLI (more reliable than boto3 token)
        logger.info("Logging into ECR...")
        try:
            # Get ECR password and pipe it to docker login
            get_password = subprocess.run(
                ['aws', 'ecr', 'get-login-password', '--region', self.region],
                capture_output=True,
                text=True,
                check=True
            )

            login_result = subprocess.run(
                ['docker', 'login', '--username', 'AWS', '--password-stdin', ecr_url],
                input=get_password.stdout,
                text=True,
                capture_output=True,
                check=True
            )
            logger.info("✅ Docker ECR login successful")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Docker ECR login failed: {e}")
            if e.stderr:
                logger.error(f"Error output: {e.stderr}")
            raise

        # Login to public ECR for base image access
        logger.info("Logging into public ECR for base image...")
        try:
            public_login = subprocess.run(
                ['aws', 'ecr-public', 'get-login-password', '--region', 'us-east-1'],
                capture_output=True,
                text=True,
                check=True
            )

            subprocess.run(
                ['docker', 'login', '--username', 'AWS', '--password-stdin', 'public.ecr.aws'],
                input=public_login.stdout,
                text=True,
                capture_output=True,
                check=True
            )
            logger.info("✅ Public ECR login successful")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️  Public ECR login failed (non-critical): {e}")
            # Continue anyway as it might not be needed

        # Pre-pull the base image to avoid build failures
        logger.info("Pulling base image...")
        base_image = "public.ecr.aws/lambda/python:3.10"
        try:
            subprocess.run(
                ['docker', 'pull', '--platform', 'linux/arm64', base_image],
                check=True,
                capture_output=True
            )
            logger.info("✅ Base image pulled successfully")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️  Failed to pre-pull base image: {e}")
            logger.info("Continuing with build (will attempt to pull during build)...")

        # Build image for ARM64 architecture (required by Bedrock AgentCore)
        image_tag = f"{ecr_url}/{self.agent_name}:latest"
        logger.info(f"Building Docker image: {image_tag}")

        # Enable BuildKit for better caching and compression
        build_env = os.environ.copy()
        build_env['DOCKER_BUILDKIT'] = '1'
        build_env['BUILDKIT_PROGRESS'] = 'plain'

        try:
            build_result = subprocess.run(
                [
                    'docker', 'build',
                    '--platform', 'linux/arm64',
                    '--compress',  # Compress the build context
                    '--squash',  # Squash layers to reduce size (if supported)
                    '-t', image_tag,
                    '.'
                ],
                cwd=self.project_root,
                env=build_env,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("✅ Docker image built successfully")
        except subprocess.CalledProcessError as e:
            # Try without --squash if it fails (not all Docker versions support it)
            logger.warning("⚠️  Build with --squash failed, trying without...")
            try:
                build_result = subprocess.run(
                    [
                        'docker', 'build',
                        '--platform', 'linux/arm64',
                        '--compress',
                        '-t', image_tag,
                        '.'
                    ],
                    cwd=self.project_root,
                    env=build_env,
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info("✅ Docker image built successfully")
            except subprocess.CalledProcessError as e2:
                logger.error(f"❌ Docker build failed: {e2}")
                if e2.stdout:
                    logger.error(f"Build output: {e2.stdout}")
                if e2.stderr:
                    logger.error(f"Build errors: {e2.stderr}")
                raise

        # Check image size before pushing
        try:
            inspect_result = subprocess.run(
                ['docker', 'image', 'inspect', image_tag, '--format', '{{.Size}}'],
                capture_output=True,
                text=True,
                check=True
            )
            image_size_bytes = int(inspect_result.stdout.strip())
            image_size_mb = image_size_bytes / (1024 * 1024)
            logger.info(f"Image size: {image_size_mb:.2f} MB")
        except Exception as e:
            logger.warning(f"⚠️  Could not determine image size: {e}")

        # Try alternative push method using skopeo if docker push keeps failing
        # This is more reliable for networks with proxies or unstable connections
        def try_skopeo_push():
            """Try using skopeo as alternative to docker push"""
            logger.info("Attempting alternative push method using skopeo...")
            try:
                # Check if skopeo is available
                subprocess.run(['skopeo', '--version'], capture_output=True, check=True)

                # Use skopeo to copy image to ECR
                subprocess.run([
                    'skopeo', 'copy',
                    '--dest-creds', f'AWS:{subprocess.run(["aws", "ecr", "get-login-password", "--region", self.region], capture_output=True, text=True, check=True).stdout.strip()}',
                    f'docker-daemon:{image_tag}',
                    f'docker://{image_tag}'
                ], check=True, capture_output=True, text=True, timeout=1200)
                logger.info("✅ Image pushed successfully using skopeo")
                return True
            except FileNotFoundError:
                logger.warning("⚠️  skopeo not installed, cannot use alternative method")
                return False
            except Exception as e:
                logger.warning(f"⚠️  skopeo push failed: {e}")
                return False

        # Push image with enhanced retry logic and exponential backoff
        logger.info(f"Pushing image to ECR...")
        max_retries = 5
        base_delay = 5  # Start with 5 seconds

        for attempt in range(max_retries):
            try:
                # Use subprocess.Popen for better control and real-time output
                logger.info(f"Push attempt {attempt + 1}/{max_retries}...")

                process = subprocess.Popen(
                    ['docker', 'push', image_tag],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stdout, stderr = process.communicate(timeout=self.push_timeout)

                if process.returncode == 0:
                    logger.info("✅ Docker image pushed successfully")
                    break
                else:
                    raise subprocess.CalledProcessError(process.returncode, 'docker push', stdout, stderr)

            except subprocess.TimeoutExpired:
                process.kill()
                logger.error(f"❌ Push timed out after 10 minutes")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"⚠️  Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    raise

            except subprocess.CalledProcessError as e:
                if attempt < max_retries - 1:
                    # Check if it's a network error
                    error_msg = e.stderr if e.stderr else str(e)
                    # Common network error indicators
                    network_errors = ['broken pipe', 'connection', 'eof', 'timeout', 'tls', 'reset', 'refused']
                    is_network_error = any(err in error_msg.lower() for err in network_errors)

                    if is_network_error:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"⚠️  Network error detected. Retrying in {delay} seconds...")
                        logger.warning(f"Error details: {error_msg[:200]}")  # Show first 200 chars

                        # Re-authenticate before retry
                        logger.info("Re-authenticating to ECR...")
                        get_password = subprocess.run(
                            ['aws', 'ecr', 'get-login-password', '--region', self.region],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        subprocess.run(
                            ['docker', 'login', '--username', 'AWS', '--password-stdin', ecr_url],
                            input=get_password.stdout,
                            text=True,
                            capture_output=True,
                            check=True
                        )

                        time.sleep(delay)
                    else:
                        logger.error(f"❌ Non-network error: {error_msg}")
                        raise
                else:
                    logger.error(f"❌ Docker push failed after {max_retries} attempts")
                    if e.stderr:
                        logger.error(f"Push errors: {e.stderr}")

                    # Try alternative push method with skopeo
                    logger.info("\n🔄 Trying alternative push method...")
                    if try_skopeo_push():
                        logger.info("✅ Successfully pushed using alternative method")
                        break

                    # If skopeo also fails, try manual layer-by-layer push
                    logger.info("\n🔄 Attempting manual layer upload to ECR...")
                    if self.manual_ecr_push(image_tag, ecr_url):
                        logger.info("✅ Successfully pushed using manual upload")
                        break

                    logger.error("\n💡 Troubleshooting tips:")
                    logger.error("   1. Your network appears to have a proxy (192.168.65.1:3128) causing timeouts")
                    logger.error("   2. Try disabling proxy in Docker Desktop: Settings > Resources > Proxies")
                    logger.error("   3. Increase Docker memory/CPU: Settings > Resources > Advanced")
                    logger.error("   4. Try using a wired connection or different network")
                    logger.error("   5. Check firewall/VPN settings that might interfere")
                    raise

        # If build-only mode, provide instructions for manual push
        if self.build_only:
            logger.info("✅ Docker image built successfully (build-only mode)")
            logger.info("\n📋 Manual push instructions:")
            logger.info(f"   1. The image is built and tagged as: {image_tag}")
            logger.info(f"   2. To push manually, run:")
            logger.info(f"      aws ecr get-login-password --region {self.region} | docker login --username AWS --password-stdin {ecr_url}")
            logger.info(f"      docker push {image_tag}")
            logger.info(f"   3. Or try from a different network/machine with better connectivity")
            logger.info(f"   4. You can also try: python deploy.py --disable-proxy --push-timeout 1800")
            return image_tag

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
    parser.add_argument('--build-only', action='store_true',
                       help='Build image only, skip push (for network issues)')
    parser.add_argument('--push-timeout', type=int, default=600,
                       help='Timeout for each push attempt in seconds (default: 600)')
    parser.add_argument('--disable-proxy', action='store_true',
                       help='Attempt to disable Docker proxy for this push')

    args = parser.parse_args()
    
    deployer = WildfireAgentDeployer(
        agent_name=args.agent_name,
        region=args.region,
        role_name=args.role_name
    )

    deployer.build_only = args.build_only
    deployer.push_timeout = args.push_timeout
    deployer.disable_proxy = args.disable_proxy

    if not args.skip_checks:
        deployer.check_prerequisites()

    deployer.deploy()

if __name__ == "__main__":
    main()
