#!/bin/bash

# Deployment script for Wildfire Detection Lambda function

set -e  # Exit on error

# Configuration
FUNCTION_NAME="WildfireDetectionLambda"
RUNTIME="python3.12"
HANDLER="lambda_function.lambda_handler"
ROLE_NAME="WildfireDetectionLambdaRole"
AWS_REGION="us-west-2"
TIMEOUT=300
MEMORY_SIZE=1024

# Function to display section headers
section() {
  echo ""
  echo "=========================================="
  echo "  $1"
  echo "=========================================="
  echo ""
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "AWS credentials not configured. Please run 'aws configure'."
    exit 1
fi

section "Creating IAM Role for Lambda"

# Create IAM role for Lambda if it doesn't exist
ROLE_ARN=""
if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
    echo "IAM role $ROLE_NAME already exists"
    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
else
    echo "Creating IAM role $ROLE_NAME..."
    
    # Create trust policy
    cat > trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

    # Create the role
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file://trust-policy.json \
        --description "Role for Wildfire Detection Lambda function"
    
    # Get the role ARN
    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
    
    # Clean up
    rm trust-policy.json
fi

echo "Role ARN: $ROLE_ARN"

section "Attaching IAM Policies"

# Attach basic Lambda execution policy
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

# Create and attach custom policy for DynamoDB access
POLICY_NAME="WildfireDetectionDynamoDBPolicy"

if ! aws iam get-policy --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/$POLICY_NAME" >/dev/null 2>&1; then
    echo "Creating DynamoDB policy..."
    
    cat > dynamodb-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:BatchGetItem",
                "dynamodb:BatchWriteItem"
            ],
            "Resource": [
                "arn:aws:dynamodb:$AWS_REGION:*:table/WildfireIncidents",
                "arn:aws:dynamodb:$AWS_REGION:*:table/WildfireIncidents/index/*",
                "arn:aws:dynamodb:$AWS_REGION:*:table/FireHotspots",
                "arn:aws:dynamodb:$AWS_REGION:*:table/FireHotspots/index/*",
                "arn:aws:dynamodb:$AWS_REGION:*:table/ProtectedAreas",
                "arn:aws:dynamodb:$AWS_REGION:*:table/ProtectedAreas/index/*",
                "arn:aws:dynamodb:$AWS_REGION:*:table/FireAlerts",
                "arn:aws:dynamodb:$AWS_REGION:*:table/FireAlerts/index/*"
            ]
        }
    ]
}
EOF

    # Create the policy
    POLICY_ARN=$(aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file://dynamodb-policy.json \
        --description "DynamoDB access policy for Wildfire Detection Lambda" \
        --query 'Policy.Arn' --output text)
    
    # Clean up
    rm dynamodb-policy.json
else
    POLICY_ARN="arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/$POLICY_NAME"
    echo "DynamoDB policy already exists"
fi

# Attach the custom policy
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN"

section "Creating DynamoDB Tables"

# Run the DynamoDB setup script
echo "Setting up DynamoDB tables..."
python dynamodb_models.py

section "Preparing Lambda Deployment Package"

# Create deployment directory
DEPLOY_DIR="lambda-deployment"
rm -rf "$DEPLOY_DIR"
mkdir "$DEPLOY_DIR"

# Copy Lambda function code
cp lambda_function.py "$DEPLOY_DIR/"

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt -t "$DEPLOY_DIR/"

# Create deployment package
cd "$DEPLOY_DIR"
zip -r ../wildfire-detection-lambda.zip . -q
cd ..

# Clean up deployment directory
rm -rf "$DEPLOY_DIR"

section "Deploying Lambda Function"

# Wait a bit for IAM role to propagate
echo "Waiting for IAM role to propagate..."
sleep 10

# Check if Lambda function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb://wildfire-detection-lambda.zip \
        --region "$AWS_REGION"
    
    # Update function configuration
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --handler "$HANDLER" \
        --role "$ROLE_ARN" \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY_SIZE" \
        --region "$AWS_REGION"
else
    echo "Creating new Lambda function..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "$HANDLER" \
        --zip-file fileb://wildfire-detection-lambda.zip \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY_SIZE" \
        --region "$AWS_REGION" \
        --description "Wildfire Detection and Threat Assessment Lambda"
fi

# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$AWS_REGION" --query 'Configuration.FunctionArn' --output text)

echo "Lambda ARN: $LAMBDA_ARN"

# Save Lambda ARN to file for use by other scripts
echo "LAMBDA_ARN=$LAMBDA_ARN" > lambda_arn.txt

# Clean up deployment package
rm wildfire-detection-lambda.zip

section "Deployment Complete"

echo "Wildfire Detection Lambda function deployed successfully!"
echo "Function Name: $FUNCTION_NAME"
echo "Function ARN: $LAMBDA_ARN"
echo "Runtime: $RUNTIME"
echo "Handler: $HANDLER"
echo "Timeout: ${TIMEOUT}s"
echo "Memory: ${MEMORY_SIZE}MB"
echo ""
echo "Next steps:"
echo "1. Set up environment variables if needed"
echo "2. Test the function using the AWS Console or CLI"
echo "3. Configure the gateway to use this Lambda function"
