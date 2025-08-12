#!/bin/bash

# DNA Research Platform - Development Startup Script
# This script starts the platform in development mode

set -e

echo "🧬 Starting DNA Research Platform in Development Mode..."

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker/docker-compose.yml down --remove-orphans

# Build and start development containers
echo "🏗️ Building development containers..."
docker-compose -f docker/docker-compose.yml build

echo "🚀 Starting development services..."
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 15

# Check if services are running
echo "🔍 Checking service status..."
docker-compose -f docker/docker-compose.yml ps

echo ""
echo "🎉 DNA Research Platform is now running in development mode!"
echo ""
echo "📊 Service URLs:"
echo "   Portal:    http://localhost:8080"
echo "   API:       http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   MinIO:     http://localhost:9001 (admin: minioadmin/minioadmin123)"
echo "   PostgreSQL: localhost:5432 (user: dev_user, password: dev_password, db: dnaresearch_dev)"
echo "   Redis:     localhost:6379"
echo ""
echo "📋 Useful commands:"
echo "   View logs:     docker-compose -f docker/docker-compose.yml logs -f"
echo "   Stop services: docker-compose -f docker/docker-compose.yml down"
echo "   Restart:       ./scripts/start-development.sh"
echo ""
echo "🔧 Development features enabled:"
echo "   - Hot reloading"
echo "   - Debug mode"
echo "   - Detailed error messages"