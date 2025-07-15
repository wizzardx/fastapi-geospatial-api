#!/bin/bash
# File: scripts/deploy.sh
# Day 6: Production deployment script

set -e

# Configuration
ENVIRONMENT=${1:-production}
IMAGE_TAG=${2:-latest}
AWS_REGION=${AWS_REGION:-us-east-1}

echo "🚀 Starting deployment to $ENVIRONMENT"

# Validate environment
if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "❌ Invalid environment. Use 'staging' or 'production'"
    exit 1
fi

# Set environment-specific variables
if [ "$ENVIRONMENT" = "production" ]; then
    ECS_CLUSTER="geospatial-cluster"
    ECS_SERVICE="geospatial-api-service"
    ECR_REPOSITORY="geospatial-api"
else
    ECS_CLUSTER="geospatial-staging-cluster"
    ECS_SERVICE="geospatial-api-staging-service"
    ECR_REPOSITORY="geospatial-api-staging"
fi

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "📋 Deployment configuration:"
echo "   Environment: $ENVIRONMENT"
echo "   Cluster: $ECS_CLUSTER"
echo "   Service: $ECS_SERVICE"
echo "   Image: $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"

# Pre-deployment checks
echo "🔍 Running pre-deployment checks..."

# Check if cluster exists
if ! aws ecs describe-clusters --clusters "$ECS_CLUSTER" --query 'clusters[0].status' --output text | grep -q ACTIVE; then
    echo "❌ ECS cluster $ECS_CLUSTER not found or not active"
    exit 1
fi

# Check if service exists
if ! aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" --query 'services[0].status' --output text | grep -q ACTIVE; then
    echo "❌ ECS service $ECS_SERVICE not found or not active"
    exit 1
fi

# Check if image exists in ECR
if ! aws ecr describe-images --repository-name "$ECR_REPOSITORY" --image-ids imageTag="$IMAGE_TAG" > /dev/null 2>&1; then
    echo "❌ Docker image $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG not found in ECR"
    exit 1
fi

echo "✅ Pre-deployment checks passed"

# Get current task definition
echo "📥 Downloading current task definition..."
aws ecs describe-task-definition \
    --task-definition "$ECS_SERVICE-task" \
    --query taskDefinition > current-task-definition.json

# Update image in task definition
echo "🔄 Updating task definition with new image..."
python3 << EOF
import json

with open('current-task-definition.json', 'r') as f:
    task_def = json.load(f)

# Remove fields that aren't needed for registration
for field in ['taskDefinitionArn', 'revision', 'status', 'requiresAttributes', 'placementConstraints', 'compatibilities', 'registeredAt', 'registeredBy']:
    task_def.pop(field, None)

# Update the image
for container in task_def['containerDefinitions']:
    if container['name'] == 'geospatial-api':
        container['image'] = '$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG'

with open('new-task-definition.json', 'w') as f:
    json.dump(task_def, f, indent=2)
EOF

# Register new task definition
echo "📝 Registering new task definition..."
NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://new-task-definition.json \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo "✅ New task definition registered: $NEW_TASK_DEF_ARN"

# Update service
echo "🔄 Updating ECS service..."
aws ecs update-service \
    --cluster "$ECS_CLUSTER" \
    --service "$ECS_SERVICE" \
    --task-definition "$NEW_TASK_DEF_ARN" \
    --force-new-deployment

# Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."
aws ecs wait services-stable \
    --cluster "$ECS_CLUSTER" \
    --services "$ECS_SERVICE"

# Verify deployment
echo "🔍 Verifying deployment..."
RUNNING_COUNT=$(aws ecs describe-services \
    --cluster "$ECS_CLUSTER" \
    --services "$ECS_SERVICE" \
    --query 'services[0].runningCount' \
    --output text)

DESIRED_COUNT=$(aws ecs describe-services \
    --cluster "$ECS_CLUSTER" \
    --services "$ECS_SERVICE" \
    --query 'services[0].desiredCount' \
    --output text)

if [ "$RUNNING_COUNT" = "$DESIRED_COUNT" ]; then
    echo "✅ Deployment successful!"
    echo "   Running tasks: $RUNNING_COUNT/$DESIRED_COUNT"
else
    echo "❌ Deployment may have issues"
    echo "   Running tasks: $RUNNING_COUNT/$DESIRED_COUNT"
    exit 1
fi

# Cleanup
rm -f current-task-definition.json new-task-definition.json

echo "🎉 Deployment to $ENVIRONMENT completed successfully!"
