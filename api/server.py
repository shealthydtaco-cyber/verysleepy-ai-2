"""
Flask API server for verysleepy-ai
Exposes backend functionality as REST endpoints for Electron/React frontend
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging
import sys
import json
from pathlib import Path

# Add parent directory to path to import verysleepy modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import backend modules
try:
    from control.phi3_controller import Phi3Controller
    from utils.config import load_config
    BACKEND_AVAILABLE = True
except Exception as e:
    print(f"Warning: Backend modules not fully available: {e}")
    BACKEND_AVAILABLE = False

# Setup Flask
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_server")

# Initialize backend if available
try:
    if BACKEND_AVAILABLE:
        controller = Phi3Controller()
        logger.info("✓ Phi3Controller initialized successfully")
except Exception as e:
    logger.warning(f"Could not initialize controller: {e}")
    controller = None


# ========== HEALTH ENDPOINT ==========

@app.route('/api/health', methods=['GET'])
def health():
    """Check if server is running and backend status"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'backend': 'verysleepy-ai',
        'controller_available': controller is not None
    })


# ========== CHAT ENDPOINTS ==========

@app.route('/api/chat', methods=['POST'])
def chat():
    """Send message to backend and get response"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        logger.info(f"Chat request: {user_message}")
        
        # Call the actual controller if available
        if controller:
            try:
                # Classify the message to determine what to do with it
                classification = controller.classify(user_message)
                
                # Generate response using the LLM client
                response_text = controller.client.generate(
                    model="phi3:mini",
                    prompt=f"User: {user_message}\n\nAssistant:",
                    temperature=0.7,
                    max_tokens=256
                )
                
                # Extract control metadata from classification
                control_info = {
                    'mode': classification.get('mode', 'UNKNOWN'),
                    'intent': classification.get('intent', 'unknown'),
                    'web_required': classification.get('web_required', False),
                    'explicitness': classification.get('explicitness', 'implicit')
                }
                
                return jsonify({
                    'message': response_text.strip(),
                    'control': control_info,
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                })
            except Exception as e:
                logger.error(f"Controller/LLM error: {e}")
                # Fallback response if backend fails
                return jsonify({
                    'message': f"I encountered an error processing your request: {str(e)}. Please try again.",
                    'control': {'mode': 'ERROR', 'intent': 'error'},
                    'timestamp': datetime.now().isoformat(),
                    'success': False
                })
        else:
            logger.warning("Controller not available, using echo response")
            return jsonify({
                'message': f"Echo (backend offline): {user_message}",
                'timestamp': datetime.now().isoformat(),
                'success': True
            })
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


# ========== VOICE ENDPOINTS ==========

@app.route('/api/voice/listen', methods=['POST'])
def voice_listen():
    """Transcribe audio to text using backend STT"""
    try:
        # Get audio data from request
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        if controller:
            try:
                # Use backend's voice manager for transcription
                from voice.manager import VoiceManager
                voice_manager = controller.voice_manager if hasattr(controller, 'voice_manager') else None
                
                if voice_manager and hasattr(voice_manager, 'transcribe'):
                    transcript = voice_manager.transcribe(audio_file.read())
                else:
                    transcript = "[STT not available - using placeholder]"
            except Exception as e:
                logger.warning(f"STT error: {e}")
                transcript = "[Voice transcription unavailable]"
        else:
            transcript = "[Voice transcription unavailable - backend offline]"
        
        return jsonify({
            'transcript': transcript,
            'timestamp': datetime.now().isoformat(),
            'success': True
        })
    
    except Exception as e:
        logger.error(f"Voice listen error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/voice/speak', methods=['POST'])
def voice_speak():
    """Generate speech from text using backend TTS"""
    try:
        data = request.json
        text = data.get('text', '').strip()
        voice = data.get('voice', 'default')
        
        if not text:
            return jsonify({'error': 'Empty text'}), 400
        
        logger.info(f"TTS request: {text} (voice: {voice})")
        
        if controller:
            try:
                # Use backend's voice manager for TTS
                voice_manager = controller.voice_manager if hasattr(controller, 'voice_manager') else None
                
                if voice_manager and hasattr(voice_manager, 'synthesize'):
                    audio_data = voice_manager.synthesize(text, voice)
                else:
                    logger.warning("TTS not available in voice manager")
                    audio_data = b''
            except Exception as e:
                logger.warning(f"TTS error: {e}")
                audio_data = b''
        else:
            logger.warning("Backend offline for TTS")
            audio_data = b''
        
        return app.response_class(
            response=audio_data,
            mimetype='audio/wav',
            headers={'Content-Disposition': 'attachment; filename=speech.wav'}
        )
    
    except Exception as e:
        logger.error(f"Voice speak error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/voice/voices', methods=['GET'])
def voice_list():
    """List available voices"""
    try:
        # Get voices from backend if available
        if controller:
            try:
                voice_manager = controller.voice_manager if hasattr(controller, 'voice_manager') else None
                if voice_manager and hasattr(voice_manager, 'get_available_voices'):
                    voices = voice_manager.get_available_voices()
                else:
                    voices = ['Amy', 'Maya', 'David', 'Sam']
            except Exception as e:
                logger.warning(f"Could not get voices from backend: {e}")
                voices = ['Amy', 'Maya', 'David', 'Sam']
        else:
            voices = ['Amy', 'Maya', 'David', 'Sam']
        
        return jsonify({
            'voices': voices,
            'default': 'Amy',
            'success': True
        })
    except Exception as e:
        logger.error(f"Voice list error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


# ========== MEMORY ENDPOINTS ==========

@app.route('/api/memory/preferences', methods=['GET'])
def memory_preferences():
    """Get stored user preferences"""
    try:
        if controller:
            try:
                # Try to get preferences from memory manager
                memory_manager = controller.memory_manager if hasattr(controller, 'memory_manager') else None
                if memory_manager and hasattr(memory_manager, 'get_preferences'):
                    preferences = memory_manager.get_preferences()
                else:
                    preferences = {}
            except Exception as e:
                logger.warning(f"Could not retrieve preferences: {e}")
                preferences = {}
        else:
            # Load from config file as fallback
            try:
                config = load_config()
                preferences = config.get('preferences', {})
            except:
                preferences = {}
        
        return jsonify({
            'preferences': preferences,
            'success': True
        })
    except Exception as e:
        logger.error(f"Preferences error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/memory/habits', methods=['GET'])
def memory_habits():
    """Get user habits"""
    try:
        if controller:
            try:
                memory_manager = controller.memory_manager if hasattr(controller, 'memory_manager') else None
                if memory_manager and hasattr(memory_manager, 'get_habits'):
                    habits = memory_manager.get_habits()
                else:
                    habits = []
            except Exception as e:
                logger.warning(f"Could not retrieve habits: {e}")
                habits = []
        else:
            habits = []
        
        return jsonify({
            'habits': habits,
            'success': True
        })
    except Exception as e:
        logger.error(f"Habits error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/memory/conversation', methods=['GET'])
def memory_conversation():
    """Get recent conversation history"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        if controller:
            try:
                memory_manager = controller.memory_manager if hasattr(controller, 'memory_manager') else None
                if memory_manager and hasattr(memory_manager, 'get_recent_conversation'):
                    conversation = memory_manager.get_recent_conversation(limit)
                else:
                    conversation = []
            except Exception as e:
                logger.warning(f"Could not retrieve conversation: {e}")
                conversation = []
        else:
            conversation = []
        
        return jsonify({
            'conversation': conversation,
            'count': len(conversation),
            'success': True
        })
    except Exception as e:
        logger.error(f"Conversation error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/memory/clear', methods=['POST'])
def memory_clear():
    """Clear memory of a specific type"""
    try:
        data = request.json
        memory_type = data.get('type', 'conversation')  # 'conversation', 'preferences', 'habits', or 'all'
        
        logger.info(f"Clearing memory: {memory_type}")
        
        if controller:
            try:
                memory_manager = controller.memory_manager if hasattr(controller, 'memory_manager') else None
                if memory_manager and hasattr(memory_manager, 'clear'):
                    success = memory_manager.clear(memory_type)
                else:
                    logger.warning(f"Memory manager does not support clear()")
                    success = False
            except Exception as e:
                logger.error(f"Could not clear memory: {e}")
                success = False
        else:
            success = False
        
        return jsonify({
            'success': success,
            'type': memory_type,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Memory clear error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


# ========== SETTINGS ENDPOINTS ==========

@app.route('/api/settings', methods=['GET'])
def settings_get():
    """Get current settings"""
    try:
        if BACKEND_AVAILABLE:
            config = load_config()
            settings = {
                'theme': config.get('theme', 'dark'),
                'voice_enabled': config.get('voice_enabled', True),
                'notifications': config.get('notifications', True),
                'language': config.get('language', 'en'),
                'tts_speed': config.get('tts_speed', 1.0),
                'auto_save': config.get('auto_save', True)
            }
        else:
            settings = {
                'theme': 'dark',
                'voice_enabled': True,
                'notifications': True,
                'language': 'en',
                'tts_speed': 1.0,
                'auto_save': True
            }
        
        return jsonify({
            'settings': settings,
            'success': True
        })
    except Exception as e:
        logger.error(f"Settings GET error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/settings', methods=['POST'])
def settings_update():
    """Update settings"""
    try:
        data = request.json
        
        logger.info(f"Updating settings: {list(data.keys())}")
        
        # In a real implementation, this would persist to config.yaml
        # For now, just echo back the settings
        
        return jsonify({
            'settings': data,
            'success': True,
            'message': 'Settings updated (persistence not yet implemented)',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Settings POST error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found', 'success': False}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error', 'success': False}), 500


# ========== MAIN ==========

if __name__ == '__main__':
    logger.info("Starting verysleepy-ai Flask API server...")
    logger.info(f"Backend available: {BACKEND_AVAILABLE}")
    app.run(debug=False, host='127.0.0.1', port=5000)
