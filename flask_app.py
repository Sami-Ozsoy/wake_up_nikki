import os
# OpenMP duplicate runtime workaround for macOS (FAISS et al.)
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import time

from utils.agents.agent_factory import AgentFactory
from utils.formatter import format_error_response

# Proje kök dizinini bul
project_root = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
           static_folder=os.path.join(project_root, 'assets'), 
           static_url_path='/static',
           template_folder=os.path.join(project_root, 'templates'))
app.config['SECRET_KEY'] = 'niki-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Chat geçmişi (session bazlı)
chat_histories = {}

# Agent factory
agent_factory = AgentFactory()

def get_response(user_input, session_id, agent_type="smol"):
    """Kullanıcı mesajına yanıt ver"""
    try:
        # Agent'ı al
        agent = agent_factory.get_agent(agent_type)
        
        # Bu session'a ait chat geçmişini al
        history = chat_histories.get(session_id, [])
        
        # Agent türüne göre session bilgisini aktar
        if hasattr(agent, 'chat'):
            try:
                # RAGAgent: chat_history parametresi destekleniyor
                response = agent.chat(user_input, chat_history=history)
            except TypeError:
                # SmolAgent: eski imza sadece mesaj olabilir
                try:
                    response = agent.chat(user_input, session_id=session_id)
                except TypeError:
                    # Eski imza: sadece mesaj
                    response = agent.chat(user_input)
        else:
            response = "❌ Agent geçersiz"
        
        return response
    except Exception as e:
        print(f"Yanıt alma hatası: {e}")
        return format_error_response(str(e))

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    agent_type = data.get('agent_type', 'smol')  # Varsayılan SmolAgent
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(time.time())
        session['session_id'] = session_id
    
    if session_id not in chat_histories:
        chat_histories[session_id] = []
    
    if not message.strip():
        return jsonify({'error': 'Boş mesaj gönderilemez'})
    
    try:
        print(f"----->Kullanıcı mesajı: {message}")
        print(f"----->Agent türü: {agent_type}")
        print(f"----->Session ID: {session_id}")
        
        response = get_response(message, session_id, agent_type)
        
        # Geçmişe ekle (biriktir)
        chat_histories[session_id].append((message, response))
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'agent_type': agent_type,
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({'error': f'Hata oluştu: {str(e)}'})

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Mevcut agent'ların listesini döndür"""
    try:
        agents = agent_factory.get_available_agents()
        return jsonify({'agents': agents})
    except Exception as e:
        return jsonify({'error': f'Agent listesi alınamadı: {str(e)}'})

@app.route('/api/clear', methods=['POST'])
def clear_history():
    session_id = session.get('session_id', str(time.time()))
    if session_id in chat_histories:
        chat_histories[session_id] = []
    return jsonify({'success': True})

@app.route('/api/examples', methods=['GET'])
def get_examples():
    examples = [
        "Batarya durumunu nasıl kontrol ederim?",
        "GPRS parametrelerini nasıl ayarlarım?",
        "SMS/arama bildirimlerini nasıl yapılandırırım?",
        "Cihazı uzaktan nasıl yeniden başlatırım?",
        "Araç plakasını nasıl değiştiririm?"
    ]
    return jsonify({'examples': examples})

@socketio.on('connect')
def handle_connect():
    session_id = str(time.time())
    session['session_id'] = session_id
    emit('connected', {'session_id': session_id})

@socketio.on('disconnect')
def handle_disconnect():
    session_id = session.get('session_id')
    if session_id and session_id in chat_histories:
        del chat_histories[session_id]

if __name__ == '__main__':
    print("🤖 Flask uygulaması başlatılıyor...")
    print("📱 Tarayıcıda http://localhost:5000 adresini açın")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
