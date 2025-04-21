import os
import io
import wave
import time
import tempfile
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
from ollama_tts import OrpheusOllama, AVAILABLE_VOICES

app = Flask(__name__)
CORS(app)

# Initialize the model (this may take a few moments)
model = None

def load_model():
    global model
    if model is None:
        # Initialize using Ollama integration
        model = OrpheusOllama(
            model_name=os.getenv("ORPHEUS_MODEL_NAME", "orpheus"),
            temperature=float(os.getenv("ORPHEUS_TEMPERATURE", "0.6")),
            top_p=float(os.getenv("ORPHEUS_TOP_P", "0.9")),
            repeat_penalty=float(os.getenv("ORPHEUS_REPEAT_PENALTY", "1.1")),
            sample_rate=int(os.getenv("ORPHEUS_SAMPLE_RATE", "24000"))
        )
    return model

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    try:
        model = load_model()
        connection_status = model.test_connection()
        return jsonify({
            "status": "healthy", 
            "ollama_status": connection_status["status"],
            "message": connection_status["message"]
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech and return an audio file"""
    # Get JSON data from request
    data = request.json
    
    # Validate required parameters
    if not data or 'text' not in data:
        return jsonify({"error": "Missing required parameter: 'text'"}), 400
    
    # Get parameters with defaults
    text = data['text']
    voice = data.get('voice', 'tara')  # Default voice is tara
    
    # Load the model
    try:
        model = load_model()
    except Exception as e:
        return jsonify({"error": f"Error loading model: {str(e)}"}), 500
    
    # Generate speech
    try:
        start_time = time.monotonic()
        
        # Generate speech (non-streaming)
        audio_data = model.generate_speech(
            text=text,
            voice=voice,
            stream=False
        )
        
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name
            temp_file.write(audio_data)
        
        end_time = time.monotonic()
        process_time = end_time - start_time
        
        # Return the audio file
        return send_file(
            temp_filename,
            mimetype='audio/wav',
            as_attachment=True,
            download_name=f"tts_output_{int(time.time())}.wav",
        )
    
    except Exception as e:
        return jsonify({"error": f"Error generating speech: {str(e)}"}), 500
    
    finally:
        # Clean up the temporary file
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.unlink(temp_filename)

@app.route('/tts/stream', methods=['POST'])
def stream_text_to_speech():
    """Stream audio chunks as they're generated"""
    # Get JSON data from request
    data = request.json
    
    # Validate required parameters
    if not data or 'text' not in data:
        return jsonify({"error": "Missing required parameter: 'text'"}), 400
    
    # Get parameters with defaults
    text = data['text']
    voice = data.get('voice', 'tara')
    
    try:
        model = load_model()
        
        def generate():
            # Generate and stream audio chunks
            audio_chunks = model.generate_speech(
                text=text,
                voice=voice,
                stream=True
            )
            
            for chunk in audio_chunks:
                yield chunk
        
        return Response(stream_with_context(generate()), mimetype='audio/wav')
    
    except Exception as e:
        return jsonify({"error": f"Error in streaming: {str(e)}"}), 500

@app.route('/voices', methods=['GET'])
def get_voices():
    """Return list of available voices"""
    # List of available voices
    voices = {
        "english": AVAILABLE_VOICES
    }
    return jsonify(voices)

@app.route('/emotions', methods=['GET'])
def get_emotions():
    """Return list of available emotion tags"""
    # Emotion tags from the documentation
    emotions = ["laugh", "chuckle", "sigh", "cough", "sniffle", "groan", "yawn", "gasp"]
    # Format them as they would be used in prompts
    formatted_emotions = [f"<{emotion}>" for emotion in emotions]
    return jsonify(formatted_emotions)

if __name__ == '__main__':
    # Load model at startup
    load_model()
    # Run the Flask app
    app.run(host=os.getenv("ORPHEUS_HOST", "0.0.0.0"), 
            port=int(os.getenv("ORPHEUS_PORT", "5000")), 
            debug=False) 