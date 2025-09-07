import os
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import json
import time

from config import OPENAI_API_KEY, NEO4J_URI
from utils.helpers import get_llm
from utils.loaders import load_prompt
from vector.vector_store import VectorStore
from utils.formatter import format_llm_response, format_error_response, format_no_info_response

from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage

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

# Prompt hazırla
prompt_text = load_prompt("prompts/main_prompt.txt")
prompt = ChatPromptTemplate.from_template(prompt_text)

# LLM ve retriever ayarları
llm = get_llm()
vector_store = VectorStore()

def format_input_with_vector_context(user_input, session_id):
    """Vector context ile input formatla"""
    try:
        # Her seferinde yeni bir retriever oluştur
        retriever = vector_store.get_retriever(k=8)  # Daha fazla doküman al
        retrieved_docs = retriever.invoke(user_input)
        
        # Debug: Hangi dokümanların alındığını göster
        print(f"----->Retrieved {len(retrieved_docs)} documents for: '{user_input}'")
        for i, doc in enumerate(retrieved_docs):
            print(f"----->Doc {i+1}: {doc.page_content[:100]}...")
        
        docs_content = "\n\n".join([doc.page_content for doc in retrieved_docs])

        chat_history = chat_histories.get(session_id, [])
        chat_context = "\n".join([f"Kullanıcı: {q}\nAsistan: {a}" for q, a in chat_history])

        full_context = f"{docs_content}\n\n{chat_context}\nKullanıcı: {user_input}"
        return {
            "question": user_input,
            "context": full_context
        }
    except Exception as e:
        print(f"Vector context hatası: {e}")
        return {
            "question": user_input,
            "context": f"Kullanıcı: {user_input}"
        }
def format_chat_history(input_data):
    """Chat history ve vector context'i formatla"""
    user_input = input_data["user_input"]
    session_id = input_data["session_id"]
    
    try:
        # Her seferinde yeni bir retriever oluştur
        retriever = vector_store.get_retriever(k=8)
        # Vector context al
        retrieved_docs = retriever.invoke(user_input)
        
        # Debug: Hangi dokümanların alındığını göster
        print(f"----->Chain Retrieved {len(retrieved_docs)} documents for: '{user_input}'")
        for i, doc in enumerate(retrieved_docs):
            print(f"----->Chain Doc {i+1}: {doc.page_content[:100]}...")
            
        docs_content = "\n\n".join([doc.page_content for doc in retrieved_docs])

        # Chat history al
        chat_history = chat_histories.get(session_id, [])
        chat_context = "\n".join([f"Kullanıcı: {q}\nAsistan: {a}" for q, a in chat_history])

        # Tam context oluştur
        full_context = f"{docs_content}\n\n{chat_context}\nKullanıcı: {user_input}"
        
        return {
            "question": user_input,
            "context": full_context
        }
    except Exception as e:
        print(f"Vector context hatası: {e}")
        return {
            "question": user_input,
            "context": f"Kullanıcı: {user_input}"
        }
    
chain = (
    RunnableLambda(format_chat_history)
    | prompt
    | llm
    | StrOutputParser()
)

def get_response(user_input, session_id):
    """Kullanıcı mesajına yanıt ver"""
    try:
        # Context hazırla
        context_data = format_input_with_vector_context(user_input, session_id)
        print(f"----->Context data: {context_data}")
        # Prompt'u formatla
        formatted_prompt = prompt.format(**context_data)
        
        # LLM'den yanıt al
        response = llm.invoke(formatted_prompt)
        
        # Yanıtı al
        response_content = response.content if hasattr(response, 'content') else str(response)
        
        # Yanıtı formatla
        formatted_response = format_llm_response(response_content)
        
        # Eğer yanıt çok kısaysa veya hata içeriyorsa
        if len(formatted_response.strip()) < 50 or "bilgi bulunamadı" in formatted_response.lower():
            return format_no_info_response()
        
        return formatted_response
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
    session_id = session.get('session_id', str(time.time()))
    
    if not session_id in chat_histories:
        chat_histories[session_id] = []
    
    if not message.strip():
        return jsonify({'error': 'Boş mesaj gönderilemez'})
    
    try:
        print(f"----->Kullanıcı mesajı: {message}")
        print(f"----->Session ID: {session_id}")
        response = get_response(message, session_id)
        
        # Geçmişe ekle
        chat_histories[session_id].append((message, response))
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({'error': f'Hata oluştu: {str(e)}'})

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
    print("🚀 Flask uygulaması başlatılıyor...")
    print("📱 Tarayıcıda http://localhost:5000 adresini açın")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 