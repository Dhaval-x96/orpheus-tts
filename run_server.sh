#!/bin/bash

# Make sure virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the server with gunicorn
echo "Starting Orpheus TTS API server..."
gunicorn --bind 0.0.0.0:5000 --timeout 300 --workers 1 app:app 