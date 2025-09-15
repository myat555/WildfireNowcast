"""
DynamoDB table definitions for Wildfire Detection System
"""
import boto3
import os
import logging
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_dynamodb_client():
    """Get DynamoDB client based on environment"""
    aws_region = os.getenv('AWS_REGION', 'us-west-2')
    return boto3.client('dynamodb', region_name=aws_region)

def create_wildfire_incidents_table():
    """Create WildfireIncidents table"""
    dynamodb = get_dynamodb_client()
    
    table_name = 'WildfireIncidents'
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'incident_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'incident_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_date',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'created_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        logger.info(f"Created table {table_name}")
        return response
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            logger.info(f"Table {table_name} already exists")
        else:
            logger.error(f"Error creating table {table_name}: {e}")
            raise

def create_fire_hotspots_table():
    """Create FireHotspots table"""
    dynamodb = get_dynamodb_client()
    
    table_name = 'FireHotspots'
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'hotspot_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'hotspot_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'acq_date',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'confidence',
                    'AttributeType': 'N'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'DateIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'acq_date',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'confidence',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        logger.info(f"Created table {table_name}")
        return response
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            logger.info(f"Table {table_name} already exists")
        else:
            logger.error(f"Error creating table {table_name}: {e}")
            raise

def create_protected_areas_table():
    """Create ProtectedAreas table"""
    dynamodb = get_dynamodb_client()
    
    table_name = 'ProtectedAreas'
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'area_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'area_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'priority',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'name',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'PriorityIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'priority',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'name',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        logger.info(f"Created table {table_name}")
        return response
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            logger.info(f"Table {table_name} already exists")
        else:
            logger.error(f"Error creating table {table_name}: {e}")
            raise

def create_fire_alerts_table():
    """Create FireAlerts table"""
    dynamodb = get_dynamodb_client()
    
    table_name = 'FireAlerts'
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'alert_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'alert_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_date',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'alert_level',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'AlertLevelIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'alert_level',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'created_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        logger.info(f"Created table {table_name}")
        return response
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            logger.info(f"Table {table_name} already exists")
        else:
            logger.error(f"Error creating table {table_name}: {e}")
            raise

def create_all_tables():
    """Create all required DynamoDB tables"""
    logger.info("Creating DynamoDB tables for Wildfire Detection System")
    
    try:
        create_wildfire_incidents_table()
        create_fire_hotspots_table()
        create_protected_areas_table()
        create_fire_alerts_table()
        
        logger.info("All tables created successfully")
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

def wait_for_tables():
    """Wait for all tables to be active"""
    dynamodb = get_dynamodb_client()
    
    tables = [
        'WildfireIncidents',
        'FireHotspots', 
        'ProtectedAreas',
        'FireAlerts'
    ]
    
    for table_name in tables:
        logger.info(f"Waiting for table {table_name} to be active...")
        
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(
            TableName=table_name,
            WaiterConfig={
                'Delay': 2,
                'MaxAttempts': 30
            }
        )
        
        logger.info(f"Table {table_name} is now active")

def delete_all_tables():
    """Delete all tables (for cleanup)"""
    dynamodb = get_dynamodb_client()
    
    tables = [
        'WildfireIncidents',
        'FireHotspots',
        'ProtectedAreas', 
        'FireAlerts'
    ]
    
    for table_name in tables:
        try:
            dynamodb.delete_table(TableName=table_name)
            logger.info(f"Deleted table {table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info(f"Table {table_name} does not exist")
            else:
                logger.error(f"Error deleting table {table_name}: {e}")

if __name__ == "__main__":
    # Create all tables when run directly
    create_all_tables()
    wait_for_tables()
    logger.info("DynamoDB setup complete!")
