#!/bin/bash

# NeuroFinance Startup Script
echo "🚀 Starting NeuroFinance Platform..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Navigate to infrastructure directory
cd infrastructure

# Pull latest images if needed
echo "📦 Pulling Docker images..."
docker-compose pull

# Start services
echo "🔧 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ NeuroFinance Platform is running!"
echo ""
echo "🌐 Access the platform:"
echo "   • Frontend Dashboard: http://localhost:3000"
echo "   • Backend API: http://localhost:8000"
echo "   • API Documentation: http://localhost:8000/docs"
echo ""
echo "📝 View logs with: docker-compose logs -f"
echo "🛑 Stop with: docker-compose down"
echo ""
