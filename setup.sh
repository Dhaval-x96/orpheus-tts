#!/bin/bash

# Exit on error
set -e

echo "Setting up Orpheus TTS project..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found. Please install Python 3 and try again."
    exit 1
fi

# Install system dependencies if not present
echo "Checking system dependencies..."

# Function to check and install packages
install_if_missing() {
    local package=$1
    local command=${2:-$1}
    
    if ! command -v $command &> /dev/null; then
        echo "Installing $package..."
        apt-get update -qq && apt-get install -y $package || {
            echo "Warning: Could not install $package. Some features may not work properly."
        }
    else
        echo "$package is already installed."
    fi
}

# Check for port tools (used in run_server.sh)
if [[ "$EUID" -eq 0 ]]; then  # Only attempt if running as root
    install_if_missing lsof
    install_if_missing net-tools netstat
    install_if_missing iproute2 ss
    install_if_missing psmisc fuser
else
    echo "Not running as root. Skipping system package installation."
    echo "Some dependencies may need to be installed manually if not present."
fi

# Check if virtual environment already exists
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Using existing environment."
else
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if pip is already up to date
pip_version=$(pip --version | awk '{print $2}')
latest_pip=$(pip index versions pip 2>/dev/null | grep -oP '(?<=pip )([0-9.]+)' | head -1)

if [[ "$pip_version" == "$latest_pip" ]]; then
    echo "Pip is already at the latest version $pip_version."
else
    echo "Upgrading pip from $pip_version..."
    pip install --upgrade pip
fi

# Install PyTorch if not already installed
if python -c "import torch" &>/dev/null; then
    echo "PyTorch is already installed."
else
    echo "Installing PyTorch (required for other packages)..."
    pip install torch
fi

# Check for vllm installation
if python -c "import vllm" 2>/dev/null; then
    installed_vllm=$(pip freeze | grep -i vllm | cut -d'=' -f3)
    if [[ "$installed_vllm" == "0.7.3" ]]; then
        echo "vllm version 0.7.3 is already installed."
    else
        echo "Upgrading vllm to version 0.7.3..."
        pip install vllm==0.7.3
    fi
else
    echo "Installing vllm version 0.7.3..."
    pip install vllm==0.7.3
fi

# Install orpheus-speech if not already installed
if python -c "from orpheus_tts import OrpheusModel" 2>/dev/null; then
    echo "orpheus-speech is already installed."
else
    echo "Installing orpheus-speech package..."
    pip install orpheus-speech
fi

# Check and install additional packages
echo "Checking additional development packages..."
missing_packages=()

for pkg in transformers datasets wandb trl; do
    if ! python -c "import $pkg" 2>/dev/null; then
        missing_packages+=($pkg)
    fi
done

if [ ${#missing_packages[@]} -ne 0 ]; then
    echo "Installing missing development packages: ${missing_packages[*]}"
    pip install ${missing_packages[*]}
else
    echo "All development packages are already installed."
fi

# Check and install Flask and related packages
flask_missing=false
for pkg in flask flask_cors gunicorn; do
    if ! python -c "import $pkg" 2>/dev/null; then
        flask_missing=true
        break
    fi
done

if [ "$flask_missing" = true ]; then
    echo "Installing Flask and related packages..."
    pip install flask flask-cors gunicorn
else
    echo "Flask and related packages are already installed."
fi

echo ""
echo "Setup complete! You can now use Orpheus TTS."
echo ""
echo "To activate the virtual environment in the future, run:"
echo "source venv/bin/activate"
echo ""
echo "For examples, check the README.md or try the example code." 