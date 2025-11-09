#!/bin/bash
# Stop all running mock servers
# Usage: ./stop_all_mocks.sh

set -e

echo "=========================================="
echo "Stopping All Mock Servers"
echo "=========================================="
echo ""

# Check if PID file exists
if [ -f logs/mock_pids.txt ]; then
    echo "Reading PIDs from logs/mock_pids.txt..."
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "  Killing process $pid..."
            kill $pid
        else
            echo "  Process $pid not running"
        fi
    done < logs/mock_pids.txt

    rm logs/mock_pids.txt
    echo "✓ PID file removed"
else
    echo "No PID file found. Attempting to kill by pattern..."
    pkill -f 'python mocks/' && echo "✓ Mock processes killed" || echo "No mock processes found"
fi

echo ""
echo "=========================================="
echo "All Mock Servers Stopped"
echo "=========================================="
