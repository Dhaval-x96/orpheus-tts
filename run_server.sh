#!/bin/bash

# Make sure virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Get port from environment variable or use default 5000
PORT=${ORPHEUS_PORT:-5000}
echo "Using port: $PORT"

# Check if port is in use and kill the process if needed
echo "Checking if port $PORT is in use..."

# Try multiple methods to check for and kill processes using the port
if command -v lsof &> /dev/null; then
    # If lsof is available
    PIDS=$(lsof -ti :$PORT)
    if [[ ! -z "$PIDS" ]]; then
        echo "Killing processes using port $PORT: $PIDS"
        kill -9 $PIDS
    fi
elif command -v netstat &> /dev/null; then
    # If netstat is available
    PIDS=$(netstat -tulpn 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1)
    if [[ ! -z "$PIDS" ]]; then
        echo "Killing processes using port $PORT: $PIDS"
        for PID in $PIDS; do
            kill -9 $PID 2>/dev/null
        done
    fi
elif command -v ss &> /dev/null; then
    # If ss is available
    PIDS=$(ss -tulpn 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d',' -f2 | cut -d'=' -f2)
    if [[ ! -z "$PIDS" ]]; then
        echo "Killing processes using port $PORT: $PIDS"
        for PID in $PIDS; do
            kill -9 $PID 2>/dev/null
        done
    fi
elif command -v fuser &> /dev/null; then
    # Direct approach with fuser
    echo "Using fuser to kill any process on port $PORT..."
    fuser -k ${PORT}/tcp 2>/dev/null
else
    # Last resort - look for gunicorn/python processes
    echo "No standard tools found. Checking for gunicorn processes..."
    GUNICORN_PIDS=$(ps aux | grep gunicorn | grep "$PORT" | awk '{print $2}')
    if [[ ! -z "$GUNICORN_PIDS" ]]; then
        echo "Killing gunicorn processes: $GUNICORN_PIDS"
        for PID in $GUNICORN_PIDS; do
            kill -9 $PID 2>/dev/null
        done
    fi
fi

# Wait a moment for the port to be freed
sleep 2

# Run the server with gunicorn
echo "Starting Orpheus TTS API server..."
gunicorn --bind 0.0.0.0:$PORT --timeout 300 --workers 1 app:app 