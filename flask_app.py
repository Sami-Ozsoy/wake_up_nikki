import os
from flask import Flask, request, jsonify, session, redirect, url_for,render_template
from flask_socketio import SocketIO, emit
import time
import uuid

from utils.helpers import get_llm
from utils.loaders import load_prompt
from vector.vector_store import VectorStore
from utils.formatter import format_llm_response, format_error_response

from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from agents.graph import invoke_graph
 

# Proje kök dizinini bul
project_root = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
           static_folder=os.path.join(project_root, 'assets'), 
           static_url_path='/static',
           template_folder=os.path.join(project_root, 'templates'))
app.config['SECRET_KEY'] = 'niki-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Bellek (session bazlı)
session_memories = {}

# Prompt hazırla
prompt_text = load_prompt("prompts/main_prompt.txt")
prompt = ChatPromptTemplate.from_template(prompt_text)

# LLM ve retriever ayarları
llm = get_llm()
vector_store = VectorStore()

def get_memory(session_id: str) -> ConversationBufferMemory:
    """Session'a bağlı bellek nesnesini döndür (yoksa oluştur)."""
    mem = session_memories.get(session_id)
    if mem is None:
        mem = ConversationBufferMemory(memory_key="history", input_key="question", return_messages=True)
        session_memories[session_id] = mem
    return mem


def get_response(user_input, session_id):
    """Kullanıcı mesajına yanıt ver"""
    try:
        # Geçmişi hazırla
        mem = get_memory(session_id)
        messages = getattr(mem, "chat_memory").messages if hasattr(mem, "chat_memory") else []
        formatted_pairs = []
        for m in messages:
            cls = m.__class__.__name__.lower()
            if hasattr(m, 'content'):
                if 'human' in cls:
                    formatted_pairs.append(f"Kullanıcı: {m.content}")
                elif 'ai' in cls:
                    formatted_pairs.append(f"Asistan: {m.content}")
        history_text = "\n".join(formatted_pairs)

        ai_answer = invoke_graph(user_input, history_text=history_text)

        # Belleğe yazmayı sürdür
        try:
            mem.save_context({"question": user_input}, {"answer": ai_answer})
        except Exception as e:
            print(f"Bellek hatası: {e}")
            pass

        return format_llm_response(ai_answer)
    except Exception as e:
        print(f"Yanıt alma hatası: {e}")
        return format_error_response(str(e))

@app.route('/')
def index():
    sid = session.get('session_id')
    if not sid:
        sid = str(uuid.uuid4())
        session['session_id'] = sid
    return redirect(url_for('chat_page', session_id=sid))

@app.route('/chat/<session_id>')
def chat_page(session_id):
    session['session_id'] = session_id
    return render_template('chat.html', session_id=session_id)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = (data.get('message') or '').strip()
    client_session_id = data.get('session_id')

    # İstek ile session_id geldiyse session'a yaz
    if client_session_id:
        session['session_id'] = client_session_id

    # Session'da yoksa bir kez üret ve kaydet
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    session_id = session['session_id']

    # Bellek hazırla
    _ = get_memory(session_id)

    if not message:
        return jsonify({'error': 'Boş mesaj gönderilemez'})

    try:
        print(f"----->Kullanıcı mesajı: {message}")
        print(f"----->Session ID: {session_id}")
        response = get_response(message, session_id)

        return jsonify({
            'response': response,
            'session_id': session_id,
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({'error': f'Hata oluştu: {str(e)}'})

@app.route('/api/clear', methods=['POST'])
def clear_history():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': True})
    session_memories[session_id] = ConversationBufferMemory(memory_key="history", input_key="question", return_messages=True)
    return jsonify({'success': True})

@app.route('/api/history', methods=['GET'])
def get_history():
    sid = request.args.get('session_id') or session.get('session_id')
    if not sid:
        return jsonify({'messages': [], 'session_id': None})
    mem = get_memory(sid)
    messages = getattr(mem, "chat_memory").messages if hasattr(mem, "chat_memory") else []
    payload = []
    for m in messages:
        cls = m.__class__.__name__.lower()
        role = 'user' if 'human' in cls else 'assistant'
        content = m.content if hasattr(m, 'content') else ''
        payload.append({'role': role, 'content': content})
    return jsonify({'messages': payload, 'session_id': sid})

@socketio.on('connect')
def handle_connect():
    session_id = session.get('session_id') or str(uuid.uuid4())
    session['session_id'] = session_id
    emit('connected', {'session_id': session_id})

@socketio.on('disconnect')
def handle_disconnect():
    session_id = session.get('session_id')
    if session_id and session_id in session_memories:
        del session_memories[session_id]

if __name__ == '__main__':
    print("�� Flask uygulaması başlatılıyor...")
    print("📱 Tarayıcıda http://localhost:5000 adresini açın")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
