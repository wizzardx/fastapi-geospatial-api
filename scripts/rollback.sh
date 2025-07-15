#!/bin/bash
# File: scripts/rollback.sh
# Day 6: Emergency rollback script

set -e

ENVIRONMENT=${1:-production}
TARGET_REVISION=${2}

echo "🔄 Rolling back $ENVIRONMENT environment"

if [ "$ENVIRONMENT" = "production" ]; then
    ECS_CLUSTER="geospatial-cluster"
    ECS_SERVICE="geospatial-api-service"
else
    ECS_CLUSTER="geospatial-staging-cluster"
    ECS_SERVICE="geospatial-api-staging-service"
fi

if [ -z "$TARGET_REVISION" ]; then
    echo "📋 Available task definition revisions:"
    aws ecs list-task-definitions \
        --family-prefix "$ECS_SERVICE-task" \
        --status ACTIVE \
        --sort DESC \
        --query 'taskDefinitionArns' \
        --output table

    echo "Usage: $0 $ENVIRONMENT <revision_number>"
    exit 1
fi

TASK_DEF_ARN="$ECS_SERVICE-task:$TARGET_REVISION"

echo "🔄 Rolling back to task definition: $TASK_DEF_ARN"

aws ecs update-service \
    --cluster "$ECS_CLUSTER" \
    --service "$ECS_SERVICE" \
    --task-definition "$TASK_DEF_ARN"

echo "⏳ Waiting for rollback to complete..."
aws ecs wait services-stable \
    --cluster "$ECS_CLUSTER" \
    --services "$ECS_SERVICE"

echo "✅ Rollback completed!"
