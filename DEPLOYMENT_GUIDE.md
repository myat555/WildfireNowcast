# Wildfire Early-Warning & Triage Agent - Deployment Guide

## Prerequisites

### AWS Account Setup
1. **AWS Account**: Active AWS account with appropriate permissions
2. **AWS CLI**: Installed and configured with credentials
3. **AWS Region**: Recommended `us-west-2` (Oregon) for NASA data proximity
4. **IAM Permissions**: Administrator access or specific permissions listed below

### Required IAM Permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:*",
                "dynamodb:*",
                "bedrock-agentcore:*",
                "bedrock:*",
                "cognito-idp:*",
                "ses:*",
                "sns:*",
                "iam:PassRole",
                "iam:CreateRole",
                "iam:AttachRolePolicy",
                "logs:*",
                "xray:*"
            ],
            "Resource": "*"
        }
    ]
}
```

### Development Environment
- **Python**: 3.10 or higher
- **pip**: Package installer for Python
- **Git**: Version control system
- **Text Editor**: VS Code, PyCharm, or similar

### External Services (Optional)
- **NASA Earthdata Account**: For enhanced FIRMS API access
- **Slack Workspace**: For Slack notifications
- **Email Domain**: For SES email notifications

## Step-by-Step Deployment

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd wildfire-nowcast-agent

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp env_example.txt .env
```

Edit `.env` with your specific values:

```bash
# AWS Configuration
AWS_REGION=us-west-2
ENDPOINT_URL=https://bedrock-agentcore-control.us-west-2.amazonaws.com

# Cognito Configuration (required)
COGNITO_USERPOOL_ID=your-cognito-userpool-id
COGNITO_APP_CLIENT_ID=your-cognito-app-client-id
COGNITO_DOMAIN=your-cognito-domain.auth.us-west-2.amazoncognito.com
COGNITO_CLIENT_SECRET=your-cognito-client-secret

# IAM Role Configuration
ROLE_ARN=arn:aws:iam::your-account-id:role/WildfireAgentRole

# NASA API Configuration (optional but recommended)
NASA_API_KEY=your-nasa-api-key

# Alert Configuration (optional)
ALERT_EMAIL=alerts@your-organization.com
ALERT_PHONE=+1234567890
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### 3. Create Cognito User Pool

#### Option A: AWS Console (Recommended for beginners)

1. Navigate to AWS Cognito in the console
2. Create a new User Pool:
   - **Pool name**: `wildfire-agent-users`
   - **Sign-in options**: Email
   - **Password policy**: Default
   - **MFA**: Optional
3. Create an App Client:
   - **App client name**: `wildfire-agent-client`
   - **Client secret**: Generate a client secret
   - **Auth flows**: `ALLOW_CLIENT_CREDENTIALS_AUTH`
4. Create a Domain:
   - **Domain prefix**: `your-unique-prefix`
5. Update your `.env` file with the generated values

#### Option B: AWS CLI

```bash
# Create User Pool
aws cognito-idp create-user-pool \
    --pool-name "wildfire-agent-users" \
    --policies PasswordPolicy='{MinimumLength=8,RequireUppercase=false,RequireLowercase=false,RequireNumbers=false,RequireSymbols=false}' \
    --region us-west-2

# Note the UserPoolId from the response and update .env

# Create App Client
aws cognito-idp create-user-pool-client \
    --user-pool-id <YOUR_USER_POOL_ID> \
    --client-name "wildfire-agent-client" \
    --generate-secret \
    --explicit-auth-flows ALLOW_CLIENT_CREDENTIALS_AUTH \
    --region us-west-2

# Note the ClientId and ClientSecret from the response
```

### 4. Create IAM Role

Create an IAM role for the agent:

```bash
# Create trust policy
cat > trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "lambda.amazonaws.com",
                    "bedrock-agentcore.amazonaws.com"
                ]
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Create the role
aws iam create-role \
    --role-name WildfireAgentRole \
    --assume-role-policy-document file://trust-policy.json \
    --description "Role for Wildfire Detection Agent"

# Attach necessary policies
aws iam attach-role-policy \
    --role-name WildfireAgentRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
    --role-name WildfireAgentRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

aws iam attach-role-policy \
    --role-name WildfireAgentRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# Get the role ARN and update .env
aws iam get-role --role-name WildfireAgentRole --query 'Role.Arn' --output text
```

### 5. Deploy the System

#### Automated Deployment (Recommended)

```bash
# Run the master deployment script
chmod +x deploy_all.sh
./deploy_all.sh
```

The script will:
1. Deploy Lambda functions
2. Create DynamoDB tables
3. Set up the Bedrock AgentCore Gateway
4. Deploy the Strands Agent Runtime
5. Configure observability

#### Manual Deployment (Advanced)

If you prefer to deploy components individually:

```bash
# 1. Deploy Lambda Functions
cd wildfire-detection
chmod +x deploy.sh
./deploy.sh
cd ..

# 2. Create Gateway
cd gateway
python create_gateway.py
python wildfire-detection-target.py
python gateway_observability.py
cd ..

# 3. Deploy Agent Runtime
cd agent-runtime
python wildfire_strands_agent_runtime_deploy.py --gateway_id <GATEWAY_ID>
cd ..

# 4. Setup Frontend (Optional)
cd frontend
chmod +x setup_and_run.sh
./setup_and_run.sh
```

### 6. Generate Test Data

Create sample data for testing:

```bash
cd wildfire-detection
python synthetic_data.py
cd ..
```

This creates:
- Sample protected areas (Yellowstone, Yosemite, LA Metro, etc.)
- Test hotspot data
- Sample incidents and alerts

### 7. Test the Deployment

#### Test Lambda Functions
```bash
cd wildfire-detection
python test_lambda.py
cd ..
```

#### Test Agent Runtime
```bash
# Get the gateway URL from deployment output
GATEWAY_URL="https://<GATEWAY_ID>.gateway.bedrock-agentcore.us-west-2.amazonaws.com"

# Test via curl (if you have a bearer token)
curl -X POST "$GATEWAY_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test",
    "method": "tools/call",
    "params": {
      "name": "fetch_firms_hotspots",
      "arguments": {
        "source": "VIIRS",
        "days": 1
      }
    }
  }'
```

#### Test Web Interface
```bash
cd frontend
python main.py
# Open http://localhost:5001 in your browser
```

## Configuration Options

### NASA FIRMS API Access

#### Free Tier (Default)
- No API key required
- Rate limited
- Suitable for testing and small deployments

#### Enhanced Access (Recommended for Production)
1. Register at [NASA Earthdata](https://earthdata.nasa.gov/)
2. Request FIRMS API access
3. Add API key to `.env` file
4. Higher rate limits and priority access

### Notification Setup

#### Email Notifications (AWS SES)
```bash
# Verify your email domain
aws ses verify-domain-identity --domain your-domain.com --region us-west-2

# Verify individual email address (for testing)
aws ses verify-email-identity --email-address alerts@your-domain.com --region us-west-2

# Check verification status
aws ses get-identity-verification-attributes --identities alerts@your-domain.com --region us-west-2
```

#### SMS Notifications (AWS SNS)
```bash
# Set SMS preferences (optional)
aws sns set-sms-attributes \
    --attributes DefaultSMSType=Transactional,DefaultSenderID=WildfireBot \
    --region us-west-2
```

#### Slack Notifications
1. Create a Slack app in your workspace
2. Add Incoming Webhooks feature
3. Create a webhook URL
4. Add the URL to your `.env` file

### Advanced Configuration

#### Custom Protected Areas
Edit `wildfire-detection/synthetic_data.py` to add your specific areas of interest:

```python
protected_areas = [
    {
        'area_id': 'my-custom-area',
        'name': 'My Protected Area',
        'priority': 'HIGH',
        'center_lat': Decimal('40.7128'),
        'center_lon': Decimal('-74.0060'),
        'threat_radius_km': Decimal('15'),
        'polygon': [
            [-74.1, 40.6], [-74.1, 40.8], [-73.9, 40.8], 
            [-73.9, 40.6], [-74.1, 40.6]
        ],
        # ... other fields
    }
]
```

#### Alert Thresholds
Modify `wildfire-detection/alert_processor.py`:

```python
# Adjust these values based on your requirements
self.CRITICAL_CONFIDENCE_THRESHOLD = 85  # 85% confidence
self.HIGH_CONFIDENCE_THRESHOLD = 70      # 70% confidence
self.CRITICAL_DISTANCE_THRESHOLD = 5     # 5km from protected areas
self.HIGH_DISTANCE_THRESHOLD = 15        # 15km from protected areas
```

## Monitoring & Maintenance

### CloudWatch Dashboards

Create a custom dashboard:

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
    --dashboard-name "Wildfire-Detection-System" \
    --dashboard-body file://cloudwatch-dashboard.json \
    --region us-west-2
```

### Log Monitoring

Key log groups to monitor:
- `/aws/lambda/WildfireDetectionLambda`
- `/aws/bedrock-agentcore/wildfire-detection-agent`
- `/aws/lambda/wildfire-alert-processor`

### Alerts and Alarms

Set up CloudWatch alarms:

```bash
# Lambda error rate alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "WildfireAgent-HighErrorRate" \
    --alarm-description "High error rate in wildfire agent" \
    --metric-name "Errors" \
    --namespace "AWS/Lambda" \
    --statistic "Sum" \
    --period 300 \
    --threshold 5 \
    --comparison-operator "GreaterThanThreshold" \
    --dimensions Name=FunctionName,Value=WildfireDetectionLambda \
    --evaluation-periods 2 \
    --alarm-actions "arn:aws:sns:us-west-2:ACCOUNT:wildfire-alerts" \
    --region us-west-2
```

## Troubleshooting

### Common Issues

#### 1. Gateway Creation Fails
```
Error: AccessDeniedException
```
**Solution**: Ensure your IAM role has `bedrock-agentcore:*` permissions

#### 2. Lambda Deployment Fails
```
Error: The role defined for the function cannot be assumed by Lambda
```
**Solution**: Check that the IAM role trust policy includes `lambda.amazonaws.com`

#### 3. Agent Runtime Not Responding
```
Error: Agent is not initialized
```
**Solution**: 
- Check that the gateway is running
- Verify Cognito authentication is configured correctly
- Check CloudWatch logs for detailed errors

#### 4. NASA API Rate Limits
```
Error: Too Many Requests (429)
```
**Solution**:
- Increase polling interval in configuration
- Consider getting a NASA API key for higher limits
- Implement exponential backoff in requests

#### 5. Notification Failures
```
Error: Email delivery failed
```
**Solution**:
- Verify SES domain/email verification
- Check SES sending limits
- Ensure IAM permissions for SES

### Debug Commands

```bash
# Check Lambda function logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/Wildfire" --region us-west-2

# Get recent Lambda errors
aws logs filter-log-events \
    --log-group-name "/aws/lambda/WildfireDetectionLambda" \
    --start-time $(date -d "1 hour ago" +%s)000 \
    --filter-pattern "ERROR" \
    --region us-west-2

# Test DynamoDB connectivity
aws dynamodb list-tables --region us-west-2

# Check gateway status
aws bedrock-agentcore list-gateways --region us-west-2
```

## Security Best Practices

### 1. Least Privilege Access
- Use specific IAM policies instead of `*` permissions
- Regularly audit and rotate access keys
- Enable CloudTrail for audit logging

### 2. Network Security
- Use VPC endpoints for AWS service access
- Implement WAF rules for web interface
- Enable GuardDuty for threat detection

### 3. Data Protection
- Enable encryption at rest for DynamoDB
- Use HTTPS for all API communications
- Implement proper input validation

### 4. Monitoring
- Set up CloudWatch alarms for unusual activity
- Monitor API usage patterns
- Regular security assessments

## Cost Optimization

### 1. Right-sizing Resources
- Monitor Lambda memory usage and adjust
- Use DynamoDB on-demand vs provisioned based on usage
- Implement S3 lifecycle policies for map tiles

### 2. Usage Monitoring
```bash
# Check current month costs
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE \
    --region us-east-1
```

### 3. Reserved Capacity
- Consider DynamoDB reserved capacity for predictable workloads
- Use AWS Savings Plans for consistent compute usage

## Scaling Considerations

### Horizontal Scaling
- Lambda functions auto-scale by default
- DynamoDB auto-scaling based on utilization
- Consider multi-region deployment for global coverage

### Performance Optimization
- Implement DynamoDB DAX for caching
- Use CloudFront for web interface distribution
- Optimize Lambda memory allocation based on profiling

This deployment guide provides comprehensive instructions for setting up the Wildfire Early-Warning & Triage Agent. Follow the steps carefully and refer to the troubleshooting section if you encounter any issues.
