#!/bin/bash

# Script to create Cognito User Pool for Wildfire Agent
# Run this script to automatically create the required Cognito resources

set -e

# Configuration
USER_POOL_NAME="wildfire-agent-users"
APP_CLIENT_NAME="wildfire-agent-client"
DOMAIN_PREFIX="wildfire-agent-$(whoami)-$(date +%s)"  # Makes it unique
AWS_REGION="us-east-1"

echo "Creating Cognito User Pool for Wildfire Agent..."
echo "User Pool Name: $USER_POOL_NAME"
echo "Domain Prefix: $DOMAIN_PREFIX"
echo "Region: $AWS_REGION"
echo ""

# Step 1: Create User Pool
echo "Step 1: Creating User Pool..."
USER_POOL_RESPONSE=$(aws cognito-idp create-user-pool \
    --pool-name "$USER_POOL_NAME" \
    --policies '{
        "PasswordPolicy": {
            "MinimumLength": 8,
            "RequireUppercase": false,
            "RequireLowercase": false,
            "RequireNumbers": false,
            "RequireSymbols": false
        }
    }' \
    --auto-verified-attributes email \
    --region "$AWS_REGION")

USER_POOL_ID=$(echo "$USER_POOL_RESPONSE" | jq -r '.UserPool.Id')
echo "✅ User Pool created with ID: $USER_POOL_ID"

# Step 2: Create App Client
echo "Step 2: Creating App Client..."
APP_CLIENT_RESPONSE=$(aws cognito-idp create-user-pool-client \
    --user-pool-id "$USER_POOL_ID" \
    --client-name "$APP_CLIENT_NAME" \
    --generate-secret \
    --explicit-auth-flows ALLOW_CLIENT_CREDENTIALS_AUTH \
    --supported-identity-providers COGNITO \
    --region "$AWS_REGION")

APP_CLIENT_ID=$(echo "$APP_CLIENT_RESPONSE" | jq -r '.UserPoolClient.ClientId')
APP_CLIENT_SECRET=$(echo "$APP_CLIENT_RESPONSE" | jq -r '.UserPoolClient.ClientSecret')
echo "✅ App Client created with ID: $APP_CLIENT_ID"

# Step 3: Create Domain
echo "Step 3: Creating Domain..."
aws cognito-idp create-user-pool-domain \
    --domain "$DOMAIN_PREFIX" \
    --user-pool-id "$USER_POOL_ID" \
    --region "$AWS_REGION"
echo "✅ Domain created: $DOMAIN_PREFIX"

# Step 4: Create User (optional - for testing)
echo "Step 4: Creating test user..."
aws cognito-idp admin-create-user \
    --user-pool-id "$USER_POOL_ID" \
    --username "testuser" \
    --user-attributes Name=email,Value=test@example.com \
    --temporary-password "TempPass123!" \
    --message-action SUPPRESS \
    --region "$AWS_REGION"
echo "✅ Test user created (username: testuser, temp password: TempPass123!)"

echo ""
echo "🎉 Cognito User Pool setup complete!"
echo ""
echo "Add these values to your .env file:"
echo "=================================="
echo "COGNITO_USERPOOL_ID=$USER_POOL_ID"
echo "COGNITO_APP_CLIENT_ID=$APP_CLIENT_ID"
echo "COGNITO_CLIENT_SECRET=$APP_CLIENT_SECRET"
echo "COGNITO_DOMAIN=$DOMAIN_PREFIX.auth.$AWS_REGION.amazoncognito.com"
echo "COGNITO_DISCOVERY_URL=https://$DOMAIN_PREFIX.auth.$AWS_REGION.amazoncognito.com/.well-known/openid-configuration"
echo "COGNITO_AUTH_URL=https://$DOMAIN_PREFIX.auth.$AWS_REGION.amazoncognito.com/oauth2/authorize"
echo "COGNITO_TOKEN_URL=https://$DOMAIN_PREFIX.auth.$AWS_REGION.amazoncognito.com/oauth2/token"
echo "COGNITO_PROVIDER_NAME=$DOMAIN_PREFIX"
echo ""
echo "Test user credentials:"
echo "- Username: testuser"
echo "- Temporary Password: TempPass123!"
echo "- Email: test@example.com"
echo ""
echo "Next steps:"
echo "1. Copy the above values to your .env file"
echo "2. Run your deployment script"
echo "3. Test the authentication flow"
