"""
Cleanup script for Wildfire Nowcast Agent

This script removes all AWS resources created during deployment.
"""

import argparse
import boto3
import json
import logging
import os
from pathlib import Path
from bedrock_agentcore.memory import MemoryClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WildfireAgentCleanup:
    """Cleanup utility for the Wildfire Nowcast Agent"""
    
    def __init__(self, region: str, skip_iam: bool = False):
        self.region = region
        self.skip_iam = skip_iam
        
        # Initialize AWS clients
        self.bedrock_client = boto3.client('bedrock-agentcore', region_name=region)
        self.bedrock_control_client = boto3.client('bedrock-agentcore-control', region_name=region)
        self.memory_client = MemoryClient(region_name=region)
        self.ecr_client = boto3.client('ecr', region_name=region)
        self.codebuild_client = boto3.client('codebuild', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.ssm_client = boto3.client('ssm', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        
        # Load deployment info
        self.deployment_info = self._load_deployment_info()
    
    def _load_deployment_info(self):
        """Load deployment information from file"""
        deployment_file = Path('.deployment_info')
        if deployment_file.exists():
            with open(deployment_file, 'r') as f:
                return json.load(f)
        return {}
    
    def cleanup_agentcore_runtime(self):
        """Clean up AgentCore Runtime"""
        # First try to clean up from deployment info
        if self.deployment_info.get('runtime_id'):
            runtime_id = self.deployment_info['runtime_id']
            logger.info(f"Cleaning up AgentCore Runtime from deployment info: {runtime_id}")
            
            try:
                self.bedrock_control_client.delete_agent_runtime(agentRuntimeId=runtime_id)
                logger.info("✅ AgentCore Runtime deleted")
                return
            except Exception as e:
                logger.warning(f"⚠️ Error deleting AgentCore Runtime from deployment info: {e}")
        
        # If not found in deployment info, try to discover and clean up wildfire-related runtimes
        logger.info("No runtime ID in deployment info, searching for wildfire-related runtimes...")
        
        try:
            runtimes = self.bedrock_control_client.list_agent_runtimes()
            wildfire_runtimes = [
                r for r in runtimes.get('agentRuntimes', [])
                if 'wildfire' in r.get('agentRuntimeName', '').lower() or 'nowcast' in r.get('agentRuntimeName', '').lower()
            ]
            
            for runtime in wildfire_runtimes:
                try:
                    runtime_id = runtime['agentRuntimeId']
                    logger.info(f"Cleaning up discovered AgentCore Runtime: {runtime_id}")
                    self.bedrock_control_client.delete_agent_runtime(agentRuntimeId=runtime_id)
                    logger.info(f"✅ AgentCore Runtime deleted: {runtime_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Error deleting discovered AgentCore Runtime {runtime_id}: {e}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Error listing AgentCore Runtimes: {e}")
    
    def cleanup_agentcore_memory(self):
        """Clean up AgentCore Memory instances"""
        logger.info("Cleaning up AgentCore Memory instances...")
        
        try:
            memories = self.memory_client.list_memories()
            # list_memories() returns a list directly, not a dict with 'memories' key
            wildfire_memories = [
                m for m in memories
                if 'WildfireNowcastAgentMultiStrategy' in m.get('id', '')
            ]
            
            for memory in wildfire_memories:
                try:
                    self.memory_client.delete_memory(memory_id=memory['id'])
                    logger.info(f"✅ Memory deleted: {memory['id']}")
                except Exception as e:
                    logger.warning(f"⚠️ Error deleting memory {memory['id']}: {e}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Error listing memories: {e}")
    
    def cleanup_ecr_repository(self):
        """Clean up ECR repository"""
        agent_name = self.deployment_info.get('agent_name', 'wildfire-nowcast-agent')
        logger.info(f"Cleaning up ECR repository: {agent_name}")
        
        try:
            # Delete all images first
            images = self.ecr_client.list_images(repositoryName=agent_name)
            if images.get('imageIds'):
                self.ecr_client.batch_delete_image(
                    repositoryName=agent_name,
                    imageIds=images['imageIds']
                )
                logger.info("✅ ECR images deleted")
            
            # Delete repository
            self.ecr_client.delete_repository(repositoryName=agent_name)
            logger.info("✅ ECR repository deleted")
            
        except Exception as e:
            logger.warning(f"⚠️ Error cleaning up ECR repository: {e}")
    
    def cleanup_codebuild_projects(self):
        """Clean up CodeBuild projects"""
        logger.info("Cleaning up CodeBuild projects...")
        
        try:
            projects = self.codebuild_client.list_projects()
            wildfire_projects = [
                p for p in projects.get('projects', [])
                if 'wildfire' in p.lower() or 'nowcast' in p.lower()
            ]
            
            for project in wildfire_projects:
                try:
                    self.codebuild_client.delete_project(name=project)
                    logger.info(f"✅ CodeBuild project deleted: {project}")
                except Exception as e:
                    logger.warning(f"⚠️ Error deleting CodeBuild project {project}: {e}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Error listing CodeBuild projects: {e}")
    
    def cleanup_s3_artifacts(self):
        """Clean up S3 build artifacts"""
        logger.info("Cleaning up S3 build artifacts...")
        
        try:
            # List buckets and look for wildfire-related artifacts
            buckets = self.s3_client.list_buckets()
            for bucket in buckets.get('Buckets', []):
                bucket_name = bucket['Name']
                if 'wildfire' in bucket_name.lower() or 'nowcast' in bucket_name.lower():
                    try:
                        # Delete all objects
                        objects = self.s3_client.list_objects_v2(Bucket=bucket_name)
                        if objects.get('Contents'):
                            for obj in objects['Contents']:
                                self.s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
                        
                        # Delete bucket
                        self.s3_client.delete_bucket(Bucket=bucket_name)
                        logger.info(f"✅ S3 bucket deleted: {bucket_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error deleting S3 bucket {bucket_name}: {e}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Error listing S3 buckets: {e}")
    
    def cleanup_ssm_parameters(self):
        """Clean up SSM parameters"""
        logger.info("Cleaning up SSM parameters...")
        
        try:
            parameters = self.ssm_client.describe_parameters()
            wildfire_params = [
                p for p in parameters.get('Parameters', [])
                if 'wildfire' in p.get('Name', '').lower() or 'nowcast' in p.get('Name', '').lower()
            ]
            
            for param in wildfire_params:
                try:
                    self.ssm_client.delete_parameter(Name=param['Name'])
                    logger.info(f"✅ SSM parameter deleted: {param['Name']}")
                except Exception as e:
                    logger.warning(f"⚠️ Error deleting SSM parameter {param['Name']}: {e}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Error listing SSM parameters: {e}")
    
    def cleanup_iam_resources(self):
        """Clean up IAM resources"""
        if self.skip_iam:
            logger.info("Skipping IAM cleanup as requested")
            return
        
        role_name = self.deployment_info.get('role_name', 'WildfireNowcastAgentRole')
        logger.info(f"Cleaning up IAM role: {role_name}")
        
        try:
            # Delete role policy
            self.iam_client.delete_role_policy(
                RoleName=role_name,
                PolicyName=f"{role_name}Policy"
            )
            logger.info("✅ IAM role policy deleted")
            
            # Delete role
            self.iam_client.delete_role(RoleName=role_name)
            logger.info("✅ IAM role deleted")
            
        except Exception as e:
            logger.warning(f"⚠️ Error cleaning up IAM role: {e}")
    
    def cleanup_local_files(self):
        """Clean up local deployment files"""
        logger.info("Cleaning up local deployment files...")
        
        files_to_remove = [
            '.deployment_info',
            '.runtime_id',
            '.memory_id',
            '.agent_arn',
            '.bedrock_agentcore.yaml',
            'Dockerfile'
        ]
        
        for file_path in files_to_remove:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"✅ Local file deleted: {file_path}")
            except Exception as e:
                logger.warning(f"⚠️ Error deleting local file {file_path}: {e}")
    
    def cleanup(self, dry_run: bool = False):
        """Perform complete cleanup"""
        if dry_run:
            logger.info("🔍 DRY RUN - No resources will be deleted")
            logger.info("Resources that would be deleted:")
            logger.info("- AgentCore Runtime instances")
            logger.info("- AgentCore Memory instances")
            logger.info("- ECR repositories and images")
            logger.info("- CodeBuild projects")
            logger.info("- S3 build artifacts")
            logger.info("- SSM parameters")
            if not self.skip_iam:
                logger.info("- IAM roles and policies")
            logger.info("- Local deployment files")
            return
        
        logger.info("🧹 Starting cleanup of Wildfire Nowcast Agent resources...")
        
        try:
            # Clean up resources in order
            self.cleanup_agentcore_runtime()
            self.cleanup_agentcore_memory()
            self.cleanup_ecr_repository()
            self.cleanup_codebuild_projects()
            self.cleanup_s3_artifacts()
            self.cleanup_ssm_parameters()
            self.cleanup_iam_resources()
            self.cleanup_local_files()
            
            logger.info("🎉 Cleanup completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Cleanup Wildfire Nowcast Agent')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview what would be deleted without actually deleting')
    parser.add_argument('--skip-iam', action='store_true',
                       help='Skip IAM role cleanup (useful if shared with other projects)')
    
    args = parser.parse_args()
    
    cleanup = WildfireAgentCleanup(
        region=args.region,
        skip_iam=args.skip_iam
    )
    
    cleanup.cleanup(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
