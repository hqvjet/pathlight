#!/bin/bash

# Environment Setup Script for Pathlight Agentic Service

echo "🚀 Setting up Pathlight Agentic Service Environment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your configuration."
else
    echo "✅ .env file already exists."
fi

# Check environment type
if [ "$AWS_LAMBDA_FUNCTION_NAME" ]; then
    echo "🔍 Detected Lambda environment"
    export ENVIRONMENT=lambda
elif [ -f "/.dockerenv" ]; then
    echo "🐳 Detected Docker container environment"
    export ENVIRONMENT=container
else
    echo "💻 Detected local development environment"
    export ENVIRONMENT=local
fi

# Display OpenSearch configuration recommendation
echo ""
echo "📋 OpenSearch Configuration Recommendations:"
echo "============================================="

case "$ENVIRONMENT" in
    "lambda")
        echo "🔧 Lambda Environment:"
        echo "   - OPENSEARCH_ENABLED=true (required for production)"
        echo "   - Ensure OpenSearch is accessible from Lambda VPC"
        echo "   - Configure proper security groups and NACLs"
        ;;
    "local")
        echo "🔧 Local Development:"
        echo "   - OPENSEARCH_ENABLED=false (recommended)"
        echo "   - FORCE_OPENSEARCH_LOCAL=false (unless using VPN/tunnel)"
        echo "   - OpenSearch indexing will be skipped automatically"
        ;;
    "container")
        echo "🔧 Container Environment:"
        echo "   - Configure based on container networking"
        echo "   - Use docker-compose for local OpenSearch if needed"
        ;;
esac

echo ""
echo "🎯 Environment setup complete!"
echo "📖 Edit .env file with your specific configuration before running the service."

# Check if Python dependencies are installed
if [ -f "requirements.txt" ]; then
    echo ""
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed."
fi

echo ""
echo "🚀 Ready to start the service!"
echo "   Local: uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
echo "   Docker: docker-compose up"
