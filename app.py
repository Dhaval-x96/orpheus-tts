import os
import io
import wave
import time
import tempfile
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
from orpheus_tts import OrpheusModel

app = Flask(__name__)
CORS(app)

# Initialize the model (this may take a few moments)
model = None

def load_model():
    global model
    if model is None:
        # Default to the finetuned model, but could be configurable
        model = OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod")
    return model

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

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
    
    # Optional LLM generation parameters
    temperature = data.get('temperature', 1.0)
    top_p = data.get('top_p', 0.9)
    repetition_penalty = data.get('repetition_penalty', 1.1)  # Required for stable generations
    
    # Load the model
    try:
        model = load_model()
    except Exception as e:
        return jsonify({"error": f"Error loading model: {str(e)}"}), 500
    
    # Generate speech
    try:
        start_time = time.monotonic()
        
        # Generate speech from text
        syn_tokens = model.generate_speech(
            prompt=text,
            voice=voice,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=repetition_penalty
        )
        
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name
            
            # Write the audio to the WAV file
            with wave.open(temp_filename, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                
                # Combine all audio chunks
                audio_data = bytearray()
                for audio_chunk in syn_tokens:
                    audio_data.extend(audio_chunk)
                
                # Write to file
                wf.writeframes(audio_data)
        
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
    
    # Optional LLM generation parameters
    temperature = data.get('temperature', 1.0)
    top_p = data.get('top_p', 0.9)
    repetition_penalty = data.get('repetition_penalty', 1.1)
    
    try:
        model = load_model()
        
        def generate():
            # Start WAV header
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(b'')  # Write empty frames to create header
            
            header = buffer.getvalue()
            yield header  # Send WAV header first
            
            # Generate speech chunks and stream them
            syn_tokens = model.generate_speech(
                prompt=text,
                voice=voice,
                temperature=temperature,
                top_p=top_p,
                repetition_penalty=repetition_penalty
            )
            
            for audio_chunk in syn_tokens:
                yield audio_chunk
        
        return Response(stream_with_context(generate()), mimetype='audio/wav')
    
    except Exception as e:
        return jsonify({"error": f"Error in streaming: {str(e)}"}), 500

@app.route('/voices', methods=['GET'])
def get_voices():
    """Return list of available voices"""
    # List of available voices from the documentation
    voices = {
        "english": ["tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe"],
        # Could add multilingual voices here when using those models
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
    app.run(host='0.0.0.0', port=5000, debug=False) 