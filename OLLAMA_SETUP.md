# Orpheus TTS with Ollama

This guide explains how to set up and use Orpheus TTS with Ollama as the inference backend.

## Why Use Ollama?

Ollama provides several benefits for running Orpheus TTS:

1. **Better GPU Memory Management**: Ollama automatically handles GPU memory allocation
2. **No Python Dependency Issues**: Ollama runs as a separate service, avoiding conflicts
3. **Better Performance**: Ollama is optimized for inference on consumer GPUs
4. **Simplified Setup**: Just install Ollama and pull the model

## Installation Steps

### 1. Install Ollama

First, install Ollama from [ollama.ai](https://ollama.ai/download).

### 2. Run the Ollama Setup Script

```bash
./setup_ollama.sh
```

This script:
- Creates a custom Modelfile for Orpheus with optimal parameters
- Pulls the Orpheus model
- Starts the Ollama service

### 3. Start the API Server

```bash
./run_server.sh
```

The Flask API server will connect to the Ollama backend automatically.

## Manual Setup (Alternative)

If you prefer to set things up manually:

1. Install Ollama from [ollama.ai](https://ollama.ai/download)

2. Pull the Orpheus model:
   ```bash
   ollama pull orpheus-tts-0.1-finetune-prod
   ```

3. Create a custom model with optimized parameters:
   ```bash
   cat > Modelfile << EOL
   FROM orpheus-tts-0.1-finetune-prod
   PARAMETER temperature 0.6
   PARAMETER top_p 0.9
   PARAMETER repeat_penalty 1.1
   EOL
   
   ollama create orpheus -f Modelfile
   ```

4. Start Ollama:
   ```bash
   ollama serve
   ```

5. Start the Flask API server:
   ```bash
   ./run_server.sh
   ```

## API Usage

The API endpoints are the same as before:

- `POST /tts`: Convert text to speech and return a WAV file
- `POST /tts/stream`: Stream audio chunks for real-time playback
- `GET /voices`: List available voices
- `GET /emotions`: List available emotion tags

### Example cURL Request

```bash
curl -X POST http://localhost:5000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test.", "voice": "tara"}' \
  --output output.wav
```

## Troubleshooting

### Ollama Connection Issues

If you see the error "Failed to connect to Ollama":

1. Make sure Ollama is running:
   ```bash
   ollama serve
   ```

2. Check if the Orpheus model is available:
   ```bash
   ollama list
   ```

3. If not, pull the model:
   ```bash
   ollama pull orpheus-tts-0.1-finetune-prod
   ```

### GPU Memory Issues

Ollama automatically manages GPU memory, but if you experience problems:

1. Check your GPU memory usage:
   ```bash
   nvidia-smi
   ```

2. Restart Ollama to clear GPU memory:
   ```bash
   killall ollama
   ollama serve
   ```

## Environment Variables

You can customize the behavior with these environment variables:

- `ORPHEUS_MODEL_NAME`: Name of the model in Ollama (default: "orpheus")
- `ORPHEUS_TEMPERATURE`: Temperature for generation (default: 0.6)
- `ORPHEUS_TOP_P`: Top-p sampling parameter (default: 0.9)
- `ORPHEUS_REPEAT_PENALTY`: Repetition penalty (default: 1.1)
- `ORPHEUS_SAMPLE_RATE`: Audio sample rate (default: 24000)
- `ORPHEUS_HOST`: API server host (default: "0.0.0.0")
- `ORPHEUS_PORT`: API server port (default: 5000)
- `OLLAMA_API_URL`: URL for Ollama API (default: "http://localhost:11434/api/generate") 