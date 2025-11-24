#!/bin/bash
# Simple test runner script for Django backend

echo "🚀 Django Backend Test Suite"
echo "============================"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Run this script from the backend directory."
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating your virtual environment first"
fi

echo ""
echo "1️⃣  Quick Setup Test"
echo "-------------------"
python quick_test.py

echo ""
echo "2️⃣  Starting Django Server (in background)"
echo "----------------------------------------"

# Check if server is already running
if curl -s http://localhost:8000/api/ > /dev/null 2>&1; then
    echo "✅ Django server is already running"
    SERVER_RUNNING=true
else
    echo "🔄 Starting Django development server..."
    python manage.py runserver > server.log 2>&1 &
    SERVER_PID=$!
    SERVER_RUNNING=false
    
    # Wait for server to start
    echo "⏳ Waiting for server to start..."
    for i in {1..10}; do
        if curl -s http://localhost:8000/api/ > /dev/null 2>&1; then
            echo "✅ Server started successfully"
            SERVER_RUNNING=true
            break
        fi
        sleep 2
        echo "   Attempt $i/10..."
    done
    
    if [ "$SERVER_RUNNING" = false ]; then
        echo "❌ Server failed to start. Check server.log for details."
        exit 1
    fi
fi

echo ""
echo "3️⃣  API Request Tests"
echo "-------------------"
python test_api_requests.py

echo ""
echo "4️⃣  Full Backend Tests"
echo "--------------------"
python test_backend.py

# Cleanup
if [ ! -z "$SERVER_PID" ]; then
    echo ""
    echo "🧹 Cleaning up..."
    kill $SERVER_PID 2>/dev/null
    echo "✅ Test server stopped"
fi

echo ""
echo "🎉 Test suite completed!"
echo ""
echo "Next steps:"
echo "1. Create superuser: python manage.py createsuperuser"
echo "2. Import test data: python manage.py import_case ../test_comprehensive_artifacts.json"
echo "3. Start server: python manage.py runserver"
echo "4. Visit: http://localhost:8000/admin/"