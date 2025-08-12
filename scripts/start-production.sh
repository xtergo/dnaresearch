#!/bin/bash

# DNA Research Platform - Production Startup Script
# This script starts the platform in production mode with proper configuration

set -e

echo "🧬 Starting DNA Research Platform in Production Mode..."

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "❌ Error: .env.prod file not found!"
    echo "Please copy .env.prod.template to .env.prod and configure your production settings."
    exit 1
fi

# Load environment variables
export $(cat .env.prod | grep -v '^#' | xargs)

# Validate required environment variables
required_vars=("POSTGRES_PASSWORD" "API_SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set in .env.prod"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# Create necessary directories
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/minio

echo "✅ Directories created"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker/docker-compose.prod.yml down --remove-orphans

# Build and start production containers
echo "🏗️ Building production containers..."
docker-compose -f docker/docker-compose.prod.yml build --no-cache

echo "🚀 Starting production services..."
docker-compose -f docker/docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
services=("postgres" "redis" "minio" "api" "portal")
for service in "${services[@]}"; do
    echo "Checking $service..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose -f docker/docker-compose.prod.yml ps $service | grep -q "healthy\|Up"; then
            echo "✅ $service is healthy"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        echo "❌ $service failed to start properly"
        docker-compose -f docker/docker-compose.prod.yml logs $service
        exit 1
    fi
done

echo ""
echo "🎉 DNA Research Platform is now running in production mode!"
echo ""
echo "📊 Service URLs:"
echo "   Portal:    http://localhost:8080"
echo "   API:       http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   MinIO:     http://localhost:9001 (admin: minioadmin/minioadmin123)"
echo ""
echo "📋 Useful commands:"
echo "   View logs:     docker-compose -f docker/docker-compose.prod.yml logs -f"
echo "   Stop services: docker-compose -f docker/docker-compose.prod.yml down"
echo "   Restart:       ./scripts/start-production.sh"
echo ""
echo "🔍 Monitor the services:"
echo "   docker-compose -f docker/docker-compose.prod.yml ps"