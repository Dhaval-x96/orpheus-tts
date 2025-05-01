#!/bin/bash

# Exit on error
set -e

echo "Setting up Orpheus TTS with Ollama..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Please install Ollama first:"
    echo "Visit https://ollama.ai/download for installation instructions"
    exit 1
fi

# Create Modelfile for Orpheus
echo "Creating Modelfile for Orpheus..."
cat > Modelfile << EOL
FROM orpheus-tts-0.1-finetune-prod

# Set parameters for optimal TTS generation
PARAMETER temperature 0.6
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
EOL

# Create the Ollama model
echo "Creating Orpheus model in Ollama..."
ollama create orpheus -f Modelfile

echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start
echo "Waiting for Ollama to start..."
sleep 5

echo "Pulling the Orpheus model (this may take some time)..."
# Start downloading the model
ollama pull orpheus-tts-0.1-finetune-prod

echo ""
echo "Setup complete! Ollama is running with the Orpheus model."
echo ""
echo "To use the TTS service, start the Flask app with:"
echo "./run_server.sh"
echo ""
echo "Press Ctrl+C to stop Ollama"

# Keep the script running to maintain Ollama service
wait $OLLAMA_PID 