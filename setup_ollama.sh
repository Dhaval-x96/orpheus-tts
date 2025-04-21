#!/bin/bash

# Exit on error
set -e

echo "Setting up Orpheus TTS with Ollama..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Installing it now..."
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Check if installation was successful
    if ! command -v ollama &> /dev/null; then
        echo "Failed to install Ollama. Please install it manually:"
        echo "Visit https://ollama.ai/download for installation instructions"
        exit 1
    else
        echo "Ollama installed successfully!"
    fi
else
    echo "Ollama is already installed."
fi

# Check for GPU detection tools
if ! command -v lspci &> /dev/null || ! command -v lshw &> /dev/null; then
    echo "Installing GPU detection tools..."
    apt-get update && apt-get install -y pciutils lshw || {
        echo "Warning: Could not install GPU detection tools. GPU might not be detected properly."
    }
fi

# Start Ollama service
echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start
echo "Waiting for Ollama to start..."
sleep 5

# Test GPU detection
echo "Checking GPU availability for Ollama..."
if nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected and accessible."
else
    echo "Warning: NVIDIA GPU not detected or not accessible."
    echo "Ollama will run in CPU mode, which will be very slow for TTS."
    echo "Ensure your container has GPU access with --gpus all flag."
fi

echo ""
echo "Setup complete! Ollama is running without any models."
echo ""
echo "To download the Orpheus model, you can run:"
echo "ollama pull orpheus-tts-0.1-finetune-prod"
echo ""
echo "To use the TTS service, start the Flask app with:"
echo "./run_server.sh"
echo ""
echo "Press Ctrl+C to stop Ollama"

# Keep the script running to maintain Ollama service
wait $OLLAMA_PID 