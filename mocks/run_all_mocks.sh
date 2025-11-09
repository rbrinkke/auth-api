#!/bin/bash
# Quick start script for running all mock servers locally
# Usage: ./run_all_mocks.sh

set -e

echo "=========================================="
echo "Starting All Mock Servers"
echo "=========================================="
echo ""

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Warning: Port $1 is already in use"
        return 1
    fi
    return 0
}

# Check ports
echo "Checking ports..."
check_port 9000 || echo "  - Email Mock port (9000) in use"
check_port 9001 || echo "  - HIBP Mock port (9001) in use"
check_port 9002 || echo "  - Redis Mock port (9002) in use"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q -r mocks/requirements.txt
echo "✓ Dependencies installed"
echo ""

# Start mock servers in background
echo "Starting mock servers..."

# Email Service Mock
echo "  Starting Email Service Mock (port 9000)..."
python mocks/email_service_mock.py > logs/email_mock.log 2>&1 &
EMAIL_PID=$!
echo "    PID: $EMAIL_PID"

sleep 1

# HIBP API Mock
echo "  Starting HIBP API Mock (port 9001)..."
python mocks/hibp_mock.py > logs/hibp_mock.log 2>&1 &
HIBP_PID=$!
echo "    PID: $HIBP_PID"

sleep 1

# Redis Mock
echo "  Starting Redis Mock (port 9002)..."
python mocks/redis_mock.py > logs/redis_mock.log 2>&1 &
REDIS_PID=$!
echo "    PID: $REDIS_PID"

echo ""
echo "=========================================="
echo "All Mock Servers Started!"
echo "=========================================="
echo ""
echo "Mock Servers:"
echo "  • Email Service: http://localhost:9000/docs"
echo "  • HIBP API:      http://localhost:9001/docs"
echo "  • Redis Mock:    http://localhost:9002/docs"
echo ""
echo "Process IDs:"
echo "  • Email: $EMAIL_PID"
echo "  • HIBP:  $HIBP_PID"
echo "  • Redis: $REDIS_PID"
echo ""
echo "Logs:"
echo "  • Email: logs/email_mock.log"
echo "  • HIBP:  logs/hibp_mock.log"
echo "  • Redis: logs/redis_mock.log"
echo ""
echo "To stop all mocks:"
echo "  kill $EMAIL_PID $HIBP_PID $REDIS_PID"
echo ""
echo "Or use: pkill -f 'python mocks/'"
echo "=========================================="

# Save PIDs to file for easy cleanup
echo "$EMAIL_PID" > logs/mock_pids.txt
echo "$HIBP_PID" >> logs/mock_pids.txt
echo "$REDIS_PID" >> logs/mock_pids.txt

echo ""
echo "PIDs saved to logs/mock_pids.txt"
