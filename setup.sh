#!/bin/bash

# Exit on error
set -e

echo "Setting up Orpheus TTS project..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found. Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install PyTorch first (required for flash_attn)
echo "Installing PyTorch (required for other packages)..."
pip install torch

# Install stable vllm version (needed by orpheus-speech)
echo "Installing stable vllm version..."
pip install vllm==0.7.3

# Install dependencies
echo "Installing orpheus-speech package..."
pip install orpheus-speech

# Install additional packages that might be needed for training/finetuning
echo "Installing additional packages for development..."
pip install transformers datasets wandb trl

# Install Flask and related packages
echo "Installing Flask and related packages..."
pip install flask flask-cors gunicorn

echo ""
echo "Setup complete! You can now use Orpheus TTS."
echo ""
echo "To activate the virtual environment in the future, run:"
echo "source venv/bin/activate"
echo ""
echo "For examples, check the README.md or try the example code." 