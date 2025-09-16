"""
Memory Tools for Wildfire Nowcast Agent

This module contains memory-related tools for managing wildfire incidents,
tracking historical data, and maintaining persistent memory using AgentCore Memory.
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from strands import tool
from bedrock_agentcore.memory import MemoryClient
from botocore.exceptions import ClientError
import hashlib

logger = logging.getLogger(__name__)

def create_wildfire_memory():
    """Create or retrieve existing AgentCore Memory for the wildfire agent with multiple memory strategies"""
    from bedrock_agentcore.memory.constants import StrategyType
    import boto3
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    memory_name = "WildfireNowcastAgentMultiStrategy"
    client = MemoryClient(region_name=region)
    
    # Use SSM Parameter Store for distributed coordination
    ssm_client = boto3.client('ssm', region_name=region)
    param_name = "/bedrock-agentcore/wildfire-nowcast-agent/memory-id"
    
    # Check SSM Parameter Store for existing memory ID
    try:
        response = ssm_client.get_parameter(Name=param_name)
        saved_memory_id = response['Parameter']['Value']
        
        # Verify this memory still exists and is active
        memories = client.list_memories()
        for memory in memories:
            if (memory.get('id') == saved_memory_id and 
                memory.get('status') == 'ACTIVE'):
                logger.info(f"Using memory ID from SSM: {saved_memory_id}")
                return client, saved_memory_id
        
        # Saved memory doesn't exist or isn't active, remove the parameter
        logger.warning(f"Memory ID {saved_memory_id} from SSM is not active, removing parameter")
        try:
            ssm_client.delete_parameter(Name=param_name)
        except Exception as delete_error:
            logger.warning(f"Could not delete SSM parameter: {delete_error}")
            
    except ssm_client.exceptions.ParameterNotFound:
        logger.info("No memory ID found in SSM Parameter Store")
    except Exception as e:
        logger.warning(f"Error reading memory ID from SSM: {e}")
    
    # Fallback: Check local file for development/testing
    memory_id_file = '.memory_id'
    if os.path.exists(memory_id_file):
        try:
            with open(memory_id_file, 'r') as f:
                saved_memory_id = f.read().strip()
            
            # Verify this memory still exists and is active
            memories = client.list_memories()
            for memory in memories:
                if (memory.get('id') == saved_memory_id and 
                    memory.get('status') == 'ACTIVE'):
                    logger.info(f"Using saved memory ID from local file: {saved_memory_id}")
                    
                    # Save to SSM for future distributed access
                    try:
                        ssm_client.put_parameter(
                            Name=param_name,
                            Value=saved_memory_id,
                            Type='String',
                            Overwrite=True,
                            Description='Memory ID for Wildfire Nowcast Agent'
                        )
                        logger.info("Saved memory ID to SSM Parameter Store")
                    except Exception as ssm_error:
                        logger.warning(f"Could not save to SSM: {ssm_error}")
                    
                    return client, saved_memory_id
            
            # Saved memory doesn't exist or isn't active, remove the file
            logger.warning(f"Saved memory ID {saved_memory_id} is not active, removing file")
            os.remove(memory_id_file)
            
        except Exception as e:
            logger.warning(f"Error reading saved memory ID: {e}")
            if os.path.exists(memory_id_file):
                os.remove(memory_id_file)
    
    # Check if any memory already exists
    logger.info(f"Checking if memory '{memory_name}' already exists...")
    try:
        memories = client.list_memories()
        active_memories = []
        for memory in memories:
            if (memory.get('id', '').startswith(memory_name + '-') and 
                memory.get('status') == 'ACTIVE'):
                active_memories.append(memory)
        
        if active_memories:
            # Use the first active memory and save its ID
            memory_id = active_memories[0]['id']
            logger.info(f"Found existing ACTIVE memory '{memory_name}' with ID: {memory_id}")
            
            # Save the memory ID to SSM Parameter Store
            try:
                ssm_client.put_parameter(
                    Name=param_name,
                    Value=memory_id,
                    Type='String',
                    Overwrite=True,
                    Description='Memory ID for Wildfire Nowcast Agent'
                )
                logger.info("Saved existing memory ID to SSM Parameter Store")
            except Exception as ssm_error:
                logger.warning(f"Could not save to SSM: {ssm_error}")
            
            # Also save to local file for development
            try:
                with open('.memory_id', 'w') as f:
                    f.write(memory_id)
            except Exception as file_error:
                logger.warning(f"Could not save to local file: {file_error}")
            
            return client, memory_id
            
    except Exception as e:
        logger.warning(f"Error checking existing memories: {e}")
    
    # Memory doesn't exist, create it
    logger.info("Creating new AgentCore Memory with multiple memory strategies...")
    
    # Define memory strategies for wildfire agent
    strategies = [
        {
            StrategyType.INCIDENT_TRACKING.value: {
                "name": "IncidentTracking",
                "description": "Tracks active wildfire incidents, asset locations, and threat assessments",
                "namespaces": ["wildfire/incident/{incidentId}/tracking"]
            }
        },
        {
            StrategyType.SEMANTIC.value: {
                "name": "WildfireSemantic",
                "description": "Stores fire behavior patterns, historical data, and response strategies",
                "namespaces": ["wildfire/semantic/{incidentId}/patterns"]
            }
        }
    ]
    
    try:
        memory = client.create_memory_and_wait(
            name=memory_name,
            description="Wildfire Nowcast Agent with multi-strategy memory for incident tracking",
            strategies=strategies,
            event_expiry_days=30,  # Keep incidents for 30 days
            max_wait=300,
            poll_interval=10
        )
        memory_id = memory['id']
        
        # Save the memory ID to SSM Parameter Store
        try:
            ssm_client.put_parameter(
                Name=param_name,
                Value=memory_id,
                Type='String',
                Overwrite=True,
                Description='Memory ID for Wildfire Nowcast Agent'
            )
            logger.info("Saved new memory ID to SSM Parameter Store")
        except Exception as ssm_error:
            logger.warning(f"Could not save to SSM: {ssm_error}")
        
        # Also save to local file for development
        try:
            with open('.memory_id', 'w') as f:
                f.write(memory_id)
        except Exception as file_error:
            logger.warning(f"Could not save to local file: {file_error}")
        
        logger.info(f"Multi-strategy memory created successfully with ID: {memory_id}")
        return client, memory_id
        
    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        raise

def create_memory_tools(memory_client: MemoryClient, memory_id: str, session_id: str, default_actor_id: str):
    """Create memory tools with the provided memory client and configuration"""
    
    @tool
    def track_active_incidents(incident_data: str, actor_id_override: str = None):
        """Track active wildfire incidents in memory
        
        Args:
            incident_data: JSON string containing incident information
            actor_id_override: Specific actor_id to use for tracking
        """
        try:
            current_actor_id = actor_id_override or default_actor_id
            incident_info = json.loads(incident_data)
            
            # Extract incident ID
            incident_id = incident_info.get('incident_id', f"incident_{datetime.now().strftime('%Y%m%d%H%M%S')}")
            
            # Create conversation for memory storage
            conversation = [
                (f"Track wildfire incident: {incident_id}", "USER"),
                (f"Incident {incident_id} tracked successfully. Status: {incident_info.get('status', 'active')}", "ASSISTANT")
            ]
            
            memory_client.create_event(
                memory_id=memory_id,
                actor_id=current_actor_id,
                session_id=session_id,
                messages=conversation
            )
            
            return f"Incident {incident_id} tracked successfully in memory"
            
        except Exception as e:
            logger.error(f"Error tracking incident: {e}")
            return f"Error tracking incident: {e}"
    
    @tool
    def get_incident_history(incident_id: str = None, actor_id_override: str = None):
        """Retrieve historical incident data from memory
        
        Args:
            incident_id: Specific incident ID to retrieve (optional)
            actor_id_override: Specific actor_id to use for retrieval
        """
        try:
            current_actor_id = actor_id_override or default_actor_id
            
            # Get recent events
            events = memory_client.list_events(
                memory_id=memory_id,
                actor_id=current_actor_id,
                session_id=session_id,
                max_results=20
            )
            
            if events:
                # Filter by incident ID if provided
                if incident_id:
                    filtered_events = []
                    for event in events:
                        if 'messages' in event:
                            for message in event['messages']:
                                content = message.get('content', '')
                                if incident_id in content:
                                    filtered_events.append(event)
                                    break
                    events = filtered_events
                
                # Convert events to readable format
                history_parts = []
                for i, event in enumerate(events[-10:], 1):  # Show last 10 events
                    if 'messages' in event:
                        for message in event['messages']:
                            content = message.get('content', '').strip()
                            role = message.get('role', 'unknown')
                            if content:
                                history_parts.append(f"{role.upper()}: {content[:100]}...")
                
                if history_parts:
                    return "Recent incident history:\n" + "\n".join(history_parts)
                else:
                    return "No incident history found"
            else:
                return "No incident history available"
                
        except Exception as e:
            logger.error(f"Error retrieving incident history: {e}")
            return "Unable to retrieve incident history"
    
    @tool
    def update_incident_status(incident_id: str, status_update: str, actor_id_override: str = None):
        """Update incident status and progress in memory
        
        Args:
            incident_id: ID of the incident to update
            status_update: Status update information
            actor_id_override: Specific actor_id to use for update
        """
        try:
            current_actor_id = actor_id_override or default_actor_id
            
            # Create conversation for memory storage
            conversation = [
                (f"Update incident {incident_id} status: {status_update}", "USER"),
                (f"Incident {incident_id} status updated successfully. New status: {status_update}", "ASSISTANT")
            ]
            
            memory_client.create_event(
                memory_id=memory_id,
                actor_id=current_actor_id,
                session_id=session_id,
                messages=conversation
            )
            
            return f"Incident {incident_id} status updated successfully"
            
        except Exception as e:
            logger.error(f"Error updating incident status: {e}")
            return f"Error updating incident status: {e}"
    
    @tool
    def store_threat_assessment(assessment_data: str, incident_id: str, actor_id_override: str = None):
        """Store threat assessment data in memory
        
        Args:
            assessment_data: JSON string containing threat assessment
            incident_id: ID of the incident
            actor_id_override: Specific actor_id to use for storage
        """
        try:
            current_actor_id = actor_id_override or default_actor_id
            assessment_info = json.loads(assessment_data)
            
            # Extract key assessment data
            critical_threats = assessment_info.get('summary', {}).get('critical_threats', 0)
            high_threats = assessment_info.get('summary', {}).get('high_threats', 0)
            total_assessments = assessment_info.get('total_assessments', 0)
            
            # Create conversation for memory storage
            conversation = [
                (f"Store threat assessment for incident {incident_id}", "USER"),
                (f"Threat assessment stored for incident {incident_id}. Critical: {critical_threats}, High: {high_threats}, Total: {total_assessments}", "ASSISTANT")
            ]
            
            memory_client.create_event(
                memory_id=memory_id,
                actor_id=current_actor_id,
                session_id=session_id,
                messages=conversation
            )
            
            return f"Threat assessment stored for incident {incident_id}"
            
        except Exception as e:
            logger.error(f"Error storing threat assessment: {e}")
            return f"Error storing threat assessment: {e}"
    
    @tool
    def retrieve_incident_patterns(incident_id: str = None, actor_id_override: str = None):
        """Retrieve fire behavior patterns and historical data
        
        Args:
            incident_id: Specific incident ID to analyze (optional)
            actor_id_override: Specific actor_id to use for retrieval
        """
        try:
            current_actor_id = actor_id_override or default_actor_id
            
            # Get namespaces for semantic memory
            try:
                strategies = memory_client.get_memory_strategies(memory_id)
                namespaces_dict = {i["type"]: i["namespaces"][0] for i in strategies}
            except Exception as e:
                logger.error(f"Error getting namespaces: {e}")
                return "Unable to retrieve incident patterns"
            
            all_patterns = []
            
            # Retrieve from semantic memory strategy
            for strategy_type, namespace_template in namespaces_dict.items():
                if strategy_type == "SEMANTIC":
                    try:
                        namespace = namespace_template.format(incidentId=incident_id or "general")
                        
                        memories = memory_client.retrieve_memories(
                            memory_id=memory_id,
                            namespace=namespace,
                            query="fire behavior patterns historical data response strategies",
                            top_k=5
                        )
                        
                        for memory in memories:
                            if isinstance(memory, dict):
                                content = memory.get('content', {})
                                if isinstance(content, dict):
                                    text = content.get('text', '').strip()
                                    if text and len(text) > 20:
                                        all_patterns.append(f"[{strategy_type.upper()}] {text}")
                                        
                    except Exception as strategy_error:
                        logger.info(f"No patterns found in {strategy_type} strategy: {strategy_error}")
            
            if all_patterns:
                return "Fire Behavior Patterns:\n" + "\n\n".join(all_patterns)
            else:
                return "No fire behavior patterns found in memory"
                
        except Exception as e:
            logger.error(f"Error retrieving incident patterns: {e}")
            return "Unable to retrieve incident patterns"
    
    @tool
    def store_response_strategy(strategy_data: str, incident_id: str, actor_id_override: str = None):
        """Store response strategy and lessons learned
        
        Args:
            strategy_data: JSON string containing response strategy
            incident_id: ID of the incident
            actor_id_override: Specific actor_id to use for storage
        """
        try:
            current_actor_id = actor_id_override or default_actor_id
            strategy_info = json.loads(strategy_data)
            
            # Extract key strategy data
            strategy_type = strategy_info.get('strategy_type', 'general')
            effectiveness = strategy_info.get('effectiveness', 'unknown')
            lessons_learned = strategy_info.get('lessons_learned', '')
            
            # Create conversation for memory storage
            conversation = [
                (f"Store response strategy for incident {incident_id}: {strategy_type}", "USER"),
                (f"Response strategy stored for incident {incident_id}. Type: {strategy_type}, Effectiveness: {effectiveness}, Lessons: {lessons_learned[:100]}...", "ASSISTANT")
            ]
            
            memory_client.create_event(
                memory_id=memory_id,
                actor_id=current_actor_id,
                session_id=session_id,
                messages=conversation
            )
            
            return f"Response strategy stored for incident {incident_id}"
            
        except Exception as e:
            logger.error(f"Error storing response strategy: {e}")
            return f"Error storing response strategy: {e}"
    
    return [
        track_active_incidents,
        get_incident_history,
        update_incident_status,
        store_threat_assessment,
        retrieve_incident_patterns,
        store_response_strategy
    ]
