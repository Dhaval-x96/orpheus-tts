# Orpheus TTS API Documentation

This API provides endpoints to interact with the Orpheus TTS (Text-to-Speech) model.

## Endpoints

### Health Check
```
GET /health
```
Returns the health status of the API.

### Text to Speech
```
POST /tts
```
Converts text to speech and returns an audio file.

#### Request Body
```json
{
  "text": "Your text to convert to speech",
  "voice": "tara",
  "temperature": 1.0,
  "top_p": 0.9,
  "repetition_penalty": 1.1
}
```

#### Parameters
- `text` (required): The text to convert to speech
- `voice` (optional): The voice to use (default: "tara")
- `temperature` (optional): Controls randomness (default: 1.0)
- `top_p` (optional): Controls diversity (default: 0.9)
- `repetition_penalty` (optional): Prevents repetition (default: 1.1)

#### Response
Returns a WAV audio file.

### Streaming Text to Speech
```
POST /tts/stream
```
Streams audio chunks as they're generated.

#### Request Body
Same as `/tts` endpoint.

#### Response
Streams WAV audio data chunks.

### Available Voices
```
GET /voices
```
Returns a list of available voices.

#### Response
```json
{
  "english": ["tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe"]
}
```

### Available Emotions
```
GET /emotions
```
Returns a list of available emotion tags.

#### Response
```json
["<laugh>", "<chuckle>", "<sigh>", "<cough>", "<sniffle>", "<groan>", "<yawn>", "<gasp>"]
```

## Example Usage

### Using cURL

```bash
# Basic text-to-speech request
curl -X POST http://localhost:5000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test.", "voice": "tara"}' \
  --output tts_output.wav

# Stream audio
curl -X POST http://localhost:5000/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a streaming test.", "voice": "leo"}' \
  --output streaming_output.wav
```

### Using Python

```python
import requests

# Basic text-to-speech request
response = requests.post(
    "http://localhost:5000/tts",
    json={
        "text": "Hello, this is a test.",
        "voice": "tara",
        "temperature": 1.0,
        "repetition_penalty": 1.1
    }
)

# Save the audio file
if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
else:
    print(f"Error: {response.json()}")
```

## Using Emotion Tags

You can include emotion tags in your text:

```json
{
  "text": "This is so funny <laugh> I can't believe it <sigh>",
  "voice": "jess"
}
``` 